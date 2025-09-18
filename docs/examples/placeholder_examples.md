# Примеры работы с плейсхолдер-процессором

Плейсхолдер-процессор — это мощная система для динамической подстановки и преобразования данных в сценариях. Он позволяет создавать гибкие шаблоны с поддержкой модификаторов, арифметических операций и форматирования.

## Основные концепции

### Синтаксис плейсхолдеров

- **Простая замена**: `{field_name}`
- **С модификатором**: `{field_name|modifier:param}`
- **Цепочка модификаторов**: `{field_name|modifier1:param1|modifier2:param2}`
- **Fallback значение**: `{field_name|fallback:default_value}`
- **Вложенные плейсхолдеры**: `{field_name|modifier:{nested_field}}` или `{field_name|modifier:value_{nested_field}}`

### Источники данных

- **`prev_data`** — данные из предыдущих действий в цепочке
- **`response_data`** — данные, возвращенные сервисами
- **`parsed_action`** — данные текущего действия
- **Любые поля** из контекста выполнения

### Включение обработки плейсхолдеров

**⚠️ Важно:** По умолчанию плейсхолдеры **НЕ обрабатываются** для оптимизации производительности.

**Для включения обработки плейсхолдеров:**
- Добавьте `placeholder: true` к действию
- Это включает обработку плейсхолдеров во всех полях действия

**Исключение — сервис Messenger:**
- **По умолчанию включена** автоматическая обработка плейсхолдеров в текстовых сообщениях
- Это самый частый сценарий использования — подстановка данных в сообщения
- Не требует дополнительной настройки для простых текстовых подстановок

## Пример 1: Простая подстановка данных

```yaml
simple_substitution:
  actions:
    - type: send
      text: "Привет, {username}! Ваш ID: {user_id}"
      callback_edit: false
    - type: send
      text: "Текущее время: {current_time|format:datetime}"
      callback_edit: false
      chain: true
    - type: send
      text: "Количество сообщений: {message_count|+1}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `{username}` — простая подстановка имени пользователя
- `{user_id}` — подстановка ID пользователя
- `{current_time|format:datetime}` — форматирование времени
- `{message_count|+1}` — арифметическая операция

**💡 Автоматическая обработка:** В сервисе `tg_messenger` (тип `send`) плейсхолдеры обрабатываются автоматически без дополнительных настроек.

## Пример 2: Арифметические операции

```yaml
arithmetic_operations:
  actions:
    - type: send
      text: "🔢 Арифметические операции с плейсхолдерами"
      callback_edit: false
    - type: send
      text: |
        Исходное значение: {base_value}
        + 10: {base_value|+10}
        - 5: {base_value|-5}
        * 2: {base_value|*2}
        / 3: {base_value|/3}
        % 7: {base_value|%7}
      callback_edit: false
      chain: true
    - type: send
      text: "Результат вычислений: {result}"
      callback_edit: false
      chain: completed
```

**Поддерживаемые операции:**
- `|+value` — сложение
- `|-value` — вычитание
- `|*value` — умножение
- `|/value` — деление
- `|%value` — остаток от деления

## Пример 3: Преобразования текста

```yaml
text_transformations:
  actions:
    - type: send
      text: "🔤 Преобразования текста"
      callback_edit: false
    - type: send
      text: |
        Исходный текст: {original_text}
        Верхний регистр: {original_text|upper}
        Нижний регистр: {original_text|lower}
        Заглавные буквы: {original_text|title}
        Первая заглавная: {original_text|capitalize}
      callback_edit: false
      chain: true
    - type: send
      text: "Обрезанный текст: {long_text|truncate:50}"
      callback_edit: false
      chain: completed
```

**Поддерживаемые преобразования:**
- `|upper` — верхний регистр
- `|lower` — нижний регистр
- `|title` — заглавные буквы каждого слова
- `|capitalize` — первая заглавная буква
- `|length` — подсчет длины строки (количество символов)
- `|truncate:length` — обрезка текста с "..."
- `|regex:pattern` — извлечение данных по регулярному выражению

## Пример 4: Извлечение данных по регулярным выражениям

```yaml
regex_extraction:
  actions:
    - type: send
      text: "🔍 Извлечение данных по регулярным выражениям"
      callback_edit: false
    - type: send
      text: |
        Время из текста: {event_text|regex:(?:\\d+\\s*[dhms]\\s*)+}
        Email из сообщения: {message|regex:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}}
        Телефон: {contact|regex:\\+?[1-9]\\d{1,14}}
        URL: {text|regex:https?://[^\\s]+}
      callback_edit: false
      chain: true
    - type: send
      text: "Извлеченные данные: {extracted_data}"
      callback_edit: false
      chain: completed
```

**Как работает regex модификатор:**
- `|regex:pattern` — извлекает данные по регулярному выражению
- Возвращает первое совпадение (группа 0)
- Если совпадение не найдено, возвращает пустую строку
- Поддерживает все стандартные regex паттерны Python

**Примеры паттернов:**
- `(?:\\d+\\s*[dhms]\\s*)+` — время (1h 30m, 2d 5h, etc.)
- `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}` — email
- `\\+?[1-9]\\d{1,14}` — номер телефона
- `https?://[^\\s]+` — URL

## Пример 5: Форматирование дат и времени

```yaml
datetime_formatting:
  actions:
    - type: send
      text: "📅 Форматирование дат и времени"
      callback_edit: false
    - type: send
      text: |
        Timestamp: {timestamp|format:timestamp}
        Дата: {timestamp|format:date}
        Время: {timestamp|format:time}
        Дата и время: {timestamp|format:datetime}
      callback_edit: false
      chain: true
    - type: send
      text: "Относительное время: {relative_time}"
      callback_edit: false
      chain: completed
```

**Поддерживаемые форматы:**
- `|format:timestamp` — преобразование в timestamp
- `|format:date` — формат даты (dd.mm.yyyy)
- `|format:time` — формат времени (hh:mm)
- `|format:datetime` — полный формат даты и времени

## Пример 6: Работа со списками

```yaml
list_operations:
  actions:
    - type: send
      text: "📋 Работа со списками"
      callback_edit: false
    - type: send
      text: |
        Список пользователей: {users|list}
        Через запятую: {users|comma}
        Теги: {users|tags}
        Количество: {users|length}
      callback_edit: false
      chain: true
    - type: send
      text: "Первый пользователь: {users|first}"
      callback_edit: false
      chain: completed
```

**Поддерживаемые операции со списками:**
- `|list` — маркированный список (• item)
- `|comma` — через запятую (item1, item2)
- `|tags` — преобразование в теги (@user)
- `|length` — количество элементов
- `|first` — первый элемент
- `|last` — последний элемент

## Пример 7: Fallback значения

```yaml
fallback_values:
  actions:
    - type: send
      text: "🔄 Fallback значения"
      callback_edit: false
    - type: send
      text: |
        Имя пользователя: {username|fallback:Гость}
        Возраст: {age|fallback:Не указан}
        Email: {email|fallback:Нет данных}
        Пустое поле: {|fallback:100}
      callback_edit: false
      chain: true
    - type: send
      text: "Комбинированный fallback: {value|upper|fallback:ПО УМОЛЧАНИЮ}"
      callback_edit: false
      chain: completed
```

**Как работает fallback:**
- `|fallback:value` — замена при отсутствии значения
- Можно комбинировать с другими модификаторами
- Работает с пустыми полями и отсутствующими данными

## Пример 8: Цепочки модификаторов

```yaml
modifier_chains:
  actions:
    - type: send
      text: "🔗 Цепочки модификаторов"
      callback_edit: false
    - type: send
      text: |
        Сложная цепочка: {raw_data|lower|truncate:20|fallback:Нет данных}
        Математика + форматирование: {number|+100|*2|format:number}
        Список + теги + обрезка: {users|tags|truncate:50}
        Regex + форматирование: {event_text|regex:(?:\\d+\\s*[dhms]\\s*)+|upper}
      callback_edit: false
      chain: true
    - type: send
      text: "Результат: {processed_result}"
      callback_edit: false
      chain: completed
```

**Порядок выполнения:**
1. Модификаторы выполняются слева направо
2. Результат каждого модификатора передается следующему
3. Fallback применяется в конце цепочки

## Пример 9: Условная подстановка

```yaml
conditional_substitution:
  actions:
    - type: send
      text: "🎯 Условная подстановка"
      callback_edit: false
    - type: send
      text: |
        Статус: {status|fallback:Неизвестно}
        Сообщение: {status|equals:active|fallback:Неактивен|value:Активен}
        Роль: {role|in_list:admin,moderator|fallback:Пользователь|value:Администратор}
      callback_edit: false
      chain: true
    - type: send
      text: "Условный текст: {condition|true|value:Да|fallback:Нет}"
      callback_edit: false
      chain: completed
```

**Как работают условные модификаторы:**
- `|equals:value` — проверяет равенство значения
- `|in_list:item1,item2` — проверяет вхождение в список
- `|true` — проверяет истинность значения
- `|value:result` — возвращает результат при истинности (работает в связке с другими условными модификаторами)

## Пример 10: Рекурсивная обработка плейсхолдеров

```yaml
recursive_placeholders:
  actions:
    - type: send
      text: "🔄 Рекурсивная обработка плейсхолдеров"
      callback_edit: false
    - type: send
      text: |
        Простая замена: {username}
        Рекурсивная замена: {nested_field}
        Цепочка модификаторов: {username|upper|truncate:10}
      callback_edit: false
      chain: true
    - type: send
      text: "Результат: {processed_result}"
      callback_edit: false
      chain: completed
```

**Как работает рекурсивная обработка:**
- Если значение поля содержит плейсхолдеры, они обрабатываются рекурсивно
- Поддерживается до 3 уровней вложенности (настраивается в `max_nesting_depth`)
- При достижении максимальной глубины плейсхолдер возвращается как есть с предупреждением

**Пример рекурсивной обработки:**
```yaml
# Если в values_dict есть:
# username: "john"
# nested_field: "Привет, {username}!"  # Содержит плейсхолдер
# 
# То {nested_field} будет обработан как: "Привет, john!"
```

## Пример 11: Автоматическая vs ручная обработка плейсхолдеров

```yaml
placeholder_processing_modes:
  actions:
    # Автоматическая обработка в tg_messenger (по умолчанию)
    - type: send
      text: "Привет, {username}! Ваш ID: {user_id}"
      callback_edit: false
      # placeholder: true НЕ нужно - обрабатывается автоматически
    
    # Ручное включение для других сервисов
    - type: validator
      rules:
        processed_username:
          - rule: not_empty
          - rule: length_min
            value: 3
      placeholder: true  # Обязательно для обработки плейсхолдеров
      chain: true
    
    # Ручное включение для пользовательских действий
    - type: user
      user_state: "awaiting_{action_type}"
      placeholder: true  # Включаем обработку плейсхолдеров
      chain: completed
    
    # Автоматическая обработка в messenger (снова)
    - type: send
      text: "Состояние: {user_state}, Обработанное имя: {processed_username|title}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- **Messenger (send)**: Плейсхолдеры обрабатываются автоматически
- **Другие сервисы**: Требуют `placeholder: true` для обработки
- **Пользовательские действия**: Также требуют явного включения

## Пример 12: Сложные вычисления

```yaml
complex_calculations:
  actions:
    - type: send
      text: "🧮 Сложные вычисления"
      callback_edit: false
    - type: send
      text: |
        Процент: {score|/100|*100|format:percent}
        Среднее: {total|/count|format:number}
        Скидка: {price|*0.9|format:currency}
        Рейтинг: {rating|*5|format:number}/5
      callback_edit: false
      chain: true
    - type: send
      text: "Итоговая сумма: {base_price|+tax|+fee|format:currency}"
      callback_edit: false
      chain: completed
```

## Пример 13: Форматирование дат и времени

```yaml
datetime_formatting:
  actions:
    - type: send
      text: "📅 Форматирование дат и времени"
      callback_edit: false
    - type: send
      text: |
        Timestamp: {timestamp|format:timestamp}
        Дата: {timestamp|format:date}
        Время: {timestamp|format:time}
        Дата и время: {timestamp|format:datetime}
      callback_edit: false
      chain: true
    - type: send
      text: "Итог: {current_time|format:datetime|fallback:Неизвестно}"
      callback_edit: false
      chain: completed
```

**Поддерживаемые форматы:**
- **Даты и время:**
  - `|format:timestamp` — преобразование в timestamp (Unix time)
  - `|format:date` — формат даты (dd.mm.yyyy)
  - `|format:time` — формат времени (hh:mm)
  - `|format:datetime` — полный формат даты и времени (dd.mm.yyyy hh:mm)
- **Числа и валюты:**
  - `|format:currency` — форматирование валюты (1000.00 ₽)
  - `|format:percent` — форматирование процентов (25.5%)
  - `|format:number` — форматирование чисел (1234.56)

## 🆕 Пример 14: Вложенные плейсхолдеры - Основные возможности

```yaml
nested_placeholders_basic:
  actions:
    - type: send
      text: "🔄 Вложенные плейсхолдеры - Основные возможности"
      callback_edit: false
    - type: send
      text: |
        Простая вложенность: {greeting_{language}}
        Вложенность в параметрах: {user|fallback:{default_user}}
        Вложенность в арифметике: {base|+{bonus}}
        Вложенность в форматировании: {timestamp|format:{format_type}}
      callback_edit: false
      chain: true
    - type: send
      text: "Результат: {nested_result}"
      callback_edit: false
      chain: completed
```

**Как работают вложенные плейсхолдеры:**
- **Простая вложенность**: `{greeting_{language}}` — если `language = "ru"`, то `greeting_{language}` станет `greeting_ru`
- **В параметрах fallback**: `{user|fallback:{default_user}}` — если `user` отсутствует, используется значение `default_user`
- **В арифметических операциях**: `{base|+{bonus}}` — к значению `base` добавляется значение `bonus`
- **В параметрах форматирования**: `{timestamp|format:{format_type}}` — тип форматирования берется из поля `format_type`

## 🆕 Пример 15: Вложенные плейсхолдеры в модификаторах

```yaml
nested_placeholders_modifiers:
  actions:
    - type: send
      text: "🎯 Вложенные плейсхолдеры в модификаторах"
      callback_edit: false
    - type: send
      text: |
        Вложенность в truncate: {long_text|truncate:{max_length}}
        Вложенность в regex: {event_text|regex:{regex_pattern}}
        Вложенность в equals: {status|equals:{expected_status}|value:OK|fallback:BAD}
        Вложенность в in_list: {role|in_list:{allowed_roles}|value:Доступ|fallback:Запрет}
      callback_edit: false
      chain: true
    - type: send
      text: "Сложная вложенность: {result|format:{output_format}|truncate:{display_length}}"
      callback_edit: false
      chain: completed
```

**Примеры вложенности в модификаторах:**
- `{long_text|truncate:{max_length}}` — обрезка текста до длины, указанной в `max_length`
- `{event_text|regex:{regex_pattern}}` — извлечение данных по паттерну из `regex_pattern`
- `{status|equals:{expected_status}|value:OK|fallback:BAD}` — сравнение статуса с ожидаемым из `expected_status`
- `{role|in_list:{allowed_roles}|value:Доступ|fallback:Запрет}` — проверка роли по списку из `allowed_roles`

## 🆕 Пример 16: Многоуровневая вложенность

```yaml
multi_level_nesting:
  actions:
    - type: send
      text: "🏗️ Многоуровневая вложенность"
      callback_edit: false
    - type: send
      text: |
        Уровень 1: {user_{type}_{field}}
        Уровень 2: {config_{section}_{setting}|fallback:{default_{section}}}
        Уровень 3: {data_{category}_{item}|format:{format_{category}}|truncate:{limit_{category}}}
      callback_edit: false
      chain: true
    - type: send
      text: "Глубокая вложенность: {deeply_{nested_{field}}|upper|truncate:{max_{depth}}}"
      callback_edit: false
      chain: completed
```

**Примеры многоуровневой вложенности:**
```yaml
# Если в values_dict есть:
# type: "admin"
# field: "name"
# user_admin_name: "Администратор"
# 
# То {user_{type}_{field}} будет обработан как:
# 1. {type} = "admin"
# 2. {field} = "name"  
# 3. {user_{type}_{field}} = {user_admin_name} = "Администратор"
```

## 🆕 Пример 17: Вложенные плейсхолдеры в условной логике

```yaml
nested_conditional_logic:
  actions:
    - type: send
      text: "🎲 Вложенные плейсхолдеры в условной логике"
      callback_edit: false
    - type: send
      text: |
        Динамическое условие: {status|equals:{expected_{phase}}|value:{success_{phase}}|fallback:{error_{phase}}}
        Условная роль: {role|in_list:{permissions_{level}}|value:{allow_{level}}|fallback:{deny_{level}}}
        Динамический fallback: {value|fallback:{default_{type}_{category}}}
      callback_edit: false
      chain: true
    - type: send
      text: "Сложная логика: {condition|true|value:{positive_{mood}}|fallback:{negative_{mood}}}"
      callback_edit: false
      chain: completed
```

**Примеры условной логики с вложенностью:**
- `{status|equals:{expected_{phase}}|value:{success_{phase}}|fallback:{error_{phase}}}` — динамическое условие в зависимости от фазы
- `{role|in_list:{permissions_{level}}|value:{allow_{level}}|fallback:{deny_{level}}}` — проверка роли по динамическому списку разрешений
- `{value|fallback:{default_{type}_{category}}}` — fallback значение зависит от типа и категории

## 🆕 Пример 18: Вложенные плейсхолдеры в арифметических операциях

```yaml
nested_arithmetic:
  actions:
    - type: send
      text: "🧮 Вложенные плейсхолдеры в арифметических операциях"
      callback_edit: false
    - type: send
      text: |
        Динамическое сложение: {base_price|+{tax_{region}}}
        Динамическое умножение: {quantity|*{price_{item_type}}}
        Сложные вычисления: {total|+{bonus_{level}}|*{discount_{category}}|format:currency}
        Условные вычисления: {amount|+{bonus|equals:{bonus_type}|value:{bonus_amount}|fallback:0}}
      callback_edit: false
      chain: true
    - type: send
      text: "Итоговый расчет: {final_{calculation_type}}"
      callback_edit: false
      chain: completed
```

**Примеры арифметических операций с вложенностью:**
- `{base_price|+{tax_{region}}}` — добавление налога в зависимости от региона
- `{quantity|*{price_{item_type}}}` — умножение на цену в зависимости от типа товара
- `{total|+{bonus_{level}}|*{discount_{category}}|format:currency}` — сложные вычисления с бонусом и скидкой
- `{amount|+{bonus|equals:{bonus_type}|value:{bonus_amount}|fallback:0}}` — условное добавление бонуса

## 🆕 Пример 19: Вложенные плейсхолдеры в форматировании

```yaml
nested_formatting:
  actions:
    - type: send
      text: "🎨 Вложенные плейсхолдеры в форматировании"
      callback_edit: false
    - type: send
      text: |
        Динамический формат: {timestamp|format:{date_format_{locale}}}
        Условное форматирование: {number|format:{format_type|equals:currency|value:currency|fallback:number}}
        Настраиваемое форматирование: {value|format:{display_{unit}}}
      callback_edit: false
      chain: true
    - type: send
      text: "Сложное форматирование: {result|format:{output_{type}_{format}}|truncate:{max_{display}}}"
      callback_edit: false
      chain: completed
```

**Примеры форматирования с вложенностью:**
- `{timestamp|format:{date_format_{locale}}}` — формат даты зависит от локали
- `{number|format:{format_type|equals:currency|value:currency|fallback:number}}` — условный выбор типа форматирования
- `{value|format:{display_{unit}}}` — форматирование в зависимости от единицы измерения

## 🆕 Пример 20: Вложенные плейсхолдеры в списках и тегах

```yaml
nested_lists_and_tags:
  actions:
    - type: send
      text: "📋 Вложенные плейсхолдеры в списках и тегах"
      callback_edit: false
    - type: send
      text: |
        Динамические теги: {users_{group}|tags}
        Условный список: {items_{category}|list|truncate:{max_{category}}}
        Форматированный список: {data_{type}|format:{list_format_{style}}|list}
      callback_edit: false
      chain: true
    - type: send
      text: "Сложный список: {result_{category}|tags|truncate:{limit_{category}}}"
      callback_edit: false
      chain: completed
```

**Примеры списков и тегов с вложенностью:**
- `{users_{group}|tags}` — теги пользователей в зависимости от группы
- `{items_{category}|list|truncate:{max_{category}}}` — список элементов с динамическим ограничением
- `{data_{type}|format:{list_format_{style}}|list}` — форматированный список в зависимости от стиля

## 🆕 Пример 21: Вложенные плейсхолдеры в regex

```yaml
nested_regex:
  actions:
    - type: send
      text: "🔍 Вложенные плейсхолдеры в regex"
      callback_edit: false
    - type: send
      text: |
        Динамический паттерн: {event_text|regex:{regex_{pattern_type}}}
        Условное извлечение: {message|regex:{extract_{data_type}|fallback:.*}}}
        Настраиваемый поиск: {text|regex:{search_{field}_{format}}}
      callback_edit: false
      chain: true
    - type: send
      text: "Сложный regex: {result|regex:{pattern_{type}_{version}}}"
      callback_edit: false
      chain: completed
```

**Примеры regex с вложенностью:**
- `{event_text|regex:{regex_{pattern_type}}}` — паттерн regex зависит от типа данных
- `{message|regex:{extract_{data_type}|fallback:.*}}` — условное извлечение с fallback паттерном
- `{text|regex:{search_{field}_{format}}}` — настраиваемый поиск в зависимости от поля и формата

## 🆕 Пример 22: Практические сценарии использования вложенных плейсхолдеров

```yaml
practical_nested_scenarios:
  actions:
    - type: send
      text: "🚀 Практические сценарии использования вложенных плейсхолдеров"
      callback_edit: false
    - type: send
      text: |
        Персонализированное приветствие: Привет, {user_{language}|fallback:Гость}!
        Динамическая навигация: {menu_{section}_{user_level}|fallback:{menu_{section}_default}}
        Условная обработка: {status|equals:{expected_{action}}|value:{success_{action}}|fallback:{error_{action}}}
      callback_edit: false
      chain: true
    - type: send
      text: "Адаптивное сообщение: {message_{context}_{user_type}_{status}|truncate:{limit_{context}}}"
      callback_edit: false
      chain: completed
```

**Практические сценарии:**
- **Персонализация**: `Привет, {user_{language}|fallback:Гость}!` — приветствие на языке пользователя
- **Динамическая навигация**: `{menu_{section}_{user_level}|fallback:{menu_{section}_default}}` — меню в зависимости от уровня пользователя
- **Условная обработка**: `{status|equals:{expected_{action}}|value:{success_{action}}|fallback:{error_{action}}}` — сообщения в зависимости от действия
- **Адаптивные сообщения**: `{message_{context}_{user_type}_{status}|truncate:{limit_{context}}}` — сообщения с адаптивным ограничением

## 🆕 Пример 23: Отладка вложенных плейсхолдеров

```yaml
debugging_nested_placeholders:
  actions:
    - type: send
      text: "🐛 Отладка вложенных плейсхолдеров"
      callback_edit: false
    - type: send
      text: |
        Проверка вложенности: {debug_{level}_{field}|fallback:ОТСУТСТВУЕТ}
        Сложная отладка: {test_{nested_{depth}}|upper|truncate:50}
        Условная отладка: {value|equals:{expected}|value:OK|fallback:ОШИБКА {debug_{error_type}}}
      callback_edit: false
      chain: true
    - type: send
      text: "Результат отладки: {debug_result|format:{debug_{format_type}}}"
      callback_edit: false
      chain: completed
```

**Советы по отладке:**
- **Проверяйте каждый уровень** вложенности отдельно
- **Используйте fallback** для диагностики отсутствующих данных
- **Тестируйте промежуточные значения** в цепочках модификаторов
- **Проверяйте синтаксис** вложенных плейсхолдеров

## 🆕 Пример 24: Точечная нотация для доступа к вложенным полям объектов

```yaml
dot_notation_examples:
  actions:
    - type: send
      text: "🔗 Точечная нотация для доступа к вложенным полям"
      callback_edit: false
    - type: send
      text: |
        Простой доступ: {promo_data.promo_code}
        Глубокий доступ: {user.profile.settings.notifications.email}
        С модификаторами: {promo_data.started_at|format:date}
        С fallback: {promo_data.user_id|fallback:Глобальный}
        Условная логика: {promo_data.user_id|equals:123|value:Ваш промокод|fallback:Общий промокод}
      callback_edit: false
      chain: true
    - type: send
      text: "Смешанный текст: Промокод {promo_data.promo_code} для {promo_data.promo_name}"
      callback_edit: false
      chain: completed
```

**Как работает точечная нотация:**
- **Простой доступ**: `{promo_data.promo_code}` — получает значение `promo_code` из объекта `promo_data`
- **Глубокий доступ**: `{user.profile.settings.notifications.email}` — проходит по цепочке вложенных объектов
- **С модификаторами**: `{promo_data.started_at|format:date}` — применяет модификатор к вложенному полю
- **С fallback**: `{promo_data.user_id|fallback:Глобальный}` — использует fallback если поле отсутствует или равно `None`
- **Условная логика**: `{promo_data.user_id|equals:123|value:Ваш промокод|fallback:Общий промокод}` — проверяет условие и возвращает соответствующее значение

**Примеры данных:**
```yaml
# promo_data объект:
promo_data:
  promo_code: "SUMMER2024"
  promo_name: "Летняя акция"
  user_id: 123
  started_at: "2024-06-01T00:00:00"
  expired_at: "2024-08-31T23:59:59"

# user объект:
user:
  profile:
    settings:
      notifications:
        email: true
        sms: false
```

**Результат обработки:**
- `{promo_data.promo_code}` → `"SUMMER2024"`
- `{user.profile.settings.notifications.email}` → `true`
- `{promo_data.started_at|format:date}` → `"01.06.2024"`
- `{promo_data.user_id|fallback:Глобальный}` → `123`
- `{promo_data.user_id|equals:123|value:Ваш промокод|fallback:Общий промокод}` → `"Ваш промокод"`
- `Промокод {promo_data.promo_code} для {promo_data.promo_name}` → `"Промокод SUMMER2024 для Летняя акция"`

## Лучшие практики

### ✅ Рекомендуется
- **Использовать fallback** для всех критических полей
- **Группировать модификаторы** логически
- **Тестировать сложные цепочки** модификаторов
- **Документировать** сложные плейсхолдеры
- **Использовать вложенные сценарии** для сложной логики
- **Помнить про `placeholder: true`** для сервисов кроме tg_messenger
- **Использовать автоматическую обработку** в tg_messenger для простых подстановок
- **Применять условные модификаторы** для динамической логики
- **Использовать форматирование** для красивого вывода чисел и дат
- **Применять regex модификатор** для извлечения структурированных данных из текста
- **Тестировать regex паттерны** отдельно перед использованием в плейсхолдерах
- **Планировать вложенность** заранее для сложных сценариев
- **Ограничивать глубину вложенности** до разумных пределов (≤3 уровней)
- **Использовать fallback** для всех вложенных плейсхолдеров
- **Применять точечную нотацию** для доступа к вложенным полям объектов

### ❌ Запрещено
- Создавать **циклические зависимости** в плейсхолдерах
- Использовать **слишком глубокую вложенность** (>3 уровней)
- **Создавать бесконечные циклы** в рекурсивных плейсхолдерах

### ⚠️ Не рекомендуется
- **Создавать слишком длинные цепочки** модификаторов
- **Использовать сложные вычисления** без тестирования
- **Игнорировать производительность** при множественных плейсхолдерах
- **Злоупотреблять вложенностью** без необходимости
- **Создавать слишком сложные** вложенные конструкции

## Отладка плейсхолдеров

### Рекомендации по отладке
- **Включите debug режим** для получения подробных логов
- **Проверяйте промежуточные значения** в цепочках модификаторов
- **Тестируйте модификаторы** по отдельности
- **Используйте fallback** для отладки отсутствующих данных
- **Проверьте `placeholder: true`** для сервисов кроме messenger
- **Убедитесь в наличии данных** в источниках (prev_data, response_data)
- **Проверяйте вложенность** по уровням
- **Тестируйте сложные конструкции** по частям

### Проверка плейсхолдеров
```yaml
# Тестовый сценарий для проверки плейсхолдеров
test_placeholders:
  actions:
    - type: send
      text: "Тест: {test_field|upper|fallback:ТЕСТ}"
      callback_edit: false
    - type: send
      text: "Regex тест: {event_text|regex:(?:\\d+\\s*[dhms]\\s*)+|fallback:Время не найдено}"
      callback_edit: false
    - type: send
      text: "Вложенность тест: {nested_{level}|fallback:Уровень {level}}"
      callback_edit: false
    - type: send
      text: "Результат: {result}"
      callback_edit: false
      chain: completed
```

## Заключение

Плейсхолдер-процессор предоставляет мощный механизм для динамической обработки данных в сценариях. Правильное использование модификаторов, fallback значений и вложенных плейсхолдеров позволяет создавать гибкие и надежные шаблоны.

Ключевые моменты:
- **Планируйте цепочки модификаторов** заранее
- **Используйте fallback** для всех важных полей
- **Тестируйте сложные плейсхолдеры** отдельно
- **Документируйте** сложную логику подстановки
- **Следите за производительностью** при множественных плейсхолдерах
- **Планируйте вложенность** для сложных сценариев
- **Ограничивайте глубину** вложенности до разумных пределов
- **Тестируйте вложенные плейсхолдеры** по уровням 