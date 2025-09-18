from typing import Optional

from aiogram import Bot


class TgBotInitializer:
    """
    Утилита для централизованной инициализации Telegram бота.
    Получает токен через settings_manager с поддержкой переменных окружения.
    """
    
    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.settings_manager = kwargs['settings_manager']
        self._bot: Optional[Bot] = None
        self._token: Optional[str] = None
        
        # Получаем токен через settings_manager
        self._load_token()
    
    def _load_token(self):
        """Загружает токен из настроек утилиты"""
        try:
            # Получаем настройки утилиты через settings_manager
            settings = self.settings_manager.get_plugin_settings('tg_bot_initializer')
            if not settings:
                self.logger.warning("⚠️ Настройки tg_bot_initializer не найдены")
                return
            
            token = settings.get('token', '')
            if token:
                self._token = token
                self.logger.info("✅ Токен бота загружен из настроек")
            else:
                self.logger.warning("⚠️ Токен бота не установлен в настройках")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки токена: {e}")
    
    def get_token(self) -> str:
        """Получить токен бота"""
        return self._token or ""
    
    def is_initialized(self) -> bool:
        """Проверить, инициализирован ли бот"""
        return self._bot is not None
    
    def get_bot(self) -> Bot:
        """Получить экземпляр инициализированного бота"""
        if not self._token:
            self.logger.error("Токен бота не найден. Установите переменную окружения TELEGRAM_BOT_TOKEN или настройку в пресете")
            return None
        
        # Создаем бота только один раз (singleton поведение)
        if self._bot is None:
            self.logger.info("TgBotInitializer: инициализация Telegram бота...")
            self._bot = Bot(token=self._token)
            self.logger.info("TgBotInitializer: бот успешно инициализирован")
        
        return self._bot
    
    def shutdown(self):
        """Корректное завершение работы бота"""
        if self._bot:
            self.logger.info("TgBotInitializer: завершение работы бота...")
            # Закрываем сессию бота
            try:
                # Закрываем сессию если она есть
                if hasattr(self._bot.session, 'close'):
                    self._bot.session.close()
            except Exception as e:
                self.logger.warning(f"TgBotInitializer: ошибка при закрытии сессии: {e}")
            
            self._bot = None
            self.logger.info("TgBotInitializer: бот завершен") 