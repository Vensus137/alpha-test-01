import re
import datetime
from typing import Optional


class ActionParser:
    """
    Универсальный парсер действия из базы: объединяет prev_data, action_data и основные поля в один плоский dict.
    Используется всеми сервисами для получения "плоского" action.
    """
    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.datetime_formatter = kwargs['datetime_formatter']

    def parse_action(self, action: dict) -> dict:
        """
        Объединяет данные из всех источников в плоский словарь с правильным приоритетом.
        Приоритет: prev_data < action_data < placeholder_data < response_data < event_data < основные поля
        """
        merged = {}
        
        # 1. Добавляем prev_data (низший приоритет)
        prev_data = action.get('prev_data')
        if prev_data:
            merged.update(prev_data)
        
        # 2. Добавляем action_data (конфигурация действия)
        action_data = action.get('action_data', {})
        if action_data:
            merged.update(action_data)
        
        # 3. Добавляем placeholder_data (данные после плейсхолдеров, перезаписывает action_data)
        placeholder_data = action.get('placeholder_data')
        if placeholder_data:
            merged.update(placeholder_data)
        
        # 4. Добавляем response_data (результат выполнения действия)
        response_data = action.get('response_data')
        if response_data:
            merged.update(response_data)
        
        # 5. Добавляем event_data (данные события, перезаписывает response_data)
        event_data = action.get('event_data', {})
        if event_data:
            merged.update(event_data)
        
        # 6. Добавляем основные поля действия (служебные поля, высший приоритет)
        merged.update(action)

        # 7. Убираем служебные поля из результата
        self._remove_service_fields(merged)

        # 8. Обрабатываем временные атрибуты (expire, unexpired, duration)
        self._process_time_attributes(merged)

        return merged

    def _remove_service_fields(self, merged: dict):
        """Убирает поля, которые были раскрыты во флэт."""
        # Убираем только те поля, которые мы "раскрывали" во флэт
        fields_to_remove = [
            'event_data', 'action_data', 'prev_data', 'placeholder_data', 'response_data'
        ]
        
        for field in fields_to_remove:
            merged.pop(field, None)

    def _parse_time_string(self, time_string: Optional[str]) -> Optional[int]:
        """Универсальный парсер временных строк в секунды (например, '1w 5d 4h 30m 15s')"""
        if not time_string:
            return None
        
        
        pattern = r"(\d+)\s*(w|d|h|m|s)"
        total_seconds = 0
        for value, unit in re.findall(pattern, time_string):
            value = int(value)
            if unit == 'w':
                total_seconds += value * 604800
            elif unit == 'd':
                total_seconds += value * 86400
            elif unit == 'h':
                total_seconds += value * 3600
            elif unit == 'm':
                total_seconds += value * 60
            elif unit == 's':
                total_seconds += value
        
        result = total_seconds if total_seconds > 0 else None
        return result

    def _process_time_attributes(self, action: dict):
        """Обрабатывает временные атрибуты в действии, добавляя _seconds и _date версии"""
        
        # Получаем время события для вычисления дат
        event_time = self._get_event_time(action)
        
        # Обрабатываем все временные атрибуты
        for time_attr in ['expire', 'unexpired', 'duration', 'time_before', 'time_after']:
            if time_attr in action and isinstance(action[time_attr], str):
                seconds = self._parse_time_string(action[time_attr])
                if seconds is not None:
                    # Добавляем _seconds версию
                    action[f'{time_attr}_seconds'] = seconds
                    
                    # Добавляем _date версию только если она не указана явно
                    date_attr = f'{time_attr}_date'
                    if date_attr not in action and event_time:
                        from datetime import timedelta
                        if time_attr in ['time_before', 'expire', 'unexpired']:
                            # Для time_before, expire, unexpired - вычитаем время
                            calculated_date = event_time - timedelta(seconds=seconds)
                        else:  # time_after, duration
                            # Для time_after, duration - прибавляем время
                            calculated_date = event_time + timedelta(seconds=seconds)
                        
                        # Конвертируем в ISO строку
                        action[date_attr] = calculated_date.isoformat()

    def _get_event_time(self, action: dict):
        """Получает время события для вычисления дат (в локальном времени)"""
        # Пробуем получить время из различных источников
        event_time_str = action.get('event_date') or action.get('created_at') or action.get('timestamp')
        
        if event_time_str:
            try:
                # Используем datetime_formatter для парсинга (работает с локальным временем)
                if isinstance(event_time_str, str):
                    return self.datetime_formatter.parse_to_local(event_time_str)
                elif isinstance(event_time_str, datetime.datetime):
                    return event_time_str
            except Exception as e:
                pass
        
        # Если не удалось получить время события, используем текущее локальное время
        return self.datetime_formatter.now_local()
