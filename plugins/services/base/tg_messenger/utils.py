import mimetypes
import os
from typing import Optional, Union

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove)


class MessengerUtils:
    """Утилиты для работы с сообщениями и вложениями"""
    
    def __init__(self, **kwargs):
        self.logger = kwargs.get('logger')
    
    def detect_attachment_type(self, file_path: str) -> str:
        """Определяет тип вложения по расширению файла."""
        # Специальная обработка GIF как анимации (должна быть ПЕРЕД проверкой image/)
        if file_path.lower().endswith('.gif'):
            return 'animation'
        
        mime, _ = mimetypes.guess_type(file_path)
        
        if not mime:
            return 'document'
        
        if mime.startswith('image/'):
            return 'photo'
        if mime.startswith('video/'):
            return 'video'
        if mime.startswith('audio/'):
            return 'audio'
        return 'document'

    def resolve_attachment_path(self, file_path: str, settings_manager) -> str:
        """Разрешает путь к файлу вложения."""
        if os.path.isabs(file_path):
            resolved_path = file_path
        else:
            # Используем глобальную настройку для базового пути
            resolved_path = settings_manager.resolve_file_path(file_path)
        return resolved_path

    def build_reply_markup(self, inline, reply, tg_button_mapper) -> Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove]]:
        """Строит разметку клавиатуры."""
        # Приоритет: inline > reply
        if inline:
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        self.build_inline_button(btn, tg_button_mapper) for btn in row
                    ]
                    for row in inline
                ]
            )
            return markup
        
        # Обработка reply клавиатуры
        if reply is not None:  # Изменено: проверяем на None, а не на truthiness
            if reply == []:  # Пустой список = убрать клавиатуру
                return ReplyKeyboardRemove()
            elif reply:  # Непустой список = показать клавиатуру
                markup = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text=btn) for btn in row]
                        for row in reply
                    ],
                    resize_keyboard=True
                )
                return markup
        
        return None

    def build_inline_button(self, btn, tg_button_mapper) -> InlineKeyboardButton:
        """
        Строит InlineKeyboardButton с универсальной логикой.
        
        Поддерживаемые форматы:
        - "Текст" -> callback_data с нормализованным текстом
        - {"Текст": "scenario_name"} -> callback_data с :scenario_name
        - {"Текст": "https://example.com"} -> URL кнопка (если значение похоже на ссылку)
        """
        if isinstance(btn, str):
            # Простая строка -> callback_data
            return InlineKeyboardButton(
                        text=btn,
                        callback_data=tg_button_mapper.normalize(btn)
                    )
        elif isinstance(btn, dict):
            text = list(btn.keys())[0]
            value = list(btn.values())[0]
            
            if isinstance(value, str):
                # Проверяем, является ли значение ссылкой
                if value.startswith(("http://", "https://", "tg://")):
                    return InlineKeyboardButton(
                        text=text,
                        url=value
                    )
                else:
                    # Иначе считаем это именем сценария
                    return InlineKeyboardButton(
                        text=text,
                        callback_data=f":{value}"
                    )
            else:
                # Неизвестный тип значения -> резервный вариант
                return InlineKeyboardButton(
                    text=text,
                    callback_data=tg_button_mapper.normalize(text)
                )
        else:
            # Неизвестный тип -> резервный вариант
            return InlineKeyboardButton(
                text=str(btn),
                callback_data=tg_button_mapper.normalize(str(btn))
            )
