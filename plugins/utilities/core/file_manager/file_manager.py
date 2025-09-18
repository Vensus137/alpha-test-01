import os
import time
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Импорт новых модулей
from .core.file_downloader import FileDownloader
from .core.file_analyzer import FileAnalyzer
from .core.file_cache import FileCache

# Импорт для работы с аудио
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

# Импорт для работы с видео
try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    ffmpeg = None

# Импорт для определения MIME-типов
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None


class FileManager:
    """
    Универсальная утилита для работы с файлами с поддержкой аудио и видео.
    Поддерживает определение форматов, проверку размеров и длительности.
    """
    
    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.settings_manager = kwargs['settings_manager']
        
        # Получаем настройки
        settings = self.settings_manager.get_plugin_settings("file_manager")
        
        # Настройка папки по умолчанию для скачивания
        self.default_download_folder = settings.get('default_download_folder', 'download')
        
        # Проверяем доступность библиотек
        self._check_dependencies()
        
        # Инициализируем модули
        self.file_downloader = FileDownloader(**kwargs)
        self.file_analyzer = FileAnalyzer(**kwargs)
        self.file_cache = FileCache(**kwargs)
        
        # Создаем необходимые директории при инициализации
        self._ensure_directories()

    def _check_dependencies(self):
        """Проверяет доступность необходимых библиотек"""
        if not PYDUB_AVAILABLE:
            self.logger.warning("pydub недоступен - ограниченная поддержка аудио")
        
        if not FFMPEG_AVAILABLE:
            self.logger.warning("ffmpeg-python недоступен - ограниченная поддержка видео")
        
        if not MAGIC_AVAILABLE:
            self.logger.warning("python-magic недоступен - определение MIME-типов отключено")

    def validate_file(self, file_path: str, max_size_mb: float = None,
                     max_duration_seconds: int = None, check_exists: bool = True) -> Dict[str, Any]:
        """
        Универсальная валидация файла
        """
        return self.file_analyzer.validate_file(
            file_path, max_size_mb, max_duration_seconds, check_exists
        )

    def get_file_extension(self, file_path: str) -> Dict[str, Any]:
        """
        Определение расширения файла по содержимому
        """
        return self.file_analyzer.get_file_extension(file_path)

    def get_file_duration(self, file_path: str, extension_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Получение длительности файла (аудио/видео)
        """
        return self.file_analyzer.get_file_duration(file_path, extension_info)

    def get_content_type(self, file_path: str) -> Dict[str, Any]:
        """
        Определение Content-Type (MIME-типа) файла
        """
        return self.file_analyzer.get_content_type(file_path)

    def get_audio_encoding(self, file_path: str) -> Dict[str, Any]:
        """
        Определение audio_encoding для SaluteSpeech API
        """
        return self.file_analyzer.get_audio_encoding(file_path)

    async def download_file(self, file_id: str, target_folder: str = None, media_type: str = None, 
                           access_hash: int = None, file_reference: bytes = None, thumb_size: str = None, download_type: str = None) -> Dict[str, Any]:
        """
        Универсальный метод скачивания файла.
        Автоматически определяет нужный API, создает папку и скачивает файл.
        Возвращает абсолютный путь к готовому файлу.
        """
        return await self.file_downloader.download_file(file_id, target_folder, media_type, access_hash, file_reference, thumb_size, download_type)
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Получает информацию о файле (расширение, MIME-тип, метод определения).
        Использует анализатор файлов для определения по содержимому.
        """
        return self.file_analyzer.get_file_info(file_path)
        
    async def save_to_cache(self, file_path: str, cache_key: str, **metadata) -> bool:
        """
        Публичный метод для сохранения файла в кэш.
        """
        return await self.file_cache.save_file_to_cache(file_path, cache_key, **metadata)
    
    async def get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Публичный метод для получения данных из кэша.
        """
        return await self.file_cache.get_cached_file_info(cache_key)
    
    async def delete_from_cache(self, cache_key: str) -> bool:
        """
        Публичный метод для удаления записи из кэша.
        """
        return await self.file_cache.delete_from_cache(cache_key)

    def _ensure_directories(self):
        """Создает необходимые директории для работы с файлами"""
        try:
            # Создаем папку по умолчанию для скачивания
            default_path = self.settings_manager.resolve_file_path(self.default_download_folder)
            if not os.path.exists(default_path):
                os.makedirs(default_path, exist_ok=True)
                self.logger.info(f"Создана директория для скачивания: {default_path}")
                    
        except Exception as e:
            self.logger.error(f"Ошибка создания директорий: {e}")
