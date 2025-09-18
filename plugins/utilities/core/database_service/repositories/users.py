from typing import Any, Dict, Optional

from sqlalchemy import select, update


class UsersRepository:
    """
    Репозиторий для работы с таблицей Users (пользователи бота).
    """
    def __init__(self, session, logger, model, datetime_formatter, data_preparer, data_converter):
        self.logger = logger
        self.session = session
        self.model = model
        self.datetime_formatter = datetime_formatter
        self.data_preparer = data_preparer
        self.data_converter = data_converter

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по user_id."""
        try:
            stmt = select(self.model).where(self.model.user_id == user_id)
            user = self.session.execute(stmt).scalar_one_or_none()
            
            if not user:
                return None
                
            return self.data_converter.to_dict(user)
            
        except Exception as e:
            self.logger.error(f"Ошибка получения пользователя {user_id}: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получает пользователя по username (без учета регистра)."""
        try:
            # Приводим к нижнему регистру для сравнения
            username_lower = username.lower()
            stmt = select(self.model).where(self.model.username.ilike(username_lower))
            user = self.session.execute(stmt).scalar_one_or_none()
            
            if not user:
                return None
                
            return self.data_converter.to_dict(user)
            
        except Exception as e:
            self.logger.error(f"Ошибка получения пользователя по username {username}: {e}")
            return None

    def update_user(self, user_id: int, **fields) -> bool:
        """Обновляет пользователя по user_id."""
        try:
            # Добавляем автоматическое поле updated_at
            if 'updated_at' not in fields:
                fields['updated_at'] = self.datetime_formatter.now_local()
            
            # Подготавливаем поля через универсальный подготовщик
            prepared_fields = self.data_preparer.prepare_for_update(
                model=self.model,
                fields=fields
            )
            
            if not prepared_fields:
                self.logger.warning(f"Нет валидных полей для обновления пользователя {user_id}")
                return False
            
            # Выполняем обновление
            stmt = update(self.model).where(self.model.user_id == user_id).values(**prepared_fields)
            result = self.session.execute(stmt)
            self.session.commit()
            
            if result.rowcount > 0:
        
                return True
            else:
                self.logger.warning(f"Пользователь {user_id} не найден для обновления")
                return False
                
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Ошибка обновления пользователя {user_id}: {e}")
            return False

    def add_user(self, **fields) -> int:
        """Добавляет нового пользователя."""
        try:
            # Добавляем автоматические поля
            if 'created_at' not in fields:
                fields['created_at'] = self.datetime_formatter.now_local()
            if 'updated_at' not in fields:
                fields['updated_at'] = self.datetime_formatter.now_local()
            
            # Подготавливаем поля через универсальный подготовщик
            prepared_fields = self.data_preparer.prepare_for_insert(
                model=self.model,
                fields=fields
            )
            
            if not prepared_fields:
                self.logger.error("Не удалось подготовить поля для создания пользователя")
                return 0
            
            # Создаем нового пользователя
            user = self.model(**prepared_fields)
            self.session.add(user)
            self.session.commit()
            self.session.flush()
            
            user_id = getattr(user, 'user_id', 0)
    
            return user_id
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Ошибка создания пользователя: {e}")
            return 0

    def add_or_update(self, **fields) -> bool:
        """Добавляет или обновляет пользователя."""
        try:
            # МЯГКАЯ ОБРАБОТКА: entity_id и user_id
            entity_id = fields.get('entity_id')
            user_id = fields.get('user_id')
            
            # Если есть entity_id - используем его как user_id
            if entity_id:
                user_id = entity_id
                fields['user_id'] = entity_id
                fields.pop('entity_id', None)
            # Если нет ни entity_id, ни user_id - ошибка
            elif not user_id:
                self.logger.error("user_id или entity_id обязательны для работы метода")
                return False
            
            # Исключаем user_id из полей для обновления
            fields_for_update = fields.copy()
            fields_for_update.pop('user_id', None)
            
            # Проверяем существование пользователя
            stmt = select(self.model).where(self.model.user_id == user_id)
            user = self.session.execute(stmt).scalar_one_or_none()
            
            if user:
                # Обновляем существующего пользователя с защитой
                # Передаем уже полученные данные для оптимизации
                user_dict = self.data_converter.to_dict(user)
                return self.update_user_with_protection(user_id, existing_user_data=user_dict, **fields_for_update)
            else:
                # Создаем нового пользователя
                # Проверяем, нет ли уже user_id в fields (избегаем дублирования)
                if 'user_id' not in fields:
                    fields['user_id'] = user_id
                
                new_user_id = self.add_user(**fields)
                return new_user_id > 0
                
        except Exception as e:
            self.logger.error(f"Ошибка операции с пользователем {user_id}: {e}")
            return False

    def update_user_with_protection(self, user_id: int, existing_user_data: Optional[Dict] = None, **fields) -> bool:
        """Обновляет пользователя с защитой от затирания важных полей."""
        try:
            # Получаем текущие данные пользователя
            if existing_user_data is not None:
                # Используем переданные данные (оптимизация)
                user_dict = existing_user_data
            else:
                # Запрашиваем данные из БД
                stmt = select(self.model).where(self.model.user_id == user_id)
                user = self.session.execute(stmt).scalar_one_or_none()
                
                if not user:
                    self.logger.warning(f"Пользователь {user_id} не найден для обновления")
                    return False
                
                user_dict = self.data_converter.to_dict(user)
            
            # Фильтруем поля с защитой от затирания
            fields_to_update = {}
            for field_name, new_value in fields.items():
                if field_name in ['username', 'first_name', 'last_name']:
                    # Если поле уже заполнено и новое значение пустое - пропускаем
                    if user_dict.get(field_name) and not new_value:
                        continue
                elif field_name == 'is_bot':
                    # Для is_bot: если уже установлено значение и новое None - пропускаем
                    # MTProto может возвращать None для атрибута bot, если информация недоступна
                    if user_dict.get('is_bot') is not None and new_value is None:
                        continue
                fields_to_update[field_name] = new_value
            
            # Проверяем, есть ли поля для обновления
            if not fields_to_update:
                return True  # Возвращаем True, так как операция "успешна" (ничего не нужно было обновлять)
            
            # Выполняем обновление отфильтрованными полями
            return self.update_user(user_id, **fields_to_update)
                
        except Exception as e:
            self.logger.error(f"Ошибка защищенного обновления пользователя {user_id}: {e}")
            return False
