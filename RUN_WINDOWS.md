# Инструкция по запуску приложения на Windows

## Предварительные требования

1. **Python 3.10+** - скачайте с [python.org](https://www.python.org/downloads/)
2. **Git** (опционально) - для клонирования репозитория

## Вариант 1: Быстрый запуск через PowerShell

### Шаг 1: Откройте PowerShell в папке проекта

```powershell
cd C:\Users\user\family-finance
```

### Шаг 2: Создайте виртуальное окружение

```powershell
python -m venv venv
```

### Шаг 3: Активируйте виртуальное окружение

```powershell
.\venv\Scripts\Activate.ps1
```

> ⚠️ **Если ошибка выполнения скриптов:**
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Шаг 4: Установите зависимости

```powershell
pip install sqlalchemy fastapi uvicorn pydantic python-jose[cryptography] passlib[bcrypt] python-multipart pandas openpyxl bcrypt==4.0.1
```

### Шаг 5: Настройте переменные окружения (опционально)

Создайте файл `.env` в корне проекта:

```env
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=ChangeMe123!
DATABASE_URL=sqlite:///./family_finance.db
SECRET_KEY=your-secret-key-here
```

Или используйте переменные окружения PowerShell:

```powershell
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="ChangeMe123!"
```

### Шаг 6: Запустите сервер

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Шаг 7: Откройте браузер

Перейдите по адресу: **http://localhost:8000/docs**

---

## Вариант 2: Использование Docker (рекомендуется)

### Требования

- [Docker Desktop для Windows](https://www.docker.com/products/docker-desktop/)

### Запуск

```powershell
docker-compose up -d --build
```

### Проверка логов

```powershell
docker-compose logs -f
```

### Остановка

```powershell
docker-compose down
```

Приложение будет доступно по адресу: **http://localhost:8000/docs**

---

## Первый вход

После запуска используйте учетные данные администратора:

- **Логин:** `admin`
- **Пароль:** `ChangeMe123!` (или значение из `ADMIN_PASSWORD`)

### Получение токена доступа

```powershell
# Через curl
curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"ChangeMe123!"}'

# Или через PowerShell
$body = @{username="admin";password="ChangeMe123!"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method Post -ContentType "application/json" -Body $body
```

---

## Управление справочниками

После входа в систему через Swagger UI (http://localhost:8000/docs):

1. **Кредиторы:** `/creditors` (GET, POST, PATCH, DELETE)
2. **Эмитенты кредитных карт:** `/credit-card-issuers` (GET, POST, PATCH, DELETE)

Все операции требуют авторизации (кнопка "Authorize" в Swagger UI).

---

## Устранение проблем

### Ошибка bcrypt

```
ValueError: password cannot be longer than 72 bytes
```

**Решение:** Установите совместимую версию bcrypt:
```powershell
pip install bcrypt==4.0.1
```

### Ошибка отсутствия модуля

```
ModuleNotFoundError: No module named 'sqlalchemy'
```

**Решение:** Убедитесь, что виртуальное окружение активировано и зависимости установлены:
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Порт 8000 занят

**Решение:** Используйте другой порт:
```powershell
uvicorn app.main:app --reload --port 8001
```

---

## Резервное копирование базы данных

База данных находится в файле `family_finance.db` в корне проекта.

Для резервного копирования:
```powershell
Copy-Item family_finance.db family_finance_backup.db
```

---

## Дополнительная документация

- Полное руководство по деплою: [DEPLOYMENT.md](DEPLOYMENT.md)
- API документация: http://localhost:8000/docs
- Исходный код: [/workspace/app](/workspace/app)
