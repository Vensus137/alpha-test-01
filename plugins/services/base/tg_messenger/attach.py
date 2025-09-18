import os
from typing import Dict, List

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (FSInputFile, InputMediaDocument,
                           InputMediaPhoto, InputMediaVideo)

from .utils import MessengerUtils

# Максимальное количество файлов в media group
MAX_MEDIA_GROUP = 10


class AttachmentHandler:
    """Обработчик вложений для tg_messenger сервиса"""
    
    def __init__(self, **kwargs):
        self.logger = kwargs.get('logger')
        self.settings_manager = kwargs.get('settings_manager')
        self.utils = MessengerUtils(**kwargs)
    
    def _parse_attachments(self, action: dict) -> List[dict]:
        """
        Преобразует вложения в список словарей с ключами: file, type (document, photo, video, audio)
        Поддерживает старый и новый формат.
        Если явно указан type — использовать его приоритетно, не определять по mime.
        """
        raw = action.get('attachment')
        if not raw:
            return []
        
        result = []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    file = item.get('attachment') or item.get('file')
                    atype = item.get('type')
                    if not file:
                        continue  # пропускаем если нет файла
                    if atype:
                        result.append({'file': file, 'type': atype})
                    else:
                        detected_type = self.utils.detect_attachment_type(file)
                        result.append({'file': file, 'type': detected_type})
                elif isinstance(item, str):
                    detected_type = self.utils.detect_attachment_type(item)
                    result.append({'file': item, 'type': detected_type})
        elif isinstance(raw, dict):
            file = raw.get('attachment') or raw.get('file')
            if not file:
                return result
            atype = raw.get('type')
            if atype:
                result.append({'file': file, 'type': atype})
            else:
                detected_type = self.utils.detect_attachment_type(file)
                result.append({'file': file, 'type': detected_type})
        elif isinstance(raw, str):
            detected_type = self.utils.detect_attachment_type(raw)
            result.append({'file': raw, 'type': detected_type})
        
        return result

    def _group_attachments(self, attachments: List[dict]) -> Dict[str, List[dict]]:
        """
        Группирует вложения: media (фото+видео), animation (только анимации), document (только документы).
        Анимации и аудио отправляются отдельно, так как не поддерживаются в media groups.
        """
        groups = {'media': [], 'animation': [], 'document': [], 'audio': []}
        for att in attachments:
            if att['type'] == 'photo' or att['type'] == 'video':
                groups['media'].append(att)
            elif att['type'] == 'animation':
                groups['animation'].append(att)
            elif att['type'] == 'document':
                groups['document'].append(att)
            elif att['type'] == 'audio':
                groups['audio'].append(att)
        return groups

    async def send_attachments(self, bot, chat_id, text, attachments, reply_markup, parse_mode, 
                              message_id=None, message_reply=False):
        """Отправляет вложения с правильной группировкой и обработкой ошибок."""
        # Группируем вложения: media (фото+видео), animation (только анимации), document (только документы)
        groups = self._group_attachments(attachments)
        text_sent = False
        any_sent = False
        first_group = True
        last_message_id = None
        
        for group_type in ("media", "animation", "document", "audio"):
            files = groups.get(group_type, [])
            if not files:
                continue
            # --- Одиночное вложение ---
            if len(files) == 1:
                att = files[0]
                file_path = self.utils.resolve_attachment_path(att['file'], self.settings_manager)
                if not os.path.isfile(file_path):
                    self.logger.warning(f"Вложение не найдено: {file_path}")
                    continue
                try:
                    file = FSInputFile(file_path)
                    caption = text if not text_sent else None
                    
                    # Подготавливаем параметры для отправки
                    send_kwargs = dict(
                        chat_id=chat_id,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
                    
                    # Добавляем reply_to_message_id если нужно
                    if message_reply and message_id:
                        send_kwargs['reply_to_message_id'] = message_id
                    
                    msg = None
                    try:
                        if att['type'] == 'photo':
                            send_kwargs.update(photo=file, caption=caption)
                            msg = await bot.send_photo(**send_kwargs)
                        elif att['type'] == 'animation':
                            send_kwargs.update(animation=file, caption=caption)
                            msg = await bot.send_animation(**send_kwargs)
                        elif att['type'] == 'video':
                            send_kwargs.update(video=file, caption=caption)
                            msg = await bot.send_video(**send_kwargs)
                        elif att['type'] == 'document':
                            send_kwargs.update(document=file, caption=caption)
                            msg = await bot.send_document(**send_kwargs)
                        elif att['type'] == 'audio':
                            send_kwargs.update(audio=file, caption=caption)
                            msg = await bot.send_audio(**send_kwargs)
                    except TelegramBadRequest as e:
                        if 'message to reply not found' in str(e).lower() and message_reply and message_id:
                            self.logger.warning(f"ответ на сообщение не удался (сообщение для ответа не найдено) для chat_id={chat_id}, message_id={message_id}: {e}. Отправляю вложение без reply_to_message_id.")
                            send_kwargs.pop('reply_to_message_id', None)
                            if att['type'] == 'photo':
                                send_kwargs.update(photo=file, caption=caption)
                                msg = await bot.send_photo(**send_kwargs)
                            elif att['type'] == 'animation':
                                send_kwargs.update(animation=file, caption=caption)
                                msg = await bot.send_animation(**send_kwargs)
                            elif att['type'] == 'video':
                                send_kwargs.update(video=file, caption=caption)
                                msg = await bot.send_video(**send_kwargs)
                            elif att['type'] == 'document':
                                send_kwargs.update(document=file, caption=caption)
                                msg = await bot.send_document(**send_kwargs)
                            elif att['type'] == 'audio':
                                send_kwargs.update(audio=file, caption=caption)
                                msg = await bot.send_audio(**send_kwargs)
                        else:
                            raise
                    
                    if msg:
                        last_message_id = msg.message_id
                    text_sent = True
                    any_sent = True
                    first_group = False
                except Exception as e:
                    self.logger.error(f"Ошибка при отправке вложения {file_path}: {e}")
                continue  # не обрабатываем как группу
            
            # --- Анимации и аудио всегда отправляются по отдельности ---
            if group_type in ('animation', 'audio'):
                for att in files:
                    file_path = self.utils.resolve_attachment_path(att['file'], self.settings_manager)
                    if not os.path.isfile(file_path):
                        self.logger.warning(f"Вложение не найдено: {file_path}")
                        continue
                    try:
                        file = FSInputFile(file_path)
                        caption = text if not text_sent else None
                        
                        # Подготавливаем параметры для отправки
                        send_kwargs = dict(
                            chat_id=chat_id,
                            reply_markup=reply_markup,
                            parse_mode=parse_mode
                        )
                        
                        # Добавляем reply_to_message_id если нужно
                        if message_reply and message_id:
                            send_kwargs['reply_to_message_id'] = message_id
                        
                        try:
                            if group_type == 'animation':
                                send_kwargs.update(animation=file, caption=caption)
                                msg = await bot.send_animation(**send_kwargs)
                            elif group_type == 'audio':
                                send_kwargs.update(audio=file, caption=caption)
                                msg = await bot.send_audio(**send_kwargs)
                        except TelegramBadRequest as e:
                            if 'message to reply not found' in str(e).lower() and message_reply and message_id:
                                self.logger.warning(f"ответ на сообщение не удался (сообщение для ответа не найдено) для chat_id={chat_id}, message_id={message_id}: {e}. Отправляю вложение без reply_to_message_id.")
                                send_kwargs.pop('reply_to_message_id', None)
                                if group_type == 'animation':
                                    send_kwargs.update(animation=file, caption=caption)
                                    msg = await bot.send_animation(**send_kwargs)
                                elif group_type == 'audio':
                                    send_kwargs.update(audio=file, caption=caption)
                                    msg = await bot.send_audio(**send_kwargs)
                            else:
                                raise
                        
                        if msg:
                            last_message_id = msg.message_id
                        text_sent = True
                        any_sent = True
                        first_group = False
                    except Exception as e:
                        self.logger.error(f"Ошибка при отправке анимации/аудиофайла {file_path}: {e}")
                continue  # не обрабатываем как группу

            # --- Несколько вложений ---
            for i in range(0, len(files), MAX_MEDIA_GROUP):
                batch = files[i:i+MAX_MEDIA_GROUP]
                media = []
                for idx, att in enumerate(batch):
                    file_path = self.utils.resolve_attachment_path(att['file'], self.settings_manager)
                    if not os.path.isfile(file_path):
                        self.logger.warning(f"Вложение не найдено: {file_path}")
                        continue
                    try:
                        file = FSInputFile(file_path)
                        caption = text if first_group and idx == 0 and not text_sent else None
                        if group_type == 'media':
                            if att['type'] == 'photo':
                                media.append(InputMediaPhoto(media=file, caption=caption, parse_mode=parse_mode))
                            elif att['type'] == 'video':
                                media.append(InputMediaVideo(media=file, caption=caption, parse_mode=parse_mode))
                        elif group_type == 'document':
                            media.append(InputMediaDocument(media=file, caption=caption, parse_mode=parse_mode))
                    except Exception as e:
                        self.logger.error(f"Ошибка при подготовке media {file_path}: {e}")
                if media:
                    try:
                        # Подготавливаем параметры для отправки media group
                        send_kwargs = dict(chat_id=chat_id, media=media)
                        
                        # Добавляем reply_to_message_id если нужно (поддерживается в Telegram API)
                        if message_reply and message_id:
                            send_kwargs['reply_to_message_id'] = message_id
                        
                        try:
                            await bot.send_media_group(**send_kwargs)
                        except TelegramBadRequest as e:
                            if 'message to reply not found' in str(e).lower() and message_reply and message_id:
                                self.logger.warning(f"ответ на сообщение не удался (сообщение для ответа не найдено) для chat_id={chat_id}, message_id={message_id}: {e}. Отправляю группу медиа без reply_to_message_id.")
                                send_kwargs.pop('reply_to_message_id', None)
                                await bot.send_media_group(**send_kwargs)
                            else:
                                raise
                        text_sent = True
                        any_sent = True
                        first_group = False
                        
                        # Для групп медиа используем последний файл как приближение last_message_id
                        # Telegram API не возвращает массив сообщений, поэтому это лучшее приближение
                        if media:
                            last_message_id = None  # Группы медиа не дают точного message_id
                    except Exception as e:
                        self.logger.error(f"Ошибка при отправке группы медиа: {e}")
        
        # Если ни одно вложение не отправлено, а текст есть — отправить текстовое сообщение
        if not any_sent and text:
            msg = await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
            if msg:
                last_message_id = msg.message_id
        elif not any_sent and not text:
            # Нет ни вложений, ни текста - это ошибка
            self.logger.error("Не отправлено ни вложений, ни текста")
            return None
        
        return last_message_id
