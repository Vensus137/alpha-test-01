import os
import re
from typing import Dict, List, Optional

import emoji
import yaml
from unidecode import unidecode

# Максимальная длина callback_data для Telegram (лимит 64 байта, используем 60 символов для запаса)
CALLBACK_DATA_LIMIT = 60

class TgButtonMapper:
    """
    Утилита для маппинга текста кнопок в callback_data и поиска по ним.
    Загружает кнопки из текущего пресета через settings_manager.
    """
    def __init__(self, **kwargs):
        self.logger = kwargs['logger']
        self.settings_manager = kwargs.get('settings_manager')

        button_texts = self._collect_button_texts()
        self.button_map: Dict[str, str] = {}
        self.normalized_map: Dict[str, str] = {}
        self._build_map(button_texts)

    @staticmethod
    def normalize(text: str) -> str:
        text = emoji.replace_emoji(text, replace='')  # удаляем emoji
        text = text.lower().strip()
        text = unidecode(text)
        text = re.sub(r'[^a-z0-9 _-]', '', text)
        text = re.sub(r'\s+', '_', text)
        text = re.sub(r'_+', '_', text).strip('_')
        # Ограничиваем длину до CALLBACK_DATA_LIMIT символов
        return text[:CALLBACK_DATA_LIMIT]

    def _collect_button_texts(self) -> List[str]:
        button_texts = set()
        
        # Определяем текущий пресет
        preset = self.settings_manager.get_current_preset() if self.settings_manager else 'default'
        
        # 1. Сценарии (inline/reply)
        scenarios_dir = os.path.join('config', 'presets', preset, 'scenarios')
        if os.path.isdir(scenarios_dir):
            for root, _, files in os.walk(scenarios_dir):
                for fname in files:
                    if fname.endswith('.yaml') or fname.endswith('.yml'):
                        with open(os.path.join(root, fname), encoding='utf-8') as f:
                            data = yaml.safe_load(f) or {}
                            for scenario in data.values():
                                for action in scenario.get('actions', []):
                                    for key in ['inline', 'reply']:
                                        for row in action.get(key, []):
                                            for btn in row:
                                                if isinstance(btn, str):
                                                    button_texts.add(btn)
                                                elif isinstance(btn, dict):
                                                    button_texts.update(btn.keys())
        
        # 2. Триггеры (callback exact/contains)
        triggers_path = os.path.join('config', 'presets', preset, 'triggers.yaml')
        if os.path.exists(triggers_path):
            with open(triggers_path, encoding='utf-8') as f:
                triggers_data = yaml.safe_load(f) or {}
                callback_exact = triggers_data.get('callback', {}).get('exact', {})
                callback_contains = triggers_data.get('callback', {}).get('contains', {})
                button_texts.update(callback_exact.keys())
                button_texts.update(callback_contains.keys())
        
        return list(button_texts)

    def _build_map(self, button_texts: List[str]):
        for text in button_texts:
            callback = self.normalize(text)
            self.button_map[text] = callback
            self.normalized_map[callback] = text

    def get_button_text(self, callback_data: str) -> Optional[str]:
        # Обрезаем callback_data до лимита для поиска
        trimmed = callback_data[:CALLBACK_DATA_LIMIT]
        return self.normalized_map.get(trimmed)
