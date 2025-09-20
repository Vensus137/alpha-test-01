FROM python:3.11-slim

# Устанавливаем все системные зависимости за один раз
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    curl \
    ffmpeg \
    git \
    libmagic1 \
    libmagic-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /workspace

# Устанавливаем зависимости НАПРЯМУЮ (автономный образ)
# Шаг 1: Основные зависимости
RUN pip install aiogram==3.4.1 PyYAML==6.0.1 SQLAlchemy==2.0.25 aiosqlite==0.19.0

# Шаг 2: Утилиты
RUN pip install python-dotenv==1.0.0 pytz==2024.1 unidecode emoji

# Шаг 3: Сетевые библиотеки
RUN pip install requests>=2.31.0

# Шаг 4: Медиа обработка
RUN pip install pydub==0.25.1 ffmpeg-python==0.2.0 python-magic==0.4.27

# Шаг 5: Telegram библиотеки
RUN pip install telethon==1.41.0

# Шаг 6: AI и форматирование
RUN pip install gigachat>=0.1.0 telegramify-markdown>=0.1.0
