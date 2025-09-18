FROM python:3.11-slim

# Устанавливаем системные зависимости + libmagic для python-magic
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /workspace

# Устанавливаем зависимости НАПРЯМУЮ (автономный образ)
RUN pip install \
    aiogram==3.4.1 \
    PyYAML==6.0.1 \
    SQLAlchemy==2.0.25 \
    aiosqlite==0.19.0 \
    python-dotenv==1.0.0 \
    pytz==2024.1 \
    unidecode \
    emoji \
    requests>=2.31.0 \
    pydub==0.25.1 \
    ffmpeg-python==0.2.0 \
    python-magic==0.4.27 \
    telethon==1.41.0 \
    gigachat>=0.1.0 \
    telegramify-markdown>=0.1.0
