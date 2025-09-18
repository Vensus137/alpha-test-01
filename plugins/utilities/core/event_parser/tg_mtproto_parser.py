from typing import Any, Dict, Optional, List
from telethon.tl.types import User, Chat, Channel, MessageMediaPhoto, MessageMediaDocument, DocumentAttributeAudio, DocumentAttributeVideo, DocumentAttributeSticker, DocumentAttributeAnimated


class TgMtprotoParser:
    """
    Парсер событий MTProto (Telethon) в стандартный формат событий.
    Только парсинг данных, без бизнес-логики.
    """

    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.datetime_formatter = kwargs['datetime_formatter']
        self.data_converter = kwargs['data_converter']
        self.tg_api_utils = kwargs['tg_api_utils']
        self.tg_entities_parser = kwargs.get('tg_entities_parser')

    async def parse_message(self, message, event) -> Optional[Dict[str, Any]]:
        """
        Парсинг сообщения MTProto в стандартный формат события.
        """
        try:
            # Создание события
            event_data = await self._create_message_event(message, event)
            if event_data:
                # Конвертируем в безопасный словарь
                return self.data_converter.to_safe_dict(event_data)
            return None

        except Exception as e:
            self.logger.error(f"❌ Ошибка парсинга MTProto сообщения: {e}")
            return None

    async def _create_message_event(self, message, event) -> Optional[Dict[str, Any]]:
        """Создаёт событие из MTProto сообщения."""
        try:
            # Получаем информацию о чате (где было сообщение)
            chat_id = message.chat_id
            chat_entity_info = None
            
            # Если есть объект чата, получаем его информацию
            if hasattr(message, 'chat') and message.chat:
                chat_entity_info = self.tg_api_utils.get_entity_id(message.chat)
            
            # Определяем chat_id и chat_type
            if chat_entity_info and 'id' in chat_entity_info and 'type' in chat_entity_info:
                chat_id = chat_entity_info['id']
                chat_type = chat_entity_info['type']
            else:
                # Fallback: нормализуем raw ID если нет объекта чата
                chat_id = self.tg_api_utils.normalize_entity_id(chat_id)
                chat_type = 'unknown'
            
            # Получаем информацию об отправителе (user_id - без изменений)
            sender_id = message.sender_id.user_id if hasattr(message.sender_id, 'user_id') else message.sender_id
            
            # Определяем entity_id и entity_type отправителя через get_sender()
            entity_id = sender_id  # fallback
            entity_type = 'user'   # fallback
            
            try:
                sender = await event.get_sender() if hasattr(event, 'get_sender') and event else None
                if sender:
                    # Используем get_entity_id для получения нормализованного ID и типа
                    entity_info = self.tg_api_utils.get_entity_id(sender)
                    if entity_info:
                        entity_id = entity_info['id']
                        entity_type = entity_info['type']
                    else:
                        # Fallback: нормализуем sender.id без типа
                        entity_id = self.tg_api_utils.normalize_entity_id(sender.id)
                        entity_type = 'unknown'
            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка определения типа отправителя: {e}")
                # Fallback: используем sender_id
                entity_id = self.tg_api_utils.normalize_entity_id(sender_id, 'user')
                entity_type = 'user'
            
            # Обрабатываем entities для MarkdownV2 и HTML (если доступен tg_entities_parser)
            entities = getattr(message, 'entities', []) or []
            if self.tg_entities_parser:
                event_text_markdown = self.tg_entities_parser.to_markdownv2(message.message, entities)
                event_text_html = self.tg_entities_parser.to_html(message.message, entities)
            else:
                # Fallback: пустой текст (tg_entities_parser недоступен)
                event_text_markdown = ''
                event_text_html = ''
            
            # Базовое событие из данных, которые есть в сообщении
            event_data = {
                'source_type': 'text',  # унифицируем с Bot API
                'user_id': sender_id,  # отправитель
                'chat_id': chat_id,    # где было сообщение
                'chat_type': chat_type,  # тип чата
                'chat_title': getattr(message.chat, 'title', None) if hasattr(message, 'chat') and message.chat else None,
                'entity_id': entity_id,  # отправитель (нормализованный)
                'entity_type': entity_type,  # тип отправителя (user)
                'message_id': message.id,
                'event_text': message.message,  # чистый текст
                'event_text_markdown': event_text_markdown,  # текст с MarkdownV2 разметкой
                'event_text_html': event_text_html,  # текст с HTML разметкой
                'event_date': self.datetime_formatter.to_iso_string(
                    self.datetime_formatter.to_local(message.date) if message.date else self.datetime_formatter.now_local()
                )
            }
            
            # Добавляем данные sender (уже получен выше для определения entity_type)
            try:
                sender = await event.get_sender() if hasattr(event, 'get_sender') and event else None
                if sender:
                    # Универсальный маппинг для всех типов sender
                    event_data['username'] = getattr(sender, 'username', None)
                    
                    if isinstance(sender, User):
                        # Пользователи
                        event_data.update({
                            'first_name': getattr(sender, 'first_name', None),
                            'last_name': getattr(sender, 'last_name', None),
                            'is_bot': getattr(sender, 'bot', False),
                            'phone': getattr(sender, 'phone', None),
                            'verified': getattr(sender, 'verified', False)
                        })
                    elif isinstance(sender, (Chat, Channel)):
                        # Группы и каналы - title -> first_name
                        event_data.update({
                            'first_name': getattr(sender, 'title', None),  # title -> first_name
                            'last_name': None,  # нет last_name для групп/каналов
                            'is_bot': False,  # группы/каналы не боты
                            'phone': None,  # нет phone для групп/каналов
                            'verified': getattr(sender, 'verified', False)
                        })
                    else:
                        # Неизвестный тип - базовые поля
                        event_data.update({
                            'first_name': None,
                            'last_name': None,
                            'is_bot': False,
                            'phone': None,
                            'verified': False
                        })
                        
            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка получения данных sender: {e}")
                # Fallback на старый способ (только для пользователей)
                if hasattr(message, 'sender') and message.sender:
                    event_data.update({
                        'first_name': getattr(message.sender, 'first_name', None),
                        'last_name': getattr(message.sender, 'last_name', None),
                        'username': getattr(message.sender, 'username', None),
                        'is_bot': getattr(message.sender, 'bot', None)
                    })
            
            # Добавляем данные чата, если есть
            if hasattr(message, 'chat') and message.chat:
                event_data.update({
                    'chat_type': self._get_chat_type(message.chat),
                    'chat_title': getattr(message.chat, 'title', None)
                })
            
            # Добавляем вложения, если есть
            if hasattr(message, 'media') and message.media:
                event_data['attachments'] = self._extract_attachments(message)
            else:
                event_data['attachments'] = []
            
            # Добавляем флаги is_reply и is_forward
            event_data['is_reply'] = bool(hasattr(message, 'reply_to') and message.reply_to is not None)
            event_data['is_forward'] = bool(hasattr(message, 'fwd_from') and message.fwd_from is not None)
            
            # Обработка reply сообщений
            if hasattr(message, 'reply_to') and message.reply_to:
                event_data['reply_message_id'] = message.reply_to.reply_to_msg_id
                
                # Получаем данные отправителя исходного сообщения
                if hasattr(message.reply_to, 'reply_to_peer_id'):
                    reply_peer = message.reply_to.reply_to_peer_id
                    
                    # Используем универсальный метод для получения entity_id
                    reply_entity_info = self.tg_api_utils.get_entity_id(reply_peer)
                    
                    if reply_entity_info:
                        reply_entity_id = reply_entity_info['id']
                        reply_entity_type = reply_entity_info['type']
                        
                        # Универсальные поля entity уже добавлены ниже
                        pass
                    else:
                        reply_entity_id = None
                        reply_entity_type = 'unknown'
                    
                    # Добавляем универсальные поля entity
                    event_data['reply_entity_id'] = reply_entity_id
                    event_data['reply_entity_type'] = reply_entity_type
            
            # Обработка forward сообщений
            if hasattr(message, 'fwd_from') and message.fwd_from:
                fwd_from = message.fwd_from
                forward_from_id = getattr(fwd_from, 'from_id', None)
                forward_from_name = getattr(fwd_from, 'from_name', None)
                
                # Сохраняем имя отправителя (если есть) - унифицируем с Bot API
                if forward_from_name:
                    event_data['forward_from_user_first_name'] = forward_from_name
                    event_data['forward_from_user_username'] = None  # MTProto не дает username в пересылках
                    event_data['forward_from_user_last_name'] = None  # MTProto не дает last_name в пересылках
                
                if forward_from_id:
                    # Используем универсальный метод для получения entity_id
                    forward_entity_info = self.tg_api_utils.get_entity_id(forward_from_id)
                    
                    if forward_entity_info:
                        forward_entity_id = forward_entity_info['id']
                        forward_entity_type = forward_entity_info['type']
                        pass
                    else:
                        forward_entity_id = None
                        forward_entity_type = 'unknown'
                else:
                    forward_entity_id = None
                    forward_entity_type = 'unknown'
                
                # Добавляем универсальные поля entity
                event_data['forward_entity_id'] = forward_entity_id
                event_data['forward_entity_type'] = forward_entity_type
                
                event_data['forward_date'] = self.datetime_formatter.to_iso_string(
                    self.datetime_formatter.to_local(fwd_from.date) if fwd_from.date else self.datetime_formatter.now_local()
                )
                event_data['forward_message_id'] = getattr(fwd_from, 'channel_post', None)
            
            # Добавляем grouped_id, если есть (для медиа-групп)
            if hasattr(message, 'grouped_id') and message.grouped_id:
                event_data['grouped_id'] = message.grouped_id
            
            return event_data
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания MTProto события: {e}")
            return None

    def _get_chat_type(self, chat) -> str:
        """Определяет тип чата по объекту чата MTProto."""
        if not chat:
            return 'unknown'
        
        # Определяем тип чата по классу объекта
        chat_class = type(chat).__name__
        
        if chat_class == 'User':
            return 'private'
        elif chat_class == 'Chat':
            return 'group'
        elif chat_class == 'Channel':
            return 'supergroup' if getattr(chat, 'megagroup', False) else 'channel'
        else:
            return 'unknown'

    def _extract_attachments(self, message) -> List[Dict[str, Any]]:
        """Извлекает вложения из MTProto сообщения."""
        attachments = []
        
        if not hasattr(message, 'media') or not message.media:
            return attachments
        
        # В Telethon message.media - это один объект, а не список
        media = message.media
        
        try:
            if isinstance(media, MessageMediaPhoto):
                # Извлекаем максимальный размер фотографии
                photo_obj = media.photo
                sizes = getattr(photo_obj, 'sizes', [])
                
                # Выбираем максимальный размер (приоритет: z > y > x > m > s)
                available_sizes = [getattr(size, 'type', '') for size in sizes]
                max_size = 's'  # Минимальный fallback
                
                if 'z' in available_sizes:
                    max_size = 'z'
                elif 'y' in available_sizes:
                    max_size = 'y'
                elif 'x' in available_sizes:
                    max_size = 'x'
                elif 'm' in available_sizes:
                    max_size = 'm'
                
                file_id = getattr(photo_obj, 'id', None)
                access_hash = getattr(photo_obj, 'access_hash', None)
                file_reference = getattr(photo_obj, 'file_reference', None)
                file_size = getattr(photo_obj, 'size', None)
                
                attachments.append({
                    'type': 'photo',
                    'download_type': 'photo',  # MessageMediaPhoto скачивается как photo
                    'file_id': file_id,
                    'access_hash': access_hash,
                    'file_reference': file_reference,
                    'file_size': file_size,
                    'thumb_size': max_size
                })
            elif isinstance(media, MessageMediaDocument):
                # Определяем тип по MIME и атрибутам
                mime_type = getattr(media.document, 'mime_type', '') or ''
                file_name = ''
                duration = None
                voice = False
                
                # Анализируем атрибуты документа
                if hasattr(media.document, 'attributes') and media.document.attributes:
                    has_animated_attr = False
                    has_sticker_attr = False
                    
                    for attr in media.document.attributes:
                        if isinstance(attr, DocumentAttributeAudio):
                            duration = getattr(attr, 'duration', None)
                            voice = getattr(attr, 'voice', False)
                        elif isinstance(attr, DocumentAttributeVideo):
                            duration = getattr(attr, 'duration', None)
                        elif isinstance(attr, DocumentAttributeAnimated):
                            has_animated_attr = True
                        elif isinstance(attr, DocumentAttributeSticker):
                            has_sticker_attr = True
                        elif hasattr(attr, 'file_name'):
                            file_name = attr.file_name
                    
                    # Альтернативная логика: проверяем MIME-тип для анимированных стикеров
                    is_tgs_by_mime = mime_type == 'application/x-tgsticker'
                    is_lottie_by_mime = mime_type == 'application/json' or mime_type == 'application/x-lottie'
                    
                    if has_animated_attr and has_sticker_attr:
                        # Это анимированный стикер (TGS/Lottie)
                        attachment_type = 'animated_sticker'
                    elif has_sticker_attr and (is_tgs_by_mime or is_lottie_by_mime):
                        # Это анимированный стикер по MIME-типу
                        attachment_type = 'animated_sticker'
                    elif has_animated_attr:
                        # Это обычная анимация (GIF/MP4)
                        attachment_type = 'animation'
                    elif has_sticker_attr:
                        # Это обычный стикер (НЕ анимированный)
                        attachment_type = 'sticker'
                    else:
                        # Нет специальных атрибутов - определяем по MIME
                        attachment_type = None
                    
                    # Если определили специальный тип - создаем attachment и выходим
                    if attachment_type:
                        attachments.append({
                            'type': attachment_type,
                            'download_type': 'document',  # MessageMediaDocument всегда скачивается как document
                            'file_id': getattr(media.document, 'id', None),
                            'access_hash': getattr(media.document, 'access_hash', None),
                            'file_reference': getattr(media.document, 'file_reference', None),
                            'file_size': getattr(media.document, 'size', None),
                            'mime_type': mime_type
                        })
                        return attachments  # Выходим, так как определили специальный тип
                
                # Определяем тип по MIME и атрибутам
                if voice:
                    attachment_type = 'voice'
                elif mime_type.startswith('image/'):
                    attachment_type = 'photo'
                elif mime_type.startswith('video/'):
                    # Проверяем, не является ли это видео-сообщением
                    if any(isinstance(attr, DocumentAttributeVideo) and getattr(attr, 'round_message', False) for attr in media.document.attributes):
                        attachment_type = 'video_note'
                    else:
                        attachment_type = 'video'
                elif mime_type.startswith('audio/'):
                    attachment_type = 'audio'
                else:
                    attachment_type = 'document'
                
                attachment_data = {
                    'type': attachment_type,
                    'download_type': 'document',  # MessageMediaDocument всегда скачивается как document
                    'file_id': getattr(media.document, 'id', None),
                    'access_hash': getattr(media.document, 'access_hash', None),
                    'file_reference': getattr(media.document, 'file_reference', None),
                    'file_size': getattr(media.document, 'size', None),
                    'mime_type': mime_type,
                    'file_name': file_name
                }
                
                # Добавляем длительность для аудио/видео
                if duration and attachment_type in ['audio', 'video', 'voice']:
                    attachment_data['duration'] = duration
                
                attachments.append(attachment_data)

        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка обработки медиа: {e}")
        
        return attachments
