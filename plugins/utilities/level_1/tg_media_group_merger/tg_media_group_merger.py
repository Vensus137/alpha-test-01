from typing import Any, Dict, List, Optional


class TgMediaGroupMerger:
    """
    Утилита для объединения событий медиа-групп в единое событие.
    Чистая логика без asyncio - только обработка данных.
    """

    def __init__(self, **kwargs):
        self.logger = kwargs['logger']

    def merge_group_events(self, events: List[Dict[str, Any]], group_field: str = 'media_group_id') -> Optional[Dict[str, Any]]:
        """
        Объединяет события группы в одно событие.
        """
        if not events:
            return None

        # Проверяем, что все события принадлежат к одной группе
        first_group_id = events[0].get(group_field)
        if not first_group_id:
            self.logger.warning(f"⚠️ Первое событие не имеет {group_field}")
            return None
            
        for event in events[1:]:
            current_group_id = event.get(group_field)
            if current_group_id != first_group_id:
                self.logger.warning(
                    f"⚠️ События с разными {group_field}: "
                    f"{first_group_id} vs {current_group_id}. "
                    f"Объединяются только события с одинаковым {group_field}."
                )
                return None

        # Берем первое событие как основу
        combined = events[0].copy()
        
        # Объединяем вложения из всех событий
        all_attachments = []
        event_text = None
        
        for event in events:
            # Добавляем вложения
            attachments = event.get('attachments', [])
            all_attachments.extend(attachments)
            
            # Берем текст из первого события с текстом
            if not event_text and event.get('event_text'):
                event_text = event['event_text']

        # Обновляем объединенное событие
        combined['attachments'] = all_attachments
        if event_text:
            combined['event_text'] = event_text

        # Проверяем консистентность данных
        self._validate_group_consistency(events, combined, group_field)

        return combined

    def _validate_group_consistency(self, events: List[Dict[str, Any]], combined: Dict[str, Any], group_field: str):
        """
        Проверяет консистентность данных в группе событий.
        Логирует предупреждения при несоответствиях.
        """
        group_id = combined.get(group_field)
        
        for event in events[1:]:  # Проверяем все кроме первого
            # Проверяем user_id
            if event.get('user_id') != combined.get('user_id'):
                self.logger.warning(
                    f"⚠️ Разные user_id в группе {group_id}: "
                    f"{combined.get('user_id')} vs {event.get('user_id')}"
                )
            
            # Проверяем chat_id
            if event.get('chat_id') != combined.get('chat_id'):
                self.logger.warning(
                    f"⚠️ Разные chat_id в группе {group_id}: "
                    f"{combined.get('chat_id')} vs {event.get('chat_id')}"
                )
