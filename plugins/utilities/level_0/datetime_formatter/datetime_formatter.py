import datetime
from typing import Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    raise ImportError("Для работы DatetimeFormatter требуется Python 3.9+ с модулем zoneinfo. Пожалуйста, обновите Python.")

class DatetimeFormatter:

    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.settings_manager = kwargs['settings_manager']
        # Получаем настройки через settings_manager
        settings = self.settings_manager.get_plugin_settings("datetime_formatter")
        self.timezone = settings.get('timezone', 'Europe/Moscow')
        self.format_name = settings.get('format', 'iso')
        self._tz = ZoneInfo(self.timezone)

    def now_utc(self) -> datetime.datetime:
        # Возвращает naive UTC, но получает время через timezone-aware способ
        return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    def now_utc_tz(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    def now_local(self) -> datetime.datetime:
        return datetime.datetime.now(self._tz).replace(tzinfo=None)

    def now_local_tz(self) -> datetime.datetime:
        return datetime.datetime.now(self._tz)

    def to_utc(self, dt: datetime.datetime) -> datetime.datetime:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._tz)
        return dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)

    def to_utc_tz(self, dt: datetime.datetime) -> datetime.datetime:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._tz)
        return dt.astimezone(datetime.timezone.utc)

    def to_local(self, dt: datetime.datetime) -> datetime.datetime:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(self._tz).replace(tzinfo=None)

    def to_local_tz(self, dt: datetime.datetime) -> datetime.datetime:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(self._tz)

    def format(self, dt: datetime.datetime) -> str:
        if self.format_name == 'iso':
            return dt.isoformat()
        # Можно добавить другие форматы по необходимости
        return dt.isoformat()

    def to_string(self, dt: datetime.datetime, fmt: Optional[str] = None) -> str:
        """
        Преобразует datetime в строку по формату (по умолчанию ISO).
        fmt: 'iso' (default), либо любой формат strftime.
        """
        if fmt is None:
            fmt = self.format_name
        if fmt == 'iso':
            return dt.isoformat()
        return dt.strftime(fmt)

    def to_iso_string(self, dt: datetime.datetime) -> str:
        """
        Короткий алиас для ISO-строки.
        """
        return dt.isoformat()

    def to_datetime_string(self, dt) -> str:
        """
        Преобразует datetime или ISO-строку в читаемый формат ДДДД-ММ-ГГ ЧЧ:ММ:СС.
        Универсальный метод: принимает datetime.datetime или строку ISO формата.
        """
        if isinstance(dt, str):
            # Если передана строка - парсим её в datetime
            dt = self.parse(dt)
        elif not isinstance(dt, datetime.datetime):
            self.logger.error(f"Ожидается datetime или строка ISO, получено: {type(dt)}")
            return None
        
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    def to_date_string(self, dt) -> str:
        """
        Преобразует datetime или ISO-строку в формат даты ДДДД-ММ-ГГ.
        Универсальный метод: принимает datetime.datetime или строку ISO формата.
        """
        if isinstance(dt, str):
            # Если передана строка - парсим её в datetime
            dt = self.parse(dt)
        elif not isinstance(dt, datetime.datetime):
            self.logger.error(f"Ожидается datetime или строка ISO, получено: {type(dt)}")
            return None
        
        return dt.strftime('%Y-%m-%d')

    def to_serializable(self, obj):
        """
        Рекурсивно преобразует все datetime в строку (ISO) для сериализации в JSON.
        """
        import datetime
        if isinstance(obj, dict):
            return {k: self.to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.to_serializable(i) for i in obj]
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return obj

    def parse(self, dt_str: str) -> datetime.datetime:
        dt = datetime.datetime.fromisoformat(dt_str)
        # Возвращаем как есть: если в строке есть tzinfo — будет aware, если нет — naive
        return dt

    def parse_to_local(self, dt_str: str) -> datetime.datetime:
        """
        Парсит строку с датой и возвращает datetime в локальном времени (naive).
        Предполагает, что входная строка в локальном времени.
        Поддерживает форматы: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, ISO формат.
        """
        dt = self.parse_date_string(dt_str)  # Используем универсальный парсер
        # Если datetime naive - считаем его локальным
        if dt.tzinfo is None:
            return dt
        # Если datetime aware - конвертируем в локальное время
        return self.to_local(dt)

    def parse_to_local_tz(self, dt_str: str) -> datetime.datetime:
        """
        Парсит строку с датой и возвращает datetime в локальном времени с timezone.
        Предполагает, что входная строка в локальном времени.
        Поддерживает форматы: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, ISO формат.
        """
        dt = self.parse_date_string(dt_str)  # Используем универсальный парсер
        # Если datetime naive - считаем его локальным и добавляем timezone
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self._tz)
        # Если datetime aware - конвертируем в локальное время
        return self.to_local_tz(dt)

    def parse_to_utc(self, dt_str: str) -> datetime.datetime:
        """
        Парсит строку с датой и возвращает datetime в UTC (naive).
        Если datetime naive - считаем его ЛОКАЛЬНЫМ временем и конвертируем в UTC.
        Если datetime aware - конвертируем в UTC.
        Поддерживает форматы: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, ISO формат.
        """
        dt = self.parse_date_string(dt_str)  # Используем универсальный парсер
        # Если datetime naive - считаем его ЛОКАЛЬНЫМ временем и конвертируем в UTC
        if dt.tzinfo is None:
            # Добавляем локальную таймзону и конвертируем в UTC
            dt_local = dt.replace(tzinfo=self._tz)
            return dt_local.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        # Если datetime aware - конвертируем в UTC
        return self.to_utc(dt)

    def parse_to_utc_tz(self, dt_str: str) -> datetime.datetime:
        """
        Парсит строку с датой и возвращает datetime в UTC с timezone.
        Если datetime naive - считаем его ЛОКАЛЬНЫМ временем и конвертируем в UTC.
        Если datetime aware - конвертируем в UTC.
        Поддерживает форматы: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, ISO формат.
        """
        dt = self.parse_date_string(dt_str)  # Используем универсальный парсер
        # Если datetime naive - считаем его ЛОКАЛЬНЫМ временем и конвертируем в UTC
        if dt.tzinfo is None:
            # Добавляем локальную таймзону и конвертируем в UTC
            dt_local = dt.replace(tzinfo=self._tz)
            return dt_local.astimezone(datetime.timezone.utc)
        # Если datetime aware - конвертируем в UTC
        return self.to_utc_tz(dt)

    def parse_date_string(self, date_str: str) -> datetime.datetime:
        """
        Универсальный метод для парсинга дат из строк в различных форматах.
        
        Поддерживаемые форматы:
        - ГГГГ-ММ-ДД (например, "2025-01-15")
        - ГГГГ-ММ-ДД ЧЧ:ММ:СС (например, "2025-01-15 14:30:00")
        - ISO формат с таймзоной (например, "2025-01-15T14:30:00+03:00")
        - ISO формат без таймзоны (например, "2025-01-15T14:30:00")
        - ISO формат с микросекундами (например, "2025-01-15T14:30:00.123456")
        
        Args:
            date_str: Строка с датой для парсинга
            
        Returns:
            datetime.datetime: Объект datetime (aware если есть tzinfo, иначе naive)
            
        Raises:
            ValueError: Если строка не соответствует ни одному из поддерживаемых форматов
        """
        if not date_str or not isinstance(date_str, str):
            self.logger.error(f"Ожидается непустая строка, получено: {date_str}")
            return None
        
        date_str = date_str.strip()
        
        # Список форматов для попытки парсинга (в порядке приоритета)
        formats = [
            # ISO формат с таймзоной и микросекундами
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            # ISO формат с таймзоной
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            # Обычный формат с секундами
            "%Y-%m-%d %H:%M:%S",
            # Только дата
            "%Y-%m-%d",
        ]
        
        # Сначала пробуем стандартный ISO парсер (он лучше обрабатывает таймзоны)
        try:
            return datetime.datetime.fromisoformat(date_str)
        except ValueError:
            pass
        
        # Затем пробуем наши форматы
        for fmt in formats:
            try:
                dt = datetime.datetime.strptime(date_str, fmt)
                return dt
            except ValueError:
                continue
        
        # Если ничего не подошло, пробуем более гибкие варианты
        try:
            # Пробуем парсить как ISO, но с заменой пробела на T
            if ' ' in date_str and 'T' not in date_str:
                iso_str = date_str.replace(' ', 'T')
                return datetime.datetime.fromisoformat(iso_str)
        except ValueError:
            pass
        
        # Если все попытки не удались
        self.logger.error(f"Не удалось распарсить дату '{date_str}'. "
                         f"Поддерживаемые форматы: ГГГГ-ММ-ДД, ГГГГ-ММ-ДД ЧЧ:ММ:СС, ISO формат")
        return None

    def time_diff(self, dt1, dt2) -> datetime.timedelta:
        """
        Вычисляет разность между двумя datetime объектами с учетом часовых поясов.
        """
        # Парсим строки в datetime если нужно
        if isinstance(dt1, str):
            dt1 = self.parse(dt1)
        if isinstance(dt2, str):
            dt2 = self.parse(dt2)
        
        # Приводим к UTC для корректного сравнения
        dt1_utc = self.to_utc_tz(dt1)
        dt2_utc = self.to_utc_tz(dt2)
        
        return dt2_utc - dt1_utc

    def is_older_than(self, dt, seconds: int) -> bool:
        """
        Проверяет, прошло ли больше указанного количества секунд с момента dt.
        """
        time_diff = self.time_diff(dt, self.now_local())
        return time_diff.total_seconds() > seconds

    def is_newer_than(self, dt, seconds: int) -> bool:
        """
        Проверяет, прошло ли меньше указанного количества секунд с момента dt.
        """
        time_diff = self.time_diff(dt, self.now_local())
        return time_diff.total_seconds() < seconds


