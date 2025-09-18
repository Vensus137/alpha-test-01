import datetime
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv


class SettingsManager:
    """Менеджер настроек бота и глобальных параметров"""

    @staticmethod
    def _find_project_root(start_path: Path) -> Path:
        """Надежно определяет корень проекта"""
        # Сначала проверяем переменную окружения
        env_root = os.environ.get('PROJECT_ROOT')
        if env_root and Path(env_root).exists():
            return Path(env_root)
        
        # Ищем по ключевым файлам/папкам
        current = start_path
        while current != current.parent:
            # Проверяем наличие ключевых файлов проекта
            if (current / "main.py").exists() and \
               (current / "plugins").exists() and \
               (current / "app").exists():
                return current
            current = current.parent
        
        # Если не найден - используем fallback
        return start_path.parent.parent.parent.parent

    def __init__(self, config_dir: str = "config", **kwargs):
        self.logger = kwargs['logger']
        self.plugins_manager = kwargs['plugins_manager']
        self.config_dir = config_dir
        
        # Кеш для настроек и планов запуска
        self._cache: Dict[str, Any] = {}
        
        # Время запуска приложения (будем получать по требованию)
        self._startup_time = None

        # Устанавливаем корень проекта надежным способом
        self.project_root = self._find_project_root(Path(__file__))

        # Загружаем переменные окружения из .env файла
        self._load_environment_variables()

        # Загружаем настройки
        self._load_settings()

    def _load_environment_variables(self):
        """Загружает переменные окружения из .env файла"""
        try:
            # Загружаем .env из корня проекта
            load_dotenv(self.project_root / '.env')
            self.logger.info("Переменные окружения загружены")
        except Exception as e:
            self.logger.warning(f"Ошибка загрузки переменных окружения: {e}")

    def _load_settings(self):
        """Загрузка всех настроек с поддержкой пресетов и мерджа"""
        # Сначала загружаем глобальные настройки для получения active_preset
        global_settings = self._load_yaml_file('settings.yaml')
        preset = global_settings.get('global', {}).get('active_preset', 'default')
        
        # Если active_preset не указан, используем default_preset из config.yaml
        if not preset:
            plugin_settings = self.get_plugin_settings('settings_manager')
            preset = plugin_settings.get('default_preset', 'default')
        
        # Сохраняем пресет в кэш для быстрого доступа
        self._cache['current_preset'] = preset
        
        self.logger.info(f"Загрузка настроек для пресета: {preset}")
        
        # Очищаем только настройки, сохраняя кэш планов запуска
        settings_keys = ['settings']
        for key in settings_keys:
            if key in self._cache:
                del self._cache[key]

        # Загружаем настройки пресета
        preset_settings = self._load_yaml_file(f'presets/{preset}/settings.yaml')
        
        # Мерджим: глобальные + пресет (пресет перекрывает глобальные)
        merged_settings = self._deep_merge(global_settings, preset_settings)
        
        # Обрабатываем переменные окружения в итоговых настройках
        self._cache['settings'] = self._resolve_env_variables(merged_settings)

        self.logger.info(f"Настройки загружены для пресета: {preset}")

    def _load_yaml_file(self, relative_path: str) -> dict:
        """Загружает YAML файл по относительному пути от config_dir"""
        file_path = os.path.join(self.project_root, self.config_dir, relative_path)
        if os.path.exists(file_path):
            return self._load_yaml_from_path(file_path)
        
        self.logger.warning(f"Файл конфигурации не найден: {relative_path}")
        return {}

    def _load_yaml_from_path(self, file_path: str) -> dict:
        """Загружает YAML файл по абсолютному пути"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Обрабатываем переменные окружения
                processed_content = self.resolve_env_variables(content)
                return yaml.safe_load(processed_content) or {}
        except Exception as e:
            self.logger.error(f"Ошибка загрузки файла {file_path}: {e}")
            return {}

    def _deep_merge(self, base_dict: dict, override_dict: dict) -> dict:
        """Глубокое слияние словарей: override_dict перекрывает base_dict"""
        result = base_dict.copy()
        
        for key, value in override_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Рекурсивно мерджим вложенные словари
                result[key] = self._deep_merge(result[key], value)
            else:
                # Перекрываем значение
                result[key] = value
        
        return result

    # === Публичные методы ===

    def get_startup_time(self):
        """Получить время запуска приложения"""
        if self._startup_time is None:
            self._startup_time = self._get_local_time()
        return self._startup_time

    def get_current_preset(self) -> str:
        """Получить текущий активный пресет из кэша"""
        return self._cache.get('current_preset', 'default')


    def get_settings_section(self, section: str) -> dict:
        """Получить секцию из settings.yaml по имени (например, 'logger', 'bot_docs')."""
        settings = self._cache.get('settings', {})
        return settings.get(section, {})

    def get_all_settings(self) -> dict:
        """Получить все настройки из settings.yaml"""
        return self._cache.get('settings', {}).copy()

    def get_project_root(self) -> Path:
        """Получить корень проекта"""
        return self.project_root

    def get_global_settings(self) -> dict:
        """Получить глобальные настройки из секции 'global'"""
        return self.get_settings_section('global')

    def get_file_base_path(self) -> str:
        """Получить базовый путь для файлов из глобальных настроек"""
        global_settings = self.get_global_settings()
        return global_settings.get('file_base_path', 'resources')

    def get_ssl_certificates_path(self) -> str:
        """Получить путь к папке SSL сертификатов из глобальных настроек"""
        global_settings = self.get_global_settings()
        return global_settings.get('ssl_certificates_path', 'data/ssl_certificates')
    
    def get_ssl_certificate_path(self, certificate_name: str = None) -> str:
        """Получить полный путь к конкретному SSL сертификату"""
        global_settings = self.get_global_settings()
        
        # Если указан конкретный сертификат
        if certificate_name:
            ssl_certs_dir = self.get_ssl_certificates_path()
            project_root = self.get_project_root()
            return os.path.join(project_root, ssl_certs_dir, certificate_name)
        
        # Иначе возвращаем путь к дефолтному сертификату
        default_cert = global_settings.get('default_ssl_certificate', 'russian_certs.pem')
        ssl_certs_dir = self.get_ssl_certificates_path()
        project_root = self.get_project_root()
        return os.path.join(project_root, ssl_certs_dir, default_cert)

    
    def _resolve_env_variables(self, data: Any) -> Any:
        """
        Рекурсивно обрабатывает переменные окружения в формате ${VARIABLE}
        """
        if isinstance(data, dict):
            return {key: self._resolve_env_variables(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._resolve_env_variables(item) for item in data]
        elif isinstance(data, str):
            return self._resolve_env_variable_in_string(data)
        else:
            return data
    
    def _resolve_env_variable_in_string(self, value: str) -> str:
        """
        Заменяет переменные окружения в строке
        """
        if not isinstance(value, str):
            return value
        
        # Проверяем, является ли вся строка переменной окружения
        if value.startswith('${') and value.endswith('}'):
            env_var = value[2:-1]
            resolved_value = os.getenv(env_var, '')
            if not resolved_value:
                self.logger.warning(f"Переменная окружения {env_var} не установлена")
            return resolved_value
        
        # Проверяем, содержит ли строка переменные окружения
        import re
        pattern = r'\$\{([^}]+)\}'
        
        def replace_env_var(match):
            env_var = match.group(1)
            resolved_value = os.getenv(env_var, '')
            if not resolved_value:
                self.logger.warning(f"Переменная окружения {env_var} не установлена")
            return resolved_value
        
        return re.sub(pattern, replace_env_var, value)
    
    def resolve_env_variables(self, data: Any) -> Any:
        """
        Публичный метод для обработки переменных окружения в данных
        """
        return self._resolve_env_variables(data)

    def resolve_file_path(self, path: str) -> str:
        """
        Универсальное разрешение пути в абсолютный.
        Работает с любыми путями: относительными, абсолютными, смешанными.
        """
        # Если уже абсолютный и в правильной базовой папке - возвращаем как есть
        base_path = self.get_file_base_path()
        full_base_path = os.path.join(self.project_root, base_path)
        
        if path.startswith(full_base_path):
            return path  # Уже корректный абсолютный путь
        
        # Если относительный - разрешаем
        return os.path.join(self.project_root, base_path, path)

    def get_relative_path(self, path: str) -> str:
        """
        Универсальное получение относительного пути.
        Работает с любыми путями: относительными, абсолютными, смешанными.
        """
        try:
            base_path = self.get_file_base_path()
            full_base_path = os.path.join(self.project_root, base_path)
            
            # Если уже относительный - возвращаем как есть
            if not os.path.isabs(path):
                return path.replace('\\', '/')  # Уже относительный, нормализуем
            
            # Если абсолютный - преобразуем в относительный
            if path.startswith(full_base_path):
                relative_path = os.path.relpath(path, full_base_path)
                return relative_path.replace('\\', '/')
            else:
                # Если файл не в базовом пути, возвращаем имя файла
                return os.path.basename(path)
        except Exception as e:
            self.logger.warning(f"Ошибка получения относительного пути для {path}: {e}")
            return os.path.basename(path)

    def get_plugin_settings(self, plugin_name: str) -> dict:
        """
        Универсальный метод для получения настроек любого плагина (утилиты или сервиса)
        с учётом приоритета: глобальные из settings.yaml > локальные из config.yaml плагина
        """
        # Получаем информацию о плагине из plugins_manager
        plugin_info = self.plugins_manager.get_plugin_info(plugin_name)
        if not plugin_info:
            self.logger.warning(f"Плагин {plugin_name} не найден")
            return {}
        
        plugin_type = plugin_info.get('type', 'unknown')
        
        # Глобальные настройки из settings.yaml
        global_settings = self.get_settings_section(plugin_name)
        
        # Локальные настройки из config.yaml плагина
        local_settings = plugin_info.get('settings', {})
        
        # Собираем итоговый dict с приоритетом: глобальные > локальные
        all_keys = set(global_settings.keys()) | set(local_settings.keys())
        merged = {}
        for key in all_keys:
            global_val = global_settings.get(key, None)
            local_val = local_settings.get(key, None)
            
            # Если локальный параметр — dict с default, берём default
            if isinstance(local_val, dict) and 'default' in local_val:
                local_val = local_val['default']
            
            # Приоритет: глобальные > локальные
            merged[key] = global_val if global_val is not None else local_val
        
        # Обрабатываем переменные окружения в итоговых настройках
        return self._resolve_env_variables(merged)

    def reload(self):
        """Перезагрузить настройки бота и глобальные параметры"""
        self.logger.info("Перезагрузка настроек...")
        self._load_settings()
        # Очищаем кэш планов запуска при перезагрузке
        self.invalidate_startup_cache()
    
    def _get_local_time(self) -> datetime.datetime:
        """Получить текущее локальное время без зависимости от datetime_formatter"""
        import datetime
        from zoneinfo import ZoneInfo

        # Получаем настройки timezone из datetime_formatter (если доступен)
        # или используем значение по умолчанию
        timezone_name = "Europe/Moscow"  # значение по умолчанию
        
        try:
            # Пытаемся получить настройки datetime_formatter
            datetime_settings = self.get_plugin_settings("datetime_formatter")
            timezone_name = datetime_settings.get('timezone', timezone_name)
        except Exception:
            # Если не удалось получить настройки, используем значение по умолчанию
            pass
        
        # Создаем timezone и получаем локальное время
        tz = ZoneInfo(timezone_name)
        return datetime.datetime.now(tz).replace(tzinfo=None)
    
    # === Методы планирования запуска ===
    
    def get_startup_plan(self) -> Dict[str, Any]:
        """Получает полный план запуска приложения с кэшированием"""
        self.logger.info("Запрос плана запуска...")
        
        try:
            # Проверяем инициализацию кэша
            if not hasattr(self, '_cache') or self._cache is None:
                self.logger.error("Кэш не инициализирован!")
                self._cache = {}
            
            if 'startup_plan' not in self._cache:
                self.logger.info("План запуска не кэширован, строим...")
                self._cache['startup_plan'] = None
            
            if self._cache['startup_plan'] is None:
                self.logger.info("Строим план запуска...")
                try:
                    self._cache['startup_plan'] = self._build_startup_plan()
                    self.logger.info("План запуска построен успешно")
                except Exception as e:
                    self.logger.error(f"Ошибка построения плана запуска: {e}")
                    # Возвращаем пустой план вместо None
                    self._cache['startup_plan'] = {
                        'enabled_services': [],
                        'required_utilities': [],
                        'dependency_order': [],
                        'total_services': 0,
                        'total_utilities': 0
                    }
            else:
                self.logger.info("Используем кэшированный план запуска")
            
            return self._cache['startup_plan']
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка в get_startup_plan: {e}")
            # Возвращаем пустой план в случае критической ошибки
            return {
                'enabled_services': [],
                'required_utilities': [],
                'dependency_order': [],
                'total_services': 0,
                'total_utilities': 0
            }
    
    def get_enabled_services(self) -> List[str]:
        """Получает список включенных сервисов с кэшированием"""
        if 'enabled_services' not in self._cache or self._cache['enabled_services'] is None:
            self._cache['enabled_services'] = self._analyze_enabled_services()
        return self._cache['enabled_services']
    
    def get_required_utilities(self) -> List[str]:
        """Получает список нужных утилит с кэшированием"""
        if 'required_utilities' not in self._cache or self._cache['required_utilities'] is None:
            self._cache['required_utilities'] = self._analyze_required_utilities()
        return self._cache['required_utilities']
    
    def _build_startup_plan(self) -> Dict[str, Any]:
        """Строит полный план запуска приложения"""
        self.logger.info("Строим план запуска приложения...")
        
        # Проверяем доступность plugins_manager
        if not self.plugins_manager:
            self.logger.error("PluginsManager недоступен, возвращаем пустой план")
            return {
                'enabled_services': [],
                'required_utilities': [],
                'dependency_order': [],
                'total_services': 0,
                'total_utilities': 0
            }
        
        # Получаем сервисы, которые МОГУТ запуститься (включены + все зависимости доступны)
        enabled_services = self._analyze_enabled_services()
        
        # Получаем нужные утилиты напрямую
        required_utilities = self._analyze_required_utilities()
        
        # Исключаем утилиты, уже созданные в Application (циклические зависимости)
        excluded_utilities = ['settings_manager', 'plugins_manager']
        for utility in excluded_utilities:
            if utility in required_utilities:
                required_utilities.remove(utility)
                self.logger.info(f"Исключен {utility} из плана инициализации (уже создан в Application)")
        
        # Строим порядок инициализации утилит
        dependency_order = self._calculate_dependency_order(required_utilities)
        
        plan = {
            'enabled_services': enabled_services,
            'required_utilities': required_utilities,
            'dependency_order': dependency_order,
            'total_services': len(enabled_services),
            'total_utilities': len(required_utilities)
        }
        
        self.logger.info(f"План запуска: {plan['total_services']} сервисов, {plan['total_utilities']} утилит")
        
        return plan
    
    def _analyze_enabled_services(self) -> List[str]:
        """Анализирует и возвращает сервисы, которые МОГУТ запуститься (все зависимости доступны)"""
        # Получаем все сервисы напрямую из plugins_manager
        services_info = self.plugins_manager.get_plugins_by_type("services")
        if not services_info:
            self.logger.warning("Не найдено сервисов в PluginsManager")
            return []
        
        # Первый проход: проверяем базовые условия (существование и включенность)
        candidate_services = []
        for service_name in services_info.keys():
            # Получаем объединенные настройки (глобальные + локальные)
            plugin_settings = self.get_plugin_settings(service_name)
            enabled_status = plugin_settings.get('enabled', True)
            
            if enabled_status:
                candidate_services.append(service_name)
            else:
                self.logger.info(f"Сервис {service_name} отключен (глобальные или локальные настройки)")
        
        # Второй проход: проверяем возможность запуска (все зависимости доступны)
        can_start_services = []
        excluded_services = []
        
        for service_name in candidate_services:
            if self._can_plugin_start(service_name):
                can_start_services.append(service_name)
            else:
                excluded_services.append(service_name)
                self.logger.warning(f"Сервис {service_name} исключен: недоступные зависимости")
        
        if excluded_services:
            self.logger.info(f"Исключено сервисов с недоступными зависимостями: {len(excluded_services)}")
        
        self.logger.info(f"Могут запуститься сервисов: {len(can_start_services)} из {len(candidate_services)}")
        return can_start_services
    
    def _analyze_required_utilities(self) -> List[str]:
        """Анализирует и возвращает утилиты, нужные для сервисов, которые МОГУТ запуститься"""
        # Получаем сервисы, которые могут запуститься
        can_start_services = self._analyze_enabled_services()
        
        if not can_start_services:
            self.logger.warning("Нет сервисов, которые могут запуститься")
            return []
        
        # Собираем все транзитивные зависимости для каждого сервиса
        all_required_utilities = set()
        
        for service_name in can_start_services:
            # Получаем ВСЕ транзитивные зависимости сервиса
            service_dependencies = self._collect_all_transitive_dependencies(service_name)
            
            # Добавляем в общий набор (исключаем сам сервис)
            service_dependencies.discard(service_name)
            all_required_utilities.update(service_dependencies)
            
        # Фильтруем только включенные утилиты
        enabled_utilities = self._filter_enabled_utilities(list(all_required_utilities))
        
        self.logger.info(f"Нужно утилит для запуска: {len(enabled_utilities)} из {len(all_required_utilities)}")
        return enabled_utilities
    
    def _filter_enabled_utilities(self, utility_names: List[str]) -> List[str]:
        """Фильтрует только включенные утилиты"""
        enabled_utilities = []
        disabled_count = 0
        
        for utility_name in utility_names:
            # Получаем объединенные настройки (глобальные + локальные)
            plugin_settings = self.get_plugin_settings(utility_name)
            enabled_status = plugin_settings.get('enabled', True)
            
            if enabled_status:
                enabled_utilities.append(utility_name)
            else:
                disabled_count += 1
                self.logger.info(f"Утилита {utility_name} отключена (глобальные или локальные настройки)")
        
        if disabled_count > 0:
            self.logger.info(f"Пропущено отключенных утилит: {disabled_count}")
        
        return enabled_utilities
    
    def _collect_all_transitive_dependencies(self, plugin_name: str) -> set:
        """Собирает ВСЕ транзитивные зависимости для плагина"""
        collected = set()
        self._collect_transitive_dependencies_recursive(plugin_name, collected, [])
        return collected
    
    def _collect_transitive_dependencies_recursive(self, plugin_name: str, collected: set, path: List[str] = None):
        """Рекурсивно собирает транзитивные зависимости для одного плагина"""
        if path is None:
            path = []
        
        # Проверяем циклическую зависимость в текущем пути
        if plugin_name in path:
            # Обнаружена циклическая зависимость
            cycle_start = path.index(plugin_name)
            cycle_path = path[cycle_start:] + [plugin_name]
            self.logger.error(f"Обнаружена циклическая зависимость: {' → '.join(cycle_path)}")
            return  # Избегаем бесконечной рекурсии
        
        # Если уже обрабатывали этот плагин, пропускаем
        if plugin_name in collected:
            return
        
        # Добавляем текущий плагин в путь и в собранные
        path.append(plugin_name)
        collected.add(plugin_name)
        
        # Получаем обязательные и опциональные зависимости отдельно
        mandatory_deps = self.plugins_manager.get_plugin_mandatory_dependencies(plugin_name)
        optional_deps = self.plugins_manager.get_plugin_optional_dependencies(plugin_name)
        
        # Проверяем доступность обязательных зависимостей
        for dep_name in mandatory_deps:
            if not self._is_dependency_available(dep_name):
                self.logger.warning(f"Обязательная зависимость {dep_name} для {plugin_name} недоступна - исключаем плагин")
                # Убираем текущий плагин из собранных (он исключен)
                collected.discard(plugin_name)
                path.pop()
                return
        
        # Если все обязательные доступны, обрабатываем все зависимости
        all_deps = mandatory_deps + optional_deps
        for dep_name in all_deps:
            self._collect_transitive_dependencies_recursive(dep_name, collected, path.copy())
        
        # Убираем текущий плагин из пути
        path.pop()
    
    def _is_dependency_available(self, dep_name: str) -> bool:
        """Проверяет доступность зависимости"""
        # Проверяем существование
        dep_info = self.plugins_manager.get_plugin_info(dep_name)
        if not dep_info:
            return False
        
        # Проверяем включенность
        dep_settings = self.get_plugin_settings(dep_name)
        return dep_settings.get('enabled', True)
    
    def _can_plugin_start(self, plugin_name: str) -> bool:
        """Проверяет, может ли плагин запуститься (базовые проверки)"""
        # Проверяем существование плагина
        plugin_info = self.plugins_manager.get_plugin_info(plugin_name)
        if not plugin_info:
            self.logger.warning(f"Плагин {plugin_name} не найден")
            return False
        
        # Проверяем включенность плагина (объединенные настройки)
        plugin_settings = self.get_plugin_settings(plugin_name)
        if not plugin_settings.get('enabled', True):
            self.logger.info(f"Плагин {plugin_name} отключен (глобальные или локальные настройки)")
            return False
        
        # Проверяем циклические зависимости в цепочке зависимостей
        if self._has_circular_dependencies(plugin_name):
            self.logger.warning(f"Плагин {plugin_name} исключен: обнаружены циклические зависимости")
            return False
        
        return True
    
    def _has_circular_dependencies(self, plugin_name: str) -> bool:
        """Проверяет наличие циклических зависимостей для плагина"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            # Получаем зависимости узла (ВСЕ зависимости для проверки циклических зависимостей)
            dependencies = self.plugins_manager.get_plugin_dependencies(node)
            
            for neighbor in dependencies:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Обнаружена циклическая зависимость
                    cycle_start = list(rec_stack).index(neighbor)
                    cycle_path = list(rec_stack)[cycle_start:] + [neighbor]
                    self.logger.error(f"Обнаружена циклическая зависимость: {' → '.join(cycle_path)}")
                    return True
            
            rec_stack.remove(node)
            return False
        
        return has_cycle(plugin_name)
    
    def _collect_transitive_dependencies(self, dependencies: List[str], collected: set):
        """Рекурсивно собирает транзитивные зависимости (legacy метод для совместимости)"""
        for dep_name in dependencies:
            if dep_name not in collected:
                # Добавляем саму утилиту
                collected.add(dep_name)
                
                # Получаем зависимости этой утилиты (ВСЕ зависимости для правильного порядка)
                dep_deps = self.plugins_manager.get_plugin_dependencies(dep_name)
                collected.update(dep_deps)
                
                # Рекурсивно собираем зависимости зависимостей
                self._collect_transitive_dependencies(dep_deps, collected)
    
    def _calculate_dependency_order(self, utility_names: List[str]) -> List[str]:
        """Вычисляет правильный порядок инициализации для утилит"""
        if not utility_names:
            return []
        
        # Получаем полный граф зависимостей (ВСЕ зависимости для правильного порядка)
        full_graph = {}
        for utility_name in utility_names:
            deps = self.plugins_manager.get_plugin_dependencies(utility_name)
            # Фильтруем только те зависимости, которые есть в нашем списке
            filtered_deps = [dep for dep in deps if dep in utility_names]
            full_graph[utility_name] = set(filtered_deps)
        
        # Топологическая сортировка для подмножества
        def topological_sort(graph: Dict[str, set]) -> List[str]:
            result = []
            visited = set()
            temp_visited = set()
            excluded_nodes = set()  # Узлы с циклическими зависимостями
            
            def visit(node: str):
                if node in temp_visited:
                    # Обнаружена циклическая зависимость - критическая ошибка
                    cycle_start = list(temp_visited).index(node)
                    cycle_path = list(temp_visited)[cycle_start:] + [node]
                    self.logger.error(f"Обнаружена циклическая зависимость: {' → '.join(cycle_path)}")
                    
                    # Исключаем ВСЕ узлы в цикле
                    for cycle_node in cycle_path:
                        excluded_nodes.add(cycle_node)
                        self.logger.warning(f"Исключен узел с циклической зависимостью: {cycle_node}")
                    return
                
                if node in visited:
                    return
                
                temp_visited.add(node)
                
                for neighbor in graph.get(node, set()):
                    visit(neighbor)
                
                temp_visited.remove(node)
                visited.add(node)
                
                # Добавляем узел только если он не исключен
                if node not in excluded_nodes:
                    result.append(node)
                else:
                    self.logger.warning(f"Узел {node} исключен из порядка инициализации")
            
            for node in graph:
                if node not in visited:
                    visit(node)
            
            return result
        
        return topological_sort(full_graph)
    
    def invalidate_startup_cache(self):
        """Инвалидирует кэш планов запуска"""
        self._cache['startup_plan'] = None
        self._cache['enabled_services'] = None
        self._cache['required_utilities'] = None
        self.logger.info("Кэш планов запуска очищен")
    