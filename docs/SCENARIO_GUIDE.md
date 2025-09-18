# Документация по сценариям

Сценарии описываются в YAML-файлах в папке `config/presets/{preset}/scenarios/`. Каждый сценарий — это ключ (example_scenario), внутри которого actions — список шагов.

## Пример сценария

```yaml
example_scenario:             # Название сценария, должно быть уникальным для всех сценариев
  actions:
    - type: "send"            # Тип действия (должен совпадать с action_type в сервисах)
      text: "Пример приветствия"
      inline:                 # Inline-клавиатура (опционально)
        - ["Кнопка 1", {"Назад": "main_menu"}, "Кнопка 2"]
        # "Кнопка 1" и "Кнопка 2" — обычные кнопки (callback_data = нормализованный текст)
        # {"Назад": "main_menu"} — явный переход к сценарию main_menu (callback_data = :main_menu)
        - ["Кнопка 3"]
    - type: "scenario"        # Вызов другого сценария (например, системного)
      value: "system.api"     # Путь к сценарию, который будет развёрнут на этом месте
    - type: "send"
      text: "Ещё одно сообщение"
      reply:                  # Reply-клавиатура (опционально)
        - ["Назад", "Меню"]
      callback_edit: true     # Редактирование исходного сообщения, которое создало событие
    - type: "custom_action"   # Можно добавить любые поддерживаемые действия
      param1: "value1"
      param2: "value2"
    - type: "wait_for_reply"  # Пример цепного действия (будет заблокировано до завершения предыдущего)
      prompt: "Введите ответ"
      chain: true             # Это действие будет заблокировано (ожидает завершения предыдущего)
    - type: "send"            # Секретное сообщение только для администраторов с плейсхолдером {...}
      text: "🔐 Секретная информация для администраторов! {secret_info}"
      required_role: ["admin", "moderator"]     # Доступ к ролям admin ИЛИ moderator
      chain: [completed]      # Это действие будет заблокировано (ожидает упешного завершения предыдущего)
    - type: "send"            # Сверхсекретное действие только с нужными разрешениями
      text: "🚀 Сверхсекретная операция выполнена!"
      message_reply: true     # Отправить сообщение ответом на исходное
      attachment:             # Можно добавлять вложения
        - "test.png"
        - ["file1.pdf",file2.pdf]
      required_permission: ["manage_users", "system_commands"]  # Нужны ВСЕ разрешения
```

<details>
<summary>Пояснения</summary>

- Каждый сценарий — это ключ (example_scenario), внутри которого actions — список шагов.
- type — тип действия, должен совпадать с action_type, поддерживаемым сервисами.
- **Inline-кнопки**:
    - Строка — обычная кнопка, работает по triggers.yaml.
    - Словарь {"Текст": "сценарий"} — явный переход к сценарию (callback_data = :сценарий).
- type: scenario — позволяет вставить действия другого сценария (или сценариев) по указанному пути (value).
- chain: true — действие будет заблокировано (ожидать завершения предыдущего).
- **Ролевая модель**:
    - `required_role` — список требуемых ролей (достаточно одной из списка).
    - `required_permission` — список требуемых разрешений (нужны ВСЕ из списка).
- Приоритет: `required_permission` > `required_role`. Если указаны оба — проверяются только permissions.
- Параметры действия (text, state, inline, reply и т.д.) зависят от типа действия и описаны в конфиге соответствующего сервиса.
- Можно использовать любые поддерживаемые действия и параметры.
- Для действий типа send можно использовать параметр **attachment**:
    - attachment: "file.jpg" — вложение одного файла (фото, документ, видео и т.д.)
    - attachment: ["file1.jpg", "file2.pdf"] — массив вложений (отправка группы файлов)
    - Можно комбинировать фото, документы, видео и другие типы файлов, вложения будут отправлены корректно по типу.
    - Поддерживаются как одиночные, так и множественные вложения, а также явное указание типа (см. config сервиса messenger).

</details>

<details>
<summary>Атрибут chain</summary>

Атрибут `chain` управляет зависимостью выполнения действия от статуса предыдущего действия в цепочке:

- `chain: true` или `chain: "any"` — действие будет выполнено после любого завершения предыдущего (completed, failed, drop).
- `chain: false` (или отсутствие chain) — действие не зависит от предыдущего, выполняется сразу.
- `chain: "completed"` — действие будет выполнено только если предыдущее завершилось успешно.
- `chain: "failed"` — действие будет выполнено только если предыдущее завершилось с ошибкой.
- `chain: "drop"` — действие будет выполнено только если предыдущее было пропущено (drop).
- `chain: ["completed", "failed"]` — действие будет выполнено, если предыдущее завершилось любым из указанных статусов.

**Важно:** Если статус предыдущего действия не входит в список `unlock_statuses`, следующее действие будет переведено в статус `drop` (пропущено).

</details>

## Список действий

### any

**🔧 Плагин:** placeholder_processor (utilities)

**⚡ Доступно:** Pro

**📝 Описание:** Возможность замены плейсхолдеров и переопределения любых атрибутов в действиях сценариев через универсальную систему подстановки значений.

**⚙️ Параметры для сценария (config_attrs):**
- `placeholder` (boolean): Если true — данные действия будут обработаны через placeholder_processor перед использованием.
По умолчанию false.



<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "any"
  placeholder: true
```

</details>
<details>
<summary>📖 Дополнительная информация</summary>

Синтаксис плейсхолдеров: 
  - {field_name}
  - {field_name|modifier:param}
  - {field_name|modifier1:param1|modifier2:param2}
  - Вложенные плейсхолдеры в параметрах модификаторов: {field|modifier:{inner}}
  - Точечная нотация для доступа к вложенным полям: {object.field.subfield}

Арифметические операции:
  - |+value - сложение
  - |-value - вычитание
  - |*value - умножение
  - |/value - деление
  - |%value - остаток от деления
  
Преобразования:
  - |tags - преобразование в теги (@user)
  - |list - маркированный список (• item)
  - |comma - через запятую (item1, item2)
  - |upper - верхний регистр
  - |lower - нижний регистр
  - |title - заглавные буквы каждого слова
  - |capitalize - первая заглавная буква
  - |length - подсчет длины строки (количество символов)
  - |regex:pattern - извлечение данных по регулярному выражению
  
Форматирование:
  - |truncate:length - обрезка текста с ...
  - |format:timestamp - преобразование в timestamp
  - |format:date - формат даты (dd.mm.yyyy)
  - |format:time - формат времени (hh:mm)
  - |format:datetime - полный формат даты и времени
  - |format:currency - форматирование валюты (1000.00 ₽)
  - |format:percent - форматирование процентов (25.5%)
  - |format:number - форматирование чисел (1234.56)
  - |case:type - преобразование регистра (upper/lower/title/capitalize)
  
Условные модификаторы:
  - |equals:value - проверка равенства
  - |in_list:item1,item2 - проверка вхождения в список
  - |true - проверка истинности
  - |value:result - возврат значения при истинности
  
Fallback:
  - |fallback:value - замена при отсутствии значения

Примеры использования:
  - {user_id} - простая замена
  - {username|fallback:Гость} - с дефолтом
  - {seconds|/3600} - деление на 3600
  - {users|tags|list} - цепочка модификаторов
  - {price|*0.9|format:currency} - скидка с форматированием
  - {status|equals:active|value:Активен|fallback:Неактивен} - условная подстановка
  - {event_text|regex:(?:\\d+\\s*[dhms]\\s*)+} - извлечение времени из текста
  - {text|length} - подсчет символов в тексте
  - Привет, {username}! Ваш ID: {user_id} - смешанный текст
  - {|fallback:100} - пустое поле с дефолтом 
  - {reply_entity_id|fallback:{user_forward_id}} - вложенный плейсхолдер в параметре fallback
  - {a|+{b}} - вложенный плейсхолдер в параметре арифметического модификатора
  - {created|format:{fmt}} - вложенный плейсхолдер как тип форматирования
  - {status|equals:{expected}|value:OK|fallback:BAD} - вложенный плейсхолдер в условном модификаторе
  - {promo_data.promo_code} - доступ к полю promo_code внутри объекта promo_data
  - {user.profile.name|fallback:Неизвестный} - точечная нотация с fallback
  - {response.data.items|length} - доступ к длине массива items внутри data
  - {event.user.id|equals:123|value:Админ|fallback:Пользователь} - точечная нотация с условными модификаторами

</details>

---

### any

**🔧 Плагин:** trigger_manager (utilities)

**🆓 Доступно:** Base

**📝 Описание:** Универсальные настройки для всех действий сценариев: управление цепочками действий, ограничения доступа, роли и разрешения.

**⚙️ Параметры для сценария (config_attrs):**
- `chain` (['boolean', 'string', 'array']): Управляет зависимостью выполнения действия от статуса предыдущего действия в цепочке (подробнее см. в сценариях). 

- `chain_drop` (['string', 'array']): Статусы, при которых цепочка действий прерывается.
Можно указать строку ("failed") или массив статусов (["failed", "error"]).
Если текущий статус действия входит в этот список - вся цепочка прерывается.
По умолчанию null (цепочка не прерывается).



<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "any"
  chain: ...
  chain_drop: ...
```

</details>
<details>
<summary>📖 Дополнительная информация</summary>

Эти параметры применяются ко всем действиям сценариев и позволяют:
- Управлять зависимостями между действиями в цепочке
- Прерывать цепочку действий при определенных статусах

</details>

---

### any

**🔧 Плагин:** permission_manager (utilities)

**⚡ Доступно:** Pro

**📝 Описание:** Атрибуты доступа, которые могут использоваться в любых действиях сценариев для ограничения доступа пользователей

**⚙️ Параметры для сценария (config_attrs):**
- `group_admin` (boolean): Если true — действие будет выполнено только если пользователь, вызвавший действие, является администратором группы (chat_id).
По умолчанию false. Используется для ограничения доступа к действиям только для админов групповых чатов.
При отсутствии прав доступа действие переводится в статус "failed".

- `required_role` (['string', 'array']): Требуемая роль пользователя для выполнения действия. Можно указать строку ("admin") или массив ролей (["admin", "moderator"]).
Достаточно наличия хотя бы одной роли из списка.
Если не указано — доступ открыт для всех.
При отсутствии требуемых ролей действие переводится в статус "failed".

- `required_permission` (['string', 'array']): Требуемые разрешения пользователя для выполнения действия. Можно указать строку ("manage_users") или массив разрешений (["manage_users", "edit_messages"]).
Пользователь должен иметь все указанные разрешения.
Если не указано — доступ открыт для всех.
При отсутствии требуемых разрешений действие переводится в статус "failed".



<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "any"
  group_admin: true
  required_role: ...
  required_permission: ...
```

</details>
<details>
<summary>📖 Дополнительная информация</summary>

Эти атрибуты применяются ко всем действиям сценариев и позволяют:
- Ограничивать доступ по ролям и разрешениям
- Контролировать выполнение только для администраторов групп
- Создавать многоуровневую систему безопасности

Атрибуты обрабатываются permission_manager при выполнении действий через trigger_manager.
Логика проверки: сначала проверяются основные права (роли/разрешения), затем дополнительно group_admin если требуется.

</details>

---

### send

**🔧 Плагин:** tg_messenger (services)

**🆓 Доступно:** Base

**📝 Описание:** Отправить сообщение в чат или отредактировать существующее (если callback_edit=true).

**⚙️ Параметры для сценария (config_attrs):**
- `text` (string): Текст сообщения (поддерживает HTML-разметку и плейсхолдеры {имя_поля})
- `additional_text` (string): Дополнительный текст, который добавляется к основному тексту перед обработкой плейсхолдеров. Полезно для цепочек действий, где нужно добавить статичный текст к динамическому содержимому.
- `inline` (array): Inline-клавиатура (массив массивов строк или словарей)
- `reply` (array): Reply-клавиатура (массив массивов строк)
- `message_reply` (boolean): Если true — сообщение будет отправлено как reply (ответ) на исходное сообщение (reply_to_message_id из message_id)
- `exact_message_id` (integer): Точный ID сообщения для подмены. Если указан, заменяет message_id из action_data для редактирования, reply и других операций
- `callback_edit` (boolean): Если true — редактировать исходное сообщение вместо отправки нового
- `remove` (boolean): Если true — удалить исходное сообщение после отправки нового
- `attachment` (['string', 'object', 'array']): Вложение (файл, медиа, музыка и т.п.). Можно указывать несколько раз для отправки нескольких вложений.
- `parse_mode` (string): Режим разметки для сообщения (HTML или MarkdownV2). Если указан, переопределяет глобальный parse_mode из настроек сервиса.
- `private_answer` (boolean): Если true — сообщение будет отправлено в личный чат пользователя (user_id), а не в группу. Работает только для типа send.
- `placeholder` (boolean): Если false — отключить обработку плейсхолдеров для этого сообщения (имеет приоритет над глобальной настройкой enable_placeholder)


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "send"
  text: "пример текста"
  additional_text: "пример текста"
  inline: ["item1", "item2"]
  reply: ["item1", "item2"]
  message_reply: true
  exact_message_id: 123
  callback_edit: true
  remove: true
  attachment: ...
  parse_mode: "пример текста"
  private_answer: true
  placeholder: true
```

</details>
<details>
<summary>📖 Дополнительная информация</summary>

Поддерживает HTML-разметку: <b>жирный</b>, <i>курсив</i>, <u>подчеркнутый</u>

Inline кнопки (inline) поддерживают универсальный формат:

• "Текст" — обычная кнопка с callback_data (нормализованный текст)
• {"Текст": "scenario_name"} — переход к сценарию (callback_data: :scenario_name)
• {"Текст": "https://example.com"} — URL кнопка (если значение похоже на ссылку)

Примеры inline кнопок:
  - [{"Назад": "start_menu"}, {"Помощь": "help"}]
  - [{"🌐 Сайт": "https://example.com"}, {"📞 Контакты": "https://t.me/your_bot"}]
  - [{"✅ Подтвердить": "confirm_action"}, {"❌ Отмена": "cancel_action"}]

Примечание: URL кнопки не отправляют callback в бота, пользователь просто переходит по ссылке.

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `chat_id`
- `user_id`
- `message_id`

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `last_message_id` (integer): ID последнего отправленного сообщения (только для успешных операций)
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### remove

**🔧 Плагин:** tg_messenger (services)

**🆓 Доступно:** Base

**📝 Описание:** Удалить сообщение из чата. Использует message_id из action_data.

**⚙️ Параметры для сценария (config_attrs):**
- `remove_message_id` (integer): ID сообщения для удаления. Если указан, удаляет именно это сообщение, иначе использует message_id из action_data.


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "remove"
  remove_message_id: 123
```

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `chat_id`
- `message_id`

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### user

**🔧 Плагин:** user_manager (services)

**🆓 Доступно:** Base

**📝 Описание:** Установить состояние пользователя (user_state) в базе данных

**⚙️ Параметры для сценария (config_attrs):**
- `user_state` (string): Тип состояния пользователя (например, feedback, bug_report). Пустая строка ('') для сброса состояния.
- `expire` (string): Срок действия ссылки (например, '2d 3h 15m').


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "user"
  user_state: "пример текста"
  expire: "пример текста"
```

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `user_id`

</details>

---

### history

**🔧 Плагин:** tg_event_history (services)

**⚡ Доступно:** Pro

**📝 Описание:** Получение истории сообщений из чата

**⚙️ Параметры для сценария (config_attrs):**
- `from_chat` (integer): ID чата для получения истории (по умолчанию текущий чат из action)
- `chat_type` (string): Тип чата: 'user', 'chat', 'channel' или пустое значение для умного автоопределения
- `limit` (integer): Количество сообщений для получения
- `time_before` (string): Период до времени события в формате '1d 2h 30m' (опционально, автоматически создает time_before_date)
- `time_before_date` (string): Явно указанная дата для time_before в формате ISO (опционально, приоритет над автоматическим вычислением)
- `reverse` (boolean): Обрабатывать сообщения в обратном порядке (от старых к новым, по умолчанию true)
- `offset_id` (integer): ID сообщения для offset - начать получение с сообщения после указанного ID (для пагинации)


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "history"
  from_chat: 123
  chat_type: "пример текста"
  limit: 123
  time_before: "пример текста"
  time_before_date: "пример текста"
  reverse: true
  offset_id: 123
```

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `messages_processed` (integer): Количество обработанных сообщений
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### gigachat

**🔧 Плагин:** gigachat_service (services)

**⚡ Доступно:** Pro

**📝 Описание:** Получение ответа от GigaChat на основе системного промпта и сообщения

**⚙️ Параметры для сценария (config_attrs):**
- `system_prompt` (string): Системный промпт для настройки поведения модели
- `user_message` (string): Сообщение пользователя
- `model` (string): Модель GigaChat (переопределяет настройку по умолчанию)
- `temperature` (float): Температура генерации (переопределяет настройку по умолчанию)
- `max_tokens` (integer): Максимальное количество токенов (переопределяет настройку по умолчанию)


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "gigachat"
  system_prompt: "пример текста"
  user_message: "пример текста"
  model: "пример текста"
  temperature: 123
  max_tokens: 123
```

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `response_text` (string): Ответ от GigaChat в исходной разметке Markdown (без экранирования)
- `response_text_md2` (string): Ответ от GigaChat в разметке MarkdownV2 (экранированный для Telegram)
- `model_used` (string): Модель, которая была использована
- `tokens_used` (integer): Количество использованных токенов
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### create_promo

**🔧 Плагин:** promo_manager (services)

**⚡ Доступно:** Pro

**📝 Описание:** Создание промокода (ручное или автогенерация)

**⚙️ Параметры для сценария (config_attrs):**
- `promo_code` (string): Код промокода (опционально, если не указан - генерируется автоматически)
- `target_user_id` (integer): ID пользователя для привязки (опционально, 'Any'/'Null' = для всех, по умолчанию user_id из ивента или глобальный согласно настройке default_global_promos)
- `started_at` (string): Дата начала действия (опционально, ISO формат, по умолчанию - текущее время)
- `expired_at` (string): Дата окончания действия (опционально, ISO формат)
- `expire` (string): Срок действия от текущего времени (например, '2d 4h 30m')
- `permanent` (boolean): Постоянный промокод (действует с 2000 по 2999 год)
- `length` (integer): Длина кода (6-16 символов)
- `use_digits` (boolean): Использовать цифры
- `use_letters` (boolean): Использовать буквы
- `salt` (string): Соль для детерминированной генерации (по умолчанию 'default')
- `use_random` (boolean): Случайная генерация (true) или детерминированная (false)


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "create_promo"
  promo_code: "пример текста"
  target_user_id: 123
  started_at: "пример текста"
  expired_at: "пример текста"
  expire: "пример текста"
  permanent: true
  length: 123
  use_digits: true
  use_letters: true
  salt: "пример текста"
  use_random: true
```

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `promo_name`

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `success` (boolean): Успех операции
- `promo_id` (integer): ID созданного промокода
- `promo_code` (string): Созданный код промокода
- `promo_name` (string): Название промокода
- `started_at` (string): Дата начала действия
- `expired_at` (string): Дата окончания действия
- `target_user_id` (integer): ID пользователя для привязки (None = для всех)
- `permanent` (boolean): Постоянный промокод
- `use_digits` (boolean): Использовать цифры при генерации
- `use_letters` (boolean): Использовать буквы при генерации
- `salt` (string): Соль для детерминированной генерации
- `use_random` (boolean): Случайная генерация (true) или детерминированная (false)
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### modify_promo

**🔧 Плагин:** promo_manager (services)

**⚡ Доступно:** Pro

**📝 Описание:** Изменение любых полей промокода

**⚙️ Параметры для сценария (config_attrs):**
- `promo_code` (string): Новый код промокода (опционально)
- `promo_name` (string): Новое название (опционально)
- `target_user_id` (integer): Новый ID пользователя (опционально, 'Any'/'Null' = для всех)
- `started_at` (string): Новая дата начала (опционально, ISO формат)
- `expired_at` (string): Новая дата окончания (опционально, ISO формат)
- `expire` (string): Новый срок действия от текущего времени (например, '2d 4h 30m')
- `permanent` (boolean): Сделать промокод постоянным (действует с 2000 по 2999 год)


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "modify_promo"
  promo_code: "пример текста"
  promo_name: "пример текста"
  target_user_id: 123
  started_at: "пример текста"
  expired_at: "пример текста"
  expire: "пример текста"
  permanent: true
```

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `promo_id`

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `success` (boolean): Успех операции
- `promo_id` (integer): ID измененного промокода
- `promo_code` (string): Код промокода
- `promo_name` (string): Название промокода
- `started_at` (string): Дата начала действия
- `expired_at` (string): Дата окончания действия
- `target_user_id` (integer): ID пользователя для привязки (None = для всех)
- `permanent` (boolean): Постоянный промокод
- `use_digits` (boolean): Использовать цифры при генерации
- `use_letters` (boolean): Использовать буквы при генерации
- `salt` (string): Соль для детерминированной генерации
- `use_random` (boolean): Случайная генерация (true) или детерминированная (false)
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### check_promo

**🔧 Плагин:** promo_manager (services)

**⚡ Доступно:** Pro

**📝 Описание:** Проверка доступности промокода для пользователя


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "check_promo"
```

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `promo_code`
- `user_id`

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `promo_available` (boolean): Доступен ли промокод
- `promo_data` (object): Данные промокода (если доступен)
- `reason` (string): Причина недоступности (если не доступен)
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### promo_management

**🔧 Плагин:** promo_manager (services)

**⚡ Доступно:** Pro

**📝 Описание:** Управление промокодами (просмотр списка, детали)

**⚙️ Параметры для сценария (config_attrs):**
- `operation` (string): Тип операции: 'list' или 'details'
- `name_pattern` (string): Фильтр по названию промокода (частичное совпадение)
- `user_filter` (string): Фильтр по пользователю (username с @ или без, user_id)
- `promo_code` (string): Фильтр по коду промокода
- `date_from` (string): Фильтр по дате создания
- `date_to` (string): Фильтр по дате создания
- `expired_before` (string): Фильтр по дате истечения
- `expired_after` (string): Фильтр по дате истечения
- `limit` (integer): Максимальное количество промокодов для отображения
- `event_text` (string): ID промокода для операции 'details'
- `promo_id` (integer): ID промокода для операции 'details' (приоритет над event_text)


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "promo_management"
  operation: "пример текста"
  name_pattern: "пример текста"
  user_filter: "пример текста"
  promo_code: "пример текста"
  date_from: "пример текста"
  date_to: "пример текста"
  expired_before: "пример текста"
  expired_after: "пример текста"
  limit: 123
  event_text: "пример текста"
  promo_id: 123
```

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `response_text` (string): Форматированный текст результата
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### request_management

**🔧 Плагин:** request_manager (services)

**⚡ Доступно:** Pro

**📝 Описание:** Управление запросами (просмотр списка, детали)

**⚙️ Параметры для сценария (config_attrs):**
- `operation` (string): Тип операции: 'list' или 'details'
- `time_before` (integer): Фильтр по времени (в секундах от текущего момента)
- `from_date` (string): Фильтр по дате (ISO формат)
- `request_name` (string): Фильтр по названию типа запроса
- `limit` (integer): Максимальное количество запросов для отображения
- `event_text` (string): ID запроса для операции 'details'


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "request_management"
  operation: "пример текста"
  time_before: 123
  from_date: "пример текста"
  request_name: "пример текста"
  limit: 123
  event_text: "пример текста"
```

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `operation`

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `response_text` (string): Форматированный текст результата
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### request

**🔧 Плагин:** request_service (services)

**⚡ Доступно:** Pro

**📝 Описание:** Обработка и сохранение запроса пользователя

**⚙️ Параметры для сценария (config_attrs):**
- `event_text` (string): Текст запроса пользователя
- `attachments` (array): Вложения к запросу
- `request_name` (string): Название типа запроса
- `request_info` (string): Дополнительная информация о запросе


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "request"
  event_text: "пример текста"
  attachments: ["item1", "item2"]
  request_name: "пример текста"
  request_info: "пример текста"
```

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `user_id`
- `chat_id`

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `request_text` (string): Текст запроса пользователя
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### to_speech

**🔧 Плагин:** salute_speech (services)

**⚡ Доступно:** Pro

**📝 Описание:** Синтез речи из текста (Text-to-Speech)

**⚙️ Параметры для сценария (config_attrs):**
- `text_to_speech` (string): Текст для синтеза речи
- `voice` (string): Голос для синтеза (baya, aidar, kseniya, dasha, etc.)
- `format` (string): Формат аудио (oggopus, wav, mp3)
- `ssml` (boolean): Использовать SSML разметку в тексте
- `max_text_length` (integer): Максимальная длина текста (переопределяет глобальную настройку)


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "to_speech"
  text_to_speech: "пример текста"
  voice: "пример текста"
  format: "пример текста"
  ssml: true
  max_text_length: 123
```

</details>
<details>
<summary>📖 Дополнительная информация</summary>

Синтезирует речь из текста и сохраняет аудиофайл.

Поддерживаемые голоса SaluteSpeech:
  - Женские голоса:
    - Nec_24000 - Наталья (24 кГц, высокое качество)
    - Nec_8000 - Наталья (8 кГц, стандартное качество)
    - May_24000 - Марфа (24 кГц, высокое качество)
    - May_8000 - Марфа (8 кГц, стандартное качество)
    - Ost_24000 - Александра (24 кГц, высокое качество)
    - Ost_8000 - Александра (8 кГц, стандартное качество)
  
  - Мужские голоса:
    - Bys_24000 - Борис (24 кГц, высокое качество)
    - Bys_8000 - Борис (8 кГц, стандартное качество)
    - Tur_24000 - Тарас (24 кГц, высокое качество)
    - Tur_8000 - Тарас (8 кГц, стандартное качество)
    - Pon_24000 - Сергей (24 кГц, высокое качество)
    - Pon_8000 - Сергей (8 кГц, стандартное качество)
  
  - Английская речь:
    - Kin_24000 - Kira (24 кГц, английская речь, высокое качество)
    - Kin_8000 - Kira (8 кГц, английская речь, стандартное качество)
  
Примечание: 
  - 24 кГц = высокое качество, больше размер файла
  - 8 кГц = стандартное качество, меньше размер файла
  - Рекомендуется использовать 24 кГц для лучшего звучания

Поддерживаемые форматы:
  - oggopus - OGG с кодеком Opus (рекомендуется, лучшее качество)
  - wav - WAV без сжатия (большой размер, высокое качество)
  - mp3 - MP3 сжатие (универсальный формат)

SSML разметка (если включена):
  - <speak>текст</speak> - основной тег
  - <break time="1s"/> - пауза (0.1s, 0.5s, 1s, 2s, 3s)
  - <prosody rate="slow">текст</prosody> - скорость (x-slow, slow, medium, fast, x-fast)
  - <prosody pitch="high">текст</prosody> - высота тона (x-low, low, medium, high, x-high)
  - <prosody volume="loud">текст</prosody> - громкость (silent, x-soft, soft, medium, loud, x-loud)
  - <emphasis level="strong">текст</emphasis> - ударение (strong, moderate, reduced)
  - <say-as interpret-as="cardinal">123</say-as> - произношение чисел
  - <say-as interpret-as="date">2024-01-01</say-as> - произношение дат

Источник: https://developers.sber.ru/docs/ru/salutespeech/guides/synthesis/voices

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `file_path` (string): Путь к сохраненному аудиофайлу
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### from_speech

**🔧 Плагин:** salute_speech (services)

**⚡ Доступно:** Pro

**📝 Описание:** Распознавание речи из аудиофайла (Speech-to-Text) - гибридный режим

**⚙️ Параметры для сценария (config_attrs):**
- `audio_file` (string): Путь к аудиофайлу (опционально, по умолчанию берется из вложений)
- `audio_file_id` (string): File ID аудиофайла в Telegram (опционально, приоритет выше чем поиск в вложениях)
- `language` (string): Язык распознавания (ru-RU, en-US)
- `max_audio_duration` (integer): Максимальная длительность аудио в секундах (переопределяет глобальную настройку)
- `force_async` (boolean): Принудительно использовать асинхронный режим (по умолчанию - автоматический выбор)


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "from_speech"
  audio_file: "пример текста"
  audio_file_id: "пример текста"
  language: "пример текста"
  max_audio_duration: 123
  force_async: true
```

</details>
<details>
<summary>📖 Дополнительная информация</summary>

Распознает речь из аудиофайла и возвращает текст.

Гибридный режим работы:
  - Синхронный API: для аудио до 1 минуты (быстрый ответ)
  - Асинхронный API: для аудио 1-10 минут (поддержка длинных записей)
  - Автоматический выбор режима на основе длительности

Приоритет поиска аудиофайла:
  1. audio_file - явно указанный путь к файлу
  2. audio_file_id - указанный file_id в Telegram
  3. Автоматический поиск в вложениях attachments:
    - Сначала ищет voice (голосовые сообщения)
    - Затем ищет audio (аудиофайлы)

Поддерживаемые форматы аудио:
  - wav - WAV без сжатия
  - mp3 - MP3 сжатие
  - ogg - OGG с кодеком Opus
  - m4a - AAC в контейнере M4A
  - flac - FLAC без потерь

Поддерживаемые языки:
  - ru-RU - Русский язык
  - en-US - Английский язык

Ограничения по режимам:
  - Синхронный API:
    - Максимальная длительность: 1 минута
    - Максимальный размер файла: 2 МБ
    - Мгновенный ответ
  
  - Асинхронный API:
    - Максимальная длительность: 10 минут
    - Максимальный размер файла: 100 МБ
    - Ответ через 5-30 секунд (зависит от длины аудио)

Автоматическое кэширование результатов

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `chat_id`
- `user_id`
- `message_id`

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `speech_to_text` (string): Распознанный текст
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### restrict

**🔧 Плагин:** tg_group_manager (services)

**⚡ Доступно:** Pro

**📝 Описание:** Ограничить права пользователя в группе (мут)

**⚙️ Параметры для сценария (config_attrs):**
- `duration_seconds` (integer): Длительность ограничения в секундах
- `can_send_messages` (boolean): Если true - пользователь может отправлять сообщения, если false - ограничен
- `restrict_user_id` (integer): ID пользователя для ограничения (приоритет над username)
- `restrict_username` (string): Username пользователя для ограничения (без @, используется если нет restrict_user_id)


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "restrict"
  duration_seconds: 123
  can_send_messages: true
  restrict_user_id: 123
  restrict_username: "пример текста"
```

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `chat_id`

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `restrict_user_id` (integer): ID пользователя, к которому применено ограничение
- `restrict_username` (string): Username пользователя, к которому применено ограничение
- `duration_seconds` (integer): Длительность ограничения в секундах
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### invite_link

**🔧 Плагин:** tg_link_generator (services)

**⚡ Доступно:** Pro

**📝 Описание:** Создать новую пригласительную ссылку для группы.

**⚙️ Параметры для сценария (config_attrs):**
- `member_limit` (integer): Максимальное количество пользователей по ссылке.
- `expire` (string): Срок действия ссылки (например, '2d 3h 15m').
- `requires_approval` (boolean): Требуется ли одобрение вступления по ссылке.
- `cleanup` (boolean): Если true — удалить все ссылки, указанные в тексте сообщения.
- `group_admin` (boolean): Если true — выполнять действие только если пользователь, вызвавший действие, является администратором группы.


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "invite_link"
  member_limit: 123
  expire: "пример текста"
  requires_approval: true
  cleanup: true
  group_admin: true
```

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `chat_id`

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `invite_link` (string): Созданная пригласительная ссылка
- `invite_links_deleted` (array): Список удаленных ссылок (режим cleanup)
- `invite_links_failed` (array): Список ссылок, которые не удалось удалить (режим cleanup)
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### copy

**🔧 Плагин:** tg_message_copy (services)

**⚡ Доступно:** Pro

**📝 Описание:** Копирует сообщение в указанный чат с форматированием (имя пользователя, время, реплаи, форварды)

**⚙️ Параметры для сценария (config_attrs):**
- `chat_to` (integer): ID чата, куда копировать сообщение


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "copy"
  chat_to: 123
```

</details>
<details>
<summary>📖 Дополнительная информация</summary>

Копирует сообщение в указанный чат с форматированием:

• Отображает имя пользователя с кликабельной ссылкой или username/ID
• Показывает время сообщения в локальном часовом поясе
• Обрабатывает реплаи и форварды
• Показывает информацию о медиа-вложениях
• Создает "чистые" реплаи на скопированные сообщения

Формат: `<code>Имя Фамилия</code> • время • @username`
Приоритет: имя в коде → @username → `ID: 123...`
Username добавляется после времени если есть и имя и логин

При реплаях на ранее скопированные сообщения создается настоящий реплай
в целевом чате, а не просто текстовая ссылка.

</details>
<details>
<summary>🔧 Внутренние параметры (required_data)</summary>

- `chat_id`
- `user_id`
- `message_id`

</details>
<details>
<summary>📤 Возвращаемые данные (response_data)</summary>

- `last_message_id` (integer): ID скопированного сообщения (только для успешных операций)
- `error` (string): Описание ошибки при неудачном выполнении

</details>

---

### validator

**🔧 Плагин:** validator (services)

**⚡ Доступно:** Pro

**📝 Описание:** Валидация данных по заданным правилам

**⚙️ Параметры для сценария (config_attrs):**
- `rules` (object): Правила валидации {field_name: [{rule: 'type', value: 'check_value'}]}


<details>
<summary>💡 Пример использования в сценарии</summary>

```yaml
- type: "validator"
  rules: {}
```

</details>
<details>
<summary>📖 Дополнительная информация</summary>

Поведение валидатора:
  - Если rules не указаны или пустые - валидация пропускается, действие помечается как completed
  - Если rules указаны - выполняется валидация по правилам
  - Универсальный параметр on_error доступен для КАЖДОГО правила:
      - on_error: "fail" — считать правило не пройденным (по умолчанию)
      - on_error: "pass" — считать правило пройденным
      - on_error: "skip" — пометить действие как drop (пропустить дальнейшую цепочку)
      - on_error: "drop" — синоним skip, помечает действие как drop

Поддерживаемые типы правил для поля rules:
  - equals: значение поля должно быть равно value
  - not_equals: значение поля не должно быть равно value
  - not_empty: поле не должно быть пустым
  - empty: поле должно быть пустым
  - contains: значение поля должно содержать value (строка, без учета регистра)
  - starts_with: значение поля должно начинаться с value (строка, без учета регистра)
  - regex: значение поля должно соответствовать регулярному выражению value
  - length_min: длина значения поля не менее value
  - length_max: длина значения поля не более value
  - in_list: значение поля должно входить в список value
  - not_in_list: значение поля не должно входить в список value

Дополнительное правило:
  - is_member: проверка, что пользователь состоит в группе/супергруппе или подписан на канал
    Параметры правила:
      - chat: integer | string | array
        Описание: ID чата (включая отрицательные ID супергрупп/каналов) либо юзернейм чата в формате "@username" или "username". Можно указать список чатов.
        По умолчанию используется action.chat_id, если chat не указан.
      - mode: "any" | "all"
        Описание: агрегирование для массива chat. По умолчанию "any".
      - target_user: integer | string
        Описание: Кого проверять. По умолчанию используется action.user_id. Если указана строка-логин ("@login"/"login"), требуется резолв в user_id (на текущем этапе — заглушка). Поддерживается также устаревший параметр target_user_id.
      - on_error: см. универсальный параметр выше.
    Логика: через Telegram Bot API getChatMember — пользователь считается состоящим, если статус не "left" и не "kicked".

</details>

---
