import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Action, Base, Cache, InviteLink, Request, User, UserState, PromoCode
from .repositories.actions import ActionsRepository
from .repositories.cache import CacheRepository

from .repositories.invite_links import InviteLinksRepository
from .repositories.requests import RequestsRepository
from .repositories.user_states import UserStatesRepository
from .repositories.users import UsersRepository
from .repositories.promo_codes import PromoCodesRepository


class DatabaseService:
    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.settings_manager = kwargs['settings_manager']
        self.datetime_formatter = kwargs['datetime_formatter']
        self.data_preparer = kwargs['data_preparer']
        self.data_converter = kwargs['data_converter']
        self.action_parser = kwargs['action_parser']
        self.placeholder_processor = kwargs.get('placeholder_processor')
        
        # Получаем настройки через settings_manager
        settings = self.settings_manager.get_plugin_settings("database_service")
        
        self.database_url = settings.get('database_url', 'sqlite:///data/core.db')
        self.echo = settings.get('echo', False)
        
        # Создаём директорию для базы данных, если её нет
        self._ensure_database_directory()
        
        # Создаём engine и фабрику сессий
        self.engine = create_engine(self.database_url, echo=self.echo, future=True)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)
        
        # Создаём таблицы при инициализации
        self.create_all()

    def _ensure_database_directory(self):
        """Создаёт директорию для базы данных, если её нет."""
        try:
            # Извлекаем путь к директории из URL базы данных
            if self.database_url.startswith('sqlite:///'):
                # Убираем 'sqlite:///' и получаем путь к файлу
                db_path = self.database_url[10:]  # Убираем 'sqlite:///'
                db_dir = os.path.dirname(db_path)
                
                # Создаём директорию, если она не существует
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                    self.logger.info(f"Создана директория для базы данных: {db_dir}")
                elif db_dir:
                    pass
            else:
                # Для других типов БД (PostgreSQL, MySQL) директория не нужна
                pass
                
        except Exception as e:
            self.logger.error(f"Ошибка при создании директории для базы данных: {e}")
            # Не прерываем инициализацию - возможно, директория уже существует

    @contextmanager
    def session_scope(self, *repo_names):
        """Контекстный менеджер для сессии и репозиториев."""
        session = self.session_factory()
        try:
            repos = {}
            if 'actions' in repo_names:
                repos['actions'] = ActionsRepository(
                    session=session,
                    logger=self.logger,
                    model=Action,
                    datetime_formatter=self.datetime_formatter,
                    data_preparer=self.data_preparer,
                    data_converter=self.data_converter,
                    action_parser=self.action_parser,
                    placeholder_processor=self.placeholder_processor
                )
            if 'users' in repo_names:
                repos['users'] = UsersRepository(
                    session=session,
                    logger=self.logger,
                    model=User,
                    datetime_formatter=self.datetime_formatter,
                    data_preparer=self.data_preparer,
                    data_converter=self.data_converter
                )
            if 'user_states' in repo_names:
                repos['user_states'] = UserStatesRepository(
                    session=session,
                    logger=self.logger,
                    model=UserState,
                    datetime_formatter=self.datetime_formatter,
                    data_preparer=self.data_preparer,
                    data_converter=self.data_converter
                )
            if 'requests' in repo_names:
                repos['requests'] = RequestsRepository(
                    session=session,
                    logger=self.logger,
                    model=Request,
                    datetime_formatter=self.datetime_formatter,
                    data_preparer=self.data_preparer,
                    data_converter=self.data_converter
                )
            if 'invite_links' in repo_names:
                repos['invite_links'] = InviteLinksRepository(
                    session=session,
                    logger=self.logger,
                    model=InviteLink,
                    datetime_formatter=self.datetime_formatter,
                    data_preparer=self.data_preparer,
                    data_converter=self.data_converter
                )
            if 'cache' in repo_names:
                repos['cache'] = CacheRepository(
                    session=session,
                    logger=self.logger,
                    model=Cache,
                    datetime_formatter=self.datetime_formatter,
                    data_preparer=self.data_preparer,
                    data_converter=self.data_converter
                )
            if 'promo_codes' in repo_names:
                repos['promo_codes'] = PromoCodesRepository(
                    session=session,
                    logger=self.logger,
                    model=PromoCode,
                    datetime_formatter=self.datetime_formatter,
                    data_preparer=self.data_preparer,
                    data_converter=self.data_converter
                )

            yield session, repos
        finally:
            session.close()

    def create_all(self):
        """Создаёт все таблицы в БД согласно моделям."""
        try:
            Base.metadata.create_all(self.engine)
            self.logger.info("Все таблицы успешно созданы.")
        except Exception as e:
            self.logger.error(f"Ошибка при создании таблиц: {e}")
    
    def get_table_class_map(self):
        """Получает карту таблиц: имя таблицы -> класс модели."""
        table_class_map = {}
        for table_name, table in Base.metadata.tables.items():
            # Находим соответствующую модель
            for model_class in Base.registry._class_registry.values():
                if hasattr(model_class, '__tablename__') and model_class.__tablename__ == table_name:
                    table_class_map[table_name] = model_class
                    break
        return table_class_map
