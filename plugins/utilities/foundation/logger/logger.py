import logging
import os
import sys
from logging.handlers import RotatingFileHandler
# Новый импорт для поиска bot.yaml
from pathlib import Path

import yaml


class Logger:
    """Системный логгер для проекта"""
    
    def __init__(self):
        """Инициализация логгера с поддержкой пресетов"""
        # Получаем текущий пресет из глобальных настроек
        self.preset = self._get_current_preset()
        
        # Путь к глобальным настройкам
        self.global_settings_path = Path('config/settings.yaml')
        
        # Путь к настройкам пресета
        self.preset_settings_path = Path(f'config/presets/{self.preset}/settings.yaml')
    
    # --- Вспомогательные преобразования для безопасного слияния настроек ---
    def _to_bool(self, value, fallback: bool) -> bool:
        if value is None:
            return fallback
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off", ""}:
                return False
        return fallback

    def _to_int(self, value, fallback: int) -> int:
        try:
            return int(value) if value is not None else fallback
        except Exception:
            return fallback

    def _to_str(self, value, fallback: str) -> str:
        try:
            return str(value) if value is not None else fallback
        except Exception:
            return fallback
    
    def _get_current_preset(self) -> str:
        """Получить текущий пресет из глобальных настроек"""
        try:
            with open(self.global_settings_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            global_settings = config.get('global', {})
            return global_settings.get('active_preset', 'default')
        except Exception:
            return 'default'

    def _load_global_logger_settings(self) -> dict:
        """Чтение секции logger из глобальных настроек и пресета с мерджем"""
        # Загружаем глобальные настройки
        global_settings = {}
        if self.global_settings_path.exists():
            try:
                with open(self.global_settings_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                global_settings = config.get('logger', {})
            except Exception:
                pass
        
        # Загружаем настройки пресета
        preset_settings = {}
        if self.preset_settings_path.exists():
            try:
                with open(self.preset_settings_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                preset_settings = config.get('logger', {})
            except Exception:
                pass
        
        # Мерджим: глобальные + пресет (пресет перекрывает глобальные)
        return self._deep_merge(global_settings, preset_settings)

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

    def _load_logging_config(self) -> dict:
        """Загрузка конфига логирования"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

        if not os.path.exists(config_path):
            local_config = {}
        else:
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    config = yaml.safe_load(file)
                local_config = config.get('settings', {}) if config else {}
            except Exception:
                local_config = {}

        # Извлекаем значения и дефолты из локального конфига (plugins/.../config.yaml)
        level = local_config.get('level', {}).get('default', 'INFO')
        file_enabled = local_config.get('file_enabled', {}).get('default', True)
        file_path = local_config.get('file_path', {}).get('default', 'logs/bot.log')
        max_file_size_mb = local_config.get('max_file_size_mb', {}).get('default', 10)
        backup_count = local_config.get('backup_count', {}).get('default', 5)
        local_console_enabled = local_config.get('console_enabled', {}).get('default', True)

        # Глобальные переопределения из настроек пресета (приоритет над локальными)
        global_logger_settings = self._load_global_logger_settings()

        # console_enabled: приоритет console_enabled, затем локальный
        if 'console_enabled' in global_logger_settings:
            console_enabled = self._to_bool(global_logger_settings.get('console_enabled'), local_console_enabled)
        else:
            console_enabled = local_console_enabled

        # Прочие поля: берём глобальные, если указаны, с аккуратным приведением типа
        file_enabled = self._to_bool(global_logger_settings.get('file_enabled', file_enabled), file_enabled)
        level = self._to_str(global_logger_settings.get('level', level), level)
        file_path = self._to_str(global_logger_settings.get('file_path', file_path), file_path)
        max_file_size_mb = self._to_int(global_logger_settings.get('max_file_size_mb', max_file_size_mb), max_file_size_mb)
        backup_count = self._to_int(global_logger_settings.get('backup_count', backup_count), backup_count)

        return {
            'level': level,
            'file_enabled': file_enabled,
            'file_path': file_path,
            'max_file_size_mb': max_file_size_mb,
            'backup_count': backup_count,
            'console_enabled': console_enabled
        }

    def setup_logger(self, name: str = "logger") -> logging.Logger:
        """Настройка основного логгера"""
        # Настройка основного логгера
        config = self._load_logging_config()
        level = config.get('level', 'INFO').upper()
        file_enabled = config.get('file_enabled', True)
        file_path = config.get('file_path', 'logs/bot.log')
        max_file_size_mb = config.get('max_file_size_mb', 10)
        backup_count = config.get('backup_count', 5)
        console_enabled = config.get('console_enabled', True)

        # Создаем логгер
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # Всегда DEBUG, фильтруем на хендлерах

        # Очищаем существующие обработчики
        logger.handlers.clear()

        # Создаем форматтер
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

        # Создаем обработчик для файла
        if file_enabled:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=max_file_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, level))
            logger.addHandler(file_handler)

        # Создаем обработчик для консоли
        if console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG)
            logger.addHandler(console_handler)

        return logger

    def get_logger(self, name: str) -> logging.Logger:
        """Получение и настройка логгера для модуля"""
        return self.setup_logger(name)
    
    # Методы для совместимости с logging.Logger (для использования в DI)
    def info(self, message: str):
        """Логирование информационного сообщения"""
        logger = self.get_logger("logger")
        logger.info(message)
    
    def debug(self, message: str):
        """Логирование отладочного сообщения"""
        logger = self.get_logger("logger")
        logger.debug(message)
    
    def warning(self, message: str):
        """Логирование предупреждения"""
        logger = self.get_logger("logger")
        logger.warning(message)
    
    def error(self, message: str):
        """Логирование ошибки"""
        logger = self.get_logger("logger")
        logger.error(message)
    
    def critical(self, message: str):
        """Логирование критической ошибки"""
        logger = self.get_logger("logger")
        logger.critical(message)