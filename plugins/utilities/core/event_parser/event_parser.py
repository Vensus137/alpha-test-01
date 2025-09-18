from typing import Any, Dict, Optional
from aiogram import types
from .tg_bot_parser import TgBotParser
from .tg_mtproto_parser import TgMtprotoParser


class EventParser:
    """
    Фасад для универсального парсинга событий Bot API и MTProto.
    Делегирует работу специализированным парсерам.
    """

    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.datetime_formatter = kwargs['datetime_formatter']
        self.data_converter = kwargs['data_converter']
        self.tg_api_utils = kwargs['tg_api_utils']
        self.tg_entities_parser = kwargs.get('tg_entities_parser')
        
        # Инициализируем специализированные парсеры
        self.tg_bot_parser = TgBotParser(**kwargs)
        self.tg_mtproto_parser = TgMtprotoParser(**kwargs)

    def parse_bot_api_message(self, message: types.Message, media_group_processor=None) -> Optional[Dict[str, Any]]:
        """
        Парсинг сообщения Bot API (aiogram) в стандартный формат события.
        """
        return self.tg_bot_parser.parse_message(message)

    async def parse_mtproto_message(self, message, event) -> Optional[Dict[str, Any]]:
        """
        Парсинг сообщения MTProto (Telethon) в стандартный формат события.
        """
        return await self.tg_mtproto_parser.parse_message(message, event)

    def parse_bot_api_callback(self, callback: types.CallbackQuery) -> Optional[Dict[str, Any]]:
        """
        Парсинг callback Bot API в стандартный формат события.
        """
        return self.tg_bot_parser.parse_callback(callback)

    def parse_bot_api_new_member(self, message: types.Message) -> Optional[Dict[str, Any]]:
        """
        Парсинг события новых участников Bot API в стандартный формат события.
        """
        return self.tg_bot_parser.parse_new_member(message)
