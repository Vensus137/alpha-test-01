from typing import Any, Dict, Optional, List
from aiogram import types


class TgBotParser:
    """
    Парсер событий Bot API (aiogram) в стандартный формат событий.
    Только парсинг данных, без бизнес-логики.
    """

    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.datetime_formatter = kwargs['datetime_formatter']
        self.data_converter = kwargs['data_converter']

    def parse_message(self, message: types.Message) -> Optional[Dict[str, Any]]:
        """
        Парсинг сообщения Bot API в стандартный формат события.
        """
        try:
            # Создание события с вложениями
            event = self._create_message_event(message)
            if event:
                # Конвертируем в безопасный словарь
                return self.data_converter.to_safe_dict(event)
            return None

        except Exception as e:
            self.logger.error(f"❌ Ошибка парсинга Bot API сообщения: {e}")
            return None

    def parse_callback(self, callback: types.CallbackQuery) -> Optional[Dict[str, Any]]:
        """
        Парсинг callback Bot API в стандартный формат события.
        """
        try:
            chat_id = callback.message.chat.id if callback.message else None
            chat_type = callback.message.chat.type if callback.message and callback.message.chat else None
            chat_title = getattr(callback.message.chat, 'title', None) if callback.message and callback.message.chat else None
            message_id = callback.message.message_id if callback.message else None
            callback_id = callback.id
            
            event = {
                'source_type': 'callback',
                'user_id': callback.from_user.id,
                'first_name': callback.from_user.first_name,
                'last_name': callback.from_user.last_name if callback.from_user else None,
                'username': callback.from_user.username if callback.from_user else None,
                'is_bot': bool(callback.from_user.is_bot) if callback.from_user and callback.from_user.is_bot is not None else False,
                'chat_id': chat_id,
                'chat_type': chat_type,
                'chat_title': chat_title,
                'message_id': message_id,
                'callback_id': callback_id,
                'callback_data': callback.data,
                'event_date': self.datetime_formatter.to_iso_string(self.datetime_formatter.now_local()),
                'is_reply': False,
                'is_forward': False,
                'entity_id': callback.from_user.id,
                'entity_type': 'user',
            }
            
            # Конвертируем в безопасный словарь
            return self.data_converter.to_safe_dict(event)

        except Exception as e:
            self.logger.error(f"❌ Ошибка парсинга Bot API callback: {e}")
            return None

    def parse_new_member(self, message: types.Message) -> Optional[Dict[str, Any]]:
        """
        Парсинг события новых участников Bot API в стандартный формат события.
        """
        try:
            joined_user_ids = []
            joined_usernames = []
            joined_first_names = []
            joined_last_names = []
            joined_is_bots = []
            
            for user in message.new_chat_members:
                joined_user_ids.append(user.id)
                joined_usernames.append(user.username)
                joined_first_names.append(user.first_name)
                joined_last_names.append(getattr(user, 'last_name', None))
                joined_is_bots.append(bool(user.is_bot) if user.is_bot is not None else False)

            event = {
                'source_type': 'new_member',
                'chat_id': message.chat.id,
                'chat_title': getattr(message.chat, 'title', None),
                'chat_type': getattr(message.chat, 'type', None),
                'joined_user_ids': joined_user_ids,
                'joined_usernames': joined_usernames,
                'joined_first_names': joined_first_names,
                'joined_last_names': joined_last_names,
                'joined_is_bots': joined_is_bots,
                'event_date': self.datetime_formatter.to_iso_string(
                    self.datetime_formatter.to_local(message.date) if message.date else self.datetime_formatter.now_local()
                ),
                'is_reply': False,
                'is_forward': False,
                'entity_id': message.chat.id,
                'entity_type': 'chat' if message.chat.type in ['group', 'supergroup'] else 'channel' if message.chat.type == 'channel' else 'unknown',
            }

            # Для совместимости: user_id и username — первый из списка
            if joined_user_ids:
                event['user_id'] = joined_user_ids[0]
            if joined_usernames:
                event['username'] = joined_usernames[0]
            if joined_first_names:
                event['first_name'] = joined_first_names[0]
            if joined_last_names:
                event['last_name'] = joined_last_names[0]
            if joined_is_bots:
                event['is_bot'] = joined_is_bots[0]

            # Информация о пригласительной ссылке, если есть
            if getattr(message, 'invite_link', None):
                invite_link = message.invite_link
                event['invite_link'] = getattr(invite_link, 'invite_link', None)
                event['invite_link_creator_id'] = getattr(getattr(invite_link, 'creator', None), 'id', None)
                event['invite_link_creator_username'] = getattr(getattr(invite_link, 'creator', None), 'username', None)
                event['invite_link_creator_first_name'] = getattr(getattr(invite_link, 'creator', None), 'first_name', None)
                event['invite_link_creates_join_request'] = getattr(invite_link, 'creates_join_request', None)

            # Информация о том, кто инициировал добавление (если есть)
            if message.from_user:
                event['initiator_user_id'] = message.from_user.id
                event['initiator_username'] = message.from_user.username
                event['initiator_first_name'] = message.from_user.first_name
                event['initiator_last_name'] = getattr(message.from_user, 'last_name', None)

            # Конвертируем в безопасный словарь
            return self.data_converter.to_safe_dict(event)

        except Exception as e:
            self.logger.error(f"❌ Ошибка парсинга Bot API new_member: {e}")
            return None

    def _create_message_event(self, message: types.Message) -> Dict[str, Any]:
        """Создаёт событие из Bot API сообщения с извлечением вложений."""
        # Универсальный маппинг для Bot API
        if message.from_user:
            # Сообщения от пользователей
            event = {
                'source_type': 'text',
                'user_id': message.from_user.id,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'username': message.from_user.username,
                'is_bot': bool(message.from_user.is_bot) if message.from_user.is_bot is not None else False,
                'chat_id': message.chat.id,
                'chat_type': message.chat.type if message.chat else None,
                'chat_title': getattr(message.chat, 'title', None),
                'message_id': message.message_id,
                'event_text': message.text or message.caption,
                'event_text_markdown': message.md_text or message.caption,
                'event_text_html': message.html_text or message.caption,
                'event_date': self.datetime_formatter.to_iso_string(
                    self.datetime_formatter.to_local(message.date) if message.date else self.datetime_formatter.now_local()
                ),
                'media_group_id': message.media_group_id,
                'attachments': []
            }
        else:
            # Сообщения от каналов/групп (channel_post, group_post)
            event = {
                'source_type': 'text',
                'user_id': message.chat.id,  # ID чата как user_id
                'first_name': getattr(message.chat, 'title', None),  # title -> first_name
                'last_name': None,  # нет last_name для чатов
                'username': getattr(message.chat, 'username', None),  # username чата
                'is_bot': False,  # чаты не боты
                'chat_id': message.chat.id,
                'chat_type': message.chat.type if message.chat else None,
                'chat_title': getattr(message.chat, 'title', None),
                'message_id': message.message_id,
                'event_text': message.text or message.caption,
                'event_text_markdown': message.md_text or message.caption,
                'event_text_html': message.html_text or message.caption,
                'event_date': self.datetime_formatter.to_iso_string(
                    self.datetime_formatter.to_local(message.date) if message.date else self.datetime_formatter.now_local()
                ),
                'media_group_id': message.media_group_id,
                'attachments': []
            }

        # Добавляем флаги is_reply и is_forward
        event['is_reply'] = bool(message.reply_to_message)
        event['is_forward'] = bool(message.forward_from or message.forward_from_chat)
        
        # Универсальные поля entity для Bot API
        if message.from_user:
            # Сообщение от пользователя
            event['entity_id'] = message.from_user.id
            event['entity_type'] = 'user'
        else:
            # Сообщение от чата/канала
            event['entity_id'] = message.chat.id
            if message.chat.type == 'channel':
                event['entity_type'] = 'channel'
            elif message.chat.type in ['group', 'supergroup']:
                event['entity_type'] = 'chat'
            else:
                event['entity_type'] = 'unknown'
        
        # Обработка reply-сообщений
        if message.reply_to_message:
            event['reply_message_id'] = message.reply_to_message.message_id
            event['reply_message_text'] = message.reply_to_message.text or message.reply_to_message.caption
            event['reply_username'] = message.reply_to_message.from_user.username if message.reply_to_message.from_user else None
            event['reply_first_name'] = message.reply_to_message.from_user.first_name if message.reply_to_message.from_user else None
            event['reply_last_name'] = getattr(message.reply_to_message.from_user, 'last_name', None) if message.reply_to_message.from_user else None
            event['reply_attachments'] = self._extract_attachments(message.reply_to_message)
            
            # Универсальные поля
            if message.reply_to_message.from_user:
                event['reply_entity_id'] = message.reply_to_message.from_user.id
                event['reply_entity_type'] = 'user'
            elif message.reply_to_message.chat:
                event['reply_entity_id'] = message.reply_to_message.chat.id
                if message.reply_to_message.chat.type == 'channel':
                    event['reply_entity_type'] = 'channel'
                else:
                    event['reply_entity_type'] = 'chat'
        
        # Обработка forward-сообщений
        if message.forward_from or message.forward_from_chat:
            event['forward_from_user_username'] = message.forward_from.username if message.forward_from else None
            event['forward_from_user_first_name'] = message.forward_from.first_name if message.forward_from else None
            event['forward_from_user_last_name'] = getattr(message.forward_from, 'last_name', None) if message.forward_from else None
            event['forward_from_chat_title'] = message.forward_from_chat.title if message.forward_from_chat else None
            event['forward_from_chat_type'] = message.forward_from_chat.type if message.forward_from_chat else None
            event['forward_date'] = self.datetime_formatter.to_iso_string(
                self.datetime_formatter.to_local(message.forward_date) if message.forward_date else self.datetime_formatter.now_local()
            )
            event['forward_message_id'] = message.forward_from_message_id
            
            # Универсальные поля
            if message.forward_from:
                event['forward_entity_id'] = message.forward_from.id
                event['forward_entity_type'] = 'user'
            elif message.forward_from_chat:
                event['forward_entity_id'] = message.forward_from_chat.id
                if message.forward_from_chat.type == 'channel':
                    event['forward_entity_type'] = 'channel'
                else:
                    event['forward_entity_type'] = 'chat'

        # Извлекаем вложения
        event['attachments'] = self._extract_attachments(message)

        return event

    def _extract_attachments(self, message: types.Message) -> List[Dict[str, Any]]:
        """Извлекает вложения из Bot API сообщения."""
        attachments = []
        
        if message.photo:
            # Берем только самый большой размер фото (последний в списке)
            largest_photo = message.photo[-1]
            attachments.append({
                'type': 'photo',
                'file_id': largest_photo.file_id,
                'file_size': largest_photo.file_size,
            })

        if message.document:
            # Проверяем MIME-тип для правильного определения типа
            mime_type = message.document.mime_type or ''
            file_name = message.document.file_name or ''

            if mime_type.startswith('image/'):
                attachment_type = 'photo'
            elif mime_type.startswith('video/'):
                attachment_type = 'video'
            elif mime_type.startswith('audio/'):
                attachment_type = 'audio'
            else:
                attachment_type = 'document'

            attachments.append({
                'type': attachment_type,
                'file_id': message.document.file_id,
                'file_size': message.document.file_size,
                'mime_type': mime_type,
                'file_name': file_name
            })

        if message.video:
            attachments.append({
                'type': 'video',
                'file_id': message.video.file_id,
                'file_size': message.video.file_size
            })

        if message.audio:
            attachments.append({
                'type': 'audio',
                'file_id': message.audio.file_id,
                'file_size': message.audio.file_size
            })

        if message.voice:
            attachments.append({
                'type': 'voice',
                'file_id': message.voice.file_id,
                'file_size': message.voice.file_size
            })

        if message.sticker:
            # Проверяем, является ли это анимированным стикером
            if message.sticker.is_animated:
                attachment_type = 'animated_sticker'
            else:
                attachment_type = 'sticker'
            
            attachments.append({
                'type': attachment_type,
                'file_id': message.sticker.file_id,
                'file_size': message.sticker.file_size
            })

        if message.animation:
            attachments.append({
                'type': 'animation',
                'file_id': message.animation.file_id,
                'file_size': message.animation.file_size
            })

        if message.video_note:
            attachments.append({
                'type': 'video_note',
                'file_id': message.video_note.file_id,
                'file_size': message.video_note.file_size
            })
            
        return attachments
