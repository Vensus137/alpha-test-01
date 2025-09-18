# Примеры работы с STT (Speech-to-Text)

STT (Speech-to-Text) — это часть сервиса обработки речи для распознавания речи из аудио через SaluteSpeech API. Он позволяет преобразовывать аудиофайлы в текст с поддержкой различных языков и режимов обработки.

## Основные концепции

### Действие `from_speech`

Сервис обрабатывает действия типа `from_speech` из очереди БД. Основные параметры:

- **`audio_file`** — путь к аудиофайлу (приоритет 1)
- **`audio_file_id`** — file_id из Telegram (приоритет 2)
- **`language`** — язык распознавания (по умолчанию "ru-RU")
- **`voice`** — голос для определения языка (опционально)

### Приоритеты источников аудио

1. **Явно указанный файл** — `audio_file: "path/to/file.mp3"`
2. **File ID из Telegram** — `audio_file_id: "CQACAgIAAxkBAAIB..."`  
3. **Вложения сообщения** — автоматический поиск аудио в Telegram вложениях

### Поддерживаемые форматы

- **Аудио файлы**: `.mp3`, `.ogg`, `.wav`, `.m4a`
- **Голосовые сообщения**: `.ogg` (Telegram voice messages)
- **Размер**: до 100 МБ для асинхронного API

## Пример 1: Простое распознавание речи

```yaml
simple_stt:
  actions:
    - type: send
      text: "🎤 Простое распознавание речи"
      callback_edit: false
    - type: from_speech
      audio_file: "speech/examples/Александра.mp3"
      language: "ru-RU"
      chain: true
    - type: send
      text: "✅ Распознавание завершено!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
1. Первое действие отправляет сообщение
2. Второе действие распознает речь из файла
3. Третье и четвертое действия показывают результат

## Пример 2: Распознавание из Telegram вложений

```yaml
stt_from_attachments:
  actions:
    - type: send
      text: "🎤 Распознавание речи из вложения"
      callback_edit: false
    - type: from_speech
      language: "ru-RU"
      chain: true
    - type: send
      text: "✅ Распознавание завершено!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
- Сервис автоматически найдет аудиофайл в вложениях сообщения
- Поддерживает голосовые сообщения и аудиофайлы
- Использует русский язык по умолчанию

## Пример 3: Распознавание с указанным file_id

```yaml
stt_with_file_id:
  actions:
    - type: send
      text: "🎤 Распознавание речи по file_id"
      callback_edit: false
    - type: from_speech
      audio_file_id: "{telegram_file_id}"
      language: "ru-RU"
      placeholder: true
      chain: true
    - type: send
      text: "✅ Распознавание завершено!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
- `{telegram_file_id}` — file_id из Telegram (можно получить из вложений)
- Более эффективно, так как не требует повторной загрузки файла
- Полезно для обработки уже загруженных файлов

## Пример 4: Многоязычное распознавание

```yaml
multilingual_stt:
  actions:
    - type: send
      text: "🌍 Многоязычное распознавание речи"
      callback_edit: false
    - type: from_speech
      audio_file: "speech/examples/Kira.mp3"
      language: "en-US"
      chain: true
    - type: send
      text: "✅ Распознавание завершено!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
- `language: "en-US"` — указывает английский язык
- Поддерживаемые языки: `ru-RU`, `en-US`, `en-GB`, `de-DE`, `fr-FR`, `es-ES`
- Автоматический выбор оптимального API (синхронный/асинхронный)

## Пример 5: Валидация аудиофайла

```yaml
stt_with_validation:
  actions:
    - type: send
      text: "🎤 Распознавание с валидацией"
      callback_edit: false
    - type: validator
      rules:
        attachments:
          - rule: not_empty
        audio_file:
          - rule: not_empty
      placeholder: true
      chain: true
    - type: send
      text: "❌ Отсутствует аудиофайл"
      placeholder: true
      chain: failed
      chain_drop: completed
    - type: from_speech
      audio_file: "{audio_file}"
      language: "ru-RU"
      placeholder: true
      chain: true
    - type: send
      text: "✅ Распознавание завершено!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
1. Валидатор проверяет наличие аудиофайла
2. При ошибке отправляется сообщение и цепочка прерывается
3. При успехе выполняется распознавание речи
4. Результат отправляется пользователю

## Пример 6: Обработка загруженного файла

```yaml
handle_uploaded_audio:
  actions:
    - type: user
      user_state: "waiting_audio_upload"
      chain: true
    - type: send
      text: |
        📤 <b>Загрузите аудиофайл для распознавания</b>
        
        📋 Статус: Ожидание аудиофайла
        🎵 Действие: Загрузите любой аудиофайл (.mp3, .ogg, .wav)
        
        После загрузки файл будет обработан через STT
      inline:
        - [{"🔙 Назад": "main_menu"}]
      callback_edit: false
      chain: completed

# Обработка загруженного аудиофайла
process_uploaded_audio:
  actions:
    - type: validator
      rules:
        attachments:
          - rule: not_empty
      chain: true
    - type: send
      text: "❌ Отсутствует аудиофайл"
      message_reply: true
      chain: failed
      chain_drop: completed
    - type: send
      text: "🎵 Файл получен! Обрабатываем через STT..."
      callback_edit: false
      chain: true
    - type: from_speech
      language: "ru-RU"
      chain: true
    - type: send
      text: "✅ Распознавание завершено!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
1. Устанавливается статус пользователя `waiting_audio_upload`
2. Пользователь загружает аудиофайл
3. Валидатор проверяет наличие файла
4. Выполняется распознавание речи
5. Результат отправляется пользователю

## Пример 7: Команда с извлечением текста

```yaml
stt_command:
  actions:
    - type: send
      text: "🎤 Обрабатываем команду распознавания речи..."
      callback_edit: false
    - type: from_speech
      audio_file: "{event_text|regex:(?<=/stt\\s).+}"
      placeholder: true
      language: "ru-RU"
      chain: true
    - type: send
      text: |
        📝 Файл для распознавания: <code>{audio_file}</code>
        Исходная команда: <code>{event_text}</code>
      placeholder: true
      callback_edit: false
      chain: true
    - type: send
      text: "✅ Распознавание завершено!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
- Обрабатывает команду вида `/stt path/to/file.mp3`
- Извлекает путь к файлу после `/stt` через регулярное выражение
- Показывает извлеченный путь для отладки
- Выполняет распознавание и отправляет результат

## Пример 8: Меню выбора языка

```yaml
language_selection_menu:
  actions:
    - type: send
      text: "🌍 Выберите язык для распознавания речи:"
      inline:
        - [{"🇷🇺 Русский": "stt_russian"}, {"🇺🇸 English": "stt_english"}]
        - [{"🇩🇪 Deutsch": "stt_german"}, {"🇫🇷 Français": "stt_french"}]
      callback_edit: false

# Сценарии для разных языков
stt_russian:
  actions:
    - type: send
      text: "🇷🇺 Распознавание речи на русском языке..."
      callback_edit: false
    - type: from_speech
      language: "ru-RU"
      chain: true
    - type: send
      text: "✅ Распознавание завершено!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed

stt_english:
  actions:
    - type: send
      text: "🇺🇸 Speech recognition in English..."
      callback_edit: false
    - type: from_speech
      language: "en-US"
      chain: true
    - type: send
      text: "✅ Recognition completed!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Result: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed
```

## Пример 9: Обработка ошибок

```yaml
stt_with_error_handling:
  actions:
    - type: send
      text: "🎤 Распознавание речи с обработкой ошибок"
      callback_edit: false
    - type: from_speech
      audio_file: "{user_audio_file|fallback:speech/examples/default.mp3}"
      placeholder: true
      language: "ru-RU"
      chain: true
    - type: send
      text: "✅ Распознавание успешно завершено!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed
    - type: send
      text: "❌ Ошибка распознавания речи: {error}"
      placeholder: true
      callback_edit: false
      chain: failed
    - type: send
      text: "🔄 Попробуйте еще раз или обратитесь к администратору"
      placeholder: true
      callback_edit: false
      chain: ["completed", "failed"]
```

**Как работает:**
- `{user_audio_file|fallback:speech/examples/default.mp3}` — использует файл пользователя или файл по умолчанию
- При успехе отправляется результат распознавания
- При ошибке показывается сообщение об ошибке
- В любом случае отправляется финальное сообщение

## Пример 10: Тестирование разных методов

```yaml
test_stt_methods:
  actions:
    - type: send
      text: |
        📋 <b>Выберите тип тестирования:</b>
        
        🔄 <b>Синхронный метод</b> - быстрая обработка небольших текстов
        ⏳ <b>Асинхронный метод</b> - обработка длинных текстов  
        🎯 <b>Общий тест</b> - переключение статуса и ожидание аудиофайла
        
        <i>Выберите действие ниже:</i>
      inline:
        - [{"🔄 Синхронный STT": "sync_stt_test"}, {"⏳ Асинхронный STT": "async_stt_test"}]
        - [{"🎯 Общий тест": "general_stt_test"}]
        - [{"🔙 Меню": "start_menu"}]
      callback_edit: false

# Синхронный тест STT
sync_stt_test:
  actions:
    - type: send
      text: "🔄 Тест синхронного STT"
      callback_edit: false
    - type: send
      text: |
        📁 Используется файл: <code>speech/examples/Александра.mp3</code>
        ⚙️ Метод: Синхронный API SaluteSpeech
        
        Обрабатываем...
      attachment: 
        - "speech/examples/Александра.mp3"
      callback_edit: false
      chain: true
    - type: from_speech
      audio_file: "speech/examples/Александра.mp3"
      language: "ru-RU"
      chain: true
    - type: send
      text: "✅ Синхронное распознавание завершено!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed

# Асинхронный тест STT
async_stt_test:
  actions:
    - type: send
      text: "⏳ Тест асинхронного STT"
      callback_edit: false
    - type: send
      text: |
        📁 Используется файл: <code>speech/examples/Борис.mp3</code>
        ⚙️ Метод: Асинхронный API SaluteSpeech
        
        Обрабатываем...
      attachment: 
        - "speech/examples/Борис.mp3"
      callback_edit: false
      chain: true
    - type: from_speech
      audio_file: "speech/examples/Борис.mp3"
      language: "ru-RU"
      chain: true
    - type: send
      text: "✅ Асинхронное распознавание завершено!"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed
```

## "Хитрые" приемы с плейсхолдерами

### 1. Извлечение файла из разных источников

```yaml
# Из вложений сообщения
audio_file: "{attachments|first|file}"

# Из команды с параметрами
audio_file: "{event_text|regex:(?<=/stt\\s).+}"

# Из предыдущего действия
audio_file: "{prev_audio_file}"

# С fallback значением
audio_file: "{user_audio|fallback:speech/examples/default.mp3}"
```

### 2. Динамический выбор языка

```yaml
# По роли пользователя
language: "{user_role|equals:admin|value:en-US|fallback:ru-RU}"

# По расширению файла
language: "{audio_file|ends_with:.en.mp3|value:en-US|fallback:ru-RU}"

# Из пользовательских настроек
language: "{user_preferred_language|fallback:ru-RU}"
```

### 3. Условная обработка

```yaml
# Проверяем размер файла перед обработкой
validator:
  rules:
    audio_file_size:
      - rule: less_than
        value: 10485760  # 10MB
```

## Лучшие практики

### ✅ Рекомендуется
- **Использовать валидацию** аудиофайла перед распознаванием
- **Добавлять fallback значения** для всех параметров
- **Обрабатывать ошибки** распознавания речи
- **Использовать кэширование** для часто обрабатываемых файлов
- **Применять правильный язык** для лучшего качества распознавания
- **Тестировать регулярные выражения** отдельно
- **Документировать** сложные плейсхолдеры

### ⚠️ Не рекомендуется
- **Обрабатывать слишком большие файлы** (>100 МБ) — может вызвать таймауты
- **Использовать неподдерживаемые форматы** — может привести к ошибкам API
- **Игнорировать ошибки распознавания** — усложняет отладку
- **Обрабатывать конфиденциальную информацию** — файлы сохраняются на сервере
- **Использовать неправильный язык** — может ухудшить качество распознавания
- **Создавать слишком много запросов** одновременно — может перегрузить систему

## Отладка распознавания речи

### Рекомендации по отладке
- **Проверьте API ключ** SaluteSpeech в настройках
- **Убедитесь в наличии аудиофайла** для распознавания
- **Проверьте логи** сервиса speech_processor
- **Тестируйте регулярные выражения** отдельно
- **Проверьте SSL сертификаты** для российских сервисов

### Проверка параметров
```yaml
# Тестовый сценарий для проверки параметров
test_stt_params:
  actions:
    - type: send
      text: |
        📋 Параметры распознавания:
        • Файл: {audio_file|fallback:Не указан}
        • Язык: {language|fallback:ru-RU}
        • File ID: {audio_file_id|fallback:Не указан}
      callback_edit: false
    - type: from_speech
      audio_file: "{audio_file|fallback:speech/examples/test.mp3}"
      language: "{language|fallback:ru-RU}"
      placeholder: true
      chain: true
    - type: send
      text: "✅ Тест завершен"
      callback_edit: false
      chain: true
    - type: send
      text: "📝 Результат: {speech_to_text}"
      placeholder: true
      callback_edit: false
      chain: completed
```

## Заключение

STT (Speech-to-Text) предоставляет мощный механизм для распознавания речи в сценариях. Правильное использование плейсхолдеров и валидации позволяет создавать гибкие и надежные системы распознавания речи.

Ключевые моменты:
- **Планируйте источники аудио** заранее
- **Используйте валидацию** для проверки файлов
- **Применяйте fallback значения** для всех параметров
- **Обрабатывайте ошибки** распознавания
- **Тестируйте сложные плейсхолдеры** отдельно
- **Мониторьте качество** распознавания
