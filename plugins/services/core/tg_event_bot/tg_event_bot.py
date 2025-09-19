import asyncio
from typing import Any, Dict

from aiogram import Dispatcher, types

from .media_group_processor import MediaGroupProcessor


class TgEventBot:
    """
    Обработчик событий Telegram (сообщения, callback, poll, inline_query).
    Создаёт события и передаёт их в trigger_manager.
    """

    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.trigger_manager = kwargs['trigger_manager']
        self.tg_bot_initializer = kwargs['tg_bot_initializer']
        self.settings_manager = kwargs['settings_manager']
        self.datetime_formatter = kwargs['datetime_formatter']
        self.tg_media_group_merger = kwargs['tg_media_group_merger']
        self.event_parser = kwargs['event_parser']
        
        # Получаем время запуска из settings_manager
        self.startup_time = self.settings_manager.get_startup_time()
        
        # Получаем настройки через settings_manager
        settings = self.settings_manager.get_plugin_settings('tg_event_bot')
        self.media_group_timeout = settings.get('media_group_timeout', 1.0)
        self.media_group_enabled = settings.get('media_group_enabled', True)
        self.max_event_age_seconds = settings.get('max_event_age_seconds', 60)
        
        # Создаем MediaGroupProcessor с tg_media_group_merger
        self.media_group_processor = MediaGroupProcessor(
            timeout=self.media_group_timeout, 
            logger=self.logger,
            media_group_merger=self.tg_media_group_merger
        )
        self._is_running = False

    async def run(self):
        """
        Запускает polling событий Telegram через aiogram Dispatcher.
        """
        self._is_running = True
        self.logger.info("▶️ старт polling Telegram событий (aiogram Dispatcher)")
        
        try:
            # Проверяем доступность бота перед запуском polling
            bot = self.tg_bot_initializer.get_bot()
            if not bot:
                self.logger.error("❌ Бот недоступен, polling не запускается")
                return
            
            dp = Dispatcher()
            router = self._create_router()
            dp.include_router(router)
            await dp.start_polling(bot)
        except Exception as e:
            self.logger.error(f"Ошибка в polling Telegram событий: {e}")
            # Не завершаем приложение, просто логируем ошибку
            await asyncio.sleep(5)  # Пауза перед повторной попыткой
            if self._is_running:
                # Рекурсивно перезапускаем polling
                await self.run()

    def _create_router(self):
        """
        Создаёт и настраивает router с обработчиками событий Telegram.
        """
        from aiogram import Router
        router = Router()

        # Обработчик обычных сообщений
        @router.message()
        async def handle_message(message: types.Message):
            # --- Новый блок: обработка вступления новых участников ---
            if message.new_chat_members:
                event = self.event_parser.parse_bot_api_new_member(message)
                if event:
                    await self._dispatch_event(event)
                return
            # --- Конец нового блока ---
            event = await self._handle_message(message)
            if event:
                await self._dispatch_event(event)

        # Обработчик callback кнопок
        @router.callback_query()
        async def handle_callback(callback: types.CallbackQuery):
            event = self.event_parser.parse_bot_api_callback(callback)
            if event:
                await self._dispatch_event(event)

        # Отредактированные сообщения, опросы, inline запросы - не обрабатываем
        # aiogram автоматически их проигнорирует без регистрации обработчиков

        return router

    async def _handle_message(self, message: types.Message):
        """
        Обрабатывает входящее сообщение. Возвращает event или None.
        """
        # Фильтрация нежелательных событий
        if self._should_ignore_message(message):
            return None

        # Создание события через event_parser
        event = self.event_parser.parse_bot_api_message(message, self.media_group_processor if self.media_group_enabled else None)

        # Обработка через Media Group Processor с callback
        if self.media_group_enabled and event:
            await self.media_group_processor.process_event(event, self._media_group_callback)
            return None  # Финальный event будет обработан в _media_group_callback
        else:
            return event

    def _should_ignore_message(self, message: types.Message) -> bool:
        """
        Проверяет, нужно ли игнорировать сообщение.
        Игнорируем каналы и специальные типы сообщений.
        """
        # Каналы (боты не работают в каналах)
        if message.chat and message.chat.type == 'channel':
            return True
        
        # Специальные типы сообщений (исключаем из копирования)
        if message.poll or message.location or message.contact or message.venue or message.game or message.invoice or message.dice:
            return True
        
        return False

    def _should_ignore_event(self, event: Dict[str, Any]) -> bool:
        """
        Пост-обработка события: проверяет, нужно ли игнорировать событие.
        Фильтруем системные сообщения без полезного содержимого.
        """
        # Проверяем только текстовые сообщения
        if event.get('message_type') != 'text':
            return False
        
        # Получаем текст сообщения
        text = event.get('text', '')
        
        # Если текст пустой или содержит только пробелы
        if not text or not text.strip():
            # Проверяем, есть ли медиа-вложения
            has_media = any([
                event.get('photo'),
                event.get('video'),
                event.get('audio'),
                event.get('document'),
                event.get('sticker'),
                event.get('voice'),
                event.get('video_note'),
                event.get('animation'),
                event.get('media_group_id')  # Медиа-группы
            ])
            
            # Если нет медиа-вложений - это системное сообщение
            if not has_media:
                return True
        
        return False

    async def _media_group_callback(self, event: dict):
        await self._dispatch_event(event)

    async def _dispatch_event(self, event: Dict[str, Any]):
        """
        Централизованная обработка и отправка event в trigger_manager.
        Здесь можно добавить pre-processing, валидацию, логику модификации event.
        """
        # event уже является безопасным словарем (из event_parser)
        
        # Пост-обработка: фильтруем системные сообщения без полезного содержимого
        if self._should_ignore_event(event):
            return
        
        event_date = event.get('event_date')
        try:
            startup_dt = self.startup_time
            event_dt = self.datetime_formatter.parse(event_date) if isinstance(event_date, str) else event_date
            delta = (startup_dt - event_dt).total_seconds()
            if self.max_event_age_seconds > delta:
                await self.trigger_manager.handle_event(event)
            else:
                return
        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка при фильтрации event по времени: {e}")
            await self.trigger_manager.handle_event(event)
