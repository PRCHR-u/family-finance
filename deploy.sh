#!/bin/bash

# Family Finance Budget Utils - Quick Deploy Script
# Автоматическая установка и запуск приложения

set -e

echo "🚀 Family Finance Budget Utils - Быстрый деплой"
echo "================================================"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 не найден. Установите Python 3.10+${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python найден:$(python3 --version)${NC}"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Виртуальное окружение создано${NC}"
else
    echo -e "${YELLOW}⚠️  Виртуальное окружение уже существует${NC}"
fi

# Активация виртуального окружения
echo "🔌 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📥 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

echo -e "${GREEN}✅ Зависимости установлены${NC}"

# Создание .env файла
if [ ! -f ".env" ]; then
    echo "⚙️  Создание файла .env..."
    cp .env.example .env
    
    # Генерация SECRET_KEY
    echo "🔑 Генерация SECRET_KEY..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/" .env
    
    echo -e "${GREEN}✅ Файл .env создан${NC}"
    echo -e "${YELLOW}⚠️  Измените ADMIN_EMAIL и ADMIN_PASSWORD в файле .env!${NC}"
else
    echo -e "${YELLOW}⚠️  Файл .env уже существует${NC}"
fi

# Инициализация базы данных
echo "💾 Инициализация базы данных..."
python3 -c "from app.database import init_db; init_db()"
echo -e "${GREEN}✅ База данных инициализирована${NC}"

# Запуск сервера
echo ""
echo "🎉 Готово к запуску!"
echo ""
echo "Выберите режим запуска:"
echo "  1. Production (Gunicorn) - для сервера"
echo "  2. Development (Uvicorn) - для локальной разработки"
echo ""
read -p "Ваш выбор [1/2]: " choice

case $choice in
    1)
        echo "🚀 Запуск в production режиме (Gunicorn)..."
        echo "Сервер будет доступен на http://0.0.0.0:8000"
        exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
        ;;
    2)
        echo "🔧 Запуск в development режиме (Uvicorn)..."
        echo "Сервер будет доступен на http://localhost:8000"
        exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    *)
        echo "🏃 Запуск в production режиме по умолчанию..."
        exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
        ;;
esac
