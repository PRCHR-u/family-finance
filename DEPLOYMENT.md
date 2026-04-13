# Family Finance Budget Utils - Deployment Guide

## 📋 Алгоритм развертывания приложения

### Вариант 1: Деплой на Linux-сервер (Ubuntu/Debian)

#### Шаг 1: Подготовка сервера

```bash
# Обновление пакетов
sudo apt update && sudo apt upgrade -y

# Установка Python 3.10+, pip, git, nginx
sudo apt install -y python3 python3-pip python3-venv git nginx

# Проверка версий
python3 --version
pip3 --version
```

#### Шаг 2: Клонирование репозитория

```bash
# Создание пользователя для приложения (опционально, но рекомендуется)
sudo useradd -m -s /bin/bash budgetuser
sudo passwd budgetuser

# Переключение на пользователя
sudo su - budgetuser

# Клонирование репозитория
cd /home/budgetuser
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> family-finance
cd family-finance
```

#### Шаг 3: Настройка виртуального окружения

```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt

# Установка production-зависимостей
pip install gunicorn
```

#### Шаг 4: Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# .env
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///./family_finance.db
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=ChangeMe123!
HOST=0.0.0.0
PORT=8000
```

**Важно:** Сгенерируйте надежный SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Шаг 5: Инициализация базы данных

```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск миграций и создание начальных данных
python3 -c "from app.database import init_db; init_db()"
```

#### Шаг 6: Настройка systemd сервиса

Создайте файл сервиса `/etc/systemd/system/family-finance.service`:

```ini
[Unit]
Description=Family Finance Budget Utils API
After=network.target

[Service]
User=budgetuser
Group=budgetuser
WorkingDirectory=/home/budgetuser/family-finance
Environment="PATH=/home/budgetuser/family-finance/venv/bin"
ExecStart=/home/budgetuser/family-finance/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always
RestartSec=10

# Логи
StandardOutput=journal
StandardError=journal
SyslogIdentifier=family-finance

[Install]
WantedBy=multi-user.target
```

Активация сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl enable family-finance
sudo systemctl start family-finance
sudo systemctl status family-finance
```

#### Шаг 7: Настройка Nginx как reverse proxy

Создайте конфиг `/etc/nginx/sites-available/family-finance`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Замените на ваш домен или IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Для веб-сокетов (если понадобятся)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Статические файлы (если есть)
    location /static/ {
        alias /home/budgetuser/family-finance/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Активация сайта:
```bash
sudo ln -s /etc/nginx/sites-available/family-finance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Шаг 8: Настройка HTTPS (рекомендуется)

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление сертификатов
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

### Вариант 2: Деплой с Docker

#### Шаг 1: Создание Dockerfile

Файл `Dockerfile` уже создан в проекте.

#### Шаг 2: Сборка образа

```bash
docker build -t family-finance:latest .
```

#### Шаг 3: Запуск контейнера

```bash
# Создание тома для сохранения данных
docker volume create family-finance-data

# Запуск контейнера
docker run -d \
  --name family-finance \
  -p 8000:8000 \
  -v family-finance-data:/app/data \
  -e SECRET_KEY=your-super-secret-key \
  -e DATABASE_URL=sqlite:///./data/family_finance.db \
  -e ADMIN_EMAIL=admin@example.com \
  -e ADMIN_PASSWORD=ChangeMe123! \
  --restart unless-stopped \
  family-finance:latest
```

#### Шаг 4: Docker Compose (рекомендуется)

Файл `docker-compose.yml` уже создан в проекте.

```bash
# Запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

---

### Вариант 3: Деплой на облачные платформы

#### Heroku

1. Установите Heroku CLI
2. `heroku login`
3. `heroku create your-app-name`
4. `git push heroku main`
5. Настройте переменные окружения в панели Heroku

#### Railway.app

1. Залейте код на GitHub
2. Подключите репозиторий в Railway
3. Настройте переменные окружения
4. Деплой автоматический

#### Render.com

1. Создайте новый Web Service
2. Подключите GitHub репозиторий
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## 🔧 Проверка работоспособности

### После деплоя выполните:

```bash
# Проверка доступности API
curl http://your-domain.com/api/docs

# Проверка здоровья
curl http://your-domain.com/health

# Логирование
# Для systemd:
sudo journalctl -u family-finance -f

# Для Docker:
docker logs -f family-finance

# Для direct run:
tail -f server.log
```

### Первый вход:

1. Откройте `http://your-domain.com`
2. Войдите под администратором:
   - Email: `admin@example.com` (или тот, что указали в ADMIN_EMAIL)
   - Пароль: `ChangeMe123!` (или тот, что указали в ADMIN_PASSWORD)
3. **Сразу смените пароль!**

---

## 📊 Мониторинг и обслуживание

### Логи приложения

```bash
# Просмотр последних 100 строк
tail -f /home/budgetuser/family-finance/server.log

# Поиск ошибок
grep ERROR /home/budgetuser/family-finance/server.log
```

### Резервное копирование БД

```bash
# Скрипт бэкапа (добавьте в crontab)
cp /home/budgetuser/family-finance/family_finance.db /backup/family_finance_$(date +%Y%m%d).db
```

### Обновление приложения

```bash
cd /home/budgetuser/family-finance
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart family-finance
```

### Перезапуск сервиса

```bash
# systemd
sudo systemctl restart family-finance

# Docker
docker restart family-finance

# Docker Compose
docker-compose restart
```

---

## ⚠️ Важные замечания по безопасности

1. **Измените все пароли по умолчанию** сразу после первого входа
2. **Настройте HTTPS** перед использованием в продакшене
3. **Регулярно делайте бэкапы** базы данных
4. **Ограничьте доступ** к серверу по SSH (используйте ключи, не пароли)
5. **Настройте firewall**:
   ```bash
   sudo ufw allow 22/tcp  # SSH
   sudo ufw allow 80/tcp  # HTTP
   sudo ufw allow 443/tcp # HTTPS
   sudo ufw enable
   ```
6. **Храните SECRET_KEY в секрете**, никогда не коммитьте в git

---

## 🆘 Troubleshooting

### Приложение не запускается

```bash
# Проверка логов
sudo journalctl -u family-finance -n 50

# Проверка порта
sudo lsof -i :8000

# Проверка прав доступа
ls -la /home/budgetuser/family-finance/
```

### Ошибки базы данных

```bash
# Проверка целостности БД
sqlite3 /home/budgetuser/family-finance/family_finance.db "PRAGMA integrity_check;"

# Восстановление из бэкапа
cp /backup/family_finance_YYYYMMDD.db /home/budgetuser/family-finance/family_finance.db
sudo systemctl restart family-finance
```

### Проблемы с Nginx

```bash
# Проверка конфига
sudo nginx -t

# Перезагрузка
sudo systemctl reload nginx

# Логи Nginx
sudo tail -f /var/log/nginx/error.log
```

---

## 📞 Контакты и поддержка

При возникновении проблем:
1. Проверьте логи приложения
2. Проверьте логи системного сервиса
3. Убедитесь, что все переменные окружения настроены правильно
4. Проверьте доступность портов
