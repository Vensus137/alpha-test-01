import asyncio
import json

from aiogram.exceptions import TelegramBadRequest

from .sender import MessageSender
from .attach import AttachmentHandler

class TgMessengerService:
    def __init__(self, **kwargs):
        self.tg_button_mapper = kwargs['tg_button_mapper']
        self.logger = kwargs['logger']
        self.database_service = kwargs['database_service']
        self.settings_manager = kwargs['settings_manager']
        self.bot = kwargs['tg_bot_initializer'].get_bot()
        self.placeholder_processor = kwargs.get('placeholder_processor')
        
        # Получаем настройки через settings_manager
        settings = self.settings_manager.get_plugin_settings('tg_messenger')
        self.callback_edit_default = settings.get('callback_edit_default', True)
        self.interval = settings.get('queue_read_interval', 0.05)
        self.batch_size = settings.get('queue_batch_size', 50)
        self.parse_mode = settings.get('parse_mode', None)
        
        # Инициализируем зависимости
        self.message_sender = MessageSender(**kwargs)
        self.attachment_handler = AttachmentHandler(**kwargs)

    async def _handle_action(self, action: dict) -> dict:
        try:
            if action.get('type') == 'send':
                params = self._extract_common_params(action)
                result = await self.message_sender.send_message(self.bot, action, params)
                if not result.get('success'):
                    self.logger.error(f"send: ошибка для chat_id={params['chat_id']}: {result.get('error', 'Неизвестная ошибка')}")
                return result
            elif action.get('type') == 'remove':
                result = await self._remove_message(action)
                if not result.get('success'):
                    self.logger.error(f"remove: ошибка для chat_id={action['chat_id']}: {result.get('error', 'Неизвестная ошибка')}")
                return result

            else:
                self.logger.error(f"неподдерживаемый тип действия: {action.get('type')}")
                return {'success': False, 'error': 'Неподдерживаемый тип действия'}
        except Exception as e:
            self.logger.exception(f"error: {e}")
            return {'success': False, 'error': str(e)}

    async def run(self):
        """
        Асинхронный цикл: читает pending-действия типа 'send' и 'remove' и обрабатывает их.
        """
        self.logger.info(f"старт фонового цикла обработки очереди действий (interval={self.interval}, batch_size={self.batch_size}).")
        while True:
            try:
                with self.database_service.session_scope('actions') as (_, repos):
                    actions_repo = repos['actions']
                    # Обрабатываем действия типа 'send' и 'remove'
                    actions = actions_repo.get_pending_actions_by_type_parsed(['send', 'remove'], limit=self.batch_size)
                    
                    for action in actions:
                        action_id = action['id']
                        try:
                            result = await self._handle_action(action)
                            status = 'completed' if result.get('success') else 'failed'
                            
                            # Подготавливаем response_data для сохранения в БД
                            response_data = {}
                            if result.get('success'):
                                if 'last_message_id' in result:
                                    response_data['last_message_id'] = result['last_message_id']
                            else:
                                if 'error' in result:
                                    response_data['error'] = result['error']
                            
                            # Сериализуем response_data в JSON-строку
                            response_data_str = json.dumps(response_data, ensure_ascii=False) if response_data else None
                            
                        except Exception as e:
                            self.logger.exception(f"Ошибка при обработке действия {action_id}: {e}")
                            status = 'failed'
                            response_data_str = json.dumps({'error': f'Ошибка обработки: {str(e)}'}, ensure_ascii=False)
                        
                        # Обновляем статус действия и response_data
                        if not actions_repo.update_action(action_id, status=status, response_data=response_data_str):
                            self.logger.error(f"Не удалось обновить статус действия {action_id} на {status}")
                    
            except Exception as e:
                self.logger.error(f"ошибка в основном цикле: {e}")
            await asyncio.sleep(self.interval)

    def _extract_common_params(self, action: dict) -> dict:
        chat_id = action['chat_id']
        message_id = action.get('message_id')

        # --- Подмена message_id через exact_message_id ---
        exact_message_id = action.get('exact_message_id')
        if exact_message_id is not None:
            message_id = exact_message_id

        # --- Обработка private_answer ---
        user_id = action.get('user_id')
        private_answer = action.get('private_answer', False)
        
        if private_answer and user_id:
            chat_id = user_id
        elif private_answer and not user_id:
            self.logger.error("private_answer=True, но user_id отсутствует в action. Сообщение будет отправлено в исходный чат.")

        inline = action.get('inline')
        reply = action.get('reply')
        attachments = self.attachment_handler._parse_attachments(action)

        # Логика приоритетов: callback_edit > remove > глобальный callback_edit_default
        message_reply = action.get('message_reply', False)
        callback_edit = action.get('callback_edit')
        if callback_edit is None:
            callback_edit = self.callback_edit_default if self.callback_edit_default is not None else False
        remove = action.get('remove', False)

        # --- Проверка совместимости параметров (message_reply > edit > remove) ---
        if message_reply:
            if callback_edit:
                self.logger.warning("Параметр callback_edit игнорируется, так как задан message_reply (message_reply > edit)")
            if remove:
                self.logger.warning("Параметр remove игнорируется, так как задан message_reply (message_reply > remove)")
            callback_edit = False
            remove = False
        elif callback_edit:
            if remove:
                self.logger.warning("Параметр remove игнорируется, так как задан edit (edit > remove)")
            remove = False
        # иначе remove может быть true

        return {
            'chat_id': chat_id,
            'message_id': message_id,
            'callback_edit': callback_edit,
            'remove': remove,
            'inline': inline,
            'reply': reply,
            'attachments': attachments,
            'message_reply': message_reply,  # Новое поле
            'private_answer': private_answer,
            'user_id': user_id,
        }

    async def _remove_message(self, action: dict) -> dict:
        """
        Удаляет сообщение из чата.
        """
        chat_id = action['chat_id']
        
        # Приоритет: remove_message_id из конфига > message_id из action_data
        message_id = action.get('remove_message_id') or action.get('message_id')
        
        if not message_id:
            return {'success': False, 'error': 'Не указан ID сообщения для удаления (ни remove_message_id, ни message_id)'}

        try:
            await self.bot.delete_message(chat_id, message_id)
            return {'success': True}
        except TelegramBadRequest as e:
            self.logger.warning(f"Не удалось удалить сообщение chat_id={chat_id}, message_id={message_id}: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Ошибка при удалении сообщения chat_id={chat_id}, message_id={message_id}: {e}")
            return {'success': False, 'error': str(e)}



