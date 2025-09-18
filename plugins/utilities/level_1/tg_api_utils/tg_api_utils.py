from typing import Optional


class TgApiUtils:
    """Универсальная утилита для работы с API Telegram (ID чатов, пользователи, нормализация)."""

    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.database_service = kwargs['database_service']
        self.tg_mtproto = kwargs.get('tg_mtproto')

    def get_user_id_by_username(self, username: str) -> Optional[int]:
        """Вернуть user_id по username (без @). Если не найден — None."""
        try:
            if not username:
                return None
            clean_username = username.lstrip('@')
            with self.database_service.session_scope('users') as (session, repos):
                users_repo = repos['users']
                user = users_repo.get_user_by_username(clean_username)
                if not user:
                    return None
                user_id = user.get('user_id')
                return int(user_id) if user_id is not None else None
        except Exception as e:
            self.logger.error(f'Ошибка поиска user_id по username {username}: {e}')
            return None

    def add_or_update_user(self, user_id: int, username: str = None, **fields) -> bool:
        """Добавить или обновить пользователя с любыми полями."""
        try:
            # Подготавливаем поля для обновления
            update_fields = {}
            
            # Добавляем username если передан
            if username is not None:
                clean_username = username.lstrip('@')
                update_fields['username'] = clean_username
            
            # Добавляем остальные поля
            update_fields.update(fields)
            
            with self.database_service.session_scope('users') as (session, repos):
                users_repo = repos['users']
                success = users_repo.add_or_update(user_id=int(user_id), **update_fields)
                session.commit()
                return bool(success)
        except Exception as e:
            self.logger.error(f'Ошибка добавления/обновления пользователя {user_id} (@{username}): {e}')
            return False

    def normalize_entity_id(self, entity_id, entity_type: str = None) -> Optional[int]:
        """
        Нормализует ID entity в универсальный формат (Bot API формат).
        """
        # Безопасное преобразование в int
        try:
            entity_id = int(entity_id)
        except Exception as e:
            self.logger.error(f'Не удалось преобразовать entity_id в int: {entity_id}, ошибка: {e}')
            return None
        
        if entity_type == 'user':
            # Пользователи - всегда положительные ID
            return abs(entity_id)
        elif entity_type in ['chat', 'channel']:
            # Группы и каналы - используем логику нормализации
            if entity_id < -1000000000000:
            # Уже в Bot API формате: -1001234567890
                return entity_id
            elif entity_id < 0:
                # Отрицательный ID без префикса -100: -123456789 → -100123456789
                return -1000000000000 + entity_id
            else:
                # Положительный ID группы → Bot API: -1001234567890
                return -1000000000000 - entity_id
        else:
            # Тип не указан - пытаемся угадать по значению ID
            if entity_id < -1000000000000:
                # Уже в Bot API формате: -1001234567890
                return entity_id
            elif entity_id < 0:
                # Отрицательный ID без префикса -100: -123456789 → -100123456789
                return -1000000000000 + entity_id
            else:
                # Положительный ID - может быть пользователь или группа
                # По умолчанию считаем группой (более безопасно)
                return -1000000000000 - entity_id

    def compare_entity_ids(self, entity_id1, entity_id2, entity_type1: str = None, entity_type2: str = None) -> bool:
        """
        Сравнивает два ID entity, приводя к универсальному формату.
        """
        # Приводим к универсальному формату для сравнения
        normalized1 = self.normalize_entity_id(entity_id1, entity_type1)
        normalized2 = self.normalize_entity_id(entity_id2, entity_type2)
        
        # Если хотя бы один ID не удалось нормализовать - возвращаем False
        if normalized1 is None or normalized2 is None:
            return False
            
        return normalized1 == normalized2

    def get_entity_id(self, obj) -> Optional[dict]:
        """
        Получает нормализованную информацию об объекте (ID + тип).
        Универсальный оркестратор, автоматически определяющий тип объекта и вызывающий соответствующий подметод.
        Возвращает универсальный формат, подходящий для Bot API и MTProto.
        """
        try:
            if not obj:
                return None
            
            # Определяем тип по названию класса
            class_name = type(obj).__name__
            
            # Entity объекты (User, Chat, Channel)
            if class_name in ['User', 'Chat', 'Channel']:
                return self._process_entity_object(obj, class_name)
            
            # Peer объекты (PeerUser, PeerChat, PeerChannel)
            elif class_name in ['PeerUser', 'PeerChat', 'PeerChannel']:
                return self._process_peer_object(obj, class_name)
            
            else:
                # Неизвестный тип объекта
                self.logger.warning(f'Неизвестный тип объекта для get_entity_id: {class_name}')
                return None
                
        except Exception as e:
            self.logger.error(f'Ошибка получения entity_id из объекта: {e}')
            return None

    def _process_entity_object(self, entity_obj, class_name: str) -> Optional[dict]:
        """
        Обрабатывает Entity объекты (User, Chat, Channel).
        """
        try:
            entity_id = getattr(entity_obj, 'id', None)
            if entity_id is None:
                return None
            
            if class_name == 'User':
                normalized_id = int(entity_id)
                normalized_type = 'user'
            elif class_name == 'Chat':
                normalized_id = self.normalize_entity_id(entity_id, 'chat')
                normalized_type = 'chat'
            elif class_name == 'Channel':
                normalized_id = self.normalize_entity_id(entity_id, 'channel')
                normalized_type = 'channel'
            else:
                # Неизвестный тип Entity - возвращаем ID как есть
                normalized_id = int(entity_id)
                normalized_type = 'unknown'
            
            return {
                'id': normalized_id,
                'type': normalized_type
            }
                
        except Exception as e:
            self.logger.error(f'Ошибка обработки Entity объекта {class_name}: {e}')
            return None

    def _process_peer_object(self, peer_obj, class_name: str) -> Optional[dict]:
        """
        Обрабатывает Peer объекты (PeerUser, PeerChat, PeerChannel).
        """
        try:
            if class_name == 'PeerUser':
                peer_id = getattr(peer_obj, 'user_id', None)
                if peer_id is None:
                    return None
                normalized_id = int(peer_id)
                normalized_type = 'user'
            elif class_name == 'PeerChat':
                peer_id = getattr(peer_obj, 'chat_id', None)
                if peer_id is None:
                    return None
                normalized_id = self.normalize_entity_id(peer_id, 'chat')
                normalized_type = 'chat'
            elif class_name == 'PeerChannel':
                peer_id = getattr(peer_obj, 'channel_id', None)
                if peer_id is None:
                    return None
                normalized_id = self.normalize_entity_id(peer_id, 'channel')
                normalized_type = 'channel'
            else:
                # Неизвестный тип Peer - возвращаем None
                # Не пытаемся угадывать, так как не знаем точно, где искать ID
                return None
            
            return {
                'id': normalized_id,
                'type': normalized_type
            }
                
        except Exception as e:
            self.logger.error(f'Ошибка обработки Peer объекта {class_name}: {e}')
            return None

    async def create_peer_object(self, entity_id: int, entity_type: str = None):
        """
        Создает готовый peer объект для MTProto API по ID и типу.
        Если тип неизвестен - умно определяет его автоматически.
        """
        try:
            from telethon.tl.types import PeerUser, PeerChat, PeerChannel
            
            # Если тип известен - создаем явно
            if entity_type:
                return self._create_peer_by_type(entity_id, entity_type)
            
            # Если тип неизвестен - умно определяем
            peer = await self._detect_and_create_peer(entity_id)
            if peer is None:
                self.logger.error(f"Не удалось определить тип entity {entity_id}")
                return None
            return peer
                
        except Exception as e:
            self.logger.error(f'Ошибка создания MTProto entity из ID {entity_id} и типа {entity_type}: {e}')
            return None

    def _create_peer_by_type(self, entity_id: int, entity_type: str):
        """Создает Peer объект по известному типу."""
        from telethon.tl.types import PeerUser, PeerChat, PeerChannel
        
        if entity_type == 'user':
            # Пользователи - положительный ID
            return PeerUser(user_id=entity_id)
        elif entity_type in ['chat', 'channel']:
            # Группы и каналы - правильно извлекаем оригинальный ID
            if entity_id < -1000000000000:
                # Bot API формат: -1001234567890 → MTProto: 1234567890
                original_id = entity_id + 1000000000000
            elif entity_id < 0:
                # Уже в MTProto формате: -123456789 → MTProto: 123456789
                original_id = abs(entity_id)
            else:
                # Положительный ID - уже в MTProto формате
                original_id = entity_id
            
            # Создаем соответствующий объект
            if entity_type == 'chat':
                return PeerChat(chat_id=original_id)
            else:  # channel
                return PeerChannel(channel_id=original_id)
        else:
            # Неизвестный тип
            self.logger.warning(f'Неизвестный тип entity для создания: {entity_type}')
            return None

    async def _detect_and_create_peer(self, entity_id: int):
        """Умно определяет тип entity и создает соответствующий Peer объект."""
        try:
            # Проверяем доступность MTProto
            if not self.tg_mtproto:
                self.logger.warning(f"⚠️ Метод недоступен: отсутствует компонент tg_mtproto для entity {entity_id}")
                return None
            
            # 1. Проверяем кэш Telethon
            client = self.tg_mtproto.get_client()
            if client:
                try:
                    input_entity = await client.get_input_entity(entity_id)
                    # Определяем тип из кэша и создаем Peer
                    entity_type = self._get_entity_type_from_cache(input_entity)
                    if entity_type:
                        return self._create_peer_by_type(entity_id, entity_type)
                    # Если тип не определен из кэша, продолжаем определение
                except Exception:
                    # Entity нет в кэше, продолжаем определение
                    pass
            
            # 2. Пробуем каналы (включая мегагруппы)
            try:
                entity_info = await self.tg_mtproto.get_entity_info(entity_id=entity_id, entity_type='channel')
                if entity_info:
                    return self._create_peer_by_type(entity_id, 'channel')
            except Exception as e:
                # Проверяем тип ошибки
                if self._is_wrong_peer_type_error(e):
                    # Неверный тип - это не канал, пробуем дальше
                    pass
                else:
                    # Другая ошибка (нет доступа, но тип правильный) - это канал
                    return self._create_peer_by_type(entity_id, 'channel')
            
            # 3. Пробуем обычные чаты
            try:
                entity_info = await self.tg_mtproto.get_entity_info(entity_id=entity_id, entity_type='chat')
                if entity_info:
                    self.logger.info(f"Entity {entity_id} определен как обычный чат")
                    return self._create_peer_by_type(entity_id, 'chat')
            except Exception as e:
                # Проверяем тип ошибки
                if self._is_wrong_peer_type_error(e):
                    # Неверный тип - это не чат, пробуем дальше
                    pass
                else:
                    # Другая ошибка (нет доступа, но тип правильный) - это чат
                    return self._create_peer_by_type(entity_id, 'chat')
            
            # 4. Fallback на пользователей
            return self._create_peer_by_type(entity_id, 'user')
            
        except Exception as e:
            self.logger.error(f"Ошибка определения типа Entity {entity_id}: {e}")
            # Не смогли определить тип - возвращаем None
            return None

    def _is_wrong_peer_type_error(self, error: Exception) -> bool:
        """Проверяет, является ли ошибка следствием неверного типа Peer."""
        # Проверяем по имени класса исключения (более надежно чем импорт)
        error_class_name = type(error).__name__
        wrong_type_error_names = [
            'PeerIdInvalidError',
            'ChannelInvalidError', 
            'ChatInvalidError',
            'UserInvalidError',
            'InputUserDeactivatedError',
            'InputChannelInvalidError',
            'InputChatInvalidError'
        ]
        
        return error_class_name in wrong_type_error_names

    def _get_entity_type_from_cache(self, input_entity) -> str:
        """Определяет тип entity из кэша Telethon."""
        # Простая эвристика на основе класса input_entity
        entity_class = type(input_entity).__name__.lower()
        if 'channel' in entity_class:
            return 'channel'
        elif 'chat' in entity_class:
            return 'chat'
        elif 'user' in entity_class:
            return 'user'
        else:
            # Неизвестный тип - возвращаем None для дальнейшего определения
            return None