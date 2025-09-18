#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import platform
import shutil
import subprocess
import tempfile
import zipfile
import datetime
from pathlib import Path

# === ГЛОБАЛЬНАЯ КОНФИГУРАЦИЯ ===
# Настройки репозиториев для разных версий
VERSIONS = {
    'base': {
        'name': "Base",
        'description': "Базовая версия",
        #'repo_url': "https://github.com/Vensus137/Coreness",
        'repo_url': "https://github.com/Vensus137/alpha-test-01",
        'branch': "main",
        'update_token_env': None  # Base версия не требует токена
    },
    'pro': {
        'name': "Pro", 
        'description': "Профессиональная версия",
        'repo_url': "https://github.com/Vensus137/coreness-pro",
        'branch': "main",
        'update_token_env': "UPDATE_TOKEN_PRO"
    }
}

# Папки и файлы для чистой синхронизации (удаляются и пересоздаются)
CLEAN_SYNC_ITEMS = [
    "plugins",              # Полная синхронизация всех плагинов
    "tools",                # Полная синхронизация инструментов
    "app",                  # Полная синхронизация приложения
    "docker"                # Полная синхронизация Docker конфигурации
]

# Файлы из корня проекта (обновляются обычным способом)
ROOT_FILES = [
    "main.py",              # Главный файл приложения
    "requirements.txt",     # Зависимости Python
    "README.md",            # Документация
    "LICENSE_BASE",         # Лицензия Base версии
    "LICENSE_PRO",          # Лицензия Pro версии
    "env.example"           # Пример переменных окружения
]

# Заводские конфиги (обновляются отдельно по запросу)
FACTORY_CONFIGS = [
    "config/settings.yaml",
    "config/presets/default",
    "resources"
]

# Папки для исключения из обновления (всегда исключаются)
EXCLUDE_PATHS = [
    "logs",
    "data", 
    ".git",
    ".github",
    ".gitignore"
]

# Настройки бэкапа
BACKUP_CONFIG = {
    'default_keep': True,  # По умолчанию сохранять бэкап
    'dir_name': ".core_update_backup"
}

# Цвета для вывода
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def load_config():
    """Возвращает конфигурацию из глобальных переменных"""
    return {
        'versions': VERSIONS,
        'clean_sync_items': CLEAN_SYNC_ITEMS,
        'root_files': ROOT_FILES,
        'factory_configs': FACTORY_CONFIGS,
        'exclude_paths': EXCLUDE_PATHS,
        'backup': BACKUP_CONFIG
    }

def print_header():
    print(f"{Colors.BLUE}{Colors.BOLD}================================{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}      CORENESS UPDATER          {Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}================================{Colors.END}")

def get_project_root():
    """Определяет корневую папку проекта на основе местоположения скрипта"""
    script_path = Path(__file__).resolve()
    script_dir = script_path.parent
    script_dir_name = script_dir.name
    script_parent_name = script_dir.parent.name
    
    # Проверяем, лежит ли скрипт в tools/core
    if script_dir_name == "core" and script_parent_name == "tools":
        # Скрипт в tools/core -> корень проекта на уровень выше tools
        return script_dir.parent.parent
    else:
        # Скрипт не в tools/core -> корень проекта в папке скрипта
        return script_dir

def check_location():
    """Проверяет папку где лежит скрипт и определяет доступные действия"""
    script_path = Path(__file__).resolve()
    script_dir = script_path.parent
    project_root = get_project_root()
    
    print(f"{Colors.CYAN}📁 Скрипт находится в: {script_dir}{Colors.END}")
    print(f"{Colors.CYAN}📁 Рабочая папка: {Path.cwd()}{Colors.END}")
    print(f"{Colors.CYAN}📁 Корень проекта: {project_root}{Colors.END}")
    
    # Проверяем, лежит ли скрипт в tools/core
    if script_dir == project_root / "tools" / "core":
        print(f"{Colors.YELLOW}⚠️ ВНИМАНИЕ: Скрипт находится в папке tools/core!{Colors.END}")
        print(f"{Colors.YELLOW}   Первичная установка здесь НЕ РЕКОМЕНДУЕТСЯ!{Colors.END}")
        print(f"{Colors.YELLOW}   Это может поломать весь проект!{Colors.END}")
        print(f"{Colors.CYAN}💡 Рекомендация: Запустите скрипт из корневой папки проекта{Colors.END}")
        return "core"
    else:
        print(f"{Colors.YELLOW}⚠️ ВНИМАНИЕ: Скрипт НЕ в папке tools/core!{Colors.END}")
        print(f"{Colors.YELLOW}   Обновление ядра здесь НЕ РЕКОМЕНДУЕТСЯ!{Colors.END}")
        print(f"{Colors.YELLOW}   Это может привести к неожиданным результатам!{Colors.END}")
        print(f"{Colors.CYAN}💡 Рекомендация: Запустите скрипт из папки tools/core{Colors.END}")
        return "other"

def check_docker():
    """Проверяет наличие Docker и возвращает True если установлен"""
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"{Colors.GREEN}✅ Docker найден: {result.stdout.strip()}{Colors.END}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{Colors.RED}❌ Docker не найден!{Colors.END}")
        return False

def install_docker():
    """Устанавливает Docker Engine в зависимости от операционной системы"""
    import platform
    import subprocess
    
    system = platform.system().lower()
    print(f"{Colors.YELLOW}🔧 Определена система: {system}{Colors.END}")
    
    if system == "linux":
        print(f"{Colors.YELLOW}📦 Устанавливаем Docker Engine для Linux...{Colors.END}")
        try:
            # Проверяем наличие apt
            subprocess.run(['which', 'apt'], check=True, capture_output=True)
            print(f"{Colors.CYAN}💡 Используем apt для установки Docker Engine...{Colors.END}")
            
            # Обновляем пакеты
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            
            # Устанавливаем зависимости
            subprocess.run([
                'sudo', 'apt', 'install', '-y', 
                'apt-transport-https', 'ca-certificates', 'curl', 'gnupg', 'lsb-release'
            ], check=True)
            
            # Добавляем GPG ключ Docker
            subprocess.run([
                'curl', '-fsSL', 'https://download.docker.com/linux/ubuntu/gpg', 
                '|', 'sudo', 'gpg', '--dearmor', '-o', '/usr/share/keyrings/docker-archive-keyring.gpg'
            ], shell=True, check=True)
            
            # Добавляем репозиторий Docker
            subprocess.run([
                'echo', '"deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"',
                '|', 'sudo', 'tee', '/etc/apt/sources.list.d/docker.list'
            ], shell=True, check=True)
            
            # Обновляем пакеты и устанавливаем Docker
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'docker-ce', 'docker-ce-cli', 'containerd.io'], check=True)
            
            # Добавляем пользователя в группу docker
            subprocess.run(['sudo', 'usermod', '-aG', 'docker', os.getenv('USER')], check=True)
            
            print(f"{Colors.GREEN}✅ Docker Engine установлен через apt!{Colors.END}")
            print(f"{Colors.YELLOW}⚠️ Перезайдите в систему для применения изменений группы docker!{Colors.END}")
            
        except subprocess.CalledProcessError:
            try:
                # Проверяем наличие yum
                subprocess.run(['which', 'yum'], check=True, capture_output=True)
                print(f"{Colors.CYAN}💡 Используем yum для установки Docker Engine...{Colors.END}")
                
                # Устанавливаем зависимости
                subprocess.run(['sudo', 'yum', 'install', '-y', 'yum-utils'], check=True)
                
                # Добавляем репозиторий Docker
                subprocess.run(['sudo', 'yum-config-manager', '--add-repo', 'https://download.docker.com/linux/centos/docker-ce.repo'], check=True)
                
                # Устанавливаем Docker
                subprocess.run(['sudo', 'yum', 'install', '-y', 'docker-ce', 'docker-ce-cli', 'containerd.io'], check=True)
                
                # Запускаем и включаем Docker
                subprocess.run(['sudo', 'systemctl', 'start', 'docker'], check=True)
                subprocess.run(['sudo', 'systemctl', 'enable', 'docker'], check=True)
                
                # Добавляем пользователя в группу docker
                subprocess.run(['sudo', 'usermod', '-aG', 'docker', os.getenv('USER')], check=True)
                
                print(f"{Colors.GREEN}✅ Docker Engine установлен через yum!{Colors.END}")
                print(f"{Colors.YELLOW}⚠️ Перезайдите в систему для применения изменений группы docker!{Colors.END}")
                
            except subprocess.CalledProcessError:
                print(f"{Colors.RED}❌ Не удалось определить пакетный менеджер!{Colors.END}")
                return False
    elif system == "darwin":  # macOS
        print(f"{Colors.YELLOW}📦 Устанавливаем Docker Engine для macOS...{Colors.END}")
        print(f"{Colors.CYAN}💡 Используем Homebrew для установки Docker Engine...{Colors.END}")
        
        try:
            # Проверяем наличие Homebrew
            subprocess.run(['which', 'brew'], check=True, capture_output=True)
            
            # Устанавливаем Docker Engine через Homebrew
            subprocess.run(['brew', 'install', 'docker'], check=True)
            
            print(f"{Colors.GREEN}✅ Docker Engine установлен через Homebrew!{Colors.END}")
            print(f"{Colors.YELLOW}⚠️ Запустите Docker Engine: brew services start docker{Colors.END}")
            
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}❌ Homebrew не найден! Установите Homebrew или Docker Desktop вручную.{Colors.END}")
            return False
    elif system == "windows":
        print(f"{Colors.YELLOW}📦 Устанавливаем Docker Engine для Windows...{Colors.END}")
        print(f"{Colors.CYAN}💡 Рекомендуем использовать WSL2 + Docker Engine{Colors.END}")
        
        try:
            # Проверяем наличие WSL2
            subprocess.run(['wsl', '--version'], check=True, capture_output=True)
            print(f"{Colors.CYAN}💡 WSL2 найден, устанавливаем Docker Engine в WSL2...{Colors.END}")
            
            # Устанавливаем Docker Engine в WSL2
            subprocess.run(['wsl', 'sudo', 'apt', 'update'], check=True)
            subprocess.run(['wsl', 'sudo', 'apt', 'install', '-y', 'docker.io'], check=True)
            subprocess.run(['wsl', 'sudo', 'systemctl', 'start', 'docker'], check=True)
            subprocess.run(['wsl', 'sudo', 'systemctl', 'enable', 'docker'], check=True)
            
            print(f"{Colors.GREEN}✅ Docker Engine установлен в WSL2!{Colors.END}")
            print(f"{Colors.YELLOW}⚠️ Docker Engine работает в WSL2 окружении{Colors.END}")
            
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}❌ WSL2 не найден! Установите WSL2 или Docker Desktop вручную.{Colors.END}")
            return False
    else:
        print(f"{Colors.RED}❌ Неподдерживаемая операционная система: {system}{Colors.END}")
        return False
    
    return True

def download_docker_config():
    """Скачивает конфигурацию Docker из открытого репозитория"""
    import subprocess
    import os
    
    print(f"{Colors.YELLOW}📥 Скачиваем конфигурацию Docker...{Colors.END}")
    
    # Создаем временную папку для скачивания
    temp_dir = "docker-temp"
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)
    
    try:
        # Получаем URL Base версии из конфигурации
        config = load_config()
        base_repo_url = config['versions']['base']['repo_url']
        
        # Клонируем только папку docker из Base репозитория
        print(f"{Colors.CYAN}💡 Клонируем папку docker из Base репозитория...{Colors.END}")
        print(f"{Colors.CYAN}   URL: {base_repo_url}{Colors.END}")
        
        # Сначала клонируем репозиторий
        subprocess.run([
            'git', 'clone', '--depth', '1', 
            '--filter=blob:none', 
            base_repo_url,
            temp_dir
        ], check=True)
        
        # Настраиваем sparse-checkout для папки docker
        subprocess.run([
            'git', 'sparse-checkout', 'init', '--cone'
        ], cwd=temp_dir, check=True)
        
        subprocess.run([
            'git', 'sparse-checkout', 'set', 'docker'
        ], cwd=temp_dir, check=True)
        
        # Копируем папку docker в корень проекта
        import shutil
        if os.path.exists('docker'):
            shutil.rmtree('docker')
        shutil.copytree(f'{temp_dir}/docker', 'docker')
        
        # Удаляем временную папку (с обработкой прав доступа на Windows)
        try:
            shutil.rmtree(temp_dir)
        except PermissionError:
            # На Windows иногда нужно сбросить атрибуты файлов
            import stat
            def remove_readonly(func, path, exc):
                if os.path.exists(path):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
            shutil.rmtree(temp_dir, onerror=remove_readonly)
        
        print(f"{Colors.GREEN}✅ Конфигурация Docker скачана!{Colors.END}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Ошибка при скачивании конфигурации: {e}{Colors.END}")
        return False

def is_docker_running():
    """Проверяет, запущен ли Docker daemon"""
    try:
        subprocess.run(['docker', 'info'], capture_output=True, check=True)
        return True
    except:
        return False

def start_docker_engine():
    """Запускает Docker Engine"""
    try:
        system = platform.system()
        
        if system == "Windows":
            print(f"{Colors.CYAN}💡 Запускаем Docker Engine на Windows...{Colors.END}")
            # На Windows Docker Engine обычно работает через WSL2
            try:
                # Пытаемся запустить через WSL2
                subprocess.run(['wsl', 'sudo', 'systemctl', 'start', 'docker'], check=True)
                return True
            except:
                # Если WSL2 не работает, пробуем через Docker Desktop (fallback)
                print(f"{Colors.YELLOW}⚠️ WSL2 не доступен, пробуем Docker Desktop...{Colors.END}")
                try:
                    subprocess.run(['cmd', '/c', 'start', 'Docker Desktop'], check=True)
                    return True
                except:
                    return False
            
        elif system == "Darwin":  # macOS
            print(f"{Colors.CYAN}💡 Запускаем Docker Engine на macOS...{Colors.END}")
            # На macOS Docker Engine через Homebrew
            try:
                subprocess.run(['brew', 'services', 'start', 'docker'], check=True)
                return True
            except:
                # Fallback на Docker Desktop
                try:
                    subprocess.run(['open', '-a', 'Docker'], check=True)
                    return True
                except:
                    return False
            
        elif system == "Linux":
            print(f"{Colors.CYAN}💡 Запускаем Docker Engine на Linux...{Colors.END}")
            # На Linux Docker Engine как сервис
            subprocess.run(['sudo', 'systemctl', 'start', 'docker'], check=True)
            return True
            
        else:
            print(f"{Colors.RED}❌ Неизвестная ОС: {system}{Colors.END}")
            return False
            
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}❌ Не удалось запустить Docker Engine{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка при запуске Docker Engine: {e}{Colors.END}")
        return False

def is_container_running():
    """Проверяет, запущен ли контейнер"""
    try:
        result = subprocess.run([
            "docker-compose", "ps", "-q", "coreness"
        ], capture_output=True, text=True, cwd="docker")
        return bool(result.stdout.strip())
    except:
        return False

def start_container():
    """Запускает контейнер"""
    print(f"{Colors.YELLOW}🚀 Запускаю контейнер...{Colors.END}")
    subprocess.run(["docker-compose", "up", "-d"], check=True, cwd="docker")
    print(f"{Colors.GREEN}✅ Контейнер запущен!{Colors.END}")

def build_and_run_container():
    """Собирает и запускает Docker контейнер"""
    import subprocess
    import os
    
    print(f"{Colors.YELLOW}🔨 Собираем и запускаем Docker контейнер...{Colors.END}")
    
    if not os.path.exists('docker'):
        print(f"{Colors.RED}❌ Папка docker не найдена!{Colors.END}")
        return False
    
    # Проверяем, что Docker запущен
    if not is_docker_running():
        print(f"{Colors.RED}❌ Docker не запущен!{Colors.END}")
        
        # Пытаемся запустить Docker Engine автоматически
        print(f"{Colors.CYAN}💡 Пытаемся запустить Docker Engine...{Colors.END}")
        if start_docker_engine():
            print(f"{Colors.GREEN}✅ Docker запущен!{Colors.END}")
            # Ждем немного, чтобы Docker успел запуститься
            import time
            print(f"{Colors.YELLOW}⏳ Ждем запуска Docker...{Colors.END}")
            time.sleep(10)
            
            # Проверяем еще раз
            if is_docker_running():
                print(f"{Colors.GREEN}✅ Docker готов к работе!{Colors.END}")
            else:
                print(f"{Colors.RED}❌ Docker не запустился. Попробуйте запустить Docker вручную.{Colors.END}")
                return False
        else:
            print(f"{Colors.RED}❌ Не удалось запустить Docker автоматически.{Colors.END}")
            print(f"{Colors.YELLOW}💡 Запустите Docker вручную и попробуйте снова.{Colors.END}")
            return False
    
    try:
        # Переходим в папку docker
        os.chdir('docker')
        
        # Собираем образ
        print(f"{Colors.CYAN}💡 Собираем Docker образ...{Colors.END}")
        subprocess.run(['docker-compose', 'build'], check=True)
        
        # Запускаем контейнер
        print(f"{Colors.CYAN}💡 Запускаем Docker контейнер...{Colors.END}")
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        
        # Возвращаемся в корневую папку
        os.chdir('..')
        
        print(f"{Colors.GREEN}✅ Docker контейнер запущен!{Colors.END}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Ошибка при сборке/запуске контейнера: {e}{Colors.END}")
        return False

def run_database_migration():
    """Запускает миграцию базы данных через Docker (не ждет результата)"""
    print(f"{Colors.YELLOW}🗄 Запускаю миграцию базы данных через Docker...{Colors.END}")
    
    # Проверяем, что контейнер запущен
    if not is_container_running():
        print(f"{Colors.YELLOW}⚠️ Контейнер не запущен, запускаю...{Colors.END}")
        start_container()
    
    # Запускаем миграцию в фоне (не ждем результата)
    subprocess.Popen([
        "docker-compose", "exec", "coreness", 
        "python", "tools/database_manager.py", "--all", "--migrate"
    ], cwd="docker")
    
    print(f"{Colors.GREEN}✅ Миграция запущена в фоне!{Colors.END}")
    print(f"{Colors.CYAN}💡 Проверьте логи контейнера для отслеживания прогресса:{Colors.END}")
    print(f"{Colors.CYAN}   docker-compose logs -f coreness{Colors.END}")

def remove_installer_script():
    """Удаляет скрипт установки, если это была первичная установка"""
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    
    # Проверяем, находится ли скрипт в папке tools/ (любой подпапке)
    is_in_tools = "tools" in script_dir.split(os.sep)
    
    if not is_in_tools:
        try:
            os.remove(script_path)
            print(f"{Colors.GREEN}🗑 Скрипт установки удален: {script_path}{Colors.END}")
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Не удалось удалить скрипт установки: {e}{Colors.END}")
    else:
        print(f"{Colors.CYAN}💡 Скрипт находится в tools/, удаление не требуется{Colors.END}")

def run_initial_setup():
    print(f"{Colors.YELLOW}⚠️ ВНИМАНИЕ: Текущая папка станет корневой для Coreness.{Colors.END}")
    confirm = input("Вы уверены, что хотите продолжить первичную установку? (y/N): ")
    if confirm.lower() != 'y':
        print(f"{Colors.RED}❌ Установка отменена.{Colors.END}")
        return
    
    print(f"{Colors.GREEN}🚀 Запускаем первичную установку...{Colors.END}")
    
    # Этап 1: Проверка и установка Docker
    print(f"\n{Colors.BLUE}=== ЭТАП 1: Установка Docker ==={Colors.END}")
    if not check_docker():
        print(f"{Colors.YELLOW}📦 Docker не найден, начинаем установку...{Colors.END}")
        if not install_docker():
            print(f"{Colors.RED}❌ Не удалось установить Docker!{Colors.END}")
            return
    else:
        print(f"{Colors.GREEN}✅ Docker уже установлен!{Colors.END}")
    
    # Этап 2: Скачивание конфигурации Docker
    print(f"\n{Colors.BLUE}=== ЭТАП 2: Скачивание конфигурации ==={Colors.END}")
    if not download_docker_config():
        print(f"{Colors.RED}❌ Не удалось скачать конфигурацию Docker!{Colors.END}")
        return
    
    # Этап 3: Сборка и запуск контейнера
    print(f"\n{Colors.BLUE}=== ЭТАП 3: Сборка и запуск контейнера ==={Colors.END}")
    if not build_and_run_container():
        print(f"{Colors.RED}❌ Не удалось собрать/запустить контейнер!{Colors.END}")
        return
    
    print(f"\n{Colors.GREEN}🎉 Первичная установка завершена!{Colors.END}")
    print(f"{Colors.CYAN}💡 Теперь переходим к этапу обновления...{Colors.END}")
    
    # Переходим к этапу обновления
    run_core_update()

def get_available_versions(config):
    """Возвращает список доступных версий"""
    return list(config['versions'].keys())

def validate_version(version, config):
    """Проверяет корректность введенной версии"""
    return version.lower() in config['versions']

def get_version_info(version, config):
    """Возвращает информацию о версии"""
    return config['versions'].get(version.lower())

def get_github_token(version_info):
    """Получает GitHub токен для версии"""
    if version_info['update_token_env'] is None:
        print(f"{Colors.CYAN}ℹ️ Base версия - публичный репозиторий, токен не требуется{Colors.END}")
        return None
    
    token_env = version_info['update_token_env']
    token = os.getenv(token_env)
    if not token:
        print(f"{Colors.YELLOW}⚠️ Переменная окружения {token_env} не установлена{Colors.END}")
        return None
    return token

def request_manual_token():
    """Запрашивает токен вручную"""
    print(f"\n{Colors.YELLOW}🔑 Введите GitHub токен:{Colors.END}")
    
    while True:
        token = input("GitHub токен: ").strip()
        if token:
            return token
        print(f"{Colors.RED}❌ Токен не может быть пустым. Попробуйте снова.{Colors.END}")

def is_excluded(path, config):
    """Проверяет, исключен ли путь из обновления"""
    for excl in config['exclude_paths']:
        if path == excl:
            return True
        if excl.endswith('*'):
            pattern = excl[:-1]
            if path.startswith(pattern):
                return True
        if excl in path.split(os.sep):
            return True
    
    return False

def is_clean_sync_item(path, config):
    """Проверяет, нужно ли полностью синхронизировать элемент"""
    return path in config['clean_sync_items']

def is_factory_config(path, config):
    """Проверяет, является ли путь заводским конфигом"""
    return path in config['factory_configs']

def remove_old(path):
    """Удаляет старый файл или папку"""
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f"{Colors.YELLOW}🗑 Удалена папка: {path}{Colors.END}")
        else:
            os.remove(path)
            print(f"{Colors.YELLOW}🗑 Удален файл: {path}{Colors.END}")

def copy_new(src, dst):
    """Копирует новый файл или папку"""
    if os.path.isdir(src):
        shutil.copytree(src, dst)
        print(f"{Colors.GREEN}📁 Скопирована папка: {dst}{Colors.END}")
    else:
        shutil.copy2(src, dst)
        print(f"{Colors.GREEN}📄 Скопирован файл: {dst}{Colors.END}")

def create_backup(project_root, config, include_factory_configs=False):
    """Создает резервную копию проекта"""
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(project_root, f"{config['backup']['dir_name']}_{timestamp}")
    
    print(f"{Colors.YELLOW}🗂 Создаю резервную копию в {backup_dir}...{Colors.END}")
    
    os.makedirs(backup_dir, exist_ok=True)
    
    total_items = 0
    processed_items = 0
    
    # Подсчитываем общее количество элементов
    for item in os.listdir(project_root):
        if not is_excluded(item, config):
            if not include_factory_configs and is_factory_config(item, config):
                continue
            total_items += 1
    
    print(f"{Colors.CYAN}📁 Всего элементов для резервного копирования: {total_items}{Colors.END}")
    
    # Копируем все файлы и папки
    for item in os.listdir(project_root):
        if is_excluded(item, config):
            continue
            
        if not include_factory_configs and is_factory_config(item, config):
            continue
            
        try:
            processed_items += 1
            print(f"{Colors.CYAN}🗂 Копирую {processed_items}/{total_items}: {item}{Colors.END}")
            
            src_path = os.path.join(project_root, item)
            backup_path = os.path.join(backup_dir, item)
            
            if os.path.isdir(src_path):
                shutil.copytree(src_path, backup_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, backup_path)
        except Exception as e:
            print(f"{Colors.RED}⚠️ Ошибка копирования {item}: {e}{Colors.END}")
            continue
    
    print(f"{Colors.GREEN}✅ Резервное копирование завершено: {processed_items}/{total_items} элементов{Colors.END}")
    return backup_dir

def restore_backup(backup_dir, project_root):
    """Восстанавливает из резервной копии"""
    print(f"{Colors.YELLOW}⏪ Восстанавливаю из резервной копии...{Colors.END}")
    
    errors = []
    
    if not os.path.exists(backup_dir):
        print(f"{Colors.RED}⚠️ Не найден бэкап: {backup_dir}{Colors.END}")
        return ["backup_dir_not_found"]
    
    # Восстанавливаем все файлы из бэкапа
    for item in os.listdir(backup_dir):
        try:
            backup_path = os.path.join(backup_dir, item)
            target_path = os.path.join(project_root, item)
            
            if is_excluded(item):
                continue
            
            # Удаляем существующий файл/папку
            if os.path.exists(target_path):
                remove_old(target_path)
            
            # Восстанавливаем из бэкапа
            if os.path.isdir(backup_path):
                shutil.copytree(backup_path, target_path)
            else:
                shutil.copy2(backup_path, target_path)
                
        except Exception as e:
            print(f"{Colors.RED}❌ Ошибка восстановления {item}: {e}{Colors.END}")
            errors.append(item)
    
    return errors

def is_factory_config(path):
    """Проверяет, является ли путь заводским конфигом"""
    factory_configs = ["config", "resources"]
    return path in factory_configs

def download_and_update(version_info, github_token, project_root, update_factory_configs=False):
    """Скачивает и обновляет проект"""
    import tempfile
    import zipfile
    import requests
    
    print(f"{Colors.YELLOW}📥 Скачиваю {version_info['name']} версию...{Colors.END}")
    
    # Определяем заголовки для запроса
    if github_token:
        headers = {"Authorization": f"token {github_token}"}
        print(f"{Colors.CYAN}🔑 Подключаюсь с токеном для Pro версии...{Colors.END}")
    else:
        headers = {}
        print(f"{Colors.CYAN}🔓 Скачиваю Base версию без токена (публичный репозиторий)...{Colors.END}")
    
    try:
        # Скачиваем архив с GitHub
        repo_url = version_info['repo_url']
        branch = version_info['branch']
        
        # Пробуем разные методы скачивания
        download_methods = [
            f"{repo_url}/archive/refs/heads/{branch}.zip",
            f"{repo_url}/releases/latest/download/source.zip",
        ]
        
        print(f"{Colors.CYAN}🔽 Скачиваю из репозитория: {repo_url}{Colors.END}")
        print(f"{Colors.CYAN}   Ветка: {branch}{Colors.END}")
        
        # Пробуем разные методы скачивания
        response = None
        for i, zip_url in enumerate(download_methods, 1):
            print(f"{Colors.CYAN}   🔍 Метод {i}: {zip_url}{Colors.END}")
            
            try:
                response = requests.get(zip_url, headers=headers)
                if response.status_code == 200:
                    print(f"{Colors.GREEN}   ✅ Успешно! Размер: {len(response.content)} байт{Colors.END}")
                    break
                else:
                    print(f"{Colors.RED}   ❌ Статус: {response.status_code}{Colors.END}")
            except Exception as e:
                print(f"{Colors.RED}   ❌ Ошибка: {e}{Colors.END}")
        
        if not response or response.status_code != 200:
            raise Exception("Ошибка скачивания: все методы не удались")
            
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка скачивания: {e}{Colors.END}")
        raise
    
    # Обрабатываем скачанный архив
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "repo.zip")
        with open(zip_path, "wb") as f:
            f.write(response.content)

        # Распаковываем архив
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        # Определяем корневую папку исходников
        repo_root = None
        for name in os.listdir(tmpdir):
            if os.path.isdir(os.path.join(tmpdir, name)) and name.endswith(f"-{branch}"):
                repo_root = os.path.join(tmpdir, name)
                break
        
        if not repo_root:
            raise Exception("Не удалось найти корневую папку исходников после распаковки!")

        # Обновляем все файлы и папки из репозитория
        print(f"{Colors.YELLOW}♻️ Обновляю все файлы и папки...{Colors.END}")
        for item in os.listdir(repo_root):
            # Проверяем исключения
            if is_excluded(item):
                print(f"{Colors.CYAN}⏭ Пропускаю исключённый: {item}{Colors.END}")
                continue
            
            # Проверяем заводские конфиги
            if not update_factory_configs and is_factory_config(item):
                print(f"{Colors.CYAN}⏭ Пропускаю заводской конфиг: {item}{Colors.END}")
                continue
            
            abs_old = os.path.join(project_root, item)
            abs_new = os.path.join(repo_root, item)
            
            # Проверяем тип синхронизации
            if is_clean_sync_item(item):
                print(f"{Colors.YELLOW}🗑 Чистая синхронизация: {item}{Colors.END}")
                remove_old(abs_old)
                copy_new(abs_new, abs_old)
            else:
                print(f"{Colors.CYAN}♻️ Обновляю: {item}{Colors.END}")
                remove_old(abs_old)
                copy_new(abs_new, abs_old)

def run_core_update():
    print(f"{Colors.GREEN}🔄 Запускаем обновление ядра...{Colors.END}")
    
    # Определяем корневую папку проекта
    project_root = get_project_root()
    
    print(f"{Colors.CYAN}📁 Корневая папка проекта: {project_root}{Colors.END}")
    
    # Показываем доступные версии
    available_versions = get_available_versions()
    print(f"{Colors.YELLOW}📋 Доступные версии:{Colors.END}")
    for version in available_versions:
        version_info = get_version_info(version)
        print(f"  • {version.upper()}: {version_info['name']} - {version_info['description']}")
    
    # Запрашиваем версию
    while True:
        selected_version = input(f"\n{Colors.YELLOW}Введите версию для обновления ({', '.join(available_versions)}): {Colors.END}").strip().lower()
        if validate_version(selected_version):
            break
        print(f"{Colors.RED}❌ Неверная версия. Доступные: {', '.join(available_versions)}{Colors.END}")
    
    version_info = get_version_info(selected_version)
    print(f"\n{Colors.GREEN}✅ Выбрана версия: {version_info['name']} ({version_info['description']}){Colors.END}")
    
    # Запрашиваем обновление заводских конфигов
    update_factory_configs = input(f"\n{Colors.YELLOW}Обновить заводские конфиги (config, resources)? (Y/N, по умолчанию N): {Colors.END}").strip().lower() == 'y'
    
    if update_factory_configs:
        print(f"{Colors.YELLOW}🛠 Включено обновление заводских конфигов!{Colors.END}")
    else:
        print(f"{Colors.CYAN}📁 Заводские конфиги будут пропущены (обновляются отдельно){Colors.END}")
    
    # Создаем резервную копию
    backup_dir = create_backup(project_root)
    
    try:
        # Проверяем наличие токена
        github_token = get_github_token(version_info)
        
        if not github_token and version_info['update_token_env']:
            # Pro версия - пробуем с ручным токеном
            print(f"{Colors.YELLOW}❌ Не удалось получить токен из окружения{Colors.END}")
            print(f"{Colors.CYAN}ℹ️ Пробую запросить токен вручную...{Colors.END}")
            github_token = request_manual_token()
        
        # Скачиваем и обновляем
        download_and_update(version_info, github_token, project_root, update_factory_configs)
        
        print(f"{Colors.GREEN}✅ Обновление завершено успешно!{Colors.END}")
        
        # Запускаем миграцию базы данных
        print(f"\n{Colors.BLUE}=== ЭТАП: Миграция базы данных ==={Colors.END}")
        run_database_migration()
        
        # Спрашиваем про удаление бэкапа
        keep_backup = input(f"\n{Colors.YELLOW}Удалить резервную копию? (Y/N, по умолчанию N): {Colors.END}").strip().lower() == 'y'
        if keep_backup:
            shutil.rmtree(backup_dir)
            print(f"{Colors.GREEN}🗑 Резервная копия удалена.{Colors.END}")
        else:
            print(f"{Colors.CYAN}💾 Резервная копия сохранена в {backup_dir}{Colors.END}")
        
        print(f"\n{Colors.GREEN}🚀 Обновление завершено! Миграция БД запущена в фоне.{Colors.END}")
        print(f"{Colors.CYAN}💡 Проверьте логи контейнера для отслеживания миграции:{Colors.END}")
        print(f"{Colors.CYAN}   docker-compose logs -f coreness{Colors.END}")
        
        # Удаляем скрипт установки, если это была первичная установка
        print(f"\n{Colors.BLUE}=== ЭТАП: Очистка ==={Colors.END}")
        remove_installer_script()
        
    except Exception as e:
        print(f"{Colors.RED}❌ Ошибка обновления: {e}{Colors.END}")
        print(f"{Colors.YELLOW}⏪ Восстанавливаю из резервной копии...{Colors.END}")
        
        errors = restore_backup(backup_dir, project_root)
        if errors:
            print(f"{Colors.RED}❌ Не удалось восстановить следующие файлы/папки: {errors}{Colors.END}")
            print(f"{Colors.YELLOW}❗ Бэкап сохранён в {backup_dir}. Восстановите вручную!{Colors.END}")
        else:
            print(f"{Colors.GREEN}✅ Откат завершён. Проект восстановлен.{Colors.END}")
            print(f"{Colors.CYAN}💾 Резервная копия сохранена в {backup_dir}{Colors.END}")

def main_menu():
    print_header()
    
    # Проверяем текущую папку
    location = check_location()
    print()  # Пустая строка для разделения
    
    print(f"{Colors.YELLOW}Выберите действие:{Colors.END}")
    
    # Показываем доступные действия в зависимости от папки
    if location == "core":
        print("1) ⚠️ Первичная установка Coreness (НЕ РЕКОМЕНДУЕТСЯ)")
        print("2) ✅ Обновление ядра Coreness (РЕКОМЕНДУЕТСЯ)")
        print("3) Выход")
        
        while True:
            choice = input("Введите номер (1-3): ")
            if choice == '1':
                print(f"{Colors.YELLOW}⚠️ ВНИМАНИЕ: Вы выбрали первичную установку из папки tools/core!{Colors.END}")
                print(f"{Colors.YELLOW}   Это может привести к неожиданным результатам.{Colors.END}")
                confirm = input("Вы уверены, что хотите продолжить? (y/N): ")
                if confirm.lower() == 'y':
                    run_initial_setup()
                break
            elif choice == '2':
                run_core_update()
                break
            elif choice == '3':
                print(f"{Colors.BLUE}До свидания!{Colors.END}")
                sys.exit(0)
            else:
                print(f"{Colors.RED}Неверный выбор. Попробуйте снова.{Colors.END}")
    else:
        print("1) ✅ Первичная установка Coreness (РЕКОМЕНДУЕТСЯ)")
        print("2) ⚠️ Обновление ядра Coreness (НЕ РЕКОМЕНДУЕТСЯ)")
        print("3) Выход")
        
        while True:
            choice = input("Введите номер (1-3): ")
            if choice == '1':
                run_initial_setup()
                break
            elif choice == '2':
                print(f"{Colors.YELLOW}⚠️ ВНИМАНИЕ: Вы выбрали обновление ядра не из папки tools/core!{Colors.END}")
                print(f"{Colors.YELLOW}   Это может привести к неожиданным результатам.{Colors.END}")
                confirm = input("Вы уверены, что хотите продолжить? (y/N): ")
                if confirm.lower() == 'y':
                    run_core_update()
                break
            elif choice == '3':
                print(f"{Colors.BLUE}До свидания!{Colors.END}")
                sys.exit(0)
            else:
                print(f"{Colors.RED}Неверный выбор. Попробуйте снова.{Colors.END}")

if __name__ == "__main__":
    main_menu()
