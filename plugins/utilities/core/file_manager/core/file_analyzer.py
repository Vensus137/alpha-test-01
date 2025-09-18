import os
from typing import Dict, Any, Optional, List
from pathlib import Path

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


class FileAnalyzer:
    """
    Модуль анализа файлов с поддержкой аудио и видео.
    Определяет форматы, проверяет размеры и длительность.
    """
    
    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.settings_manager = kwargs['settings_manager']
        
        # Получаем настройки
        settings = self.settings_manager.get_plugin_settings("file_manager")
        
        # Проверяем доступность библиотек
        self._check_dependencies()

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
        try:
            result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'file_info': {},
                'extension_info': {},
                'duration_info': {}
            }
            
            # Проверка существования
            if check_exists:
                if not os.path.exists(file_path):
                    result['valid'] = False
                    result['errors'].append(f"Файл не найден: {file_path}")
                    return result
                
                if not os.path.isfile(file_path):
                    result['valid'] = False
                    result['errors'].append(f"Путь не является файлом: {file_path}")
                    return result
            
            # Получаем информацию о файле
            file_info = self._get_file_info(file_path)
            result['file_info'] = file_info
            
            # Проверка размера (только если указан лимит)
            if max_size_mb is not None and file_info['size_mb'] > max_size_mb:
                result['valid'] = False
                result['errors'].append(
                    f"Файл слишком большой: {file_info['size_mb']:.1f} МБ > {max_size_mb} МБ"
                )
            
            # Определение расширения (только если нужно для длительности)
            extension_info = None
            if max_duration_seconds is not None:
                extension_info = self.get_file_extension(file_path)
                result['extension_info'] = extension_info
            
            # Проверка длительности (если указана)
            if max_duration_seconds is not None:
                duration_info = self.get_file_duration(file_path, extension_info)
                result['duration_info'] = duration_info
                
                if duration_info['success']:
                    duration = duration_info['duration_seconds']
                    if duration > max_duration_seconds:
                        result['valid'] = False
                        result['errors'].append(
                            f"Файл слишком длинный: {duration:.1f} сек > {max_duration_seconds} сек"
                        )
                else:
                    result['warnings'].append(f"Не удалось определить длительность: {duration_info['error']}")
            
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации файла {file_path}: {e}")
            return {
                'valid': False,
                'errors': [f"Ошибка валидации: {str(e)}"],
                'warnings': [],
                'file_info': {},
                'extension_info': {},
                'duration_info': {}
            }

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Универсальное определение информации о файле.
        Возвращает и расширение, и MIME-тип, и media_type, и метод определения.
        """
        try:
            
            result = {
                'success': False,
                'extension': None,
                'content_type': None,
                'mime_type': None,  # Дублирует content_type для совместимости
                'media_type': None,  # Telegram media type (photo, video, audio, etc.)
                'detection_method': None
            }
            
            # Определение через MIME-тип (если доступен)
            if MAGIC_AVAILABLE:
                # Проверяем, содержит ли путь кириллические символы
                if any(ord(char) > 127 for char in file_path):
                    self.logger.warning(f"Путь содержит кириллические символы, пропускаем MIME-тип: {file_path}")
                else:
                    try:
                        mime_type = magic.from_file(file_path, mime=True)
                        result['mime_type'] = mime_type
                        result['content_type'] = mime_type
                        
                        # Маппинг MIME-типов на расширения и media_type
                        extension_from_mime = self._get_extension_from_mime(mime_type)
                        media_type_from_mime = self._get_media_type_from_mime(mime_type)
                        if extension_from_mime:
                            result['extension'] = extension_from_mime
                            result['media_type'] = media_type_from_mime
                            result['detection_method'] = 'mime_type'
                            result['success'] = True
                            return result
                            
                    except Exception as e:
                        self.logger.warning(f"Ошибка определения MIME-типа: {e}")
            
            # Попытка определения через pydub (для аудио файлов)
            if PYDUB_AVAILABLE:
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(file_path)
                    # Определяем расширение по типу аудио
                    if hasattr(audio, 'format_info'):
                        detected_format = audio.format_info.get('format', '').lower()
                        if detected_format in ['ogg', 'opus']:
                            result['extension'] = 'ogg'
                            result['content_type'] = 'audio/ogg;codecs=opus'
                            result['mime_type'] = 'audio/ogg;codecs=opus'
                            result['media_type'] = 'voice'
                            result['detection_method'] = 'pydub'
                            result['success'] = True
                            return result
                        elif detected_format in ['mp3', 'mpeg']:
                            result['extension'] = 'mp3'
                            result['content_type'] = 'audio/mpeg'
                            result['mime_type'] = 'audio/mpeg'
                            result['media_type'] = 'audio'
                            result['detection_method'] = 'pydub'
                            result['success'] = True
                            return result
                        elif detected_format in ['wav', 'wave']:
                            result['extension'] = 'wav'
                            result['content_type'] = 'audio/wav'
                            result['mime_type'] = 'audio/wav'
                            result['media_type'] = 'audio'
                            result['detection_method'] = 'pydub'
                            result['success'] = True
                            return result
                except Exception as e:
                    pass
            
            # Fallback к расширению файла
            file_ext = Path(file_path).suffix.lower().lstrip('.')
            
            if file_ext:  # Только если есть расширение!
                result['extension'] = file_ext
                result['content_type'] = self._get_content_type_from_extension(file_ext)
                result['mime_type'] = result['content_type']
                result['media_type'] = self._get_media_type_from_extension(file_ext)
                result['detection_method'] = 'extension'
                result['success'] = True
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка определения информации о файле {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'extension': None,
                'content_type': None,
                'mime_type': None,
                'media_type': None,
                'detection_method': None
            }

    def get_file_extension(self, file_path: str) -> Dict[str, Any]:
        """
        Определение расширения файла по содержимому
        
        TODO: УДАЛИТЬ - использовать get_file_info() вместо этого метода
        """
        info = self.get_file_info(file_path)
        return {
            'success': info['success'],
            'extension': info['extension'],
            'mime_type': info['mime_type'],
            'detection_method': info['detection_method']
        }

    def get_file_duration(self, file_path: str, extension_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Получение длительности файла (аудио/видео)
        """
        try:
            # Если знаем расширение, используем оптимальный метод
            if extension_info and extension_info.get('success'):
                detected_extension = extension_info['extension'].lower()
                
                # Аудио форматы
                if detected_extension in ['mp3', 'ogg', 'opus', 'flac', 'wav', 'm4a', 'aac']:
                    if PYDUB_AVAILABLE:
                        try:
                            audio = AudioSegment.from_file(file_path)
                            duration_ms = len(audio)
                            duration_seconds = duration_ms / 1000.0
                            
                            return {
                                'success': True,
                                'file_type': 'audio',
                                'duration_seconds': duration_seconds,
                                'sample_rate': audio.frame_rate,
                                'channels': audio.channels,
                            }
                        except Exception as e:
                            pass
                
                # Видео форматы
                elif detected_extension in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
                    if FFMPEG_AVAILABLE:
                        try:
                            probe = ffmpeg.probe(file_path)
                            duration = float(probe['format']['duration'])
                            
                            return {
                                'success': True,
                                'file_type': 'video',
                                'duration_seconds': duration,
                                'format': probe['format']['format_name'],
                                'bit_rate': probe['format'].get('bit_rate'),
                                'size': probe['format'].get('size')
                            }
                        except Exception as e:
                            pass
            
            # Fallback: пробуем оба метода (если расширение не определено или не распознано)
            # Сначала пробуем как аудио
            if PYDUB_AVAILABLE:
                try:
                    audio = AudioSegment.from_file(file_path)
                    duration_ms = len(audio)
                    duration_seconds = duration_ms / 1000.0
                    
                    return {
                        'success': True,
                        'file_type': 'audio',
                        'duration_seconds': duration_seconds,
                        'sample_rate': audio.frame_rate,
                        'channels': audio.channels
                    }
                except Exception as e:
                    pass
            
            # Пробуем как видео
            if FFMPEG_AVAILABLE:
                try:
                    probe = ffmpeg.probe(file_path)
                    duration = float(probe['format']['duration'])
                    
                    return {
                        'success': True,
                        'file_type': 'video',
                        'duration_seconds': duration,
                        'format': probe['format']['format_name'],
                        'bit_rate': probe['format'].get('bit_rate'),
                        'size': probe['format'].get('size')
                    }
                except Exception as e:
                    pass
            
            # Не удалось определить длительность
            return {
                'success': False,
                'error': 'Файл не поддерживается для определения длительности',
                'file_type': 'unknown',
                'duration_seconds': 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения длительности файла {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_type': 'unknown',
                'duration_seconds': 0.0
            }

    def get_content_type(self, file_path: str) -> Dict[str, Any]:
        """
        Определение Content-Type (MIME-типа) файла
        
        TODO: УДАЛИТЬ - использовать get_file_info() вместо этого метода
        """
        info = self.get_file_info(file_path)
        return {
            'success': info['success'],
            'content_type': info['content_type'],
            'detection_method': info['detection_method']
        }

    def get_audio_encoding(self, file_path: str) -> Dict[str, Any]:
        """
        Определение audio_encoding для SaluteSpeech API
        """
        try:
            result = {
                'success': True,
                'audio_encoding': None,
                'detection_method': None
            }
            
            # Определяем расширение файла
            extension_result = self.get_file_extension(file_path)
            
            if extension_result['success']:
                extension_type = extension_result['extension'].lower()
                
                # Маппинг расширений на audio_encoding для SaluteSpeech
                encoding_map = {
                    'mp3': 'MP3',
                    'ogg': 'OPUS',
                    'opus': 'OPUS',
                    'flac': 'FLAC',
                    'wav': 'PCM_S16LE',
                    'pcm': 'PCM_S16LE',
                    'alaw': 'ALAW',
                    'mulaw': 'MULAW'
                }
                
                audio_encoding = encoding_map.get(extension_type, 'MP3')
                result['audio_encoding'] = audio_encoding
                result['detection_method'] = 'extension_detection'
                return result
            
            # Fallback к определению по расширению
            file_ext = Path(file_path).suffix.lower()
            
            encoding_map = {
                '.mp3': 'MP3',
                '.mpeg': 'MP3',
                '.ogg': 'OPUS',
                '.opus': 'OPUS',
                '.flac': 'FLAC',
                '.wav': 'PCM_S16LE',
                '.pcm': 'PCM_S16LE',
                '.alaw': 'ALAW',
                '.mulaw': 'MULAW'
            }
            
            audio_encoding = encoding_map.get(file_ext, 'MP3')
            result['audio_encoding'] = audio_encoding
            result['detection_method'] = 'extension'
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка определения audio_encoding файла {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'audio_encoding': 'MP3',  # Fallback
                'detection_method': None
            }

    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Получение базовой информации о файле"""
        try:
            stat = os.stat(file_path)
            size_bytes = stat.st_size
            size_mb = size_bytes / (1024 * 1024)
            
            return {
                'size_bytes': size_bytes,
                'size_mb': size_mb
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о файле {file_path}: {e}")
            return {
                'size_bytes': 0,
                'size_mb': 0.0
            }

    def _get_extension_from_mime(self, mime_type: str) -> Optional[str]:
        """Получение расширения из MIME-типа"""
        mime_to_extension = {
            # Аудио форматы
            'audio/mpeg': 'mp3',
            'audio/mp3': 'mp3',
            'audio/ogg': 'ogg',
            'audio/opus': 'ogg',  # Telegram voice обычно OGG с Opus кодеком
            'audio/flac': 'flac',
            'audio/wav': 'wav',
            'audio/x-wav': 'wav',
            'audio/aac': 'aac',
            'audio/mp4': 'm4a',
            'audio/x-m4a': 'm4a',
            # Telegram voice специфичные типы
            'application/octet-stream': 'ogg',  # Fallback для неизвестных аудио
            
            # Видео форматы (подготовка к будущему)
            'video/mp4': 'mp4',
            'video/avi': 'avi',
            'video/quicktime': 'mov',
            'video/x-matroska': 'mkv',
            'video/webm': 'webm',
            
            # Другие форматы
            'application/pdf': 'pdf',
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif'
        }
        
        return mime_to_extension.get(mime_type)

    def _get_content_type_from_extension(self, file_ext: str) -> Optional[str]:
        """Получение Content-Type из расширения файла"""
        # Автоматически приводим расширение к нужному формату (с точкой)
        if file_ext and not file_ext.startswith('.'):
            normalized_ext = f'.{file_ext.lower()}'
        else:
            normalized_ext = file_ext.lower() if file_ext else ''
        
        content_types = {
            # Аудио форматы
            '.mp3': 'audio/mpeg',
            '.ogg': 'audio/ogg;codecs=opus',
            '.opus': 'audio/ogg;codecs=opus',
            '.flac': 'audio/flac',
            '.wav': 'audio/x-pcm;bit=16;rate=16000',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            
            # Видео форматы
            '.mp4': 'video/mp4',
            '.avi': 'video/avi',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            
            # Другие форматы
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif'
        }
        
        return content_types.get(normalized_ext)
    
    def _get_media_type_from_mime(self, mime_type: str) -> str:
        """
        Определяет Telegram media_type по MIME-типу
        """
        mime_to_media_map = {
            'image/jpeg': 'photo',
            'image/png': 'photo', 
            'image/gif': 'animation',
            'image/webp': 'sticker',
            'video/mp4': 'video',
            'video/avi': 'video',
            'video/mov': 'video',
            'video/webm': 'video',
            'audio/mpeg': 'audio',
            'audio/ogg': 'voice',
            'audio/wav': 'audio',
            'audio/mp3': 'audio',
            'audio/mp4': 'audio',
            'application/pdf': 'document',
            'text/plain': 'document',
            'application/zip': 'document',
            'application/x-rar': 'document'
        }
        return mime_to_media_map.get(mime_type, 'document')
    
    def _get_media_type_from_extension(self, extension: str) -> str:
        """
        Определяет Telegram media_type по расширению файла
        """
        ext_to_media_map = {
            'jpg': 'photo',
            'jpeg': 'photo',
            'png': 'photo',
            'gif': 'animation',
            'webp': 'sticker',
            'mp4': 'video',
            'avi': 'video',
            'mov': 'video',
            'webm': 'video',
            'mp3': 'audio',
            'ogg': 'voice',
            'wav': 'audio',
            'pdf': 'document',
            'txt': 'document',
            'zip': 'document',
            'rar': 'document'
        }
        return ext_to_media_map.get(extension, 'document')
    
    def get_fallback_extension(self, media_type: str) -> str:
        """
        Fallback расширение по типу медиа, если не удалось определить по содержимому.
        """
        extension_map = {
            'photo': '.jpg',
            'video': '.mp4',
            'audio': '.mp3',
            'voice': '.mp3',
            'document': '.bin',
            'sticker': '.webp',
            'animated_sticker': '.tgs',
            'animation': '.gif',
            'video_note': '.mp4'
        }
        
        return extension_map.get(media_type, '.bin')
