FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем все файлы проекта
COPY . .

# Установка poetry и зависимостей
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

# Установка прав на выполнение
RUN chmod +x /app/alembic/versions/*.py

CMD ["python", "__main__.py"] 