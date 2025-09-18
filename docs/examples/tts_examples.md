# Примеры работы с TTS (Text-to-Speech)

TTS (Text-to-Speech) — это часть сервиса обработки речи для синтеза речи из текста через SaluteSpeech API. Он позволяет создавать аудиофайлы из текста с различными голосами, скоростью и качеством.

## Основные концепции

### Действие `to_speech`

Сервис обрабатывает действия типа `to_speech` из очереди БД. Основные параметры:

- **`text_to_speech`** — текст для синтеза (обязательный)
- **`voice`** — голос (по умолчанию "baya")
- **`speed`** — скорость воспроизведения (по умолчанию 1.0)
- **`format`** — формат аудио (по умолчанию "opus")
- **`quality`** — качество (по умолчанию "high")
- **`ssml`** — поддержка SSML (по умолчанию false)

### Поддерживаемые голоса

- **👨 Борис** — `Bys_24000`
- **👩 Наталья** — `Nec_24000`
- **👨 Тарас** — `Tur_24000`
- **👩 Марфа** — `May_24000`
- **👨 Сергей** — `Pon_24000`
- **🇺🇸 Kira** — `Kin_24000` (английский)

## Пример 1: Простой синтез речи

```yaml
simple_speech:
  actions:
    - type: send
      text: "🎤 Простой синтез речи"
      callback_edit: false
    - type: to_speech
      text_to_speech: "Привет! Это демонстрация синтеза речи."
      voice: "Bys_24000"
      speed: 1.0
      format: "opus"
      quality: "high"
      chain: true
    - type: send
      text: "✅ Аудиофайл готов!"
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
1. Первое действие отправляет сообщение
2. Второе действие создает аудиофайл
3. Третье действие отправляет готовый файл

## Пример 2: Синтез с извлечением текста из сообщения

```yaml
speech_from_message:
  actions:
    - type: send
      text: "🎤 Синтез речи из сообщения пользователя"
      callback_edit: false
    - type: to_speech
      text_to_speech: "{reply_message_text}"
      placeholder: true
      voice: "Nec_24000"
      chain: true
    - type: send
      text: "✅ Аудиофайл создан из вашего сообщения"
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
- `{reply_message_text}` — извлекает текст из ответного сообщения
- `placeholder: true` — включает обработку плейсхолдеров
- Сервис синтезирует речь из текста пользователя

## Пример 3: Извлечение текста через регулярные выражения

```yaml
speech_with_regex:
  actions:
    - type: send
      text: "🎤 Синтез речи с извлечением текста"
      callback_edit: false
    - type: to_speech
      text_to_speech: "{event_text|regex:(?<=/speech\\s).+}"
      placeholder: true
      voice: "Tur_24000"
      chain: true
    - type: send
      text: "✅ Аудиофайл создан из команды"
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
- `{event_text|regex:(?<=/speech\\s).+}` — извлекает текст после команды `/speech`
- Например: `/speech Привет мир` → синтезируется "Привет мир"
- Регулярное выражение `(?<=/speech\\s).+` означает "все символы после '/speech '"

## Пример 4: Валидация текста перед синтезом

```yaml
speech_with_validation:
  actions:
    - type: send
      text: "🎤 Синтез речи с валидацией"
      callback_edit: false
    - type: validator
      rules:
        text_to_speech:
          - rule: not_empty
          - rule: length_min
            value: 1
      placeholder: true
      chain: true
    - type: send
      text: "❌ Не удалось извлечь текст для синтеза"
      placeholder: true
      chain: failed
      chain_drop: completed
    - type: to_speech
      text_to_speech: "{text_to_speech}"
      placeholder: true
      voice: "May_24000"
      chain: true
    - type: send
      text: "✅ Аудиофайл готов!"
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
1. Валидатор проверяет наличие текста для синтеза
2. При ошибке отправляется сообщение и цепочка прерывается
3. При успехе выполняется синтез речи
4. Готовый файл отправляется пользователю

## Пример 5: Динамический выбор голоса

```yaml
dynamic_voice_selection:
  actions:
    - type: send
      text: "🎤 Динамический выбор голоса"
      callback_edit: false
    - type: to_speech
      text_to_speech: "Привет! Это демонстрация динамического выбора голоса."
      voice: "{selected_voice|fallback:Bys_24000}"
      placeholder: true
      chain: true
    - type: send
      text: "✅ Аудиофайл создан голосом: {selected_voice|fallback:Борис}"
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
- `{selected_voice|fallback:Bys_24000}` — использует выбранный голос или Бориса по умолчанию
- Голос может быть передан через предыдущие действия или пользовательский ввод

## Пример 6: Синтез с SSML

```yaml
speech_with_ssml:
  actions:
    - type: send
      text: "🎤 Синтез речи с SSML"
      callback_edit: false
    - type: to_speech
      text_to_speech: |
        <speak>
          Привет! Это <prosody rate="slow">медленная</prosody> речь.
          А это <prosody rate="fast">быстрая</prosody> речь.
          <break time="1s"/>
          И пауза в секунду.
        </speak>
      voice: "Pon_24000"
      ssml: true
      chain: true
    - type: send
      text: "✅ Аудиофайл с SSML готов!"
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
- `ssml: true` — включает поддержку SSML разметки
- SSML позволяет управлять интонацией, скоростью, паузами
- `<prosody rate="slow">` — замедляет речь
- `<break time="1s"/>` — добавляет паузу

## Пример 7: Команда с извлечением текста

```yaml
speech_command:
  actions:
    - type: send
      text: "🎤 Обрабатываем команду синтеза речи..."
      callback_edit: false
    - type: to_speech
      text_to_speech: "{event_text|regex:(?<=/speech\\s).+}"
      placeholder: true
      voice: "Kin_24000"
      chain: true
    - type: send
      text: |
        📝 Текст для синтеза: <code>{text_to_speech}</code>
        Исходный текст: <code>{event_text}</code>
      placeholder: true
      callback_edit: false
      chain: true
    - type: send
      text: "✅ Аудиофайл готов!"
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed
```

**Как работает:**
- Обрабатывает команду вида `/speech Текст для синтеза`
- Извлекает текст после `/speech` через регулярное выражение
- Показывает извлеченный текст для отладки
- Синтезирует речь и отправляет файл

## Пример 8: Меню выбора голоса

```yaml
voice_selection_menu:
  actions:
    - type: send
      text: "🎤 Выберите голос для синтеза речи:"
      inline:
        - [{"👨 Борис": "speech_boris"}, {"👩 Наталья": "speech_natalia"}]
        - [{"👨 Тарас": "speech_taras"}, {"👩 Марфа": "speech_marfa"}]
        - [{"👨 Сергей": "speech_sergey"}, {"🇺🇸 Kira": "speech_kira"}]
      callback_edit: false

# Сценарии для разных голосов
speech_boris:
  actions:
    - type: send
      text: "🎤 Синтез речи голосом Бориса..."
      callback_edit: false
    - type: to_speech
      text_to_speech: "Привет! Меня зовут Борис. Это демонстрация синтеза речи."
      voice: "Bys_24000"
      speed: 1.0
      format: "opus"
      quality: "high"
      chain: true
    - type: send
      text: "✅ Аудиофайл готов!"
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed

speech_natalia:
  actions:
    - type: send
      text: "🎤 Синтез речи голосом Натальи..."
      callback_edit: false
    - type: to_speech
      text_to_speech: "Здравствуйте! Я Наталья. Это демонстрация синтеза речи."
      voice: "Nec_24000"
      speed: 1.0
      format: "opus"
      quality: "high"
      chain: true
    - type: send
      text: "✅ Аудиофайл готов!"
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed
```

## Пример 9: Синтез с обработкой ошибок

```yaml
speech_with_error_handling:
  actions:
    - type: send
      text: "🎤 Синтез речи с обработкой ошибок"
      callback_edit: false
    - type: to_speech
      text_to_speech: "{user_text|fallback:Текст по умолчанию}"
      placeholder: true
      voice: "Bys_24000"
      chain: true
    - type: send
      text: "✅ Аудиофайл успешно создан!"
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed
    - type: send
      text: "❌ Ошибка синтеза речи: {error}"
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
- `{user_text|fallback:Текст по умолчанию}` — использует текст пользователя или текст по умолчанию
- При успехе отправляется аудиофайл
- При ошибке показывается сообщение об ошибке
- В любом случае отправляется финальное сообщение

## Пример 10: Синтез с кастомными параметрами

```yaml
speech_custom_params:
  actions:
    - type: send
      text: "🎤 Синтез с кастомными параметрами"
      callback_edit: false
    - type: to_speech
      text_to_speech: "{custom_text}"
      voice: "{custom_voice|fallback:Bys_24000}"
      speed: "{custom_speed|fallback:1.0}"
      format: "{custom_format|fallback:opus}"
      quality: "{custom_quality|fallback:high}"
      placeholder: true
      chain: true
    - type: send
      text: |
        ✅ Аудиофайл создан с параметрами:
        • Голос: {custom_voice|fallback:Борис}
        • Скорость: {custom_speed|fallback:1.0}
        • Формат: {custom_format|fallback:opus}
        • Качество: {custom_quality|fallback:high}
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed
```

## "Хитрые" приемы с плейсхолдерами

### 1. Извлечение текста из разных источников

```yaml
# Из сообщения пользователя
text_to_speech: "{reply_message_text}"

# Из команды с параметрами
text_to_speech: "{event_text|regex:(?<=/speech\\s).+}"

# Из предыдущего действия
text_to_speech: "{prev_text}"

# С fallback значением
text_to_speech: "{user_input|fallback:Текст по умолчанию}"
```

### 2. Динамический выбор голоса

```yaml
# По роли пользователя
voice: "{user_role|equals:admin|value:Kin_24000|fallback:Bys_24000}"

# По языку текста
voice: "{text_language|equals:en|value:Kin_24000|fallback:Nec_24000}"

# Из пользовательских настроек
voice: "{user_preferred_voice|fallback:Bys_24000}"
```

### 3. Адаптивная скорость

```yaml
# Медленнее для длинного текста
speed: "{text_length|>100|value:0.8|fallback:1.0}"

# Быстрее для коротких сообщений
speed: "{text_length|<50|value:1.2|fallback:1.0}"
```

### 4. Условный SSML

```yaml
# Включаем SSML только для определенных голосов
ssml: "{voice|in_list:Kin_24000,Pon_24000|value:true|fallback:false}"

# SSML для длинного текста
ssml: "{text_length|>200|value:true|fallback:false}"
```

## Лучшие практики

### ✅ Рекомендуется
- **Использовать валидацию** текста перед синтезом
- **Добавлять fallback значения** для всех параметров
- **Обрабатывать ошибки** синтеза речи
- **Использовать кэширование** для часто используемых фраз
- **Применять SSML** для сложных интонаций
- **Тестировать регулярные выражения** отдельно
- **Документировать** сложные плейсхолдеры

### ⚠️ Не рекомендуется
- **Синтезировать слишком длинный текст** (>1000 символов) — может вызвать таймауты
- **Использовать неподдерживаемые голоса** — может привести к ошибкам API
- **Игнорировать ошибки синтеза** — усложняет отладку
- **Синтезировать конфиденциальную информацию** — файлы сохраняются на сервере
- **Использовать слишком быструю/медленную скорость** (<0.5 или >2.0) — может ухудшить качество
- **Создавать слишком много аудиофайлов** одновременно — может перегрузить систему

## Отладка синтеза речи

### Рекомендации по отладке
- **Проверьте API ключ** SaluteSpeech в настройках
- **Убедитесь в наличии текста** для синтеза
- **Проверьте логи** сервиса speech_processor
- **Тестируйте регулярные выражения** отдельно
- **Проверьте SSL сертификаты** для российских сервисов

### Проверка параметров
```yaml
# Тестовый сценарий для проверки параметров
test_speech_params:
  actions:
    - type: send
      text: |
        📋 Параметры синтеза:
        • Текст: {text_to_speech|fallback:Не указан}
        • Голос: {voice|fallback:По умолчанию}
        • Скорость: {speed|fallback:1.0}
      callback_edit: false
    - type: to_speech
      text_to_speech: "{text_to_speech|fallback:Тестовый текст}"
      voice: "{voice|fallback:Bys_24000}"
      speed: "{speed|fallback:1.0}"
      placeholder: true
      chain: true
    - type: send
      text: "✅ Тест завершен"
      attachment: "{file_path}"
      placeholder: true
      callback_edit: false
      chain: completed
```

## Заключение

Speech Processor предоставляет мощный механизм для синтеза речи в сценариях. Правильное использование плейсхолдеров и валидации позволяет создавать гибкие и надежные системы синтеза речи.

Ключевые моменты:
- **Планируйте извлечение текста** заранее
- **Используйте валидацию** для проверки данных
- **Применяйте fallback значения** для всех параметров
- **Обрабатывайте ошибки** синтеза
- **Тестируйте сложные плейсхолдеры** отдельно
- **Мониторьте качество** синтезированной речи 