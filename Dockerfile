FROM python:3.12-slim

# Рабочая директория
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Копирование кода приложения
COPY . .

# Создание директории для данных (БД, логи)
RUN mkdir -p /app/data /app/logs

# Переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:///./data/family_finance.db \
    HOST=0.0.0.0 \
    PORT=8000

# Порт приложения
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Запуск приложения через Gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
