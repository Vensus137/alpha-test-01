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

# Белый список - что обновляется (только эти пути)
INCLUDED_PATHS = [
    "app",                  # Папка приложения
    "plugins",              # Папка плагинов
    "tools",                # Папка инструментов
    "docker",               # Папка Docker конфигурации
    "data/ssl_certificates",# Подпапка сертификатов
    "main.py",              # Главный файл
    "requirements.txt",     # Зависимости
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

# Настройки зависимостей для разных модулей
DEPENDENCY_PACKAGES = {
    'docker': [  # Зависимости для работы с Docker
        'requests'  # Для скачивания с GitHub
    ],
    'update': [  # Зависимости для обновления проекта
        'requests'  # Для скачивания с GitHub
    ],
    'migration': [  # Зависимости для миграции базы данных
        'sqlalchemy',  # ORM для работы с БД
        'aiosqlite',   # Асинхронный SQLite
        'pyyaml'       # Для работы с YAML конфигами
    ]
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
    
    def __init__(self, messages_handler, utility_manager):
        """Инициализация Docker менеджера"""
        self.messages = messages_handler
        self.utils = utility_manager
        self.config = self.utils.get_config()
        self.project_root = self.utils.get_project_root()
        self.script_path = self.utils.get_script_path()
    
    def check_dependencies(self):
        """Проверяет и устанавливает необходимые зависимости для работы с Docker"""
        return self.utils.check_dependencies('docker')
    
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

class UtilityManager:
    """Универсальный утилитарный класс для управления проектом"""
    
    def __init__(self, messages_handler):
        """Инициализация утилитарного менеджера"""
        self.messages = messages_handler
        self.script_path, self.project_root = self._get_paths()
        self.config = self._load_config()
    
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
    
    def _load_config(self):
        """Загружает конфигурацию"""
        return {
            'versions': VERSIONS,
            'included_paths': INCLUDED_PATHS,
            'factory_configs': FACTORY_CONFIGS,
            'backup': BACKUP_CONFIG,
            'non_critical_paths': NON_CRITICAL_PATHS,
            'dependency_packages': DEPENDENCY_PACKAGES
        }
    
    def get_script_path(self):
        """Возвращает путь к скрипту"""
        return self.script_path
    
    def get_project_root(self):
        """Возвращает корень проекта"""
        return self.project_root
    
    def get_config(self):
        """Возвращает конфигурацию"""
        return self.config
    
    def is_in_project_root(self):
        """Проверяет, находится ли скрипт в корне проекта"""
        return self.script_path.parent == self.project_root
    
    def get_dependencies(self, module_type):
        """Возвращает зависимости для указанного модуля"""
        if module_type not in self.config['dependency_packages']:
            raise ValueError(f"Неизвестный тип модуля: {module_type}")
        
        return self.config['dependency_packages'][module_type]
    
    def check_dependencies(self, module_type):
        """Проверяет и устанавливает необходимые зависимости для модуля"""
        required_packages = self.get_dependencies(module_type)
        self.messages.print_output(f"{Colors.YELLOW}🔍 Проверяю зависимости для {module_type}...{Colors.END}\n")
        
        missing_packages = []
        
        # Проверяем только внешние пакеты (встроенные модули всегда доступны)
        for package in required_packages:
            try:
                __import__(package)
                self.messages.print_output(f"{Colors.GREEN}✅ {package} (установлен){Colors.END}\n")
            except ImportError:
                missing_packages.append(package)
                self.messages.print_output(f"{Colors.RED}❌ {package} (не найден){Colors.END}\n")
        
        # Устанавливаем недостающие пакеты
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

class UpdateManager:
    """Класс для обновления проекта Coreness"""
    
    def __init__(self, messages_handler, utility_manager):
        """Инициализация менеджера обновлений"""
        self.messages = messages_handler
        self.utils = utility_manager
        self.config = self.utils.get_config()
        self.project_root = self.utils.get_project_root()
    
    def check_dependencies(self):
        """Проверяет и устанавливает необходимые зависимости для обновления"""
        return self.utils.check_dependencies('update')
    
    def get_available_versions(self):
        """Возвращает список доступных версий"""
        return list(self.config['versions'].keys())
    
    def validate_version(self, version):
        """Проверяет корректность введенной версии"""
        return version.lower() in self.config['versions']
    
    def get_version_info(self, version):
        """Возвращает информацию о версии"""
        return self.config['versions'].get(version.lower())
    
    def validate_github_token(self, token):
        """Проверяет корректность GitHub токена"""
        if not token:
            return False, "Токен пустой"
        
        # Проверяем формат токена (должен начинаться с ghp_ или gho_ или ghu_)
        if not token.startswith(('ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_')):
            return False, "Неверный формат токена (должен начинаться с ghp_, gho_, ghu_, ghs_ или ghr_)"
        
        # Проверяем длину токена
        if len(token) < 20:
            return False, "Токен слишком короткий"
        
        # Проверяем токен через GitHub API
        try:
            import requests
            headers = {"Authorization": f"token {token}"}
            response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "Токен валиден"
            elif response.status_code == 401:
                return False, "Токен недействителен или истек"
            elif response.status_code == 403:
                return False, "Токен заблокирован или не имеет необходимых прав"
            else:
                return False, f"Ошибка проверки токена: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Ошибка подключения к GitHub API: {e}"
        except Exception as e:
            return False, f"Неожиданная ошибка: {e}"
    
    def get_github_token(self, version_info):
        """Получает GitHub токен для версии с валидацией"""
        if version_info['update_token_env'] is None:
            self.messages.print_output(f"{Colors.CYAN}ℹ️ Base версия - публичный репозиторий, токен не требуется{Colors.END}\n")
            return None
        
        token_env = version_info['update_token_env']
        token = os.getenv(token_env)
        
        if not token:
            self.messages.print_output(f"{Colors.YELLOW}⚠️ Переменная окружения {token_env} не установлена{Colors.END}\n")
            return None
        
        # Проверяем токен из окружения
        self.messages.print_output(f"{Colors.CYAN}🔍 Проверяю токен из переменной окружения {token_env}...{Colors.END}\n")
        is_valid, message = self.validate_github_token(token)
        
        if is_valid:
            self.messages.print_output(f"{Colors.GREEN}✅ {message}{Colors.END}\n")
            return token
        else:
            self.messages.print_output(f"{Colors.RED}❌ Токен из окружения недействителен: {message}{Colors.END}\n")
            return None
    
    def request_manual_token(self):
        """Запрашивает токен вручную с валидацией"""
        self.messages.print_output(f"\n{Colors.YELLOW}🔑 Введите GitHub токен:{Colors.END}\n")
        self.messages.print_output(f"{Colors.CYAN}💡 Для отмены введите '0'{Colors.END}\n")
        
        while True:
            token = self.messages.safe_input("GitHub токен: ").strip()
            
            # Проверяем на отмену
            if token == '0':
                self.messages.print_output(f"{Colors.YELLOW}⚠️ Ввод токена отменен{Colors.END}\n")
                return None
            
            if not token:
                self.messages.print_output(f"{Colors.RED}❌ Токен не может быть пустым. Попробуйте снова.{Colors.END}\n")
                continue
            
            # Проверяем токен
            self.messages.print_output(f"{Colors.CYAN}🔍 Проверяю токен...{Colors.END}\n")
            is_valid, message = self.validate_github_token(token)
            
            if is_valid:
                self.messages.print_output(f"{Colors.GREEN}✅ {message}{Colors.END}\n")
                return token
            else:
                self.messages.print_output(f"{Colors.RED}❌ Токен недействителен: {message}{Colors.END}\n")
                self.messages.print_output(f"{Colors.YELLOW}🔄 Попробуйте снова или введите '0' для отмены{Colors.END}\n")
    
    
    def is_factory_config(self, path):
        """Проверяет, является ли путь заводским конфигом"""
        for factory_path in self.config['factory_configs']:
            # Проверяем точное совпадение
            if path == factory_path:
                return True
            # Проверяем, что path является родительской папкой для factory_path
            if factory_path.startswith(path + "/"):
                return True
        return False
    
    def get_all_paths_to_update(self, include_factory_configs=False):
        """Возвращает полный список путей для обновления"""
        paths = []
        
        # Добавляем основные включенные пути
        for included_path in self.config['included_paths']:
            paths.append({
                'path': included_path,
                'type': 'included',
                'description': f"Обновляю: {included_path}"
            })
        
        # Добавляем заводские конфиги (если нужно)
        if include_factory_configs:
            for factory_config in self.config['factory_configs']:
                paths.append({
                    'path': factory_config,
                    'type': 'factory',
                    'description': f"Обновляю заводской конфиг: {factory_config}"
                })
        
        return paths
    
    def is_non_critical(self, path):
        """Проверяет, является ли путь некритичным для обновления"""
        # Нормализуем пути для корректного сравнения
        normalized_path = path.replace("\\", "/")
        
        for non_critical_path in self.config['non_critical_paths']:
            normalized_non_critical = non_critical_path.replace("\\", "/")
            
            # Проверяем точное совпадение пути
            if normalized_path == normalized_non_critical:
                return True
            
            # Проверяем, что путь заканчивается на некритичный путь
            # Но только если это действительно подпуть, а не случайное совпадение
            if normalized_path.endswith(normalized_non_critical):
                # Дополнительная проверка: убеждаемся, что это подпуть
                # Например: "tools/core" должен совпадать с "tools/core", но не с "utilities/core"
                if normalized_path == normalized_non_critical or normalized_path.endswith("/" + normalized_non_critical):
                    return True
        
        return False
    
    def remove_old(self, path):
        """Удаляет старый файл или папку"""
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    self.messages.print_output(f"{Colors.YELLOW}🗑 Удалена папка: {path}{Colors.END}\n")
                else:
                    os.remove(path)
                    self.messages.print_output(f"{Colors.YELLOW}🗑 Удален файл: {path}{Colors.END}\n")
            except Exception as e:
                # Проверяем, является ли ошибка некритичной
                if self.is_non_critical(path):
                    self.messages.print_output(f"{Colors.YELLOW}⚠️ Не удалось удалить {path}: {e}{Colors.END}\n")
                    self.messages.print_output(f"{Colors.CYAN}💡 Продолжаю без удаления...{Colors.END}\n")
                    # НЕ пробрасываем ошибку для некритичных путей
                else:
                    # Критичная ошибка - пробрасываем исключение
                    raise e
    
    def copy_new(self, src, dst):
        """Копирует новый файл или папку с автоматическим созданием недостающих папок"""
        try:
            if os.path.isdir(src):
                # Создаем родительские папки если их нет
                parent_dir = os.path.dirname(dst)
                if parent_dir and not os.path.exists(parent_dir):
                    self.messages.print_output(f"{Colors.YELLOW}⚠️ Создаю родительскую папку: {parent_dir}{Colors.END}\n")
                    os.makedirs(parent_dir, exist_ok=True)
                
                # Копируем папку
                if os.path.exists(dst):
                    self.messages.print_output(f"{Colors.CYAN}🔄 Обновляю существующую папку: {dst}{Colors.END}\n")
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    self.messages.print_output(f"{Colors.CYAN}📁 Создаю новую папку: {dst}{Colors.END}\n")
                    shutil.copytree(src, dst)
                self.messages.print_output(f"{Colors.GREEN}✅ Скопирована папка: {dst}{Colors.END}\n")
            else:
                # Для файлов тоже создаем родительские папки
                parent_dir = os.path.dirname(dst)
                if parent_dir and not os.path.exists(parent_dir):
                    self.messages.print_output(f"{Colors.YELLOW}⚠️ Создаю родительскую папку: {parent_dir}{Colors.END}\n")
                    os.makedirs(parent_dir, exist_ok=True)
                
                # Копируем файл
                shutil.copy2(src, dst)
                self.messages.print_output(f"{Colors.GREEN}✅ Скопирован файл: {dst}{Colors.END}\n")
        except Exception as e:
            # Проверяем, является ли ошибка некритичной
            if self.is_non_critical(dst):
                self.messages.print_output(f"{Colors.YELLOW}⚠️ Не удалось скопировать {dst}: {e}{Colors.END}\n")
                self.messages.print_output(f"{Colors.CYAN}💡 Продолжаю без копирования...{Colors.END}\n")
                # НЕ пробрасываем ошибку для некритичных путей
            else:
                # Критичная ошибка - пробрасываем исключение
                raise e
    
    def create_backup(self, include_factory_configs=False):
        """Создает резервную копию проекта"""
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.project_root, f"{self.config['backup']['dir_name']}_{timestamp}")
        
        self.messages.print_output(f"{Colors.YELLOW}🗂 Создаю резервную копию в {backup_dir}...{Colors.END}\n")
        
        os.makedirs(backup_dir, exist_ok=True)
        
        total_items = 0
        processed_items = 0
        
        # Получаем полный список путей для резервного копирования
        paths_to_backup = self.get_all_paths_to_update(include_factory_configs)
        
        # Фильтруем только существующие пути
        existing_paths = []
        for path_info in paths_to_backup:
            path = path_info['path']
            project_path = os.path.join(self.project_root, path)
            if os.path.exists(project_path):
                existing_paths.append(path)
        
        total_items = len(existing_paths)
        self.messages.print_output(f"{Colors.CYAN}📁 Всего элементов для резервного копирования: {total_items}{Colors.END}\n")
        
        # Копируем элементы для резервного копирования
        for backup_item in existing_paths:
            # Пропускаем папку бэкапа (чтобы избежать рекурсии)
            if backup_item.startswith(self.config['backup']['dir_name']):
                continue
                
            try:
                processed_items += 1
                self.messages.print_output(f"{Colors.CYAN}🗂 Копирую {processed_items}/{total_items}: {backup_item}{Colors.END}\n")
                
                src_path = os.path.join(self.project_root, backup_item)
                backup_path = os.path.join(backup_dir, backup_item)
                
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, backup_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, backup_path)
            except Exception as e:
                self.messages.print_output(f"{Colors.RED}⚠️ Ошибка копирования {backup_item}: {e}{Colors.END}\n")
                continue
        
        self.messages.print_output(f"{Colors.GREEN}✅ Резервное копирование завершено: {processed_items}/{total_items} элементов{Colors.END}\n")
        return backup_dir
    
    def restore_backup(self, backup_dir):
        """Восстанавливает из резервной копии"""
        self.messages.print_output(f"{Colors.YELLOW}⏪ Восстанавливаю из резервной копии...{Colors.END}\n")
        
        errors = []
        
        if not os.path.exists(backup_dir):
            self.messages.print_output(f"{Colors.RED}⚠️ Не найден бэкап: {backup_dir}{Colors.END}\n")
            return ["backup_dir_not_found"]
        
        # Восстанавливаем все файлы из бэкапа
        for item in os.listdir(backup_dir):
            try:
                backup_path = os.path.join(backup_dir, item)
                target_path = os.path.join(self.project_root, item)
                
                # Пропускаем исключенные элементы
                if self.is_excluded(item):
                    self.messages.print_output(f"{Colors.CYAN}⏭ Пропускаю исключённый: {item}{Colors.END}\n")
                    continue
                
                self.messages.print_output(f"{Colors.CYAN}🔄 Восстанавливаю: {item}{Colors.END}\n")
                
                # ЭТАП 1: Пробуем удалить существующий файл/папку (не критично если не удалось)
                if os.path.exists(target_path):
                    try:
                        if os.path.isdir(target_path):
                            shutil.rmtree(target_path)
                        else:
                            os.remove(target_path)
                        self.messages.print_output(f"{Colors.YELLOW}🗑 Удален: {item}{Colors.END}\n")
                    except Exception as e:
                        self.messages.print_output(f"{Colors.YELLOW}⚠️ Не удалось удалить {item}: {e}{Colors.END}\n")
                        self.messages.print_output(f"{Colors.CYAN}💡 Продолжаю копирование...{Colors.END}\n")
                
                # ЭТАП 2: Копируем из бэкапа (всегда пробуем)
                if os.path.isdir(backup_path):
                    shutil.copytree(backup_path, target_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(backup_path, target_path)
                self.messages.print_output(f"{Colors.GREEN}✅ Восстановлен: {item}{Colors.END}\n")
                    
            except Exception as e:
                self.messages.print_output(f"{Colors.RED}❌ Не удалось восстановить {item}: {e}{Colors.END}\n")
                errors.append(item)
        
        return errors
    
    def download_and_update(self, version_info, github_token, update_factory_configs=False):
        """Скачивает и обновляет проект"""
        import tempfile
        import zipfile
        import requests
        
        self.messages.print_output(f"{Colors.YELLOW}📥 Скачиваю {version_info['name']} версию...{Colors.END}\n")
        
        # Определяем заголовки для запроса
        if github_token:
            headers = {"Authorization": f"token {github_token}"}
            self.messages.print_output(f"{Colors.CYAN}🔑 Подключаюсь с токеном для Pro версии...{Colors.END}\n")
        else:
            headers = {}
            self.messages.print_output(f"{Colors.CYAN}🔓 Скачиваю Base версию без токена (публичный репозиторий)...{Colors.END}\n")
        
        try:
            # Скачиваем архив с GitHub
            repo_url = version_info['repo_url']
            branch = version_info['branch']
            
            # Пробуем разные методы скачивания
            download_methods = [
                f"{repo_url}/archive/refs/heads/{branch}.zip",
                f"{repo_url}/releases/latest/download/source.zip",
            ]
            
            self.messages.print_output(f"{Colors.CYAN}🔽 Скачиваю из репозитория: {repo_url}{Colors.END}\n")
            self.messages.print_output(f"{Colors.CYAN}   Ветка: {branch}{Colors.END}\n")
            
            # Пробуем разные методы скачивания
            response = None
            for i, zip_url in enumerate(download_methods, 1):
                self.messages.print_output(f"{Colors.CYAN}   🔍 Метод {i}: {zip_url}{Colors.END}\n")
                
                try:
                    response = requests.get(zip_url, headers=headers)
                    if response.status_code == 200:
                        self.messages.print_output(f"{Colors.GREEN}   ✅ Успешно! Размер: {len(response.content)} байт{Colors.END}\n")
                        break
                    else:
                        self.messages.print_output(f"{Colors.RED}   ❌ Статус: {response.status_code}{Colors.END}\n")
                except Exception as e:
                    self.messages.print_output(f"{Colors.RED}   ❌ Ошибка: {e}{Colors.END}\n")
            
            if not response or response.status_code != 200:
                raise Exception("Ошибка скачивания: все методы не удались")
                
        except Exception as e:
            self.messages.print_output(f"{Colors.RED}❌ Ошибка скачивания: {e}{Colors.END}\n")
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

            # Обновляем все пути из белого списка
            self.messages.print_output(f"{Colors.YELLOW}♻️ Обновляю включенные пути...{Colors.END}\n")
            non_critical_errors = []
            
            # Получаем полный список путей для обновления
            paths_to_update = self.get_all_paths_to_update(update_factory_configs)
            
            # Обновляем все пути
            for path_info in paths_to_update:
                path = path_info['path']
                description = path_info['description']
                
                repo_path = os.path.join(repo_root, path)
                project_path = os.path.join(self.project_root, path)
                
                # Проверяем, существует ли путь в репозитории
                if os.path.exists(repo_path):
                    self.messages.print_output(f"{Colors.CYAN}♻️ {description}{Colors.END}\n")
                    self.remove_old(project_path)
                    self.copy_new(repo_path, project_path)
                else:
                    self.messages.print_output(f"{Colors.YELLOW}⏭️ Пропускаем (не найден в репозитории): {path}{Colors.END}\n")
            
            # Если были некритичные ошибки, сообщаем об этом
            if non_critical_errors:
                self.messages.print_output(f"{Colors.YELLOW}⚠️ Некритичные ошибки при обновлении: {', '.join(non_critical_errors)}{Colors.END}\n")
                self.messages.print_output(f"{Colors.CYAN}💡 Эти папки будут обновлены при следующем запуске{Colors.END}\n")
    
    def run_update(self):
        """Запускает полный процесс обновления"""
        self.messages.print_output(f"{Colors.GREEN}🔄 Запускаем обновление проекта...{Colors.END}\n")
        
        # Проверяем и устанавливаем зависимости
        self.messages.print_output(f"\n{Colors.BLUE}=== ЭТАП: Проверка зависимостей ==={Colors.END}\n")
        if not self.check_dependencies():
            self.messages.print_output(f"{Colors.RED}❌ Не удалось установить зависимости. Обновление отменено.{Colors.END}\n")
            return False
        
        # Показываем доступные версии
        available_versions = self.get_available_versions()
        self.messages.print_output(f"{Colors.YELLOW}📋 Доступные версии:{Colors.END}\n")
        for version in available_versions:
            version_info = self.get_version_info(version)
            self.messages.print_output(f"  • {version.upper()}: {version_info['name']} - {version_info['description']}\n")
        
        # Запрашиваем версию
        while True:
            selected_version = self.messages.safe_input(f"\n{Colors.YELLOW}Введите версию для обновления ({', '.join(available_versions)}): {Colors.END}").strip().lower()
            if self.validate_version(selected_version):
                break
            self.messages.print_output(f"{Colors.RED}❌ Неверная версия. Доступные: {', '.join(available_versions)}{Colors.END}\n")
        
        version_info = self.get_version_info(selected_version)
        self.messages.print_output(f"\n{Colors.GREEN}✅ Выбрана версия: {version_info['name']} ({version_info['description']}){Colors.END}\n")
        
        # Запрашиваем обновление заводских конфигов
        update_factory_configs = self.messages.safe_input(f"\n{Colors.YELLOW}Обновить заводские конфиги (config, resources)? (Y/N, по умолчанию N): {Colors.END}").strip().lower() == 'y'
        
        if update_factory_configs:
            self.messages.print_output(f"{Colors.YELLOW}🛠 Включено обновление заводских конфигов!{Colors.END}\n")
        else:
            self.messages.print_output(f"{Colors.CYAN}📁 Заводские конфиги будут пропущены (обновляются отдельно){Colors.END}\n")
        
        # Создаем резервную копию
        backup_dir = self.create_backup(update_factory_configs)
        
        try:
            # Проверяем наличие токена
            github_token = self.get_github_token(version_info)
            
            if not github_token and version_info['update_token_env']:
                # Pro версия - пробуем с ручным токеном
                self.messages.print_output(f"{Colors.YELLOW}❌ Не удалось получить токен из окружения{Colors.END}\n")
                self.messages.print_output(f"{Colors.CYAN}ℹ️ Пробую запросить токен вручную...{Colors.END}\n")
                github_token = self.request_manual_token()
                
                # Проверяем, не отменил ли пользователь ввод
                if github_token is None:
                    self.messages.print_output(f"{Colors.YELLOW}⚠️ Обновление отменено пользователем{Colors.END}\n")
                    return False
            
            # Скачиваем и обновляем
            self.download_and_update(version_info, github_token, update_factory_configs)
            
            self.messages.print_output(f"{Colors.GREEN}✅ Обновление завершено успешно!{Colors.END}\n")
            
            # Спрашиваем про удаление бэкапа
            keep_backup = self.messages.safe_input(f"\n{Colors.YELLOW}Удалить резервную копию? (Y/N, по умолчанию N): {Colors.END}").strip().lower() == 'y'
            if keep_backup:
                shutil.rmtree(backup_dir)
                self.messages.print_output(f"{Colors.GREEN}🗑 Резервная копия удалена.{Colors.END}\n")
            else:
                self.messages.print_output(f"{Colors.CYAN}💾 Резервная копия сохранена в {backup_dir}{Colors.END}\n")
            
            self.messages.print_output(f"\n{Colors.GREEN}🚀 Обновление завершено!{Colors.END}\n")
            self.messages.print_output(f"{Colors.CYAN}💡 Все этапы выполнены успешно:{Colors.END}\n")
            self.messages.print_output(f"{Colors.CYAN}   ✅ Файлы обновлены{Colors.END}\n")
            self.messages.print_output(f"{Colors.CYAN}   ✅ Проект готов к работе{Colors.END}\n")
            
            return True
            
        except Exception as e:
            self.messages.print_output(f"{Colors.RED}❌ Ошибка обновления: {e}{Colors.END}\n")
            self.messages.print_output(f"{Colors.YELLOW}⏪ Восстанавливаю из резервной копии...{Colors.END}\n")
            
            errors = self.restore_backup(backup_dir)
            if errors:
                self.messages.print_output(f"{Colors.RED}❌ Не удалось восстановить следующие файлы/папки: {errors}{Colors.END}\n")
                self.messages.print_output(f"{Colors.YELLOW}❗ Бэкап сохранён в {backup_dir}. Восстановите вручную!{Colors.END}\n")
            else:
                self.messages.print_output(f"{Colors.GREEN}✅ Откат завершён. Проект восстановлен.{Colors.END}\n")
                self.messages.print_output(f"{Colors.CYAN}💾 Резервная копия сохранена в {backup_dir}{Colors.END}\n")
            
            return False

class CoreUpdater:
    """Основной класс для обновления Coreness"""
    
    def __init__(self):
        """Инициализация класса"""
        self.update_counter = 0
        self.messages = MessageHandler()
        self.utils = UtilityManager(self.messages)
        self.docker = DockerManager(self.messages, self.utils)
        self.updater = UpdateManager(self.messages, self.utils)
        

    def check_location(self):
        """Проверяет папку где лежит скрипт и показывает информацию"""
        script_path = self.utils.get_script_path()
        project_root = self.utils.get_project_root()
        
        self.messages.print_output(f"{Colors.CYAN}📁 Скрипт находится в: {script_path.parent}{Colors.END}\n")
        
        # Безопасно получаем рабочую директорию
        try:
            current_dir = Path.cwd()
            self.messages.print_output(f"{Colors.CYAN}📁 Рабочая папка: {current_dir}{Colors.END}\n")
        except FileNotFoundError:
            self.messages.print_output(f"{Colors.YELLOW}⚠️ Рабочая папка недоступна (возможно, удалена){Colors.END}\n")
        
        self.messages.print_output(f"{Colors.CYAN}📁 Корень проекта: {project_root}{Colors.END}\n")
        
        return self.utils.is_in_project_root()

    def _cleanup_script_from_root(self):
        """Удаляет скрипт из корня проекта, если он там есть"""
        script_path = self.utils.get_script_path()
        project_root = self.utils.get_project_root()
        
        # Проверяем, находится ли скрипт в корне проекта
        if script_path.parent == project_root:
            script_name = script_path.name
            root_script_path = project_root / script_name
            
            if root_script_path.exists():
                try:
                    self.messages.print_output(f"{Colors.YELLOW}🧹 Удаляю скрипт из корня проекта: {script_name}{Colors.END}\n")
                    root_script_path.unlink()
                    self.messages.print_output(f"{Colors.GREEN}✅ Скрипт удален из корня проекта{Colors.END}\n")
                except Exception as e:
                    self.messages.print_output(f"{Colors.RED}❌ Не удалось удалить скрипт из корня: {e}{Colors.END}\n")
            else:
                self.messages.print_output(f"{Colors.CYAN}ℹ️ Скрипт уже отсутствует в корне проекта{Colors.END}\n")
        else:
            self.messages.print_output(f"{Colors.CYAN}ℹ️ Скрипт запущен из tools/core, очистка не требуется{Colors.END}\n")

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
            # Обновление данных
            self.messages.print_output(f"{Colors.BLUE}=== ОБНОВЛЕНИЕ ДАННЫХ ==={Colors.END}\n")
            
            if not self.updater.run_update():
                self.messages.print_output(f"{Colors.RED}❌ Обновление завершилось с ошибками{Colors.END}\n")
                return True
            
            # Удаляем скрипт из корня проекта, если он там есть
            self._cleanup_script_from_root()
            
            self.messages.print_output(f"{Colors.GREEN}🎉 Обновление данных завершено успешно!{Colors.END}\n")
            return True
        elif choice == '3':
            self.messages.print_output(f"{Colors.YELLOW}⚠️ Заглушка: Миграция базы данных{Colors.END}\n")
            return True
        elif choice == '0':
            self.messages.print_output(f"{Colors.BLUE}До свидания!{Colors.END}\n")
            return True  # Возвращаем True для выхода из главного цикла
        else:
            self.messages.print_output(f"{Colors.RED}Неверный выбор. Попробуйте снова.{Colors.END}\n")
            return False

    def main_menu(self):
        """Главное меню приложения"""
        while True:
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
            choice = self.messages.safe_input(f"{Colors.YELLOW}Введите номер (0-3): {Colors.END}")
            if self._handle_menu_choice(choice):
                # Если выбор был "0" (выход), прерываем цикл
                if choice == '0':
                    break
                # Иначе продолжаем цикл (возвращаемся в меню без дополнительных действий)

if __name__ == "__main__":
    # Создаем экземпляр класса
    updater = CoreUpdater()
    
    # Запускаем главное меню
    updater.main_menu()
