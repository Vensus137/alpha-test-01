from typing import Dict, Any, Optional


class FileCache:
    """
    Модуль для работы с кэшированием файлов.
    Интегрируется с таблицей cache для автоматической очистки.
    """
    
    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.settings_manager = kwargs['settings_manager']
        self.hash_manager = kwargs['hash_manager']
        self.database_service = kwargs['database_service']
    
    async def save_file_to_cache(self, file_path: str, cache_key: str, **metadata) -> bool:
        """
        Универсальное сохранение файла в кэш.
        Все дополнительные данные сохраняются в hash_metadata.
        Путь автоматически преобразуется в относительный для хранения в БД.
        """
        try:
            # Преобразуем в относительный путь для хранения в БД
            relative_path = self.settings_manager.get_relative_path(file_path)
            
            # Сохраняем в кэш через database_service
            with self.database_service.session_scope('cache') as (_, repos):
                cache_repo = repos['cache']
                success = cache_repo.add_or_update_cache(
                    hash_key=cache_key,
                    hash_file_path=relative_path,  # Относительный путь в БД
                    **metadata  # Метаданные в JSON поле hash_metadata
                )
                
                if not success:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения в кэш {cache_key}: {e}")
            return False
    
    async def get_cached_file_info(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Универсальное получение данных из кэша.
        Возвращает все метаданные + абсолютный путь к файлу.
        """
        try:
            # Ищем в кэше
            with self.database_service.session_scope('cache') as (_, repos):
                cache_repo = repos['cache']
                cached_data = cache_repo.get_cache(cache_key)
                
                if cached_data:
                    # Объединяем метаданные с путем к файлу
                    result = cached_data.get('hash_metadata', {}).copy()
                    
                    # Получаем относительный путь из БД (если есть)
                    relative_path = cached_data.get('hash_file_path')
                    if relative_path:
                        # Преобразуем в абсолютный путь для использования
                        absolute_path = self.settings_manager.resolve_file_path(relative_path)
                        result['file_path'] = absolute_path
                    else:
                        # Если нет пути - возвращаем None для file_path
                        result['file_path'] = None
                    
                    return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения из кэша {cache_key}: {e}")
            return None
    
    async def delete_from_cache(self, cache_key: str) -> bool:
        """
        Удаление записи из кэша.
        """
        try:
            with self.database_service.session_scope('cache') as (_, repos):
                cache_repo = repos['cache']
                cache_repo.delete_cache(cache_key)
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка удаления из кэша {cache_key}: {e}")
            return False
    