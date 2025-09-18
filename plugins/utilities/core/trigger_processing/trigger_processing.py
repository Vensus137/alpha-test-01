import re
from typing import Any, Dict, Optional, List


class TriggerProcessing:
    """
    Сервис для обработки триггеров (поиск сценария по событию или кнопке).
    Использует settings_manager для доступа к триггерам и сценариям.
    Включает проверку состояний пользователей с ленивой очисткой.
    Поддерживает универсальные обработчики и множественные триггеры.
    """
    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.settings_manager = kwargs['settings_manager']
        self.scenarios_manager = kwargs['scenarios_manager']
        self.tg_button_mapper = kwargs['tg_button_mapper']
        self.database_service = kwargs['database_service']
        self.datetime_formatter = kwargs['datetime_formatter']
        self.tg_api_utils = kwargs['tg_api_utils']

    def _get_triggers_for_event(self, event: dict) -> dict:
        """
        Возвращает набор триггеров из единого файла triggers.yaml.
        Фильтрация по типам чатов теперь происходит через атрибут from_chat.
        """
        return self.scenarios_manager.get_triggers()

    def _parse_trigger_value(self, value, context: str = "text") -> list:
        """
        Парсит значение триггера, поддерживая старый и множественный формат.
        Старый формат: "/start": "command.start"
        Множественный формат: "/test": [{"scenario": "s1", "from_chat": [100]}, {"scenario": "s2", "from_chat": [200]}]
        context: "text", "callback", "new_member" - для определения дефолтного from_chat
        """
        if isinstance(value, str):
            # Старый формат - определяем дефолт по контексту
            if context == "new_member":
                # new_member события возможны только в группах
                result = [{"scenario": value, "from_chat": ["group"]}]
            else:
                # text и callback по умолчанию для приватных чатов
                result = [{"scenario": value, "from_chat": ["private"]}]
            return result
        elif isinstance(value, dict):
            # Одиночный формат - проверяем наличие scenario
            if "scenario" in value:
                result = [value]
                return result
            else:
                self.logger.error(f"Словарь триггера не содержит 'scenario': {value}")
                return []
        elif isinstance(value, list):
            # Множественный формат - проверяем каждый элемент
            result = [item for item in value if isinstance(item, dict) and "scenario" in item]
            return result
        else:
            self.logger.error(f"Неподдерживаемый тип значения триггера: {type(value)}")
            return []

    def _check_chat_filter(self, chat_id: int, chat_type: str, filter_list: list) -> bool:
        """
        Проверяет, подходит ли чат под фильтр.
        Поддерживает: конкретные ID, "group", "private", "all"
        Использует api_utils для корректного сравнения ID чатов.
        """
        if not filter_list:
            return True  # Если фильтр не указан - пропускаем все
        
        for item in filter_list:
            if item == "all":
                return True  # Высший приоритет - сразу выходим
            elif item == "group" and chat_type == "group":
                return True
            elif item == "private" and chat_type == "private":
                return True
            elif isinstance(item, int):
                # Используем api_utils для корректного сравнения ID entity
                if self.tg_api_utils.compare_entity_ids(item, chat_id):
                    return True
        
        return False

    def _get_chat_type(self, chat_id: int) -> str:
        """
        Определяет тип чата по chat_id.
        """
        if chat_id < 0:
            return "group"
        else:
            return "private"

    def find_all_scenarios_by_event(self, event: dict) -> List[str]:
        """
        Поиск всех сценариев по событию (text/callback/new_member) с поддержкой состояний пользователей.
        Возвращает список всех найденных сценариев.
        """
        triggers = self._get_triggers_for_event(event)
        event_type = event.get('source_type')

        if event_type == 'text':
            return self._find_text_scenarios(event, triggers)
        elif event_type == 'callback':
            return self._find_callback_scenarios(event, triggers)
        elif event_type == 'new_member':
            return self._find_new_member_scenarios(event, triggers)

        return []

    def _process_triggers(self, triggers_value, chat_id: int, chat_type: str, matching_scenarios: list, event: dict) -> bool:
        """
        Обрабатывает триггеры и добавляет подходящие сценарии в список.
        Возвращает True если нужно продолжить поиск (continue: true), False если остановиться.
        """
        event_type = event.get('source_type', 'text')
        
        parsed_triggers = self._parse_trigger_value(triggers_value, event_type)
        should_continue = False
        found_matching_trigger = False
        
        for trigger in parsed_triggers:
            # Проверяем forward_enabled для forward сообщений
            if event.get('is_forward', False):
                if not trigger.get('forward_enabled', False):
                    continue
            
            # Проверяем bot_enabled для сообщений от ботов
            if event.get('is_bot', False):
                if not trigger.get('bot_enabled', False):
                    continue
            
            # Определяем дефолт по типу события если from_chat не указан
            if "from_chat" not in trigger:
                if event_type == "new_member":
                    trigger["from_chat"] = ["group"]
                else:
                    trigger["from_chat"] = ["private"]
            
            if trigger["scenario"] and self._check_chat_filter(
                chat_id, chat_type, trigger["from_chat"]
            ):
                matching_scenarios.append(trigger["scenario"])
                found_matching_trigger = True
                if trigger.get("continue", False):
                    should_continue = True
        
        # Возвращаем should_continue только если нашли хотя бы один подходящий триггер
        return should_continue if found_matching_trigger else True

    def _find_text_scenarios(self, event: dict, triggers: dict) -> List[str]:
        """
        Поиск всех сценариев для текстовых событий с поддержкой множественных триггеров.
        Приоритеты: exact → state → regex → starts_with → contains → "*" (универсальный)
        По умолчанию останавливаемся на первом найденном типе, если continue: true - продолжаем.
        """
        text = event.get('event_text')
        user_id = event.get('user_id')
        chat_id = event.get('chat_id')
        chat_type = self._get_chat_type(chat_id) if chat_id else "private"
        
        matching_scenarios = []

        # Проверяем конкретные триггеры (приоритеты)
        text_triggers = triggers.get('text', {})
        
        # 1. exact (case-insensitive) - ВСЕГДА ПРИОРИТЕТ (только если есть текст)
        if text:
            for key, val in text_triggers.get('exact', {}).items():
                if key.lower() == text.lower():
                    should_continue = self._process_triggers(val, chat_id, chat_type, matching_scenarios, event)
                    if not should_continue:
                        return matching_scenarios

        # 2. state - проверка состояния пользователя (с ленивой очисткой)
        if user_id:
            state_match = self._find_state_match(user_id, text, triggers)
            if state_match:
                matching_scenarios.append(state_match)
                return matching_scenarios  # state всегда останавливает

        # 3. regex - регулярные выражения (более специфичные паттерны) (только если есть текст)
        if text:
            for pattern, val in text_triggers.get('regex', {}).items():
                try:
                    if re.search(pattern, text, re.IGNORECASE):
                        should_continue = self._process_triggers(val, chat_id, chat_type, matching_scenarios, event)
                        if not should_continue:
                            return matching_scenarios
                except re.error as e:
                    self.logger.error(f"Ошибка в регулярном выражении '{pattern}': {e}")

        # 4. starts_with (case-insensitive) - строка начинается с указанного текста (общий случай) (только если есть текст)
        if text:
            for key, val in text_triggers.get('starts_with', {}).items():
                if text.lower().startswith(key.lower()):
                    should_continue = self._process_triggers(val, chat_id, chat_type, matching_scenarios, event)
                    if not should_continue:
                        return matching_scenarios

        # 5. contains (case-insensitive) - только если есть текст
        if text:
            for key, val in text_triggers.get('contains', {}).items():
                if key.lower() in text.lower():
                    should_continue = self._process_triggers(val, chat_id, chat_type, matching_scenarios, event)
                    if not should_continue:
                        return matching_scenarios

        # 6. Универсальный обработчик (низший приоритет)
        if "*" in text_triggers:
            should_continue = self._process_triggers(
                text_triggers["*"], chat_id, chat_type, matching_scenarios, event
            )
            if not should_continue:
                return matching_scenarios

        return matching_scenarios

    def _find_callback_scenarios(self, event: dict, triggers: dict) -> List[str]:
        """
        Поиск всех сценариев для callback событий с поддержкой множественных триггеров.
        Поддерживает старый формат (строка) и новый множественный формат (массив).
        """
        callback_data = event.get('callback_data')
        if not callback_data or not self.tg_button_mapper:
            return []

        chat_id = event.get('chat_id')
        chat_type = self._get_chat_type(chat_id) if chat_id else "private"
        matching_scenarios = []

        # Явный переход по сценарию через callback_data вида ':scenario_name'
        if isinstance(callback_data, str) and callback_data.startswith(":"):
            return [callback_data[1:]]

        orig_text = self.tg_button_mapper.get_button_text(callback_data)
        if not orig_text:
            return []
        norm_orig = self.tg_button_mapper.normalize(orig_text)

        # exact (нормализованный)
        for key, val in triggers.get('callback', {}).get('exact', {}).items():
            if self.tg_button_mapper.normalize(key) == norm_orig:
                should_continue = self._process_triggers(val, chat_id, chat_type, matching_scenarios, event)
                if not should_continue:
                    return matching_scenarios

        # contains (нормализованный)
        for key, val in triggers.get('callback', {}).get('contains', {}).items():
            norm_key = self.tg_button_mapper.normalize(key)
            if norm_key in norm_orig:
                should_continue = self._process_triggers(val, chat_id, chat_type, matching_scenarios, event)
                if not should_continue:
                    return matching_scenarios

        return matching_scenarios

    def _find_new_member_scenarios(self, event: dict, triggers: dict) -> List[str]:
        """
        Поиск всех сценариев для new_member событий с поддержкой множественных триггеров.
        Поддерживает старый формат (строка) и новый множественный формат (массив).
        """
        triggers_new = triggers.get('new_member', {})
        chat_id = event.get('chat_id')
        chat_type = self._get_chat_type(chat_id) if chat_id else "private"
        matching_scenarios = []

        # 1. group (по chat_title)
        group_triggers = triggers_new.get('group', {})
        chat_title = event.get('chat_title')
        if group_triggers and chat_title:
            for title, val in group_triggers.items():
                if title.lower() == chat_title.lower():
                    should_continue = self._process_triggers(val, chat_id, chat_type, matching_scenarios, event)
                    if not should_continue:
                        return matching_scenarios

        # 2. link (по invite_link contains)
        invite_link = event.get('invite_link')
        link_triggers = triggers_new.get('link', {})
        if invite_link and link_triggers:
            for substr, val in link_triggers.items():
                if substr.lower() in invite_link.lower():
                    should_continue = self._process_triggers(val, chat_id, chat_type, matching_scenarios, event)
                    if not should_continue:
                        return matching_scenarios

        # 3. creator (по username создателя ссылки)
        creator_username = event.get('invite_link_creator_username')
        creator_triggers = triggers_new.get('creator', {})
        if creator_username and creator_triggers:
            norm_username = creator_username.lstrip('@').lower()
            for key, val in creator_triggers.items():
                norm_key = key.lstrip('@').lower()
                if norm_username == norm_key:
                    should_continue = self._process_triggers(val, chat_id, chat_type, matching_scenarios, event)
                    if not should_continue:
                        return matching_scenarios

        # 4. initiator (по username инициатора добавления)
        initiator_username = event.get('initiator_username')
        initiator_triggers = triggers_new.get('initiator', {})
        if initiator_username and initiator_triggers:
            norm_initiator = initiator_username.lstrip('@').lower()
            for key, val in initiator_triggers.items():
                norm_key = key.lstrip('@').lower()
                if norm_initiator == norm_key:
                    should_continue = self._process_triggers(val, chat_id, chat_type, matching_scenarios, event)
                    if not should_continue:
                        return matching_scenarios

        # 5. default
        if 'default' in triggers_new:
            should_continue = self._process_triggers(triggers_new['default'], chat_id, chat_type, matching_scenarios, event)
            if not should_continue:
                return matching_scenarios

        return matching_scenarios

    def _find_state_match(self, user_id: int, text: str, triggers: dict) -> Optional[str]:
        """
        Проверка состояния пользователя с ленивой очисткой.
        Возвращает сценарий если состояние пользователя совпадает с триггером состояния.
        """
        if not user_id:
            return None

        # Получаем состояние пользователя (с ленивой очисткой)
        user_state = self._get_user_state_with_cleanup(user_id)
        if not user_state:
            return None

        # Проверяем триггеры состояния
        state_triggers = triggers.get('text', {}).get('state', {})
        state_type = user_state.get('state_type')

        for trigger_state, scenario in state_triggers.items():
            if trigger_state == state_type:
                return scenario

        return None

    def _get_user_state_with_cleanup(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить состояние пользователя с ленивой очисткой.
        Если состояние истекло - очищает его и возвращает None.
        """
        try:
            with self.database_service.session_scope('user_states') as (_, repos):
                user_states_repo = repos['user_states']

                # Получаем состояние пользователя одним запросом
                user_state = user_states_repo.get_user_state(user_id)
                if not user_state:
                    return None

                # Проверяем истечение по expired_at
                now = self.datetime_formatter.now_local()
                if user_state.get('expired_at') is not None:
                    if user_state['expired_at'] < now:
                        user_states_repo.clear_user_state(user_id)
                        return None

                # Данные состояния уже декодированы в ORMConverter
                state_data = user_state.get('state_data') or {}

                return {
                    'state_type': user_state.get('state_type'),
                    'data': state_data
                }

        except Exception as e:
            self.logger.error(f"Ошибка при получении состояния пользователя {user_id}: {e}")
            return None
