# Примеры работы с сервисом промокодов

Сервис промокодов (`promo_manager`) — это полнофункциональный сервис для создания, управления и проверки промокодов. Он поддерживает детерминированную и случайную генерацию кодов, гибкую настройку сроков действия и интеграцию со сценариями.

## Основные концепции

### Типы промокодов

- **Детерминированные** — генерируются на основе `user_id + promo_name + salt`, всегда одинаковые для одинаковых параметров
- **Случайные** — генерируются с уникальным случайным `salt`, каждый раз новые
- **Глобальные** — доступны всем пользователям (`target_user_id: 'Null'`, `'Any'` или `''`)
- **Персональные** — привязаны к конкретному пользователю

### Основные действия

- **`create_promo`** — создание нового промокода
- **`modify_promo`** — изменение существующего промокода
- **`check_promo`** — проверка доступности промокода

### Настройки сервиса

- **`default_code_length`** — длина генерируемых кодов (по умолчанию 8 символов)
- **`default_expire_days`** — срок действия по умолчанию (по умолчанию 30 дней)
- **`default_global_promos`** — создавать глобальные промокоды по умолчанию (по умолчанию `false`)

## Пример 1: Создание детерминированного промокода

```yaml
create_deterministic_promo:
  actions:
    - type: promo_manager
      action: create_promo
      promo_name: "SUMMER2024"
      salt: "company_summer"
      use_random: false
      expire: 90d  # 90 дней
      target_user_id: "Null"  # Глобальный промокод
      callback_edit: false
    - type: send
      text: |
        ✅ Промокод создан!
        
        Название: {promo_name}
        Код: {promo_code}
        Срок действия: {started_at|format:date} - {expired_at|format:date}
        Тип: Детерминированный (глобальный)
      callback_edit: false
      chain: completed
```

**Как работает:**
- `promo_name: "SUMMER2024"` — название промокода
- `salt: "company_summer"` — соль для генерации (вместе с `user_id` и `promo_name` формирует хэш)
- `use_random: false` — детерминированная генерация
- `expire: 90d` — срок действия, преобразуется утилитой action parser в `expire_seconds`: 7776000 (90 дней)
- `target_user_id: "Null"` — глобальный промокод для всех пользователей

**Результат:**
- Промокод будет генерироваться одинаково для одинаковых параметров
- Хэш-идентификация предотвратит создание дубликатов
- Промокод будет доступен всем пользователям

## Пример 2: Создание случайного персонального промокода

```yaml
create_random_personal_promo:
  actions:
    - type: promo_manager
      action: create_promo
      promo_name: "WELCOME_BONUS"
      use_random: true
      target_user_id: "{user_id}"  # Персональный промокод
      callback_edit: false
    - type: send
      text: |
        🎁 Персональный промокод создан!
        
        Название: {promo_name}
        Код: {promo_code}
        Срок действия: {started_at|format:date} - {expired_at|format:date}
        Тип: Случайный (персональный)
        Пользователь: {user_id}
      callback_edit: false
      chain: completed
```

**Как работает:**
- `use_random: true` — случайная генерация с уникальным `salt`
- `target_user_id: "{user_id}"` — промокод привязан к текущему пользователю
- Каждый раз будет генерироваться новый уникальный код
- Хэш-идентификация предотвратит конфликты

## Пример 3: Создание постоянного промокода

```yaml
create_permanent_promo:
  actions:
    - type: promo_manager
      action: create_promo
      promo_name: "LOYALTY_PROGRAM"
      salt: "loyalty_2024"
      use_random: false
      permanent: true  # Постоянный промокод
      target_user_id: "Null"
      callback_edit: false
    - type: send
      text: |
        🔒 Постоянный промокод создан!
        
        Название: {promo_name}
        Код: {promo_code}
        Срок действия: Постоянный (2000-2999)
        Тип: Детерминированный (постоянный)
        Хэш: {hash_id}
      callback_edit: false
      chain: completed
```

**Как работает:**
- `permanent: true` — промокод с очень длительным сроком действия
- `started_at` автоматически устанавливается в 2000 год
- `expired_at` автоматически устанавливается в 2999 год
- Промокод практически бессрочный

## Пример 4: Модификация существующего промокода

```yaml
modify_existing_promo:
  actions:
    - type: promo_manager
      action: modify_promo
      promo_name: "SUMMER2024"
      salt: "company_summer"
      expired_seconds: 15552000  # 180 дней (продление)
      target_user_id: "Null"
      callback_edit: false
    - type: send
      text: |
        ✏️ Промокод изменен!
        
        Название: {promo_name}
        Новый срок: {started_at|format:date} - {expired_at|format:date}
        Обновлен: {updated_at|format:datetime}
        Хэш: {hash_id}
      callback_edit: false
      chain: completed
```

**Как работает:**
- `action: modify_promo` — изменение существующего промокода
- `expired_seconds: 15552000` — продление срока действия до 180 дней
- Хэш-идентификация автоматически обновляется
- Все поля обновляются в базе данных

## Пример 5: Проверка доступности промокода

```yaml
check_promo_availability:
  actions:
    - type: promo_manager
      action: check_promo
      promo_code: "{promo_code}"
      callback_edit: false
    - type: send
      text: |
        🔍 Проверка промокода
        
        Код: {promo_code}
        Доступен: {promo_available|equals:true|value:✅ Да|fallback:❌ Нет}
        Название: {promo_data.promo_name}
        Срок действия: {promo_data.started_at|format:date} - {promo_data.expired_at|format:date}
        Пользователь: {promo_data.user_id|fallback:Глобальный}
      callback_edit: false
      chain: completed
```

**Как работает:**
- `action: check_promo` — проверка доступности промокода
- `promo_code: "{promo_code}"` — код для проверки
- `promo_available` — результат проверки (true/false)
- `promo_data.*` — детальная информация о промокоде

## Пример 6: Создание промокода с пользовательскими параметрами

```yaml
create_custom_promo:
  actions:
    - type: promo_manager
      action: create_promo
      promo_name: "{custom_name}"
      salt: "{custom_salt}"
      use_random: "{use_random_generation}"
      expired_seconds: "{custom_expire_seconds}"
      target_user_id: "{target_user}"
      callback_edit: false
    - type: send
      text: |
        🎯 Промокод создан с пользовательскими параметрами!
        
        Название: {promo_name}
        Код: {promo_code}
        Соль: {salt}
        Тип: {use_random|equals:true|value:Случайный|fallback:Детерминированный}
        Срок: {started_at|format:date} - {expired_at|format:date}
        Пользователь: {user_id|fallback:Глобальный}
      callback_edit: false
      chain: completed
```

**Как работает:**
- Все параметры берутся из контекста выполнения
- `{custom_name}` — название из предыдущего действия
- `{custom_salt}` — соль из пользовательского ввода
- `{use_random_generation}` — флаг случайной генерации
- `{custom_expire_seconds}` — срок действия в секундах

## Пример 7: Создание промокода с автоматическим определением пользователя

```yaml
create_auto_user_promo:
  actions:
    - type: promo_manager
      action: create_promo
      promo_name: "PERSONAL_OFFER"
      salt: "personal_{user_id}"
      use_random: false
      # target_user_id не указан - используется user_id из события
      callback_edit: false
    - type: send
      text: |
        👤 Персональный промокод создан!
        
        Название: {promo_name}
        Код: {promo_code}
        Пользователь: {user_id}
        Срок действия: {started_at|format:date} - {expired_at|format:date}
        Тип: Детерминированный (персональный)
      callback_edit: false
      chain: completed
```

**Как работает:**
- `target_user_id` не указан — используется `user_id` из события
- `salt: "personal_{user_id}"` — соль включает ID пользователя
- Промокод автоматически привязывается к текущему пользователю
- Повторный вызов с теми же параметрами вернет существующий промокод

## Пример 8: Создание промокода с проверкой существования

```yaml
create_promo_with_check:
  actions:
    - type: promo_manager
      action: check_promo
      promo_code: "{promo_code}"
      callback_edit: false
    - type: send
      text: |
        🔍 Проверка существующего промокода
        
        Код: {promo_code}
        Статус: {promo_available|equals:true|value:Уже существует|fallback:Не найден}
      callback_edit: false
      chain: true
    - type: promo_manager
      action: create_promo
      promo_name: "NEW_OFFER"
      salt: "new_offer_{timestamp}"
      use_random: true
      expired_seconds: 2592000  # 30 дней
      target_user_id: "Null"
      callback_edit: false
    - type: send
      text: |
        ✅ Новый промокод создан!
        
        Название: {promo_name}
        Код: {promo_code}
        Срок действия: {started_at|format:date} - {expired_at|format:date}
        Хэш: {hash_id}
      callback_edit: false
      chain: completed
```

**Как работает:**
- Сначала проверяется существование промокода
- Если не найден — создается новый
- `salt: "new_offer_{timestamp}"` — уникальная соль с временной меткой
- `use_random: true` — гарантирует уникальность

## Пример 9: Создание промокода с условной логикой

```yaml
create_conditional_promo:
  actions:
    - type: promo_manager
      action: create_promo
      promo_name: "{user_role|equals:admin|value:ADMIN_BONUS|fallback:USER_OFFER}"
      salt: "{user_role}_{user_id}"
      use_random: false
      expired_seconds: "{user_role|equals:admin|value:7776000|fallback:2592000}"  # 90 дней для админов, 30 для пользователей
      target_user_id: "{user_id}"
      callback_edit: false
    - type: send
      text: |
        🎯 Условный промокод создан!
        
        Название: {promo_name}
        Код: {promo_code}
        Роль: {user_role|equals:admin|value:Администратор|fallback:Пользователь}
        Срок действия: {started_at|format:date} - {expired_at|format:date}
        Тип: {use_random|equals:true|value:Случайный|fallback:Детерминированный}
      callback_edit: false
      chain: completed
```

**Как работает:**
- `promo_name` зависит от роли пользователя
- `expired_seconds` различается для разных ролей
- `salt` включает роль и ID пользователя
- Промокод автоматически адаптируется под пользователя

## Пример 10: Создание промокода с валидацией

```yaml
create_validated_promo:
  actions:
    - type: validator
      rules:
        promo_name:
          - rule: not_empty
          - rule: length_min
            value: 3
          - rule: length_max
            value: 50
        expire_seconds:
          - rule: is_number
          - rule: min_value
            value: 3600  # Минимум 1 час
          - rule: max_value
            value: 31536000  # Максимум 1 год
      callback_edit: false
      chain: true
    - type: promo_manager
      action: create_promo
      promo_name: "{promo_name}"
      salt: "{promo_salt}"
      use_random: "{use_random}"
      expired_seconds: "{expire_seconds}"
      target_user_id: "{target_user_id}"
      callback_edit: false
    - type: send
      text: |
        ✅ Валидированный промокод создан!
        
        Название: {promo_name}
        Код: {promo_code}
        Срок действия: {started_at|format:date} - {expired_at|format:date}
        Валидация: Пройдена
      callback_edit: false
      chain: completed
```

**Как работает:**
- Сначала валидируются все параметры
- `promo_name` проверяется на длину и заполненность
- `expire_seconds` проверяется на диапазон значений
- Промокод создается только после успешной валидации

## Пример 11: Получение списка всех активных промокодов

```yaml
list_all_active_promos:
  actions:
    - type: promo_manager
      action: promo_management
      operation: list
      limit: 100
      callback_edit: false
    - type: send
      text: "{response_text}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `action: promo_management` — использует модуль управления промокодами
- `operation: list` — операция получения списка
- `limit: 100` — ограничение на количество результатов
- `{response_text}` — содержит отформатированную таблицу промокодов

**Результат:**
- Таблица с колонками: ID | Код | Название
- Автоматическое форматирование и выравнивание
- Красивое отображение в моноширинном шрифте

## Пример 12: Поиск промокодов по названию

```yaml
search_promos_by_name:
  actions:
    - type: promo_manager
      action: promo_management
      operation: list
      name_pattern: "SUMMER"
      limit: 50
      callback_edit: false
    - type: send
      text: "{response_text}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `name_pattern: "SUMMER"` — поиск промокодов, содержащих "SUMMER" в названии
- Поддерживает частичное совпадение
- Результат включает заголовок с указанием примененного фильтра

## Пример 13: Фильтрация промокодов по пользователю

```yaml
list_user_promos:
  actions:
    - type: promo_manager
      action: promo_management
      operation: list
      user_filter: "{user_id}"
      limit: 50
      placeholder: true
      callback_edit: false
    - type: send
      text: "{response_text}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `user_filter: "{user_id}"` — фильтр по ID пользователя
- Поддерживает как числовые ID, так и username
- Автоматическое резолвинг username через `api_utils`

## Пример 14: Поиск промокода по коду

```yaml
find_promo_by_code:
  actions:
    - type: promo_manager
      action: promo_management
      operation: list
      promo_code: "ABC123"
      callback_edit: false
    - type: send
      text: "{response_text}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `promo_code: "ABC123"` — точный поиск по коду промокода
- Возвращает промокод с указанным кодом
- Полезно для быстрой проверки существования кода

## Пример 15: Комбинированная фильтрация

```yaml
complex_promo_search:
  actions:
    - type: promo_manager
      action: promo_management
      operation: list
      name_pattern: "BONUS"
      user_filter: "admin"
      expired_after: "2025-06-01"
      limit: 25
      callback_edit: false
    - type: send
      text: "{response_text}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- Комбинация нескольких фильтров
- `name_pattern: "BONUS"` — название содержит "BONUS"
- `user_filter: "admin"` — пользователь с username "admin"
- `expired_after: "2025-06-01"` — истекает после 1 июня 2025
- Все фильтры применяются одновременно

## Пример 16: Получение детальной информации по промокоду

```yaml
get_promo_details:
  actions:
    - type: promo_manager
      action: promo_management
      operation: details
      promo_id: "{promo_id}"
      callback_edit: false
    - type: send
      text: "{response_text}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `operation: details` — получение детальной информации
- `promo_id: "{promo_id}"` — ID промокода для детализации
- Возвращает полную информацию: код, название, статус, пользователь, даты

## Пример 17: Поиск промокода по коду с детализацией

```yaml
find_and_detail_promo:
  actions:
    - type: promo_manager
      action: promo_management
      operation: details
      promo_code: "WELCOME2025"
      callback_edit: false
    - type: send
      text: "{response_text}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `promo_code: "WELCOME2025"` — поиск по коду
- Автоматическое определение ID промокода
- Возвращает детальную информацию без необходимости знать ID

## Пример 20: Получение деталей по ID из текста события

```yaml
get_promo_from_event:
  actions:
    - type: promo_manager
      action: promo_management
      operation: details
      event_text: "{event_text}"
      callback_edit: false
    - type: send
      text: "{response_text}"
      callback_edit: false
      chain: completed
```

**Как работает:**
- `event_text: "{event_text}"` — ID промокода из текста события
- Автоматическое извлечение числового ID
- Полезно для обработки пользовательского ввода

## Лучшие практики

### ✅ Рекомендуется
- **Использовать осмысленные названия** для промокодов
- **Применять детерминированную генерацию** для повторяющихся промокодов
- **Использовать случайную генерацию** для уникальных предложений
- **Устанавливать разумные сроки действия** (не слишком короткие, не слишком длинные)
- **Использовать хэш-идентификацию** для предотвращения дублирования
- **Применять fallback значения** в плейсхолдерах
- **Валидировать параметры** перед созданием промокодов
- **Тестировать различные комбинации** параметров

### ⚠️ Не рекомендуется
- **Создавать слишком много промокодов** для одного пользователя
- **Использовать слишком длинные названия** (> 50 символов)
- **Создавать промокоды без ограничений** по сроку действия
- **Игнорировать обработку ошибок** в сценариях

## Отладка промокодов

### Рекомендации по отладке
- **Проверяйте логи сервиса** для диагностики ошибок
- **Используйте `check_promo`** для проверки существующих промокодов
- **Тестируйте различные комбинации** параметров
- **Проверяйте хэш-идентификацию** для предотвращения дублирования
- **Валидируйте входные данные** перед созданием

### Проверка промокодов
```yaml
# Тестовый сценарий для проверки промокодов
test_promos:
  actions:
    - type: promo_manager
      action: create_promo
      promo_name: "TEST_PROMO"
      salt: "test_salt"
      use_random: false
      expired_seconds: 3600  # 1 час для тестирования
      target_user_id: "Null"
      callback_edit: false
    - type: send
      text: "Тестовый промокод создан: {promo_code}"
      callback_edit: false
      chain: true
    - type: promo_manager
      action: check_promo
      promo_code: "{promo_code}"
      callback_edit: false
      chain: true
    - type: send
      text: "Проверка: {promo_available|equals:true|value:Доступен|fallback:Недоступен}"
      callback_edit: false
      chain: completed
```

## Заключение

Сервис промокодов предоставляет мощный механизм для создания, управления и проверки промокодов. Правильное использование детерминированной и случайной генерации, хэш-идентификации и интеграции со сценариями позволяет создавать гибкие и надежные системы промокодов.

Ключевые моменты:
- **Планируйте структуру промокодов** заранее
- **Используйте детерминированную генерацию** для повторяющихся кодов
- **Применяйте случайную генерацию** для уникальных предложений
- **Валидируйте параметры** перед созданием
- **Тестируйте различные сценарии** использования
- **Мониторьте создание и использование** промокодов
- **Используйте хэш-идентификацию** для оптимизации
