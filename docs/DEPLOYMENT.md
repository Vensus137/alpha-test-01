# 🚀 Coreness - Простое развертывание

## 📥 Установка

### 1. Скачайте скрипт установки
```bash
# Скачайте core_updater.py в любую папку
wget https://github.com/Vensus137/Coreness/raw/main/tools/core/core_updater.py
```

### 2. Запустите установку
```bash
python core_updater.py
```

### 3. Следуйте инструкциям
- Выберите "Первичная установка"
- Подтвердите установку
- Дождитесь завершения

**Готово!** Coreness установлен и готов к работе.

---

## 🎮 Управление

После установки доступны глобальные команды:

### Основные команды
```bash
coreness start      # Запустить Coreness
coreness stop       # Остановить Coreness
coreness restart    # Перезапустить Coreness
coreness logs       # Показать логи
coreness status     # Показать статус
coreness update     # Обновить Coreness
coreness help       # Показать справку
```

### Короткие алиасы
```bash
coreness-start      # Запустить
coreness-stop       # Остановить
coreness-restart    # Перезапустить
coreness-logs       # Логи
coreness-status     # Статус
coreness-update     # Обновить
```

---

## 🔄 Обновление

### Автоматическое обновление
```bash
coreness update
```

### Ручное обновление
```bash
# Перейдите в папку проекта
cd /path/to/coreness

# Запустите скрипт обновления
python tools/core/core_updater.py
```

---

## 🆘 Помощь

### Встроенная справка
```bash
# Показать все доступные команды
coreness help
```

### Основные команды для диагностики
```bash
# Проверить статус системы
coreness status

# Посмотреть логи в реальном времени
coreness logs

# Перезапустить при проблемах
coreness restart
```

### Если что-то не работает
```bash
# Проверить Docker
docker --version
docker-compose --version

# Перезапустить Docker (Linux)
sudo systemctl restart docker

# Переустановить команды
cd docker/commands
bash install_commands.sh
```