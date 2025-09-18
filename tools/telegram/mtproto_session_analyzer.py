#!/usr/bin/env python3
"""
Интерактивный анализатор MTProto сессии
Позволяет просматривать кэш entities и искать конкретные записи
"""

import sqlite3
import os
import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from plugins.utilities.foundation.settings_manager.settings_manager import SettingsManager
    from plugins.utilities.foundation.logger.logger import Logger
    from plugins.utilities.foundation.plugins_manager.plugins_manager import PluginsManager
except ImportError:
    print("❌ Не удалось импортировать утилиты проекта")
    print("Убедитесь, что вы запускаете скрипт из корня проекта")
    sys.exit(1)


class SessionAnalyzer:
    """Интерактивный анализатор MTProto сессии"""
    
    def __init__(self):
        # Инициализируем утилиты проекта
        self.logger = Logger()
        self.plugins_manager = PluginsManager(logger=self.logger)
        self.settings_manager = SettingsManager(logger=self.logger, plugins_manager=self.plugins_manager)
        
        # Определяем путь к файлу сессии
        self.project_root = Path(self.settings_manager.get_project_root())
        self.session_path = self.project_root / 'data' / 'sessions' / 'mtproto_session.session'
        
        # Проверяем существование файла
        if not self.session_path.exists():
            print(f"❌ Файл сессии не найден: {self.session_path}")
            print("Убедитесь, что MTProto сессия создана и файл существует")
            sys.exit(1)
    
    def print_header(self):
        """Выводит заголовок утилиты"""
        print("🔍 Анализатор MTProto сессии")
        print("=" * 50)
        print(f"📁 Файл сессии: {self.session_path}")
        print(f"📊 Размер файла: {self.session_path.stat().st_size / 1024 / 1024:.2f} МБ")
        print()
    
    def get_entities_count(self):
        """Получает количество entities в кэше"""
        try:
            conn = sqlite3.connect(self.session_path)
            cursor = conn.cursor()
            
            # Общее количество entities
            cursor.execute("SELECT COUNT(*) FROM entities")
            total_count = cursor.fetchone()[0]
            
            # Пользователи (ID > 0)
            cursor.execute("SELECT COUNT(*) FROM entities WHERE id > 0")
            users_count = cursor.fetchone()[0]
            
            # Группы (ID < 0 и ID > -1000000000000)
            cursor.execute("SELECT COUNT(*) FROM entities WHERE id < 0 AND id > -1000000000000")
            groups_count = cursor.fetchone()[0]
            
            # Каналы (ID < -1000000000000)
            cursor.execute("SELECT COUNT(*) FROM entities WHERE id < -1000000000000")
            channels_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total': total_count,
                'users': users_count,
                'groups': groups_count,
                'channels': channels_count
            }
            
        except sqlite3.Error as e:
            print(f"❌ Ошибка при чтении кэша: {e}")
            return None
    
    def show_cache_info(self):
        """Показывает общую информацию о кэше"""
        print("📊 ИНФОРМАЦИЯ О КЭШЕ:")
        print("-" * 30)
        
        counts = self.get_entities_count()
        if counts:
            print(f"👥 Всего entities: {counts['total']}")
            print(f"👤 Пользователи: {counts['users']}")
            print(f"💬 Группы: {counts['groups']}")
            print(f"📢 Каналы: {counts['channels']}")
        else:
            print("❌ Не удалось получить информацию о кэше")
        
        print()
    
    def show_entities_examples(self, limit=5):
        """Показывает примеры entities из кэша"""
        print(f"🔍 ПРИМЕРЫ ENTITIES (первые {limit} записей):")
        print("-" * 40)
        
        try:
            conn = sqlite3.connect(self.session_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, username, name, date FROM entities ORDER BY date DESC LIMIT ?", (limit,))
            entities = cursor.fetchall()
            
            if entities:
                for i, entity in enumerate(entities, 1):
                    entity_id, username, name, date = entity
                    
                    # Определяем тип
                    if entity_id > 0:
                        entity_type = "👤 Пользователь"
                    elif entity_id < -1000000000000:
                        entity_type = "📢 Канал"
                    else:
                        entity_type = "💬 Группа"
                    
                    print(f"{i}. {entity_type}")
                    print(f"   ID: {entity_id}")
                    print(f"   Username: {username or 'Нет'}")
                    print(f"   Name: {name or 'Нет'}")
                    print(f"   Date: {date}")
                    print()
            else:
                print("❌ Entities не найдены в кэше")
            
            conn.close()
            
        except sqlite3.Error as e:
            print(f"❌ Ошибка при чтении entities: {e}")
    
    def search_entity_by_id(self, entity_id):
        """Ищет entity по ID"""
        print(f"🔍 ПОИСК ENTITY ПО ID: {entity_id}")
        print("-" * 35)
        
        try:
            conn = sqlite3.connect(self.session_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, username, name, date FROM entities WHERE id = ?", (entity_id,))
            entity = cursor.fetchone()
            
            if entity:
                entity_id, username, name, date = entity
                
                # Определяем тип
                if entity_id > 0:
                    entity_type = "👤 Пользователь"
                elif entity_id < -1000000000000:
                    entity_type = "📢 Канал"
                else:
                    entity_type = "💬 Группа"
                
                print(f"✅ Entity найдена в кэше!")
                print(f"Тип: {entity_type}")
                print(f"ID: {entity_id}")
                print(f"Username: {username or 'Нет'}")
                print(f"Name: {name or 'Нет'}")
                print(f"Date: {date}")
                
                # Проверяем доступ
                if entity_id > 0:
                    print(f"🔑 Доступ: Пользователь доступен для взаимодействия")
                elif entity_id < -1000000000000:
                    print(f"🔑 Доступ: Канал доступен для взаимодействия")
                else:
                    print(f"🔑 Доступ: Группа доступна для взаимодействия")
                
            else:
                print(f"❌ Entity с ID {entity_id} НЕ найдена в кэше")
                print("Это означает, что у вас нет доступа к этому чату/пользователю")
            
            conn.close()
            
        except sqlite3.Error as e:
            print(f"❌ Ошибка при поиске entity: {e}")
        
        print()
    
    def show_menu(self):
        """Показывает главное меню"""
        print("📋 ГЛАВНОЕ МЕНЮ:")
        print("1. 📊 Показать информацию о кэше")
        print("2. 🔍 Показать примеры entities")
        print("3. 🎯 Поиск entity по ID")
        print("4. 🔄 Обновить информацию")
        print("0. ❌ Выход")
        print()
    
    def run_interactive(self):
        """Запускает интерактивный режим"""
        self.print_header()
        
        while True:
            self.show_menu()
            
            try:
                choice = input("Выберите действие (0-4): ").strip()
                
                if choice == "0":
                    print("👋 До свидания!")
                    break
                elif choice == "1":
                    self.show_cache_info()
                elif choice == "2":
                    self.show_entities_examples()
                elif choice == "3":
                    try:
                        entity_id = int(input("Введите ID entity для поиска: ").strip())
                        self.search_entity_by_id(entity_id)
                    except ValueError:
                        print("❌ Неверный формат ID. Введите число.")
                elif choice == "4":
                    print("🔄 Информация обновлена!")
                    self.print_header()
                else:
                    print("❌ Неверный выбор. Попробуйте снова.")
                
                input("\nНажмите Enter для продолжения...")
                print("\n" + "="*50 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 До свидания!")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                input("\nНажмите Enter для продолжения...")


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Анализатор MTProto сессии')
    parser.add_argument('--id', type=int, help='Поиск entity по ID (неинтерактивный режим)')
    parser.add_argument('--info', action='store_true', help='Показать только информацию о кэше')
    parser.add_argument('--examples', action='store_true', help='Показать только примеры entities')
    
    args = parser.parse_args()
    
    analyzer = SessionAnalyzer()
    
    if args.id:
        # Неинтерактивный режим - поиск по ID
        analyzer.print_header()
        analyzer.search_entity_by_id(args.id)
    elif args.info:
        # Неинтерактивный режим - только информация
        analyzer.print_header()
        analyzer.show_cache_info()
    elif args.examples:
        # Неинтерактивный режим - только примеры
        analyzer.print_header()
        analyzer.show_entities_examples()
    else:
        # Интерактивный режим
        analyzer.run_interactive()


if __name__ == "__main__":
    main()
