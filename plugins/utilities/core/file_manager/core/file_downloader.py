import os
from typing import Dict, Any, Optional
from aiogram import Bot


class FileDownloader:
    """
    Универсальный загрузчик файлов с автоматическим определением API.
    Поддерживает как Bot API, так и MTProto API.
    """
    
    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.settings_manager = kwargs['settings_manager']
        self.hash_manager = kwargs['hash_manager']
        self.database_service = kwargs['database_service']
        self.tg_bot_initializer = kwargs['tg_bot_initializer']
        self.tg_mtproto = kwargs.get('tg_mtproto')
        
        # Получаем настройки папки по умолчанию
        settings = self.settings_manager.get_plugin_settings("file_manager")
        self.default_download_folder = settings.get('default_download_folder', 'download')
        
        # Инициализируем кэш
        from .file_cache import FileCache
        self.file_cache = FileCache(**kwargs)
        
        # Инициализируем анализатор файлов
        from .file_analyzer import FileAnalyzer
        self.file_analyzer = FileAnalyzer(**kwargs)
    
    def _determine_api_type(self, file_id: str) -> str:
        """
        Определяет тип API по формату file_id.
        
        Bot API: строки длиной > 20 символов (например: "BAADBAADrwADBREAAYag8VZHCwABWgI")
        MTProto: числа или строки из цифр (например: 5321055182701853768)
        """
        try:
            # Проверяем, является ли file_id числом
            if str(file_id).isdigit():
                return 'mtproto'
            
            # Проверяем длину строки (Bot API обычно длинные строки)
            if isinstance(file_id, str) and len(file_id) > 20:
                return 'bot_api'
            
            # Fallback - пробуем Bot API
            return 'bot_api'
            
        except Exception as e:
            self.logger.warning(f"Ошибка определения типа API для file_id {file_id}: {e}")
            return 'bot_api'  # Fallback к Bot API
    
    async def download_file(self, file_id: str, target_folder: str = None, media_type: str = None, 
                           access_hash: int = None, file_reference: bytes = None, thumb_size: str = None, download_type: str = None) -> Dict[str, Any]:
        """
        Универсальный метод скачивания файла.
        Автоматически определяет нужный API, создает папку и скачивает файл.
        Возвращает абсолютный путь к готовому файлу.
        """
        try:
            # Определяем папку для скачивания
            if target_folder is None:
                target_folder = self.default_download_folder
                # Дефолтная директория уже создана при инициализации сервиса
                resolved_target_folder = self.settings_manager.resolve_file_path(target_folder)
            else:
                # Разрешаем путь относительно глобальной настройки file_base_path
                resolved_target_folder = self.settings_manager.resolve_file_path(target_folder)
                
                # Создаем директорию только если указан кастомный target_folder
                if not os.path.exists(resolved_target_folder):
                    os.makedirs(resolved_target_folder, exist_ok=True)
                    self.logger.info(f"Создана директория для скачивания: {resolved_target_folder}")
            
            # Определяем тип API
            api_type = self._determine_api_type(file_id)
            
            # Скачиваем файл через соответствующий API
            if api_type == 'bot_api':
                result = await self._download_via_bot_api(file_id, resolved_target_folder, media_type)
            else:  # mtproto
                # Проверяем наличие обязательных параметров для MTProto
                if access_hash is None or file_reference is None:
                    self.logger.warning(f"  - ⚠️ MTProto скачивание НЕ удалось: нет access_hash или file_reference")
                    return {
                        'success': False,
                        'error': f'Для MTProto скачивания необходимы access_hash и file_reference',
                        'file_id': file_id,
                        'media_type': media_type,
                        'api_type': 'mtproto'
                    }
                
                result = await self._download_via_mtproto(file_id, resolved_target_folder, media_type, access_hash, file_reference, thumb_size, download_type)
            
            # Если скачивание успешно, сохраняем в кэш
            if result.get('success'):
                # Генерируем ключ кэша
                # Создаем уникальный ключ кэша: file_id + текущее время
                # Это гарантирует что каждый файл будет сохранен как новая запись
                import time
                timestamp = int(time.time() * 1000000)  # микросекунды для уникальности
                cache_key = self.hash_manager.generate_hash(f"file_cache_{file_id}_{timestamp}")
                
                metadata = {
                    'file_id': file_id,
                    'media_type': result.get('media_type') or media_type,
                    'api_type': api_type,
                    'file_size': result.get('file_size', 0)
                }
                
                cache_result = await self.file_cache.save_file_to_cache(
                    file_path=result.get('file_path'),
                    cache_key=cache_key,
                    **metadata
                )
            else:
                self.logger.warning(f"  - ⚠️ Скачивание НЕ удалось для file_id: {file_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка скачивания файла {file_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_id': file_id,
                'media_type': media_type,
                'api_type': 'unknown'
            }
    
    async def _download_via_bot_api(self, file_id: str, target_folder: str, media_type: str = None) -> Dict[str, Any]:
        """
        Скачивает файл через Bot API с определением реального расширения.
        target_folder уже обработан в основном методе и не может быть None.
        """
        try:
            # Получаем бота
            bot = self.tg_bot_initializer.get_bot()
            if not bot:
                return {
                    'success': False,
                    'error': 'Бот не инициализирован',
                    'file_id': file_id,
                    'api_type': 'bot_api'
                }
            
            # Генерируем временное имя файла через hash_manager
            temp_file_name = self.hash_manager.generate_filename(
                prefix="download",
                extension="tmp",
                code_length=8
            )
            temp_file_path = os.path.join(target_folder, temp_file_name)
            
            # Сначала получаем file_path через get_file
            try:
                file_info = await bot.get_file(file_id)
                if not file_info or not file_info.file_path:
                    return {
                        'success': False,
                        'error': f'Файл {file_id} недоступен для скачивания (нет file_path)',
                        'file_id': file_id,
                        'api_type': 'bot_api'
                    }
                file_path = file_info.file_path
            except Exception as get_file_error:
                return {
                    'success': False,
                    'error': f'Ошибка получения file_path для {file_id}: {get_file_error}',
                    'file_id': file_id,
                    'api_type': 'bot_api'
                }
            
            # Теперь скачиваем файл по file_path
            try:
                await bot.download_file(file_path, temp_file_path)
                
                # Проверяем что файл действительно скачался
                if not os.path.exists(temp_file_path):
                    return {
                        'success': False,
                        'error': f'Файл {file_id} не скачался (файл не найден)',
                        'file_id': file_id,
                        'api_type': 'bot_api'
                    }
                
                # Проверяем размер файла
                file_size = os.path.getsize(temp_file_path)
                if file_size == 0:
                    return {
                        'success': False,
                        'error': f'Файл {file_id} скачался пустым',
                        'file_id': file_id,
                        'api_type': 'bot_api'
                    }
            except Exception as download_error:
                return {
                    'success': False,
                    'error': f'Ошибка скачивания файла {file_id}: {download_error}',
                    'file_id': file_id,
                    'api_type': 'bot_api'
                }
            
            # Получаем полную информацию о файле через анализатор
            file_info = self.file_analyzer.get_file_info(temp_file_path)
            
            # Определяем расширение и media_type
            if file_info.get('success') and file_info.get('extension'):
                real_extension = f".{file_info['extension']}"
                detected_media_type = file_info.get('media_type')
            else:
                # Fallback на переданный media_type или document
                real_extension = self.file_analyzer.get_fallback_extension(media_type)
                detected_media_type = media_type or 'document'
            
            # Переименовываем файл с правильным расширением
            # Извлекаем префикс из временного имени (download-xxxx-xxxx.tmp -> download-xxxx-xxxx)
            temp_prefix = temp_file_name.replace('.tmp', '')
            final_file_name = f"{temp_prefix}{real_extension}"
            final_file_path = os.path.join(target_folder, final_file_name)
            os.rename(temp_file_path, final_file_path)
            
            # Получаем информацию о файле
            file_size = os.path.getsize(final_file_path)
            
            return {
                'success': True,
                'file_path': final_file_path,
                'file_name': final_file_name,
                'file_size': file_size,
                'media_type': detected_media_type or media_type,
                'api_type': 'bot_api',
                'file_id': file_id
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка Bot API скачивания для файла {file_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_id': file_id,
                'api_type': 'bot_api'
            }
    
    async def _download_via_mtproto(self, file_id: str, target_folder: str, media_type: str = None, 
                                   access_hash: int = None, file_reference: bytes = None, thumb_size: str = None, download_type: str = None) -> Dict[str, Any]:
        """
        Скачивает файл через MTProto API с определением реального расширения.
        target_folder уже обработан в основном методе и не может быть None.
        access_hash и file_reference уже проверены в основном методе.
        """
        try:
            # Проверяем доступность MTProto клиента
            if not self.tg_mtproto:
                return {
                    'success': False,
                    'error': 'MTProto клиент недоступен',
                    'file_id': file_id,
                    'api_type': 'mtproto'
                }
            
            # Генерируем временное имя файла через hash_manager
            temp_file_name = self.hash_manager.generate_filename(
                prefix="download",
                extension="tmp",
                code_length=8
            )
            temp_file_path = os.path.join(target_folder, temp_file_name)
            
            # Получаем клиент Telethon через MTProto утилиту
            client = self.tg_mtproto.get_client()
            if not client:
                return {
                    'success': False,
                    'error': 'MTProto клиент не подключен',
                    'file_id': file_id,
                    'api_type': 'mtproto'
                }
            
            # Скачиваем файл во временный файл через safe_api_call
            try:
                # Создаем правильный InputFileLocation объект для Telethon
                from telethon.tl.types import InputPhotoFileLocation, InputDocumentFileLocation
                
                # access_hash и file_reference уже проверены в основном методе
                
                # Используем download_type если есть, иначе media_type, иначе document как fallback
                file_type = download_type or media_type or 'document'
                
                
                # Создаем правильный InputFileLocation объект
                if file_type == 'photo':
                    # Для фотографий нужен thumb_size
                    photo_thumb_size = thumb_size or 'x'  # По умолчанию большой размер
                    
                    input_location = InputPhotoFileLocation(
                        id=file_id,
                        access_hash=access_hash,
                        file_reference=file_reference,
                        thumb_size=photo_thumb_size
                    )
                else:
                    # Для документов и анимаций нужен thumb_size
                    # Используем пустую строку как fallback для документов без превью
                    doc_thumb_size = thumb_size or ''
                    
                    input_location = InputDocumentFileLocation(
                        id=file_id,
                        access_hash=access_hash,
                        file_reference=file_reference,
                        thumb_size=doc_thumb_size
                    )
                
                await self.tg_mtproto.safe_api_call(
                    client.download_file,
                    input_location,
                    temp_file_path
                )
                
                # Получаем полную информацию о файле через анализатор
                file_info = self.file_analyzer.get_file_info(temp_file_path)
                
                # Определяем расширение и media_type
                if file_info.get('success') and file_info.get('extension') and file_info['extension'] != 'tmp':
                    # Анализатор определил реальное расширение (не .tmp)
                    real_extension = f".{file_info['extension']}"
                    detected_media_type = file_info.get('media_type')
                else:
                    # Fallback: используем переданный media_type для определения расширения
                    real_extension = self.file_analyzer.get_fallback_extension(media_type)
                    detected_media_type = media_type or 'document'
                
                # Переименовываем файл с правильным расширением
                # Извлекаем префикс из временного имени (download-xxxx-xxxx.tmp -> download-xxxx-xxxx)
                temp_prefix = temp_file_name.replace('.tmp', '')
                final_file_name = f"{temp_prefix}{real_extension}"
                final_file_path = os.path.join(target_folder, final_file_name)
                
                os.rename(temp_file_path, final_file_path)
                
                # Получаем информацию о файле
                file_size = os.path.getsize(final_file_path)
                
                return {
                    'success': True,
                    'file_path': final_file_path,
                    'file_name': final_file_name,
                    'file_size': file_size,
                    'media_type': detected_media_type or media_type,
                    'api_type': 'mtproto',
                    'file_id': file_id
                }
            
            except Exception as download_error:
                return {
                    'success': False,
                    'error': f'Ошибка скачивания файла {file_id}: {download_error}',
                    'file_id': file_id,
                    'api_type': 'mtproto'
                }
            
        except Exception as e:
            self.logger.error(f"Ошибка MTProto скачивания для файла {file_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_id': file_id,
                'api_type': 'mtproto'
            }
    