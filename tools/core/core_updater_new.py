#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import platform
import shutil
import subprocess
import time
from pathlib import Path

# ОТКЛЮЧАЕМ БУФЕРИЗАЦИЮ ДЛЯ РЕАЛЬНОГО ВРЕМЕНИ
if hasattr(sys.stdout, 'reconfigure'):
    # Python 3.7+
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
else:
    # Старые версии Python
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)  # line buffered
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)

# Настраиваем кодировку для всех платформ
import io
import locale

try:
    # Устанавливаем переменные окружения для UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LC_ALL'] = 'C.UTF-8'
    os.environ['LANG'] = 'C.UTF-8'
    
    # Пытаемся установить локаль UTF-8
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass
    
    # Пересоздаем потоки с UTF-8
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stdin, 'buffer'):
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
        
except Exception as e:
    # Если ничего не работает, пробуем установить только переменные окружения
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    pass

# === ГЛОБАЛЬНАЯ КОНФИГУРАЦИЯ ===
# Счетчик запусков обновления для диагностики
UPDATE_COUNTER = 0

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
    "config/presets/default"
]

# Папки для исключения из обновления (всегда исключаются)
EXCLUDE_PATHS = [
    "logs",
    "data", 
    "resources",
    ".git",
    ".github",
    ".gitignore",
    ".core_update_backup*"  # Исключаем папки бэкапов
]

# Настройки бэкапа
BACKUP_CONFIG = {
    'default_keep': True,  # По умолчанию сохранять бэкап
    'dir_name': ".core_update_backup"
}

# Папки, которые не критичны для обновления (при ошибке - пропускаем)
NON_CRITICAL_PATHS = [
    "tools",           # Вся папка tools (может быть заблокирована)
    "tools/core"       # Папка core внутри tools (заблокирована процессом)
]

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

class MessageHandler:
    """Класс для обработки вывода и ввода сообщений"""
    
    def __init__(self):
        """Инициализация обработчика сообщений"""
        pass
    
    def print_output(self, message, color=None, flush=True):
        """Централизованный вывод данных без буферизации"""
        if color:
            message = f"{color}{message}{Colors.END}"
        
        # Отправляем напрямую в stdout без буферизации
        sys.stdout.write(message)
        if flush:
            sys.stdout.flush()

    def print_header(self):
        """Выводит заголовок приложения"""
        self.print_output(f"{Colors.BLUE}{Colors.BOLD}================================{Colors.END}\n")
        self.print_output(f"{Colors.BLUE}{Colors.BOLD}      CORENESS UPDATER NEW      {Colors.END}\n")
        self.print_output(f"{Colors.BLUE}{Colors.BOLD}================================{Colors.END}\n")

    def safe_input(self, prompt):
        """Безопасный ввод с обработкой кодировки"""
        try:
            # self.print_output(f"{Colors.CYAN}[DEBUG] Запрашиваем ввод: '{prompt}'{Colors.END}\n")
            self.print_output(prompt)
            result = input()
            # Очищаем результат от лишних символов
            cleaned_result = result.strip()
            # self.print_output(f"{Colors.CYAN}[DEBUG] Получен ввод: '{result}' -> очищен: '{cleaned_result}'{Colors.END}\n")
            return cleaned_result
        except UnicodeDecodeError:
            # Если кодировка не работает, пробуем альтернативный способ
            self.print_output("Введите ответ (используйте английские буквы):\n")
            try:
                result = input("> ")
                cleaned_result = result.strip()
                # self.print_output(f"{Colors.CYAN}[DEBUG] Unicode fallback: '{result}' -> '{cleaned_result}'{Colors.END}\n")
                return cleaned_result
            except:
                # self.print_output(f"{Colors.RED}[DEBUG] Unicode fallback failed{Colors.END}\n")
                return ""
        except Exception as e:
            # self.print_output(f"{Colors.RED}[DEBUG] Ошибка ввода: {e}{Colors.END}\n")
            return ""

class DockerManager:
    """Класс для работы с Docker и контейнерами"""
    
    def __init__(self, messages_handler, config, project_root, script_path):
        """Инициализация Docker менеджера"""
        self.messages = messages_handler
        self.config = config
        self.project_root = project_root
        self.script_path = script_path
    
    def check_dependencies(self):
        """Проверяет и устанавливает необходимые зависимости для работы с Docker"""
        self.messages.print_output(f"{Colors.YELLOW}🔍 Проверяю зависимости для работы с Docker...{Colors.END}\n")
        
        # Зависимости для работы с Docker и скачивания конфигурации
        required_packages = [
            'requests',  # Для скачивания с GitHub
            'zipfile',    # Встроенный модуль Python
            'tempfile',   # Встроенный модуль Python
            'shutil',     # Встроенный модуль Python
            'subprocess'  # Встроенный модуль Python
        ]
        
        missing_packages = []
        
        # Проверяем каждый пакет
        for package in required_packages:
            try:
                if package in ['zipfile', 'tempfile', 'shutil', 'subprocess']:
                    # Встроенные модули Python
                    __import__(package)
                    self.messages.print_output(f"{Colors.GREEN}✅ {package} (встроенный модуль){Colors.END}\n")
                else:
                    # Внешние пакеты
                    __import__(package)
                    self.messages.print_output(f"{Colors.GREEN}✅ {package} (установлен){Colors.END}\n")
            except ImportError:
                if package not in ['zipfile', 'tempfile', 'shutil', 'subprocess']:
                    missing_packages.append(package)
                    self.messages.print_output(f"{Colors.RED}❌ {package} (не найден){Colors.END}\n")
        
        # Устанавливаем недостающие пакеты (одинаково везде)
        if missing_packages:
            self.messages.print_output(f"{Colors.YELLOW}📦 Устанавливаю недостающие пакеты: {', '.join(missing_packages)}{Colors.END}\n")
            return self._install_packages(missing_packages)
        else:
            self.messages.print_output(f"{Colors.GREEN}✅ Все зависимости уже установлены!{Colors.END}\n")
            return True
    
    def _install_packages(self, packages):
        """Устанавливает недостающие пакеты"""
        try:
            # Проверяем и устанавливаем pip если его нет
            self.messages.print_output(f"{Colors.CYAN}🔄 Проверяю pip...{Colors.END}\n")
            try:
                subprocess.run([sys.executable, "-m", "pip", "--version"], 
                             capture_output=True, text=True, check=True)
                self.messages.print_output(f"{Colors.GREEN}✅ pip доступен{Colors.END}\n")
            except:
                self.messages.print_output(f"{Colors.YELLOW}⚠️ pip не найден, устанавливаю...{Colors.END}\n")
                try:
                    # Устанавливаем pip через get-pip.py
                    subprocess.run([
                        sys.executable, "-c", 
                        "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', 'get-pip.py')"
                    ], check=True)
                    subprocess.run([sys.executable, "get-pip.py"], check=True)
                    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
                    self.messages.print_output(f"{Colors.GREEN}✅ pip установлен{Colors.END}\n")
                except Exception as e:
                    self.messages.print_output(f"{Colors.RED}❌ Не удалось установить pip: {e}{Colors.END}\n")
                    return False
            
            # Устанавливаем недостающие пакеты
            for package in packages:
                self.messages.print_output(f"{Colors.CYAN}💡 Устанавливаю {package}...{Colors.END}\n")
                
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.messages.print_output(f"{Colors.GREEN}✅ {package} установлен{Colors.END}\n")
                else:
                    self.messages.print_output(f"{Colors.RED}❌ Ошибка установки {package}:{Colors.END}\n")
                    self.messages.print_output(f"{Colors.RED}   stdout: {result.stdout}{Colors.END}\n")
                    self.messages.print_output(f"{Colors.RED}   stderr: {result.stderr}{Colors.END}\n")
                    return False
            
            self.messages.print_output(f"{Colors.GREEN}🎉 Все зависимости установлены!{Colors.END}\n")
            return True
            
        except Exception as e:
            self.messages.print_output(f"{Colors.RED}❌ Критическая ошибка установки зависимостей: {e}{Colors.END}\n")
            return False
    
    def check_docker(self):
        """Проверяет наличие Docker и возвращает True если установлен"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, check=True)
            self.messages.print_output(f"{Colors.GREEN}✅ Docker найден: {result.stdout.strip()}{Colors.END}\n")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.messages.print_output(f"{Colors.RED}❌ Docker не найден!{Colors.END}\n")
            return False
    
    def is_docker_running(self):
        """Проверяет, установлен ли Docker и работает ли он"""
        try:
            # Проверяем не только версию, но и подключение к daemon
            subprocess.run(['docker', 'info'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def is_running_in_container(self):
        """Проверяет, запущен ли скрипт внутри Docker контейнера"""
        return os.path.exists("/.dockerenv")
    
    def is_container_running(self):
        """Проверяет, запущен ли контейнер"""
        # Если мы внутри контейнера, контейнер всегда "доступен"
        if self.is_running_in_container():
            return True
        
        try:
            # Проверяем контейнер напрямую через docker ps
            result = subprocess.run([
                "docker", "ps", "-q", "--filter", "name=coreness-container"
            ], capture_output=True, text=True)
            return bool(result.stdout.strip())
        except:
            return False
    
    def download_docker_config(self):
        """Скачивает конфигурацию Docker из открытого репозитория"""
        self.messages.print_output(f"{Colors.YELLOW}📥 Скачиваем конфигурацию Docker...{Colors.END}\n")
        
        # Создаем временную папку для скачивания
        temp_dir = "docker-temp"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        try:
            # Получаем URL Base версии из конфигурации
            base_repo_url = self.config['versions']['base']['repo_url']
            
            # Клонируем только папку docker из Base репозитория
            self.messages.print_output(f"{Colors.CYAN}💡 Клонируем папку docker из Base репозитория...{Colors.END}\n")
            self.messages.print_output(f"{Colors.CYAN}   URL: {base_repo_url}{Colors.END}\n")
            
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
            docker_target = os.path.join(self.project_root, 'docker')
            if os.path.exists(docker_target):
                shutil.rmtree(docker_target)
            shutil.copytree(f'{temp_dir}/docker', docker_target)
            
            self.messages.print_output(f"{Colors.CYAN}📁 Конфигурация скопирована в: {docker_target}{Colors.END}\n")
            
            # Удаляем временную папку
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
            
            self.messages.print_output(f"{Colors.GREEN}✅ Конфигурация Docker скачана!{Colors.END}\n")
            return True
            
        except subprocess.CalledProcessError as e:
            self.messages.print_output(f"{Colors.RED}❌ Ошибка при скачивании конфигурации: {e}{Colors.END}\n")
            return False
    
    def install_docker(self):
        """Устанавливает Docker Engine в зависимости от операционной системы"""
        # Сначала проверяем, не установлен ли уже Docker
        if self.check_docker():
            if self.is_docker_running():
                self.messages.print_output(f"{Colors.GREEN}✅ Docker уже установлен и работает!{Colors.END}\n")
                return True
            else:
                self.messages.print_output(f"{Colors.YELLOW}⚠️ Docker установлен, но не запущен{Colors.END}\n")
                self.messages.print_output(f"{Colors.CYAN}💡 Пытаемся запустить Docker...{Colors.END}\n")
                if self.start_docker_engine():
                    self.messages.print_output(f"{Colors.GREEN}✅ Docker запущен!{Colors.END}\n")
                    return True
                else:
                    self.messages.print_output(f"{Colors.RED}❌ Не удалось запустить Docker{Colors.END}\n")
                    self.messages.print_output(f"{Colors.YELLOW}💡 Установка не требуется, но запустите Docker вручную{Colors.END}\n")
                    return False
        
        system = platform.system().lower()
        self.messages.print_output(f"{Colors.YELLOW}🔧 Определена система: {system}{Colors.END}\n")
        
        if system == "linux":
            return self._install_docker_linux()
        elif system == "darwin":  # macOS
            return self._install_docker_macos()
        elif system == "windows":
            self.messages.print_output(f"{Colors.YELLOW}⚠️ Windows: Docker не будет установлен автоматически{Colors.END}\n")
            self.messages.print_output(f"{Colors.CYAN}💡 Настройте Docker самостоятельно при необходимости{Colors.END}\n")
            return False
        else:
            self.messages.print_output(f"{Colors.RED}❌ Неподдерживаемая операционная система: {system}{Colors.END}\n")
            return False
    
    def _install_docker_linux(self):
        """Устанавливает Docker Engine для Linux"""
        self.messages.print_output(f"{Colors.YELLOW}📦 Устанавливаем Docker Engine для Linux...{Colors.END}\n")
        try:
            # Проверяем наличие apt
            subprocess.run(['which', 'apt'], check=True, capture_output=True)
            self.messages.print_output(f"{Colors.CYAN}💡 Используем apt для установки Docker Engine...{Colors.END}\n")
            
            # Обновляем пакеты
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            
            # Устанавливаем зависимости
            subprocess.run([
                'sudo', 'apt', 'install', '-y', 
                'apt-transport-https', 'ca-certificates', 'curl', 'gnupg', 'lsb-release'
            ], check=True)
            
            # Добавляем GPG ключ Docker
            subprocess.run(
                'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg',
                shell=True, check=True
            )
            
            # Добавляем репозиторий Docker
            subprocess.run(
                'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list',
                shell=True, check=True
            )
            
            # Обновляем пакеты и устанавливаем Docker
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'docker-ce', 'docker-ce-cli', 'containerd.io'], check=True)
            
            # Добавляем пользователя в группу docker
            subprocess.run(['sudo', 'usermod', '-aG', 'docker', os.getenv('USER')], check=True)
            
            self.messages.print_output(f"{Colors.GREEN}✅ Docker Engine установлен через apt!{Colors.END}\n")
            self.messages.print_output(f"{Colors.YELLOW}⚠️ Перезайдите в систему для применения изменений группы docker!{Colors.END}\n")
            return True
            
        except subprocess.CalledProcessError:
            try:
                # Проверяем наличие yum
                subprocess.run(['which', 'yum'], check=True, capture_output=True)
                self.messages.print_output(f"{Colors.CYAN}💡 Используем yum для установки Docker Engine...{Colors.END}\n")
                
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
                
                self.messages.print_output(f"{Colors.GREEN}✅ Docker Engine установлен через yum!{Colors.END}\n")
                self.messages.print_output(f"{Colors.YELLOW}⚠️ Перезайдите в систему для применения изменений группы docker!{Colors.END}\n")
                return True
                
            except subprocess.CalledProcessError:
                self.messages.print_output(f"{Colors.RED}❌ Не удалось определить пакетный менеджер!{Colors.END}\n")
                return False
    
    def _install_docker_macos(self):
        """Устанавливает Docker Engine для macOS"""
        self.messages.print_output(f"{Colors.YELLOW}📦 Устанавливаем Docker Engine для macOS...{Colors.END}\n")
        self.messages.print_output(f"{Colors.CYAN}💡 Используем Homebrew для установки Docker Engine...{Colors.END}\n")
        
        try:
            # Проверяем наличие Homebrew
            subprocess.run(['which', 'brew'], check=True, capture_output=True)
            
            # Устанавливаем Docker Engine через Homebrew
            subprocess.run(['brew', 'install', 'docker'], check=True)
            
            self.messages.print_output(f"{Colors.GREEN}✅ Docker Engine установлен через Homebrew!{Colors.END}\n")
            self.messages.print_output(f"{Colors.YELLOW}⚠️ Запустите Docker Engine: brew services start docker{Colors.END}\n")
            return True
            
        except subprocess.CalledProcessError:
            self.messages.print_output(f"{Colors.RED}❌ Homebrew не найден! Установите Homebrew или Docker Desktop вручную.{Colors.END}\n")
            return False
    
    def install_global_commands(self):
        """Устанавливает глобальные команды из docker/coreness"""
        self.messages.print_output(f"{Colors.YELLOW}📦 Устанавливаем глобальные команды...{Colors.END}\n")
        
        coreness_script = os.path.join(self.project_root, 'docker', 'coreness')
        if not os.path.exists(coreness_script):
            self.messages.print_output(f"{Colors.RED}❌ Скрипт coreness не найден!{Colors.END}\n")
            return False
        
        try:
            # Делаем скрипт исполняемым
            os.chmod(coreness_script, 0o755)
            
            # Запускаем установку команд
            self.messages.print_output(f"{Colors.CYAN}💡 Запускаем установку глобальных команд...{Colors.END}\n")
            result = subprocess.run([coreness_script, 'install'], 
                                 capture_output=True, text=True, check=True)
            
            # Выводим результат установки
            if result.stdout:
                self.messages.print_output(f"{Colors.GREEN}📋 Результат установки:{Colors.END}\n")
                self.messages.print_output(result.stdout)
            
            # Команда уже установлена как 'coreness' (исправлен скрипт)
            self.messages.print_output(f"{Colors.GREEN}✅ Команда 'coreness' установлена{Colors.END}\n")
            
            self.messages.print_output(f"{Colors.GREEN}✅ Глобальные команды установлены!{Colors.END}\n")
            return True
            
        except subprocess.CalledProcessError as e:
            self.messages.print_output(f"{Colors.RED}❌ Ошибка при установке команд: {e}{Colors.END}\n")
            if e.stdout:
                self.messages.print_output(f"{Colors.RED}stdout: {e.stdout}{Colors.END}\n")
            if e.stderr:
                self.messages.print_output(f"{Colors.RED}stderr: {e.stderr}{Colors.END}\n")
            return False
        except Exception as e:
            self.messages.print_output(f"{Colors.RED}❌ Критическая ошибка установки команд: {e}{Colors.END}\n")
            return False

    def build_and_run_container(self):
        """Собирает и запускает Docker контейнер"""
        self.messages.print_output(f"{Colors.YELLOW}🔨 Собираем и запускаем Docker контейнер...{Colors.END}\n")
        
        docker_dir = os.path.join(self.project_root, 'docker')
        if not os.path.exists(docker_dir):
            self.messages.print_output(f"{Colors.RED}❌ Папка docker не найдена!{Colors.END}\n")
            return False
        
        # Проверяем, что Docker установлен и работает
        if not self.is_docker_running():
            self.messages.print_output(f"{Colors.RED}❌ Docker не работает!{Colors.END}\n")
            self.messages.print_output(f"{Colors.CYAN}💡 Пытаемся запустить Docker...{Colors.END}\n")
            
            if self.start_docker_engine():
                self.messages.print_output(f"{Colors.GREEN}✅ Docker запущен!{Colors.END}\n")
                # Ждем немного, чтобы Docker успел запуститься
                self.messages.print_output(f"{Colors.YELLOW}⏳ Ждем запуска Docker...{Colors.END}\n")
                time.sleep(5)
                
                # Проверяем еще раз
                if self.is_docker_running():
                    self.messages.print_output(f"{Colors.GREEN}✅ Docker готов к работе!{Colors.END}\n")
                else:
                    self.messages.print_output(f"{Colors.RED}❌ Docker не запустился.{Colors.END}\n")
                    self.messages.print_output(f"{Colors.YELLOW}💡 Запустите Docker Desktop вручную и попробуйте снова.{Colors.END}\n")
                    return False
            else:
                self.messages.print_output(f"{Colors.RED}❌ Не удалось запустить Docker автоматически.{Colors.END}\n")
                self.messages.print_output(f"{Colors.YELLOW}💡 Запустите Docker Desktop вручную и попробуйте снова.{Colors.END}\n")
                return False
        
        try:
            # Собираем образ
            self.messages.print_output(f"{Colors.CYAN}💡 Собираем Docker образ...{Colors.END}\n")
            subprocess.run(['docker', 'compose', 'build'], check=True, cwd=docker_dir)
            
            # Запускаем контейнер
            self.messages.print_output(f"{Colors.CYAN}💡 Запускаем Docker контейнер...{Colors.END}\n")
            subprocess.run(['docker', 'compose', 'up', '-d'], check=True, cwd=docker_dir)
            
            self.messages.print_output(f"{Colors.GREEN}✅ Docker контейнер запущен!{Colors.END}\n")
            return True
            
        except subprocess.CalledProcessError as e:
            self.messages.print_output(f"{Colors.RED}❌ Ошибка при сборке/запуске контейнера: {e}{Colors.END}\n")
            return False
    
    def start_docker_engine(self):
        """Запускает Docker Engine"""
        try:
            system = platform.system()
            
            if system == "Windows":
                self.messages.print_output(f"{Colors.YELLOW}⚠️ Windows: Docker не будет запущен автоматически{Colors.END}\n")
                self.messages.print_output(f"{Colors.CYAN}💡 Настройте Docker самостоятельно при необходимости{Colors.END}\n")
                return False
                
            elif system == "Darwin":  # macOS
                self.messages.print_output(f"{Colors.CYAN}💡 Запускаем Docker Engine на macOS...{Colors.END}\n")
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
                self.messages.print_output(f"{Colors.CYAN}💡 Запускаем Docker Engine на Linux...{Colors.END}\n")
                # На Linux Docker Engine как сервис
                subprocess.run(['sudo', 'systemctl', 'start', 'docker'], check=True)
                return True
                
            else:
                self.messages.print_output(f"{Colors.RED}❌ Неизвестная ОС: {system}{Colors.END}\n")
                return False
                
        except subprocess.CalledProcessError:
            self.messages.print_output(f"{Colors.RED}❌ Не удалось запустить Docker Engine{Colors.END}\n")
            return False
        except Exception as e:
            self.messages.print_output(f"{Colors.RED}❌ Ошибка при запуске Docker Engine: {e}{Colors.END}\n")
            return False
    
    def remove_container(self):
        """Удаляет Docker контейнер"""
        self.messages.print_output(f"{Colors.YELLOW}🗑 Удаляем Docker контейнер...{Colors.END}\n")
        
        try:
            # Проверяем, есть ли запущенные контейнеры
            running_result = subprocess.run(['docker', 'ps', '-q'], capture_output=True, text=True)
            if running_result.stdout.strip():
                # Останавливаем все контейнеры
                self.messages.print_output(f"{Colors.CYAN}💡 Останавливаем контейнеры...{Colors.END}\n")
                subprocess.run('docker stop $(docker ps -q)', shell=True, check=True)
            else:
                self.messages.print_output(f"{Colors.CYAN}💡 Нет запущенных контейнеров{Colors.END}\n")
            
            # Проверяем, есть ли контейнеры для удаления
            all_containers_result = subprocess.run(['docker', 'ps', '-aq'], capture_output=True, text=True)
            if all_containers_result.stdout.strip():
                # Удаляем контейнеры
                self.messages.print_output(f"{Colors.CYAN}💡 Удаляем контейнеры...{Colors.END}\n")
                subprocess.run('docker rm $(docker ps -aq)', shell=True, check=True)
            else:
                self.messages.print_output(f"{Colors.CYAN}💡 Нет контейнеров для удаления{Colors.END}\n")
            
            # Проверяем, есть ли образы для удаления
            images_result = subprocess.run(['docker', 'images', '-q'], capture_output=True, text=True)
            if images_result.stdout.strip():
                # Удаляем образы
                self.messages.print_output(f"{Colors.CYAN}💡 Удаляем образы...{Colors.END}\n")
                subprocess.run('docker rmi $(docker images -q)', shell=True, check=True)
            else:
                self.messages.print_output(f"{Colors.CYAN}💡 Нет образов для удаления{Colors.END}\n")
            
            self.messages.print_output(f"{Colors.GREEN}✅ Docker контейнеры и образы удалены!{Colors.END}\n")
            return True
            
        except subprocess.CalledProcessError as e:
            self.messages.print_output(f"{Colors.RED}❌ Ошибка при удалении контейнера: {e}{Colors.END}\n")
            return False

class CoreUpdater:
    """Основной класс для обновления Coreness"""
    
    def __init__(self):
        """Инициализация класса"""
        self.update_counter = 0
        self.script_path, self.project_root = self._get_paths()
        self.config = self._load_config()
        self.messages = MessageHandler()
        self.docker = DockerManager(self.messages, self.config, self.project_root, self.script_path)
        
    def _get_paths(self):
        """Определяет пути к скрипту и корню проекта"""
        script_path = Path(__file__).resolve()
        script_dir = script_path.parent
        
        # Если скрипт в tools/core, то корень проекта на 2 уровня выше
        if script_dir.name == "core" and script_dir.parent.name == "tools":
            project_root = script_dir.parent.parent
        else:
            # Иначе скрипт уже в корне проекта
            project_root = script_dir
            
        return script_path, project_root
    
    def is_in_project_root(self):
        """Проверяет, находится ли скрипт в корне проекта"""
        # Используем уже вычисленные пути
        return self.script_path.parent == self.project_root
    
    def _load_config(self):
        """Загружает конфигурацию"""
        return {
            'versions': VERSIONS,
            'clean_sync_items': CLEAN_SYNC_ITEMS,
            'root_files': ROOT_FILES,
            'factory_configs': FACTORY_CONFIGS,
            'exclude_paths': EXCLUDE_PATHS,
            'backup': BACKUP_CONFIG,
            'non_critical_paths': NON_CRITICAL_PATHS
        }

    def check_location(self):
        """Проверяет папку где лежит скрипт и показывает информацию"""
        self.messages.print_output(f"{Colors.CYAN}📁 Скрипт находится в: {self.script_path.parent}{Colors.END}\n")
        self.messages.print_output(f"{Colors.CYAN}📁 Рабочая папка: {Path.cwd()}{Colors.END}\n")
        self.messages.print_output(f"{Colors.CYAN}📁 Корень проекта: {self.project_root}{Colors.END}\n")
        
        return self.is_in_project_root()

    def _show_menu_options(self):
        """Показывает опции меню"""
        self.messages.print_output("1) 🐳 Работа с Docker\n")
        self.messages.print_output("2) 🔄 Обновление данных\n")
        self.messages.print_output("3) 🗄 Миграция базы данных\n")
        self.messages.print_output("0) Выход\n")

    def _show_docker_submenu(self):
        """Показывает подменю для работы с Docker"""
        self.messages.print_output(f"{Colors.BLUE}=== РАБОТА С DOCKER ==={Colors.END}\n")
        self.messages.print_output("1) 📦 Установка/обновление Docker и контейнера\n")
        self.messages.print_output("2) 🗑 Удаление контейнера\n")
        self.messages.print_output("0) Назад в главное меню\n")

    def _handle_docker_choice(self, choice):
        """Обрабатывает выбор в подменю Docker"""
        if choice == '1':
            # Установка/обновление Docker и контейнера
            self.messages.print_output(f"{Colors.BLUE}=== УСТАНОВКА/ОБНОВЛЕНИЕ DOCKER ==={Colors.END}\n")
            
            # 1. Проверяем зависимости
            if not self.docker.check_dependencies():
                self.messages.print_output(f"{Colors.RED}❌ Не удалось установить зависимости{Colors.END}\n")
                return True
            
            # 2. Устанавливаем Docker
            if not self.docker.install_docker():
                self.messages.print_output(f"{Colors.RED}❌ Не удалось установить Docker{Colors.END}\n")
                return True
            
            # 3. Скачиваем конфигурацию
            if not self.docker.download_docker_config():
                self.messages.print_output(f"{Colors.RED}❌ Не удалось скачать конфигурацию Docker{Colors.END}\n")
                return True
            
            # 4. Собираем и запускаем контейнер
            if not self.docker.build_and_run_container():
                self.messages.print_output(f"{Colors.RED}❌ Не удалось собрать/запустить контейнер{Colors.END}\n")
                return True
            
            # 5. Устанавливаем глобальные команды
            if not self.docker.install_global_commands():
                self.messages.print_output(f"{Colors.RED}❌ Не удалось установить глобальные команды{Colors.END}\n")
                return True
            
            self.messages.print_output(f"{Colors.GREEN}🎉 Docker, контейнер и глобальные команды успешно установлены!{Colors.END}\n")
            return True
            
        elif choice == '2':
            # Удаление контейнера
            self.messages.print_output(f"{Colors.BLUE}=== УДАЛЕНИЕ DOCKER КОНТЕЙНЕРА ==={Colors.END}\n")
            
            # Подтверждение удаления
            confirm = self.messages.safe_input(f"{Colors.YELLOW}⚠️ Это удалит все Docker контейнеры и образы. Продолжить? (y/N): {Colors.END}")
            if confirm.lower() != 'y':
                self.messages.print_output(f"{Colors.CYAN}💡 Удаление отменено{Colors.END}\n")
                return True
            
            # Удаляем контейнер
            if not self.docker.remove_container():
                self.messages.print_output(f"{Colors.RED}❌ Не удалось удалить контейнер{Colors.END}\n")
                return True
            
            self.messages.print_output(f"{Colors.GREEN}🎉 Docker контейнеры и образы удалены!{Colors.END}\n")
            return True
            
        elif choice == '0':
            return True  # Возвращаемся в главное меню
        else:
            self.messages.print_output(f"{Colors.RED}Неверный выбор. Попробуйте снова.{Colors.END}\n")
            return False

    def _handle_menu_choice(self, choice):
        """Обрабатывает выбор пользователя в главном меню"""
        if choice == '1':
            # Показываем подменю Docker
            while True:
                self._show_docker_submenu()
                docker_choice = self.messages.safe_input(f"{Colors.YELLOW}Введите номер (0-2): {Colors.END}")
                if self._handle_docker_choice(docker_choice):
                    if docker_choice == '0':
                        break  # Возвращаемся в главное меню
                    else:
                        break  # Выполнили действие
            return True
        elif choice == '2':
            self.messages.print_output(f"{Colors.YELLOW}⚠️ Заглушка: Обновление данных{Colors.END}\n")
            return True
        elif choice == '3':
            self.messages.print_output(f"{Colors.YELLOW}⚠️ Заглушка: Миграция базы данных{Colors.END}\n")
            return True
        elif choice == '0':
            self.messages.print_output(f"{Colors.BLUE}До свидания!{Colors.END}\n")
            sys.exit(0)
        else:
            self.messages.print_output(f"{Colors.RED}Неверный выбор. Попробуйте снова.{Colors.END}\n")
            return False

    def main_menu(self):
        """Главное меню приложения"""
        self.messages.print_header()
        
        # Проверяем местоположение скрипта и показываем предупреждение
        is_root = self.check_location()
        
        # Показываем предупреждение только если скрипт в корне проекта
        if is_root:
            self.messages.print_output(f"{Colors.YELLOW}⚠️ ВНИМАНИЕ: Скрипт запущен из корня проекта!{Colors.END}\n")
            self.messages.print_output(f"{Colors.YELLOW}   Развертывание и обновление будет происходить в текущей папке.{Colors.END}\n")
            self.messages.print_output(f"{Colors.YELLOW}   Убедитесь, что это правильная папка для проекта Coreness.{Colors.END}\n")
            self.messages.print_output(f"{Colors.CYAN}💡 Если это не так, переместите скрипт в папку tools/core{Colors.END}\n")
        
        self.messages.print_output(f"{Colors.YELLOW}Выберите действие:{Colors.END}\n")
        
        # Показываем опции меню (одинаковые для всех случаев)
        self._show_menu_options()
        
        # Общая логика обработки выбора
        while True:
            choice = self.messages.safe_input(f"{Colors.YELLOW}Введите номер (0-3): {Colors.END}")
            if self._handle_menu_choice(choice):
                break

if __name__ == "__main__":
    # Создаем экземпляр класса
    updater = CoreUpdater()
    
    # Запускаем главное меню
    updater.main_menu()
