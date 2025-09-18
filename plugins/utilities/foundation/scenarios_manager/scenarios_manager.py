import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ScenariosManager:
    """Менеджер сценариев и триггеров"""

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

    def __init__(self, config_dir: str = "config", max_actions_limit: int = 50, max_nesting_depth: int = 10, **kwargs):
        self.logger = kwargs['logger']
        self.config_dir = config_dir
        self._max_actions_limit = max_actions_limit
        self._max_nesting_depth = max_nesting_depth
        
        # Кеш для сценариев и триггеров
        self._cache: Dict[str, Any] = {}
        self._scenario_name_map: Dict[str, str] = {}  # name -> full_key для поиска по короткому имени

        # Устанавливаем корень проекта надежным способом
        self.project_root = self._find_project_root(Path(__file__))

        # Получаем settings_manager для определения текущего пресета
        self.settings_manager = kwargs.get('settings_manager')

        # Загружаем сценарии и триггеры
        self._load_scenarios_and_triggers()

    def _load_scenarios_and_triggers(self):
        """Загрузка всех сценариев и триггеров из пресета"""
        self.logger.info("Загрузка сценариев и триггеров...")
        self._cache.clear()
        self._scenario_name_map.clear()

        # Определяем текущий пресет
        preset = self.settings_manager.get_current_preset()

        # Загружаем триггеры из пресета
        triggers = self._load_yaml_file(f'presets/{preset}/triggers.yaml')
        self._cache['triggers'] = triggers

        # Загружаем сценарии из пресета
        scenarios = self._load_scenarios_from_dir(f'presets/{preset}/scenarios')
        self._cache['scenarios'] = scenarios
        self.logger.info(f"Загружено сценариев: {len(scenarios)}")

    def _load_yaml_file(self, relative_path: str) -> dict:
        """Загружает YAML файл по относительному пути от config_dir"""
        file_path = os.path.join(self.config_dir, relative_path)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_scenarios_from_dir(self, relative_dir: str) -> dict:
        """Рекурсивно загружает сценарии из указанной директории и всех подпапок"""
        scenarios = {}
        scenarios_dir = os.path.join(self.config_dir, relative_dir)

        if os.path.isdir(scenarios_dir):
            for root, _, files in os.walk(scenarios_dir):
                for filename in files:
                    if filename.endswith(('.yaml', '.yml')):
                        file_path = os.path.join(root, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_scenarios = yaml.safe_load(f) or {}
                            # Получаем относительный путь от scenarios_dir до файла
                            rel_path = os.path.relpath(file_path, scenarios_dir)
                            # Удаляем расширение и заменяем разделители на точки
                            file_prefix = rel_path.replace('\\', '/').replace('/', '.')
                            if file_prefix.endswith('.yaml'):
                                file_prefix = file_prefix[:-5]
                            elif file_prefix.endswith('.yml'):
                                file_prefix = file_prefix[:-4]
                            for scenario_name, scenario_data in file_scenarios.items():
                                full_key = f"{file_prefix}.{scenario_name}"
                                scenarios[full_key] = scenario_data
                                if scenario_name in self._scenario_name_map:
                                    self.logger.warning(f"Дублирование названия сценария '{scenario_name}'. Используется первый найденный.")
                                else:
                                    self._scenario_name_map[scenario_name] = full_key
        return scenarios

    # === Публичные методы ===

    def get_scenario(self, key: str) -> Optional[dict]:
        """Получить оригинальный сценарий по полному или короткому ключу."""
        # Сначала ищем по полному ключу
        scenario = self._cache.get('scenarios', {}).get(key)
        if scenario is not None:
            return scenario
        # Если не найдено — ищем по короткому имени
        full_key = self._scenario_name_map.get(key)
        if full_key:
            return self._cache.get('scenarios', {}).get(full_key)
        return None

    def get_all_scenarios(self) -> dict:
        """Получить все оригинальные сценарии"""
        return self._cache.get('scenarios', {}).copy()

    def get_triggers(self) -> dict:
        """Получить триггеры"""
        return self._cache.get('triggers', {})

    def get_scenario_key(self, name_or_key: str) -> Optional[str]:
        """Вернуть полное имя сценария (file.scenario) по короткому или полному имени. Если не найдено — None."""
        if name_or_key in self._cache.get('scenarios', {}):
            return name_or_key
        full_key = self._scenario_name_map.get(name_or_key)
        if full_key:
            return full_key
        return None

    def get_scenario_name(self, name_or_key: str) -> Optional[str]:
        """Вернуть короткое имя сценария по короткому или полному имени. Если не найдено — None."""
        if name_or_key in self._scenario_name_map:
            return name_or_key
        if name_or_key in self._cache.get('scenarios', {}):
            return name_or_key.split('.')[-1]
        return None

    def reload(self):
        """Перезагрузить все сценарии и триггеры"""
        self.logger.info("Перезагрузка сценариев и триггеров...")
        self._load_scenarios_and_triggers() 