# Примеры работы с tg_messenger сервисом

Messenger сервис — это основной сервис для отправки и управления сообщениями в Telegram. Он поддерживает отправку текста, вложений, клавиатур и предоставляет гибкие возможности для управления сообщениями.

## Основные концепции

### Типы действий

- **`send`** — отправка сообщений с поддержкой текста, вложений и клавиатур
- **`remove`** — удаление сообщений по ID

### Возвращаемые данные

- **`last_message_id`** — ID последнего отправленного сообщения (для действия `send`)
- **`error`** — описание ошибки при неудачном выполнении

### Поддерживаемые вложения

- **Фото/видео** — автоматическое определение типа
- **Документы** — любые файлы
- **Анимации** — GIF файлы
- **Аудио** — аудиофайлы

## Пример 1: Простая отправка сообщения

```yaml
simple_message:
  actions:
    - type: send
      text: "Привет, {username}! Ваш ID: {user_id}"
      callback_edit: false
    - type: send
      text: "✅ Сообщение отправлено с ID: {last_message_id}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- Первое действие отправляет персонализированное сообщение
- Второе действие использует `{last_message_id}` из предыдущего действия
- `chain: completed` гарантирует выполнение только после успешной отправки

## Пример 2: Отправка с вложением

```yaml
message_with_attachment:
  actions:
    - type: send
      text: "📎 Файл для вас"
      attachment: "logo.png"
      callback_edit: false
    - type: send
      text: "✅ Файл отправлен! ID сообщения: {last_message_id}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `attachment: "logo.png"` — автоматическое определение типа файла
- Файл отправляется как вложение к тексту
- `last_message_id` содержит ID сообщения с вложением

## Пример 3: Отправка и удаление сообщения

```yaml
send_and_remove:
  actions:
    - type: send
      text: "📝 Временное сообщение"
      callback_edit: false
    - type: remove
      remove_message_id: "{last_message_id}"
      chain: true
    - type: send
      text: "✅ Временное сообщение удалено"
      callback_edit: false
      chain: completed
```

**Как работает:**
- Первое действие отправляет сообщение
- Второе действие удаляет его по `{last_message_id}`
- Третье действие подтверждает удаление

## Пример 4: Отправка с inline клавиатурой

```yaml
message_with_inline:
  actions:
    - type: send
      text: "Выберите действие:"
      inline:
        - ["Кнопка 1", "Кнопка 2"]
        - [{"Назад": "main_menu"}]
      callback_edit: false
    - type: send
      text: "✅ Клавиатура добавлена к сообщению #{last_message_id}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `inline` создает inline клавиатуру под сообщением
- `{"Назад": "main_menu"}` — кнопка с переходом к сценарию
- Обычные кнопки работают через triggers.yaml

## Пример 5: Отправка с reply клавиатурой

```yaml
message_with_reply:
  actions:
    - type: send
      text: "Используйте клавиатуру для ответа:"
      reply:
        - ["Да", "Нет"]
        - ["Отмена"]
      callback_edit: false
    - type: send
      text: "✅ Reply клавиатура добавлена"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `reply` создает обычную клавиатуру под полем ввода
- Клавиатура остается активной до следующего сообщения
- Для скрытия клавиатуры используйте `reply: []`

## Пример 6: Отправка ответом на сообщение

```yaml
reply_to_message:
  actions:
    - type: send
      text: "📝 Исходное сообщение"
      callback_edit: false
    - type: send
      text: "💬 Ответ на предыдущее сообщение"
      message_reply: true
      callback_edit: false
      chain: true
    - type: send
      text: "✅ Ответ отправлен как reply к сообщению #{last_message_id}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `message_reply: true` отправляет сообщение как ответ
- Использует `message_id` из предыдущего действия
- Создает связь между сообщениями в Telegram

## Пример 7: Отправка в личный чат

```yaml
private_message:
  actions:
    - type: send
      text: "🔐 Секретная информация"
      private_answer: true
      callback_edit: false
    - type: send
      text: "✅ Секретное сообщение отправлено в личный чат"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `private_answer: true` отправляет сообщение в личный чат пользователя
- Работает только для действия `send`
- Полезно для конфиденциальной информации

## Пример 8: Отправка с дополнительным текстом

```yaml
message_with_additional:
  actions:
    - type: send
      text: "Основной текст"
      additional_text: " + {username} + {user_id}"
      callback_edit: false
    - type: send
      text: "✅ Текст расширен дополнительной информацией"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `additional_text` добавляется к основному тексту
- Обрабатывается через placeholder_processor
- Полезно для цепочек действий

## Пример 9: Отправка группы вложений

```yaml
multiple_attachments:
  actions:
    - type: send
      text: "📎 Группа файлов"
      attachment:
        - "logo.png"
        - "file.pdf"
        - "city.mp4"
      callback_edit: false
    - type: send
      text: "✅ Группа файлов отправлена"
      callback_edit: false
      chain: completed
```

**Как работает:**
- Несколько файлов отправляются одним сообщением
- Автоматическая группировка по типам
- Фото/видео группируются в media group

## Пример 10: Удаление конкретного сообщения

```yaml
remove_specific_message:
  actions:
    - type: send
      text: "📝 Сообщение 1"
      callback_edit: false
    - type: send
      text: "📝 Сообщение 2"
      callback_edit: false
      chain: true
    - type: remove
      remove_message_id: "{last_message_id}"
      chain: true
    - type: send
      text: "✅ Второе сообщение удалено"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `remove_message_id` указывает конкретное сообщение для удаления
- Приоритет над `message_id` из action_data
- Полезно для выборочного удаления

## Пример 11: Отправка с HTML разметкой

```yaml
html_formatted_message:
  actions:
    - type: send
      text: |
        <b>Жирный текст</b>
        <i>Курсив</i>
        <u>Подчеркнутый</u>
        <code>Моноширинный</code>
      parse_mode: "HTML"
      callback_edit: false
    - type: send
      text: "✅ HTML разметка применена"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `parse_mode: "HTML"` включает HTML разметку
- Поддерживает основные теги: `<b>`, `<i>`, `<u>`, `<code>`
- Переопределяет глобальную настройку сервиса

## Пример 12: Отправка с плейсхолдерами

```yaml
placeholder_message:
  actions:
    - type: send
      text: "Привет, {username|title}!"
      additional_text: " Ваш статус: {user_status|equals:active|value:Активен|fallback:Неактивен}"
      placeholder: true
      callback_edit: false
    - type: send
      text: "✅ Плейсхолдеры обработаны"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `placeholder: true` включает обработку плейсхолдеров
- `{username|title}` — преобразование в заглавные буквы
- `{user_status|equals:active|value:Активен|fallback:Неактивен}` — условная подстановка

## Пример 13: Удаление сообщения по exact_message_id

```yaml
remove_by_exact_id:
  actions:
    - type: send
      text: "📝 Сообщение для удаления"
      callback_edit: false
    - type: send
      text: "📝 Другое сообщение"
      callback_edit: false
      chain: true
    - type: remove
      remove_message_id: "{last_message_id}"
      chain: true
    - type: send
      text: "✅ Второе сообщение удалено по exact_message_id"
      callback_edit: false
      chain: completed
```

**Как работает:**
- Первое действие отправляет сообщение
- Второе действие отправляет другое сообщение
- Третье действие удаляет второе сообщение по `{last_message_id}`
- Четвертое действие подтверждает удаление

## Пример 14: Изменение сообщения по exact_message_id

```yaml
edit_by_exact_id:
  actions:
    - type: send
      text: "📝 Исходное сообщение для изменения"
      callback_edit: false
    - type: send
      text: "✏️ Изменяю предыдущее сообщение"
      exact_message_id: "{last_message_id}"
      callback_edit: true
      chain: true
    - type: send
      text: "✅ Сообщение изменено по exact_message_id"
      callback_edit: false
      chain: completed
```

**Как работает:**
- Первое действие отправляет исходное сообщение
- Второе действие изменяет предыдущее сообщение через `exact_message_id: "{last_message_id}"`
- `callback_edit: true` включает режим редактирования
- Третье действие подтверждает изменение

## Пример 15: Reply на конкретное сообщение по exact_message_id

```yaml
reply_by_exact_id:
  actions:
    - type: send
      text: "📝 Исходное сообщение"
      callback_edit: false
    - type: send
      text: "💬 Ответ на конкретное сообщение"
      exact_message_id: "{last_message_id}"
      message_reply: true
      callback_edit: false
      chain: true
    - type: send
      text: "✅ Reply отправлен на конкретное сообщение по exact_message_id"
      callback_edit: false
      chain: completed
```

**Как работает:**
- Первое действие отправляет исходное сообщение
- Второе действие отправляет reply на конкретное сообщение через `exact_message_id: "{last_message_id}"`
- `message_reply: true` включает режим ответа
- Третье действие подтверждает отправку reply

## Лучшие практики

### ✅ Рекомендуется
- **Использовать `last_message_id`** для управления сообщениями
- **Применять `remove_message_id`** для точного удаления
- **Использовать `message_reply`** для связывания сообщений
- **Применять `private_answer`** для конфиденциальной информации
- **Использовать `additional_text`** для расширения текста
- **Группировать вложения** для экономии места

### ❌ Запрещено
- **Отправлять пустые сообщения** без текста и вложений
- **Использовать `callback_edit`** с вложениями
- **Смешивать `message_reply`** с `callback_edit`

### ⚠️ Не рекомендуется
- **Отправлять слишком много вложений** (>10 файлов)
- **Использовать сложную HTML разметку** без тестирования
- **Игнорировать обработку ошибок** в цепочках

## Отладка tg_messenger

### Рекомендации по отладке
- **Проверяйте логи сервиса** для диагностики ошибок
- **Используйте `last_message_id`** для отслеживания сообщений
- **Тестируйте различные типы вложений** отдельно
- **Проверяйте права бота** в чатах

### Проверка отправки
```yaml
# Тестовый сценарий для проверки tg_messenger
test_tg_messenger:
  actions:
    - type: send
      text: "Тестовое сообщение"
      callback_edit: false
    - type: send
      text: "ID предыдущего: {last_message_id}"
      callback_edit: false
      chain: true
    - type: remove
      remove_message_id: "{last_message_id}"
      chain: true
    - type: send
      text: "✅ Тест завершен"
      callback_edit: false
      chain: completed
```

## Заключение

Messenger сервис предоставляет мощный механизм для отправки и управления сообщениями. Правильное использование `last_message_id`, `remove_message_id` и различных параметров позволяет создавать гибкие и интерактивные сценарии.

Ключевые моменты:
- **Планируйте управление сообщениями** заранее
- **Используйте `last_message_id`** для связывания действий
- **Применяйте `remove_message_id`** для точного удаления
- **Тестируйте различные типы вложений** отдельно
- **Мониторьте выполнение** через логи сервиса
