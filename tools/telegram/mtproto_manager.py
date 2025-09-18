#!/usr/bin/env python3
"""
MTProto Manager - Универсальный менеджер для работы с MTProto

Объединяет функционал управления сессиями и работы с чатами.
Поддерживает диагностику, создание сессий, получение списков чатов.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Переходим в корневую директорию проекта для корректной работы DI-контейнера
os.chdir(project_root)

from app.di_container import DIContainer
from plugins.utilities.foundation.logger.logger import Logger
from plugins.utilities.foundation.plugins_manager.plugins_manager import PluginsManager
from plugins.utilities.foundation.settings_manager.settings_manager import SettingsManager


class MTProtoManager:
    """Универсальный менеджер для работы с MTProto API"""
    
    def __init__(self):
        self.di_container = None
        self.tg_mtproto = None
        self.logger = None
        self.settings_manager = None
        self.temp_dir = project_root / "data" / "temp"
        
        # Создаем папку temp если её нет
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def print_header(self):
        """Выводит заголовок утилиты"""
        print("🔐 MTProto Manager - Универсальный менеджер для работы с Telegram")
        print("=" * 70)
        print(f"📁 Папка для сохранения: {self.temp_dir}")
        print()
    
    async def initialize(self):
        """Инициализация DI-контейнера и утилит"""
        try:
            # Создаем logger
            logger = Logger()
            
            # Создаем plugins_manager
            plugins_manager = PluginsManager(logger=logger)
            
            # Создаем settings_manager
            settings_manager = SettingsManager(logger=logger, plugins_manager=plugins_manager)
            
            # Инициализируем DI-контейнер
            self.di_container = DIContainer(logger=logger, plugins_manager=plugins_manager, settings_manager=settings_manager)
            self.di_container.initialize_all_plugins()
            
            # Получаем необходимые утилиты
            self.tg_mtproto = self.di_container.get_utility("tg_mtproto")
            self.logger = self.di_container.get_utility("logger")
            self.settings_manager = self.di_container.get_utility("settings_manager")
            
            if not self.tg_mtproto:
                print("❌ Ошибка: не удалось получить tg_mtproto из DI-контейнера")
                return False
            
            if not self.logger:
                print("❌ Ошибка: не удалось получить logger из DI-контейнера")
                return False
            
            if not self.settings_manager:
                print("❌ Ошибка: не удалось получить settings_manager из DI-контейнера")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            return False
    
    def show_main_menu(self):
        """Показывает главное меню"""
        print("\n🏠 ГЛАВНОЕ МЕНЮ:")
        print("1. 🔧 Работа с сессией")
        print("2. 📋 Действия с чатами")
        print("0. ❌ Выход")
        print()
    
    def show_session_menu(self):
        """Показывает меню работы с сессией"""
        print("\n🔧 РАБОТА С СЕССИЕЙ:")
        print("1. 🔍 Диагностика сессии")
        print("2. 🚪 Выйти из сессии (logout)")
        print("3. 📁 Информация о сессии")
        print("4. 🆕 Создать новую сессию")
        print("5. ⬅️ Назад в главное меню")
        print("0. ❌ Выход")
        print()
    
    def show_chats_menu(self):
        """Показывает меню действий с чатами"""
        print("\n📋 ДЕЙСТВИЯ С ЧАТАМИ:")
        print("1. 🔍 Простой список чатов")
        print("2. 📋 Детальный список чатов")
        print("3. ⚙️ Настройки (лимит чатов)")
        print("4. 📁 Сохраненные файлы")
        print("5. ⬅️ Назад в главное меню")
        print("0. ❌ Выход")
        print()
    
    async def run_main_menu(self):
        """Запускает главное меню"""
        while True:
            self.show_main_menu()
            
            try:
                choice = input("Выберите раздел (0-2): ").strip()
                
                if choice == "0":
                    print("👋 До свидания!")
                    return False
                elif choice == "1":
                    result = await self.run_session_menu()
                    if result == "exit":
                        return False  # Полный выход из программы
                    # Если result == "back", продолжаем цикл главного меню
                elif choice == "2":
                    result = await self.run_chats_menu()
                    if result == "exit":
                        return False  # Полный выход из программы
                    # Если result == "back", продолжаем цикл главного меню
                else:
                    print("❌ Неверный выбор. Попробуйте снова.")
                    input("\nНажмите Enter для продолжения...")
                
            except KeyboardInterrupt:
                print("\n👋 До свидания!")
                return False
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                input("\nНажмите Enter для продолжения...")
    
    async def run_session_menu(self):
        """Запускает меню работы с сессией"""
        while True:
            self.show_session_menu()
            
            try:
                choice = input("Выберите действие (0-5): ").strip()
                
                if choice == "0":
                    print("👋 До свидания!")
                    return "exit"  # Полный выход из программы
                elif choice == "1":
                    await self.handle_session_diagnosis()
                elif choice == "2":
                    await self.handle_session_logout()
                elif choice == "3":
                    await self.handle_session_info()
                elif choice == "4":
                    await self.handle_session_create()
                elif choice == "5":
                    return "back"  # Возврат в главное меню
                else:
                    print("❌ Неверный выбор. Попробуйте снова.")
                
                input("\nНажмите Enter для продолжения...")
                print("\n" + "="*50 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 До свидания!")
                return "exit"
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                input("\nНажмите Enter для продолжения...")
    
    async def run_chats_menu(self):
        """Запускает меню действий с чатами"""
        limit = 50  # По умолчанию
        
        while True:
            self.show_chats_menu()
            
            try:
                choice = input("Выберите действие (0-5): ").strip()
                
                if choice == "0":
                    print("👋 До свидания!")
                    return "exit"  # Полный выход из программы
                elif choice == "1":
                    await self.handle_simple_chats(limit)
                elif choice == "2":
                    await self.handle_detailed_chats(limit)
                elif choice == "3":
                    limit = self.handle_settings(limit)
                elif choice == "4":
                    self.show_saved_files()
                elif choice == "5":
                    return "back"  # Возврат в главное меню
                else:
                    print("❌ Неверный выбор. Попробуйте снова.")
                
                input("\nНажмите Enter для продолжения...")
                print("\n" + "="*50 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 До свидания!")
                return "exit"
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                input("\nНажмите Enter для продолжения...")
    
    # === МЕТОДЫ РАБОТЫ С СЕССИЕЙ ===
    
    async def handle_session_diagnosis(self):
        """Обрабатывает диагностику сессии"""
        print("🔍 Диагностика сессии...")
        
        # Проверка конфигурации
        config_ok = self.check_configuration()
        if not config_ok:
            print("❌ Диагностика прервана: проблемы с конфигурацией")
            return
        
        # Проверка существования файла
        file_exists = self.session_exists()
        
        # Проверка валидности сессии
        session_valid = False
        if file_exists:
            session_valid = await self.check_session()
        
        # Вывод результатов
        print("📊 Результаты диагностики:")
        print(f"   ✅ Конфигурация: {'OK' if config_ok else 'FAIL'}")
        print(f"   📁 Файл сессии: {'OK' if file_exists else 'MISSING'}")
        print(f"   🔐 Валидность сессии: {'OK' if session_valid else 'INVALID'}")
        
        if not file_exists or not session_valid:
            print("💡 Рекомендация: создайте новую сессию")
    
    async def handle_session_logout(self):
        """Обрабатывает выход из сессии"""
        print("🚪 Выход из сессии...")
        
        if not self.check_configuration():
            return
        
        try:
            # Подключаемся к существующей сессии
            if not await self.tg_mtproto.connect():
                self.logger.error("❌ Не удалось подключиться к существующей сессии")
                return
            
            client = self.tg_mtproto.get_client()
            if not client:
                self.logger.error("❌ Клиент не найден")
                return
            
            # Получаем информацию о текущем пользователе
            me = await client.get_me()
            self.logger.info(f"👤 Текущий пользователь: {me.first_name} (@{me.username})")
            
            # Выходим из сессии
            self.logger.info("🔄 Выходим из текущей сессии...")
            await client.log_out()
            
            # Отключаемся
            await self.tg_mtproto.disconnect()
            
            self.logger.info("✅ Выход выполнен успешно!")
            self.logger.info("🔄 Теперь можно создать новую сессию")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка выхода из сессии: {e}")
    
    async def handle_session_info(self):
        """Обрабатывает показ информации о сессии"""
        print("📁 Информация о сессии...")
        
        session_path = self.get_session_path()
        session_file = Path(session_path)
        
        if session_file.exists():
            size = session_file.stat().st_size
            print(f"📁 Путь к сессии: {session_path}")
            print(f"📊 Размер файла: {size} байт")
            print(f"📅 Дата создания: {datetime.fromtimestamp(session_file.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📅 Дата изменения: {datetime.fromtimestamp(session_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("❌ Файл сессии не найден")
    
    async def handle_session_create(self):
        """Обрабатывает создание новой сессии"""
        print("🆕 Создание новой сессии...")
        
        if not self.check_configuration():
            return
        
        try:
            # Сначала проверяем, есть ли уже авторизованная сессия
            try:
                import asyncio
                connect_task = asyncio.create_task(self.tg_mtproto.connect())
                connected = await asyncio.wait_for(connect_task, timeout=10.0)
                
                if connected:
                    # Получаем информацию о пользователе
                    client = self.tg_mtproto.get_client()
                    if client:
                        me = await client.get_me()
                        self.logger.info("✅ Сессия уже существует и авторизована")
                        self.logger.info(f"👤 Авторизован как: {me.first_name} (@{me.username})")
                        await self.tg_mtproto.disconnect()
                        return
            except asyncio.TimeoutError:
                self.logger.warning("⚠️ Таймаут при подключении к существующей сессии")
            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка при проверке существующей сессии: {e}")
            
            # Если сессия не авторизована, начинаем процесс авторизации
            self.logger.info("🔄 Начинаем процесс авторизации...")
            self.logger.info("📱 Введите номер телефона в международном формате (например: +79001234567)")
            
            # Создаем клиент и запускаем процесс авторизации
            client = await self.tg_mtproto.create_client()
            if not client:
                self.logger.error("❌ Не удалось создать клиент")
                return
            
            # Подключаемся
            await client.connect()
            
            # Запускаем процесс авторизации
            await client.start()
            
            # Получаем информацию о пользователе
            me = await client.get_me()
            self.logger.info("✅ Авторизация успешна!")
            self.logger.info(f"👤 Авторизован как: {me.first_name} (@{me.username})")
            self.logger.info(f"📁 Сессия сохранена в: {self.get_session_path()}")
            
            # Отключаемся
            await client.disconnect()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания сессии: {e}")
    
    # === МЕТОДЫ РАБОТЫ С ЧАТАМИ ===
    
    async def handle_simple_chats(self, limit: int):
        """Обрабатывает получение простого списка чатов"""
        print("🔍 Получение простого списка чатов...")
        
        if not await self.connect_to_telegram():
            return
        
        try:
            chats_list = await self.get_simple_chats_list(limit)
            
            if chats_list:
                self.show_chats_preview(chats_list)
                
                # Сохраняем в файл
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"chats_simple_{timestamp}.json"
                file_path = await self.save_to_file(chats_list, filename, "simple")
                
                if file_path:
                    print(f"✅ Простой список сохранен: {file_path}")
                else:
                    print("❌ Ошибка сохранения файла")
            else:
                print("❌ Не удалось получить список чатов")
        
        finally:
            await self.disconnect_from_telegram()
    
    async def handle_detailed_chats(self, limit: int):
        """Обрабатывает получение детального списка чатов"""
        print("📋 Получение детального списка чатов...")
        
        if not await self.connect_to_telegram():
            return
        
        try:
            chats_list = await self.get_detailed_chats_list(limit)
            
            if chats_list:
                self.show_chats_preview(chats_list)
                
                # Сохраняем в файл
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"chats_detailed_{timestamp}.json"
                file_path = await self.save_to_file(chats_list, filename, "detailed")
                
                if file_path:
                    print(f"✅ Детальный список сохранен: {file_path}")
                else:
                    print("❌ Ошибка сохранения файла")
            else:
                print("❌ Не удалось получить список чатов")
        
        finally:
            await self.disconnect_from_telegram()
    
    def handle_settings(self, current_limit: int) -> int:
        """Обрабатывает настройки"""
        print("⚙️ Настройки:")
        print(f"Текущий лимит чатов: {current_limit}")
        
        try:
            new_limit = int(input("Введите новый лимит чатов (1-200): ").strip())
            if 1 <= new_limit <= 200:
                print(f"✅ Лимит изменен на {new_limit}")
                return new_limit
            else:
                print("❌ Лимит должен быть от 1 до 200")
                return current_limit
        except ValueError:
            print("❌ Неверный формат числа")
            return current_limit
    
    def show_saved_files(self):
        """Показывает сохраненные файлы"""
        print("📁 Сохраненные файлы:")
        print("-" * 30)
        
        if not self.temp_dir.exists():
            print("❌ Папка temp не существует")
            return
        
        files = list(self.temp_dir.glob("chats_*.json"))
        
        if not files:
            print("📭 Файлы не найдены")
            return
        
        for i, file_path in enumerate(files, 1):
            file_size = file_path.stat().st_size / 1024  # KB
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            print(f"{i}. {file_path.name}")
            print(f"   Размер: {file_size:.1f} KB")
            print(f"   Дата: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def get_session_path(self) -> str:
        """Получает путь к сессии"""
        return self.tg_mtproto.core.session_path
    
    def check_configuration(self) -> bool:
        """Проверяет наличие необходимых настроек"""
        try:
            settings = self.settings_manager.get_plugin_settings('tg_mtproto')
            if not settings:
                self.logger.error("❌ Настройки tg_mtproto не найдены")
                return False
            
            api_id_str = settings.get('api_id', '')
            api_hash = settings.get('api_hash', '')
            
            if not api_id_str:
                self.logger.error("❌ API ID не установлен в переменных окружения MTPROTO_API_ID")
                return False
            
            if not api_hash:
                self.logger.error("❌ API Hash не установлен в переменных окружения MTPROTO_API_HASH")
                return False
            
            try:
                int(api_id_str)
            except ValueError:
                self.logger.error(f"❌ API ID должен быть числом, получено: '{api_id_str}'")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки конфигурации: {e}")
            return False
    
    def session_exists(self) -> bool:
        """Проверяет существование файла сессии"""
        session_file = Path(self.get_session_path())
        exists = session_file.exists()
        if exists:
            size = session_file.stat().st_size
            self.logger.info(f"📁 Сессия найдена: {self.get_session_path()} ({size} байт)")
        else:
            self.logger.info(f"📁 Сессия не найдена: {self.get_session_path()}")
        return exists
    
    async def check_session(self) -> bool:
        """Проверяет существующую сессию"""
        if not self.session_exists():
            self.logger.warning("⚠️ Файл сессии не найден")
            return False
        
        try:
            import asyncio
            connect_task = asyncio.create_task(self.tg_mtproto.connect())
            connected = await asyncio.wait_for(connect_task, timeout=10.0)
            
            if connected:
                client = self.tg_mtproto.get_client()
                if client:
                    me = await client.get_me()
                    self.logger.info("✅ Сессия валидна и авторизована")
                    self.logger.info(f"👤 Авторизован как: {me.first_name} (@{me.username})")
                    await self.tg_mtproto.disconnect()
                    return True
            
            self.logger.warning("⚠️ Сессия найдена, но не авторизована")
            return False
                
        except asyncio.TimeoutError:
            self.logger.warning("⚠️ Таймаут при проверке сессии")
            return False
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки сессии: {e}")
            return False
    
    async def connect_to_telegram(self) -> bool:
        """Подключается к Telegram"""
        try:
            print("🔄 Подключение к Telegram...")
            
            if not await self.tg_mtproto.connect():
                self.logger.error("❌ Не удалось подключиться к MTProto API")
                return False
            
            client = self.tg_mtproto.get_client()
            if not client:
                self.logger.error("❌ Клиент не найден")
                return False
            
            print("✅ Подключение к Telegram успешно!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка подключения: {e}")
            return False
    
    async def disconnect_from_telegram(self):
        """Отключается от Telegram"""
        try:
            await self.tg_mtproto.disconnect()
            print("✅ Отключение от Telegram успешно!")
        except Exception as e:
            self.logger.error(f"❌ Ошибка отключения: {e}")
    
    async def get_simple_chats_list(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает простой список чатов"""
        try:
            print(f"🔄 Получаем простой список чатов (лимит: {limit})...")
            
            client = self.tg_mtproto.get_client()
            if not client:
                return []
            
            # Получаем диалоги
            dialogs = await self.tg_mtproto.safe_api_call(
                client.get_dialogs, limit=limit
            )
            
            if not dialogs:
                self.logger.warning("⚠️ Диалоги не найдены")
                return []
            
            chats_list = []
            
            for dialog in dialogs:
                entity = dialog.entity
                message = dialog.message
                
                # Простая информация
                chat_info = {
                    'id': entity.id,
                    'type': type(entity).__name__,
                    'title': getattr(entity, 'title', 'Без названия'),
                    'username': getattr(entity, 'username', None),
                    'first_name': getattr(entity, 'first_name', None),
                    'last_name': getattr(entity, 'last_name', None),
                    'unread_count': dialog.unread_count,
                    'pinned': dialog.pinned,
                    'last_message_date': message.date.isoformat() if message else None,
                    'last_message_text': getattr(message, 'message', '') if message else None
                }
                chats_list.append(chat_info)
            
            self.logger.info(f"✅ Получено {len(chats_list)} чатов (простой формат)")
            return chats_list
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения простого списка чатов: {e}")
            return []
    
    async def get_detailed_chats_list(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает детальный список чатов"""
        try:
            print(f"🔄 Получаем детальный список чатов (лимит: {limit})...")
            
            client = self.tg_mtproto.get_client()
            if not client:
                return []
            
            # Получаем диалоги
            dialogs = await self.tg_mtproto.safe_api_call(
                client.get_dialogs, limit=limit
            )
            
            if not dialogs:
                self.logger.warning("⚠️ Диалоги не найдены")
                return []
            
            chats_list = []
            
            for dialog in dialogs:
                chat_info = self.parse_dialog_to_dict(dialog)
                chats_list.append(chat_info)
            
            self.logger.info(f"✅ Получено {len(chats_list)} чатов (детальный формат)")
            return chats_list
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения детального списка чатов: {e}")
            return []
    
    def parse_dialog_to_dict(self, dialog) -> Dict[str, Any]:
        """Парсит диалог в словарь (детальный формат)"""
        try:
            entity = dialog.entity
            message = dialog.message
            
            # Базовая информация о чате
            chat_info = {
                'id': entity.id,
                'type': self.get_entity_type(entity),
                'title': self.get_entity_title(entity),
                'username': getattr(entity, 'username', None),
                'first_name': getattr(entity, 'first_name', None),
                'last_name': getattr(entity, 'last_name', None),
                'phone': getattr(entity, 'phone', None),
                'verified': getattr(entity, 'verified', False),
                'premium': getattr(entity, 'premium', False),
                'bot': getattr(entity, 'bot', False),
                'scam': getattr(entity, 'scam', False),
                'fake': getattr(entity, 'fake', False),
                'participants_count': getattr(entity, 'participants_count', None),
                'photo': self.get_photo_info(entity),
                'last_message': self.get_last_message_info(message) if message else None,
                'unread_count': dialog.unread_count,
                'pinned': dialog.pinned,
                'archived': dialog.archived,
                'folder_id': dialog.folder_id,
                'date': dialog.date.isoformat() if dialog.date else None
            }
            
            return chat_info
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка парсинга диалога: {e}")
            return {'id': 'unknown', 'type': 'unknown', 'title': 'Ошибка парсинга'}
    
    def get_entity_type(self, entity) -> str:
        """Определяет тип entity"""
        entity_type = type(entity).__name__
        
        if 'User' in entity_type:
            return 'user'
        elif 'Chat' in entity_type:
            return 'group'
        elif 'Channel' in entity_type:
            if getattr(entity, 'megagroup', False):
                return 'supergroup'
            elif getattr(entity, 'broadcast', False):
                return 'channel'
            else:
                return 'channel'
        else:
            return 'unknown'
    
    def get_entity_title(self, entity) -> str:
        """Получает название entity"""
        if hasattr(entity, 'title'):
            return entity.title
        elif hasattr(entity, 'first_name'):
            first_name = entity.first_name or ''
            last_name = getattr(entity, 'last_name', '') or ''
            return f"{first_name} {last_name}".strip()
        else:
            return 'Без названия'
    
    def get_photo_info(self, entity) -> Dict[str, Any]:
        """Получает информацию о фото"""
        photo = getattr(entity, 'photo', None)
        if not photo:
            return None
        
        photo_type = type(photo).__name__
        if photo_type == 'ChatPhotoEmpty':
            return {'type': 'empty'}
        
        photo_info = {
            'type': photo_type,
            'photo_id': getattr(photo, 'photo_id', None),
            'dc_id': getattr(photo, 'dc_id', None),
            'has_video': getattr(photo, 'has_video', False)
        }
        
        stripped_thumb = getattr(photo, 'stripped_thumb', None)
        if stripped_thumb:
            if isinstance(stripped_thumb, bytes):
                photo_info['stripped_thumb'] = stripped_thumb.hex()
            else:
                photo_info['stripped_thumb'] = str(stripped_thumb)
        
        return photo_info
    
    def get_last_message_info(self, message) -> Dict[str, Any]:
        """Получает информацию о последнем сообщении"""
        if not message:
            return None
        
        return {
            'id': message.id,
            'text': getattr(message, 'message', ''),
            'date': message.date.isoformat() if message.date else None,
            'out': getattr(message, 'out', False),
            'mentioned': getattr(message, 'mentioned', False),
            'media_unread': getattr(message, 'media_unread', False),
            'silent': getattr(message, 'silent', False),
            'post': getattr(message, 'post', False),
            'from_scheduled': getattr(message, 'from_scheduled', False),
            'legacy': getattr(message, 'legacy', False),
            'edit_hide': getattr(message, 'edit_hide', False),
            'pinned': getattr(message, 'pinned', False),
            'noforwards': getattr(message, 'noforwards', False),
            'media': self.get_media_info(message)
        }
    
    def get_media_info(self, message) -> Dict[str, Any]:
        """Получает информацию о медиа"""
        media = getattr(message, 'media', None)
        if not media:
            return None
        
        media_type = type(media).__name__
        media_info = {'type': media_type}
        
        # Обрабатываем фото
        photo = getattr(media, 'photo', None)
        if photo:
            media_info['photo'] = {
                'id': getattr(photo, 'id', None),
                'access_hash': getattr(photo, 'access_hash', None),
                'file_reference': getattr(photo, 'file_reference', None)
            }
        
        # Обрабатываем документ
        document = getattr(media, 'document', None)
        if document:
            media_info['document'] = {
                'id': getattr(document, 'id', None),
                'access_hash': getattr(document, 'access_hash', None),
                'file_reference': getattr(document, 'file_reference', None),
                'mime_type': getattr(document, 'mime_type', None),
                'size': getattr(document, 'size', None)
            }
        
        return media_info
    
    def clean_for_json(self, obj):
        """Очищает объект от несериализуемых типов для JSON"""
        if isinstance(obj, dict):
            return {key: self.clean_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.clean_for_json(item) for item in obj]
        elif isinstance(obj, bytes):
            return obj.hex()
        elif hasattr(obj, '__dict__'):
            return str(obj)
        else:
            return obj
    
    async def save_to_file(self, chats_list: List[Dict[str, Any]], filename: str, format_type: str = "simple"):
        """Сохраняет список чатов в файл"""
        try:
            file_path = self.temp_dir / filename
            
            # Подготавливаем данные для сохранения
            data = {
                'timestamp': datetime.now().isoformat(),
                'format_type': format_type,
                'total_chats': len(chats_list),
                'chats': chats_list
            }
            
            # Очищаем данные от несериализуемых объектов
            clean_data = self.clean_for_json(data)
            
            # Сохраняем в JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(clean_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ Список чатов сохранен в файл: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения файла: {e}")
            return None
    
    def show_chats_preview(self, chats_list: List[Dict[str, Any]], limit: int = 5):
        """Показывает превью чатов"""
        print(f"\n📋 Превью первых {limit} чатов:")
        print("-" * 50)
        
        for i, chat in enumerate(chats_list[:limit]):
            title = chat.get('title', 'Без названия')
            chat_type = chat.get('type', 'unknown')
            chat_id = chat.get('id', 'unknown')
            username = chat.get('username', '')
            
            username_str = f" (@{username})" if username else ""
            print(f"{i+1}. {title}{username_str}")
            print(f"   Тип: {chat_type} | ID: {chat_id}")
            print()
    
    async def run_interactive(self):
        """Запускает интерактивный режим"""
        self.print_header()
        
        # Инициализируем сервис
        if not await self.initialize():
            print("❌ Ошибка инициализации сервиса")
            return
        
        # Запускаем главное меню
        await self.run_main_menu()
        
        # Корректное завершение DI-контейнера
        if self.di_container:
            self.di_container.shutdown()


async def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MTProto Manager - Универсальный менеджер для работы с Telegram')
    parser.add_argument('--simple', action='store_true', help='Получить простой список чатов (неинтерактивный режим)')
    parser.add_argument('--detailed', action='store_true', help='Получить детальный список чатов (неинтерактивный режим)')
    parser.add_argument('--limit', type=int, default=50, help='Лимит чатов (по умолчанию: 50)')
    
    args = parser.parse_args()
    
    manager = MTProtoManager()
    
    try:
        if args.simple:
            # Неинтерактивный режим - простой список
            if await manager.initialize():
                if await manager.connect_to_telegram():
                    try:
                        chats_list = await manager.get_simple_chats_list(args.limit)
                        if chats_list:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"chats_simple_{timestamp}.json"
                            file_path = await manager.save_to_file(chats_list, filename, "simple")
                            if file_path:
                                print(f"✅ Простой список сохранен: {file_path}")
                    finally:
                        await manager.disconnect_from_telegram()
        elif args.detailed:
            # Неинтерактивный режим - детальный список
            if await manager.initialize():
                if await manager.connect_to_telegram():
                    try:
                        chats_list = await manager.get_detailed_chats_list(args.limit)
                        if chats_list:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"chats_detailed_{timestamp}.json"
                            file_path = await manager.save_to_file(chats_list, filename, "detailed")
                            if file_path:
                                print(f"✅ Детальный список сохранен: {file_path}")
                    finally:
                        await manager.disconnect_from_telegram()
        else:
            # Интерактивный режим
            await manager.run_interactive()
    finally:
        # Корректное завершение DI-контейнера
        if manager.di_container:
            manager.di_container.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
