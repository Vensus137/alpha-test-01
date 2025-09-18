# Примеры работы с системой запросов

Система запросов предоставляет мощный механизм для сбора, сохранения и управления пользовательскими обращениями, обратной связью и другими типами запросов. Она интегрирована с базой данных и поддерживает различные операции управления.

## Основные концепции

### Типы запросов

- **`request`** — создание нового запроса с сохранением в базу данных
- **`request_management`** — управление запросами (просмотр, фильтрация, детали)

### Структура запроса

```yaml
# Создание запроса
- type: request
  request_name: "feedback"                    # Уникальное имя типа запроса
  request_info: "Описание запроса с плейсхолдерами"  # Информация о запросе
  placeholder: true                           # (опционально) обработка плейсхолдеров

# Управление запросами
- type: request_management
  operation: "list"                          # Операция: list, details
  request_name: "feedback"                   # (опционально) фильтр по типу
  limit: 10                                  # (опционально) лимит результатов
  time_before: "7d"                         # (опционально) фильтр по времени
  from_date: "2025-01-01"                   # (опционально) фильтр с даты
```

## Пример 1: Простое создание запроса

```yaml
simple_request:
  actions:
    - type: send
      text: "📝 Создание простого запроса"
      callback_edit: false
    - type: request
      request_name: "user_feedback"
      request_info: "Обратная связь от пользователя {user_id}"
    - type: send
      text: "✅ Запрос успешно сохранен в базе данных"
      callback_edit: false
      chain: completed
```

**Как работает:**
1. Первое действие отправляет сообщение
2. Второе действие создает запрос с именем "user_feedback"
3. Третье действие подтверждает сохранение

## Пример 2: Запрос с плейсхолдерами

```yaml
request_with_placeholders:
  actions:
    - type: send
      text: "📝 Запрос с динамическими данными"
      callback_edit: false
    - type: request
      request_name: "bug_report"
      request_info: |
        Сообщение об ошибке от {username} (@{username})
        Чат: {chat_id}
        Время: {event_date|format:datetime}
        Текст: {event_text}
      placeholder: true
    - type: send
      text: "✅ Отчет об ошибке сохранен"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `placeholder: true` включает обработку плейсхолдеров
- Данные автоматически подставляются из контекста выполнения
- Запрос сохраняется с полной информацией о пользователе и событии

## Пример 3: Запрос с состоянием пользователя

```yaml
request_with_user_state:
  actions:
    - type: user
      user_state: "feedback"
      expire: 10s
    - type: send
      text: |
        📝 <b>Обратная связь</b>
        
        Пожалуйста, опишите ваши пожелания, предложения или замечания.
        Мы внимательно изучим ваше сообщение и учтем его в дальнейшей работе.
        
        <i>Просто напишите ваше сообщение в следующем сообщении.</i>
      inline:
        - [{"🔙 Назад": "main_menu"}]
      chain: completed

# Обработка обратной связи (сценарий для состояния feedback)
request_feedback_handler:
  actions:
    - type: user
      user_state: ""
    - type: request
      request_name: "feedback"
      request_info: "Фидбек от пользователя {user_id} (@{username}) в чате {chat_id}. Текст: {event_text}"
    - type: send
      text: |
        ✅ <b>Спасибо за обратную связь!</b>
        
        Ваше сообщение успешно получено и будет рассмотрено нашей командой.
        Мы обязательно учтем ваши пожелания в дальнейшей работе.
        
        🔙 <a href="command.start">Вернуться в главное меню</a>
      inline:
        - [{"🔙 Назад": "main_menu"}]
      chain: completed
```

**Как работает:**
1. Первый сценарий устанавливает состояние пользователя "feedback"
2. Пользователь отправляет сообщение в этом состоянии
3. Второй сценарий обрабатывает сообщение и создает запрос
4. Запрос сохраняется с полной информацией о пользователе и тексте

## Пример 4: Валидация запроса

```yaml
request_with_validation:
  actions:
    - type: send
      text: "📝 Создание запроса с валидацией"
      callback_edit: false
    - type: validator
      rules:
        event_text:
          - rule: not_empty
          - rule: length_min
            value: 5
      chain: true
    - type: send
      text: |
        ❌ <b>Ошибка!</b>
        
        Запрос должен содержать минимум 5 символов.
        Попробуйте еще раз!
      inline:
        - [{"🔙 Назад": "main_menu"}]
      callback_edit: false
      chain: failed
      chain_drop: completed
    - type: request
      request_name: "validated_request"
      request_info: "Валидированный запрос от {username}: {event_text}"
    - type: send
      text: "✅ Запрос прошел валидацию и сохранен"
      callback_edit: false
      chain: completed
```

**Как работает:**
1. Первое действие отправляет сообщение
2. Второе действие валидирует текст запроса
3. При ошибке валидации отправляется сообщение об ошибке
4. При успешной валидации создается запрос
5. `chain_drop: completed` прерывает цепочку при ошибке

## Пример 5: Просмотр списка запросов

```yaml
request_list_view:
  actions:
    - type: send
      text: "📋 Просмотр списка запросов"
      callback_edit: false
    - type: request_management
      operation: "list"
      request_name: "feedback"
      limit: 10
    - type: send
      text: "{response_text}"
      additional_text: |

        <b>📋 Список последних запросов получен</b>
      inline:
        - [{"🔄 Обновить": "request_list_view"}, {"🔙 Назад": "main_menu"}]
      callback_edit: false
      chain: completed
```

**Как работает:**
1. Первое действие отправляет сообщение
2. Второе действие получает список запросов типа "feedback" (автоматически создает поле `text`)
3. Третье действие добавляет дополнительную информацию через `additional_text`
4. `additional_text` добавляется к автоматически сгенерированному тексту от `request_management`

## Пример 6: Фильтрация запросов по времени

```yaml
request_filter_by_time:
  actions:
    - type: send
      text: "📅 Запросы за последние 7 дней"
      callback_edit: false
    - type: request_management
      operation: "list"
      time_before: "7d"
    - type: send
      text: "{response_text}"
      additional_text: |

        <b>📅 Результат фильтрации по времени</b>
      inline:
        - [{"🔄 Обновить": "request_filter_by_time"}, {"🔙 Назад": "main_menu"}]
      callback_edit: false
      chain: completed
```

**Как работает:**
- `request_management` автоматически создает поле `response_text` с отформатированным списком запросов
- `additional_text` добавляется к автоматически сгенерированному тексту
- Формат отображения задается самим плагином `request_management`

**Поддерживаемые форматы времени:**
- `"7d"` — 7 дней
- `"24h"` — 24 часа
- `"1h"` — 1 час
- `"30m"` — 30 минут

## Пример 7: Фильтрация запросов с даты

```yaml
request_filter_from_date:
  actions:
    - type: send
      text: "📅 Запросы с определенной даты"
      callback_edit: false
    - type: request_management
      operation: "list"
      from_date: "2025-01-01"
    - type: send
      text: "{response_text}"
      additional_text: |

        <b>📅 Результат фильтрации с даты</b>
      inline:
        - [{"🔄 Обновить": "request_filter_from_date"}, {"🔙 Назад": "main_menu"}]
      callback_edit: false
      chain: completed
```

**Как работает:**
- `request_management` автоматически создает поле `response_text` с отформатированным списком запросов
- `additional_text` добавляется к автоматически сгенерированному тексту
- Формат отображения задается самим плагином `request_management`

**Формат даты:** `"YYYY-MM-DD"`

## Пример 8: Детальная информация по запросу

```yaml
request_details:
  actions:
    - type: user
      user_state: "request_details"
    - type: send
      text: |
        🔍 <b>Детальная информация по запросу</b>
        
        <b>Пожалуйста, введите ID запроса (только число):</b>
        
        <i>❌ Для отмены нажмите кнопку ниже.</i>
      inline:
        - [{"🔙 Назад": "main_menu"}]

# Обработка ввода ID запроса
request_details_handler:
  actions:
    - type: user
      user_state: ""
    - type: request_management
      operation: "details"
    - type: send
      text: "{response_text}"
      additional_text: |

        <b>🔍 Детальная информация по запросу</b>
      inline:
        - [{"🔙 Назад": "main_menu"}]
      chain: completed
```

**Как работает:**
1. Первый сценарий устанавливает состояние для ввода ID
2. Пользователь вводит ID запроса
3. Второй сценарий получает детальную информацию по ID (автоматически создает поле `response_text`)
4. `additional_text` добавляется к автоматически сгенерированному тексту с деталями запроса

## Пример 9: Демонстрация с additional_text

```yaml
demo_request_with_additional:
  actions:
    - type: request_management
      operation: "list"
      request_name: "{username}"
      limit: 10
      placeholder: true
      chain: true
    - type: send
      text: "{response_text}"
      additional_text: |

        <b>ID запроса (для деталей):</b>
      inline:
        - [{"🔄 Обновить": "demo_request_list"}, {"🔙 Назад": "demo_requests"}]
      callback_edit: false
      chain: completed
    - type: user
      user_state: "demo_request_details"
```

**Особенности `additional_text`:**
- Добавляется к тексту, полученному от предыдущего действия
- Позволяет дополнять результаты запросов дополнительной информацией
- Сохраняет форматирование и inline-кнопки

## Пример 10: Сложная цепочка с запросами

```yaml
complex_request_chain:
  actions:
    - type: send
      text: "🔗 Сложная цепочка с запросами"
      callback_edit: false
    - type: request
      request_name: "chain_test"
      request_info: "Тестовый запрос из цепочки от {username}"
      chain: true
    - type: send
      text: "✅ Запрос создан"
      callback_edit: false
      chain: completed
    - type: request_management
      operation: "list"
      request_name: "chain_test"
      limit: 5
      chain: completed
    - type: send
      text: "{response_text}"
      additional_text: |

        <b>📋 Последние запросы из цепочки</b>
      inline:
        - [{"🔄 Обновить": "complex_request_chain"}, {"🔙 Назад": "main_menu"}]
      callback_edit: false
      chain: completed
```

**Как работает цепочка:**
1. Создается запрос
2. Подтверждается создание
3. Получается список запросов (автоматически создает поле `response_text`)
4. `additional_text` добавляется к автоматически сгенерированному тексту со списком запросов

## Пример 11: Запросы с условной логикой

```yaml
conditional_request:
  actions:
    - type: validator
      rules:
        user_role:
          - rule: in_list
            value: ["admin", "moderator"]
      chain: true
    - type: request
      request_name: "admin_request"
      request_info: "Запрос от администратора {username}: {event_text}"
      chain: completed
    - type: send
      text: "❌ У вас нет прав для создания запросов"
      callback_edit: false
      chain: failed
    - type: send
      text: "✅ Запрос администратора сохранен"
      callback_edit: false
      chain: ["completed", "failed"]
```

**Как работает:**
1. Проверяется роль пользователя
2. При наличии прав создается запрос
3. При отсутствии прав отправляется сообщение об ошибке
4. Финальное сообщение отправляется в любом случае

## Пример 12: Запросы с метаданными

```yaml
request_with_metadata:
  actions:
    - type: request
      request_name: "feature_request"
      request_info: |
        Запрос новой функции
        Пользователь: {username}
        Приоритет: {priority|fallback:normal}
        Категория: {category|fallback:general}
        Описание: {event_text}
      placeholder: true
    - type: send
      text: "✅ Запрос функции сохранен с метаданными"
      callback_edit: false
      chain: completed
```

**Преимущества метаданных:**
- Структурированное хранение информации
- Возможность фильтрации по различным параметрам
- Удобство для администраторов и модераторов

## Лучшие практики

### ✅ Рекомендуется
- **Использовать осмысленные имена** для типов запросов
- **Добавлять метаданные** в `request_info` для лучшей организации
- **Валидировать данные** перед созданием запросов
- **Использовать плейсхолдеры** для динамических данных
- **Группировать связанные запросы** по типам
- **Добавлять `placeholder: true`** для обработки плейсхолдеров
- **Использовать `additional_text`** для дополнения результатов `request_management`
- **Применять фильтрацию** для эффективного поиска запросов
- **Документировать типы запросов** в комментариях
- **Использовать `text: "{response_text}"`** в действии `send` после `request_management`

### ⚠️ Не рекомендуется
- **Создавать слишком много типов** запросов без необходимости
- **Смешивать бизнес-логику** с созданием запросов
- **Игнорировать производительность** при больших объемах запросов
- **Создавать слишком длинные `request_info`** без структурирования
- **Использовать неуникальные имена** для типов запросов
- **Игнорировать валидацию** пользовательских данных

## Отладка запросов

### Рекомендации по отладке
- **Включите debug режим** для получения подробных логов
- **Проверяйте логи** сервиса request_manager для анализа операций
- **Тестируйте плейсхолдеры** отдельно перед использованием
- **Проверяйте права доступа** для операций управления

## Заключение

Система запросов предоставляет мощный механизм для сбора и управления пользовательскими обращениями. Правильное использование типов запросов, метаданных и фильтрации позволяет создавать эффективные системы обратной связи и поддержки.

Ключевые моменты:
- **Планируйте структуру запросов** заранее
- **Используйте валидацию** для обеспечения качества данных
- **Применяйте плейсхолдеры** для динамических данных
- **Организуйте фильтрацию** для эффективного поиска
- **Документируйте типы запросов** для команды
- **Мониторьте производительность** при больших объемах
