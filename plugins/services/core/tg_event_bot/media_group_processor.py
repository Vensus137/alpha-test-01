import asyncio
from typing import Any, Callable, Dict, List

# Logger будет передан через конструктор


class MediaGroupProcessor:
    """
    Сервис для обработки Media Group сообщений от Telegram API.
    Группирует сообщения с одинаковым media_group_id и возвращает объединенное событие.
    Требует tg_media_group_merger для объединения данных.
    """

    def __init__(self, timeout: float = 1.0, logger=None, media_group_merger=None):
        self.timeout = timeout
        self.logger = logger
        self.media_group_merger = media_group_merger
        self.group_cache: Dict[str, List[Dict]] = {}
        self._background_tasks: List[asyncio.Task] = []
        
        # Проверяем обязательную зависимость
        if not self.media_group_merger:
            self.logger.error("MediaGroupProcessor требует tg_media_group_merger для работы")

    async def process_event(self, event: Dict[str, Any], callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Обрабатывает событие. Если это Media Group - группирует, иначе сразу вызывает callback.
        """
        if event.get('media_group_id'):
            await self._handle_media_group(event, callback)
        else:
            # Обычное событие - сразу вызываем callback асинхронно
            await callback(event)

    async def _handle_media_group(self, event: Dict[str, Any], callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Обрабатывает событие как часть Media Group.
        """
        group_id = event['media_group_id']

        if group_id not in self.group_cache:
            self.group_cache[group_id] = []
    
            # Запускаем таймер для обработки группы
            task = asyncio.create_task(self._process_group_after_timeout(group_id, callback))
            self._background_tasks.append(task)

        self.group_cache[group_id].append(event)

    async def _process_group_after_timeout(self, group_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Обрабатывает группу после истечения таймера.
        """
        await asyncio.sleep(self.timeout)

        if group_id in self.group_cache:
            events = self.group_cache[group_id]
            
            # Используем media_group_merger для объединения
            combined_event = self.media_group_merger.merge_group_events(events, group_field='media_group_id')

            # Вызываем callback с объединенным событием асинхронно
            if combined_event:
                await callback(combined_event)
            else:
                self.logger.warning(f"⚠️ Не удалось объединить события группы {group_id}")

            del self.group_cache[group_id]

    async def cleanup(self):
        """
        Очищает все незавершенные группы и отменяет задачи.
        """
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if self.group_cache:
            self.logger.warning(f"⚠️ Очищено {len(self.group_cache)} незавершенных групп")
            self.group_cache.clear()
