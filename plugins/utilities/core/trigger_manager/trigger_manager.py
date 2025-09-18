import json
from typing import Any, Dict, List
from collections import OrderedDict


class TriggerManager:
    """
    Менеджер триггеров: обрабатывает входящие ивенты, ищет триггер, разворачивает сценарий и кладёт действия в очередь.
    Поддерживает множественные триггеры и универсальные обработчики.
    """
    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.scenarios_manager = kwargs['scenarios_manager']
        self.database_service = kwargs['database_service']
        self.trigger_processing = kwargs['trigger_processing']
        self.permission_manager = kwargs.get('permission_manager')  # Опциональная зависимость
        self.datetime_formatter = kwargs['datetime_formatter']
        self.bot = kwargs['tg_bot_initializer'].get_bot()
        
        # Получаем глобальную настройку плейсхолдеров
        self.settings_manager = kwargs['settings_manager']
        global_settings = self.settings_manager.get_global_settings()
        self.global_placeholders_enabled = global_settings.get('enable_global_placeholders', False)
        
        # Кэш для дедупликации событий (FIFO очередь: ключ -> timestamp)
        self.event_cache = OrderedDict()
        
        # Настройки кэша из конфига
        plugin_settings = self.settings_manager.get_plugin_settings('trigger_manager')
        self.cache_ttl_seconds = plugin_settings.get('cache_ttl_seconds', 15)
        self.cleanup_frequency = plugin_settings.get('cleanup_frequency', 50)
        
        # Счетчики для очистки
        self._event_counter = 0

    async def handle_event(self, event: Dict[str, Any]):
        """
        Обрабатывает событие, запуская соответствующие сценарии.
        Поддерживает множественные триггеры.
        """
        
        # Увеличиваем счетчик событий
        self._event_counter += 1
        
        # 0. Проверка дедупликации
        if self._is_duplicate_event(event):
            return
        
        # 1. Поиск всех сценариев по событию
        scenario_names = self.trigger_processing.find_all_scenarios_by_event(event)
        if not scenario_names:
            self.logger.warning(f"Триггер не найден для ивента: {event}")
            return
            
        # 2. Обработка всех найденных сценариев
        for scenario_name in scenario_names:
            await self._process_single_scenario(event, scenario_name)

    async def _process_single_scenario(self, event: Dict[str, Any], scenario_name: str):
        """
        Обрабатывает один сценарий.
        """
        # Получение развернутого сценария
        scenario = self.scenarios_manager.get_scenario(scenario_name)
        if not scenario:
            self.logger.warning(f"Сценарий '{scenario_name}' не найден или не может быть развёрнут")
            return
            
        actions = scenario.get('actions', [])
        if not actions:
            self.logger.warning(f"Сценарий '{scenario_name}' не содержит действий")
            return
            
        # Обработка действий
        await self._process_actions(event, actions, scenario_name)

    async def _process_actions(self, event: Dict[str, Any], actions: list, scenario_name: str):
        """Обрабатывает список действий из сценария."""
        with self.database_service.session_scope('actions', 'users') as (_, repos):
            actions_repo = repos['actions']
            users_repo = repos['users']

            # Обновляем пользователя
            await self._update_user(event, users_repo)
            
            # Обрабатываем действия
            await self._process_actions_recursive(actions, event, actions_repo)

    async def _process_actions_recursive(self, actions: list, event: Dict[str, Any], 
                                       actions_repo, previous_action_id: int = None) -> int:
        """Рекурсивно обрабатывает список действий с поддержкой массивов сценариев."""
        for action in actions:
            if action.get('type') == 'scenario':
                # Обрабатываем сценарий (может быть строкой или массивом)
                # Возвращаем ID последнего действия из сценария
                last_action_id = await self._process_scenario_action(action, event, actions_repo, previous_action_id)
                if last_action_id:
                    previous_action_id = last_action_id
            else:
                # Обычное действие
                previous_action_id = await self._process_single_action(
                    action, event, actions_repo, previous_action_id
                )
        
        return previous_action_id

    async def _process_scenario_action(self, action: dict, event: Dict[str, Any], 
                                     actions_repo, previous_action_id: int = None):
        """Обрабатывает действие типа 'scenario' с поддержкой массивов."""
        scenario_names = self._normalize_to_list(action.get('value'))
        
        if not scenario_names:
            self.logger.error(f"Пустое значение value в действии scenario: {action}")
            return
        
        # Если несколько сценариев - связываем только с предыдущим действием до сценариев
        if len(scenario_names) > 1:
            for scenario_name in scenario_names:
                scenario = self.scenarios_manager.get_scenario(scenario_name)
                if not scenario:
                    self.logger.error(f"Сценарий '{scenario_name}' не найден")
                    continue
                
                scenario_actions = scenario.get('actions', [])
                if not scenario_actions:
                    self.logger.warning(f"Сценарий '{scenario_name}' не содержит действий")
                    continue
                
                # Рекурсивно обрабатываем действия сценария с тем же previous_action_id
                await self._process_actions_recursive(scenario_actions, event, actions_repo, previous_action_id)
        
        # Если один сценарий - связываем с последним действием внутри сценария
        else:
            scenario_name = scenario_names[0]
            
            scenario = self.scenarios_manager.get_scenario(scenario_name)
            if not scenario:
                self.logger.error(f"Сценарий '{scenario_name}' не найден")
                return
            
            scenario_actions = scenario.get('actions', [])
            if not scenario_actions:
                self.logger.warning(f"Сценарий '{scenario_name}' не содержит действий")
                return
            
            # Рекурсивно обрабатываем действия сценария и получаем ID последнего действия
            last_action_id = await self._process_actions_recursive(scenario_actions, event, actions_repo, previous_action_id)
            
            # Обновляем previous_action_id для следующих действий
            if last_action_id:
                return last_action_id
        
        return previous_action_id

    def _normalize_to_list(self, value) -> list:
        """Преобразует значение в список."""
        if isinstance(value, str):
            return [value]
        elif isinstance(value, list):
            return value
        else:
            self.logger.error(f"Неподдерживаемый тип value для сценария: {type(value)}")
            return []

    async def _update_user(self, event: Dict[str, Any], users_repo):
        """Обновляет или создает пользователя в базе данных."""
        user_id = event.get('user_id')
        if not user_id:
            return
            
        # Event уже содержит ISO строки дат, парсим их
        event_date = event.get('event_date')
        if event_date:
            last_activity = self.datetime_formatter.parse(event_date)
        else:
            last_activity = self.datetime_formatter.now_local()

        users_repo.add_or_update(
            user_id=user_id,
            username=event.get('username'),
            first_name=event.get('first_name'),
            last_name=event.get('last_name'),
            is_bot=event.get('is_bot', False),
            last_activity=last_activity
        )

    async def _process_single_action(self, action: dict, event: Dict[str, Any], 
                                   actions_repo, previous_action_id: int = None) -> int:
        """Обрабатывает одно действие из сценария."""
        # Проверяем доступ к действию
        fail_reason = await self._check_action_access(action, event)
        
        # Подготавливаем данные действия
        event_data, action_data = self._prepare_action_data(action, event, fail_reason)
        
        # Определяем статус и параметры цепочки
        status, chain_params = self._determine_action_status(action_data, previous_action_id)
        
        # Создаем действие в базе с привязкой к предыдущему действию
        current_action_id = self._create_action(
            event_data, action_data, status, chain_params, previous_action_id, actions_repo
        )
        
        return current_action_id

    async def _check_action_access(self, action: dict, event: Dict[str, Any]) -> str:
        """Проверяет доступ пользователя к действию."""
        user_id = event.get('user_id')
        if not user_id:
            return None
            
        # Если permission_manager недоступен - пропускаем проверки доступа
        if not self.permission_manager:
            # Логируем предупреждение о пропуске проверок
            required_role = action.get('required_role')
            required_permission = action.get('required_permission')
            group_admin = action.get('group_admin', False)
            
            if required_role or required_permission or group_admin:
                self.logger.warning(f"⚠️ Проверки доступа пропущены для user_id={user_id} к действию: {action.get('type')} (permission_manager отключен)")
            return None
            
        # Проверка ролей и разрешений
        required_role = action.get('required_role')
        required_permission = action.get('required_permission')
        
        if isinstance(required_role, str):
            required_role = [required_role]
        if isinstance(required_permission, str):
            required_permission = [required_permission]
            
        # Проверка всех типов доступа через permission_manager
        group_admin = action.get('group_admin', False)
        if not await self.permission_manager.check_access(user_id, required_role, required_permission, group_admin, event):
            self.logger.warning(f"❌ Доступ запрещен для user_id={user_id} к действию: {action.get('type')} (required_role={required_role}, required_permission={required_permission}, group_admin={group_admin})")
            return 'access_denied'
            
        return None

    def _prepare_action_data(self, action: dict, event: Dict[str, Any], fail_reason: str) -> tuple:
        """Подготавливает данные действия с разделением на event_data и action_data."""
        # Разделяем данные: event_data содержит данные события, action_data - конфигурацию действия
        
        # event_data: данные события (user_id, chat_id, event_text и т.д.)
        event_data = event.copy()
        
        # action_data: конфигурация действия из сценария
        action_data = action.copy()
        
        # Добавляем глобальную настройку плейсхолдеров, если не указана локально
        if self.global_placeholders_enabled and 'placeholder' not in action:
            action_data['placeholder'] = True
        
        if fail_reason:
            action_data['is_failed'] = True
            action_data['fail_reason'] = fail_reason
        
        return event_data, action_data

    def _determine_action_status(self, action_data: dict, previous_action_id: int) -> tuple:
        """Определяет статус действия и параметры цепочки."""
        # Используем action_data для всех параметров
        chain = action_data.get('chain', False)
        chain_drop = action_data.get('chain_drop', None)
        
        # Определяем unlock_statuses
        if chain is True or chain == 'any':
            unlock_statuses = ['completed', 'failed', 'drop']
        elif isinstance(chain, str):
            unlock_statuses = [chain]
        elif isinstance(chain, list):
            unlock_statuses = [str(x) for x in chain if x]
        else:
            unlock_statuses = ['completed']
            
        is_chain = bool(chain)
        
        # Проверяем статус ошибки из action_data
        is_failed = action_data.get('is_failed', False)
        
        # Определяем статус
        if is_chain:
            if previous_action_id is not None:
                status = 'hold'
            else:
                if is_failed:
                    status = 'failed'
                else:
                    status = 'pending'
                self.logger.warning(f"Действие chain=true, но previous_id отсутствует — создаем как {status}")
        else:
            if is_failed:
                status = 'failed'
            else:
                status = 'pending'
        
        # Обрабатываем chain_drop_status
        chain_drop_status = None
        if chain_drop:
            if isinstance(chain_drop, str):
                chain_drop_status = [chain_drop]
            elif isinstance(chain_drop, list):
                chain_drop_status = [str(x) for x in chain_drop if x]
            else:
                self.logger.warning(f"Неподдерживаемый тип chain_drop: {type(chain_drop)}, значение: {chain_drop}")
        
        chain_params = {
            'is_chain': is_chain,
            'unlock_statuses': unlock_statuses,
            'chain_drop_status': chain_drop_status
        }
        
        return status, chain_params

    def _create_action(self, event_data: dict, action_data: dict, 
                      status: str, chain_params: dict, previous_action_id: int, actions_repo) -> int:
        """Создает действие в базе данных с разделенными данными."""
        action_type = action_data.get('type')
        
        # Подготавливаем параметры для создания действия
        action_params = {
            'action_type': action_type,
            'event_data': event_data,    # Данные события
            'action_data': action_data,  # Конфигурация действия
            'status': status,
            'chain_drop_status': chain_params['chain_drop_status']
        }
        
        # Добавляем prev_action_id если это цепочка
        if chain_params['is_chain'] and previous_action_id:
            action_params['prev_action_id'] = previous_action_id
            action_params['unlock_status'] = json.dumps(chain_params['unlock_statuses'], ensure_ascii=False)
        
        return actions_repo.add_action(**action_params)

    def _is_duplicate_event(self, event: Dict[str, Any]) -> bool:
        """
        Проверяет, является ли событие дублированным.
        Использует временной кэш с TTL на основе chat_id + message_id для сообщений,
        chat_id + callback_id для коллбеков.
        """
        # Создаем уникальный ключ для события
        source_type = event.get('source_type', 'unknown')
        chat_id = event.get('chat_id')
        message_id = event.get('message_id')
        callback_id = event.get('callback_id')
        
        if not chat_id:
            return False  # Не можем дедуплицировать без chat_id
        
        # Формируем ключ в зависимости от типа события
        if source_type == 'callback' and callback_id:
            event_key = f"{chat_id}:{callback_id}"
        elif source_type == 'text' and message_id:
            event_key = f"{chat_id}:{message_id}"
        else:
            return False  # Не можем дедуплицировать
        
        # Получаем текущее время
        current_time = self.datetime_formatter.now_local()
        
        # Проверяем, есть ли событие в кэше и не истекло ли время
        if event_key in self.event_cache:
            cache_time = self.event_cache[event_key]
            if (current_time - cache_time).total_seconds() < self.cache_ttl_seconds:
                return True
        
        # Добавляем событие в конец FIFO очереди
        self.event_cache[event_key] = current_time
        
        # Периодическая очистка кэша
        if self._event_counter % self.cleanup_frequency == 0:
            self._cleanup_cache()
        
        return False

    def _cleanup_cache(self):
        """
        Очищает кэш от устаревших записей (FIFO: идем с начала до первого свежего).
        """
        current_time = self.datetime_formatter.now_local()
        
        # Идем с начала FIFO очереди и удаляем старые записи
        while self.event_cache:
            # Берем первый (самый старый) элемент
            try:
                key, cache_time = next(iter(self.event_cache.items()))
            except StopIteration:
                # Кэш стал пустым во время итерации (маловероятно, но защита)
                break
            
            # Если время истекло - удаляем и продолжаем
            if (current_time - cache_time).total_seconds() >= self.cache_ttl_seconds:
                del self.event_cache[key]
            else:
                # Нашли свежую запись - все следующие тоже свежие, выходим
                break