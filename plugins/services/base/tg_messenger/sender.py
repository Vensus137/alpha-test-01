from aiogram.exceptions import TelegramBadRequest

from .attach import AttachmentHandler
from .utils import MessengerUtils


class MessageSender:
    """Отправитель сообщений для tg_messenger сервиса"""
    
    def __init__(self, **kwargs):
        self.logger = kwargs.get('logger')
        self.settings_manager = kwargs.get('settings_manager')
        self.placeholder_processor = kwargs.get('placeholder_processor')
        self.tg_button_mapper = kwargs.get('tg_button_mapper')
        
        # Получаем настройки через settings_manager
        settings = self.settings_manager.get_plugin_settings('tg_messenger')
        self.enable_placeholder = settings.get('enable_placeholder', True)
        
        # Инициализируем зависимости
        self.attachment_handler = AttachmentHandler(**kwargs)
        self.utils = MessengerUtils(**kwargs)
    
    async def send_message(self, bot, action: dict, params: dict) -> dict:
        """Отправляет сообщение с правильной обработкой ошибок."""
        try:
            # Критическая проверка 1: бот инициализирован
            if not bot:
                self.logger.error("Бот не инициализирован")
                return {'success': False, 'error': 'Бот не инициализирован'}

            chat_id = params['chat_id']
            
            # Получаем текст (может быть пустым или отсутствовать)
            text = action.get('text', '')
            
            # --- Добавляем additional_text если указан ---
            additional_text = action.get('additional_text')
            if additional_text:
                text = text + additional_text
            
            # --- Обработка плейсхолдеров в тексте ---
            # Проверяем глобальную настройку и явное отключение в action
            placeholders_enabled = self.enable_placeholder
            if 'placeholder' in action:
                # Явное указание в action имеет приоритет над глобальной настройкой
                placeholders_enabled = action['placeholder']
            
            if placeholders_enabled and self.placeholder_processor:
                try:
                    # Используем action как словарь значений для плейсхолдеров
                    text = self.placeholder_processor.process_text_placeholders(text, action)
                except Exception as e:
                    self.logger.warning(f"Ошибка обработки плейсхолдеров в тексте: {e}")
            
            # --- Обработка плейсхолдеров в attachment ---
            if placeholders_enabled and self.placeholder_processor and 'attachment' in action:
                try:
                    attachment_raw = action['attachment']
                    if isinstance(attachment_raw, str) and '{' in attachment_raw:
                        processed_attachment = self.placeholder_processor.process_text_placeholders(attachment_raw, action)
                        action['attachment'] = processed_attachment
                except Exception as e:
                    self.logger.warning(f"Ошибка обработки плейсхолдеров в attachment: {e}")
            
            message_id = params['message_id']
            callback_edit = params['callback_edit']
            remove = params['remove']
            inline = params['inline']
            reply = params['reply']
            attachments = params['attachments']
            message_reply = params.get('message_reply', False)

            # Определяем parse_mode: приоритет у action, иначе используем настройку
            parse_mode = action.get('parse_mode') or self.settings_manager.get_plugin_settings('tg_messenger').get('parse_mode', None)

            # --- Проверка и обрезка длины текста ---
            if text:  # Проверяем только если текст не пустой
                max_text_length = 1000 if attachments else 4080  # Запас от лимитов Telegram
                if len(text) > max_text_length:
                    original_length = len(text)
                    # Обрезаем с запасом для троеточия
                    text = text[:max_text_length-3] + "..."
                    self.logger.warning(
                        f"Текст обрезан с {original_length} до {max_text_length} символов "
                        f"(лимит для {'вложений' if attachments else 'обычных сообщений'}) + '...'"
                    )

            # Если есть вложения, всегда отправляем новое сообщение (редактировать с вложениями нельзя)
            if attachments and callback_edit:
                self.logger.warning(f"callback_edit=True игнорируется, так как у сообщения есть вложения. Будет отправлено новое сообщение без редактирования.")
                callback_edit = False

            # Получаем координаты из action_data для формирования callback_data
            reply_markup = self.utils.build_reply_markup(inline, reply, self.tg_button_mapper)

            # Отправляем или редактируем сообщение
            try:
                last_message_id = None
                if callback_edit and message_id:
                    await self._edit_message(bot, chat_id, message_id, text, reply_markup, parse_mode)
                    last_message_id = message_id
                else:
                    if attachments:
                        last_message_id = await self.attachment_handler.send_attachments(
                            bot, chat_id, text, attachments, reply_markup, parse_mode, 
                            message_id, message_reply
                        )
                    elif text:  # Отправляем текстовое сообщение только если есть текст
                        # Новое: если message_reply true и есть message_id, отправляем как reply
                        send_kwargs = dict(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
                        if message_reply and message_id:
                            send_kwargs['reply_to_message_id'] = message_id
                            try:
                                msg = await bot.send_message(**send_kwargs)
                                last_message_id = msg.message_id
                            except TelegramBadRequest as e:
                                if 'message to reply not found' in str(e).lower():
                                    self.logger.warning(f"ответ на сообщение не удался (сообщение для ответа не найдено) для chat_id={chat_id}, message_id={message_id}: {e}. Отправляю новое сообщение без reply_to_message_id.")
                                    send_kwargs.pop('reply_to_message_id', None)
                                    msg = await bot.send_message(**send_kwargs)
                                    last_message_id = msg.message_id
                                else:
                                    raise
                        else:
                            msg = await bot.send_message(**send_kwargs)
                            last_message_id = msg.message_id
                    else:
                        # Нет ни текста, ни вложений - это ошибка
                        self.logger.error("Тип действия 'send' требует либо 'text', либо 'attachment'")
                        return {'success': False, 'error': 'Не указан текст или вложение'}
            except Exception as e:
                self.logger.error(f"Критическая ошибка при отправке сообщения: {e}")
                return {'success': False, 'error': f'Ошибка отправки сообщения: {str(e)}'}

            # Удаляем исходное сообщение если указан атрибут remove
            if remove and message_id:
                try:
                    await bot.delete_message(chat_id, message_id)
                except TelegramBadRequest as e:
                    self.logger.warning(f"Не удалось удалить исходное сообщение chat_id={chat_id}, message_id={message_id}: {e}")
                except Exception as e:
                    self.logger.error(f"Ошибка при удалении исходного сообщения chat_id={chat_id}, message_id={message_id}: {e}")

            return {'success': True, 'last_message_id': last_message_id}

        except Exception as e:
            self.logger.error(f"Неожиданная ошибка в send_message: {e}")
            return {'success': False, 'error': f'Неожиданная ошибка: {str(e)}'}

    async def _edit_message(self, bot, chat_id, message_id, text, reply_markup, parse_mode):
        """Редактирует сообщение с fallback на отправку нового."""
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except TelegramBadRequest as e:
            await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
