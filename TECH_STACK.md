# 🛠️ Стек технологий Family Finance API

## Основной стек

### Backend
- **Python 3.12** - язык программирования
- **FastAPI 0.115.6** - современный асинхронный веб-фреймворк
- **SQLAlchemy 2.0.36** - ORM для работы с базой данных
- **Pydantic 2.10.4** - валидация данных и сериализация
- **SQLite** - легковесная база данных (встроенная)

### Аутентификация и безопасность
- **python-jose 3.4.0** - работа с JWT токенами
- **passlib 1.7.4 + bcrypt 4.2.1** - хеширование паролей
- **OAuth2 Password Bearer** - схема аутентификации

### Работа с данными
- **Pandas 2.2.3** - обработка табличных данных
- **NumPy 1.26.4** - числовые вычисления
- **openpyxl 3.1.5** - работа с Excel файлами
- **python-multipart 0.0.20** - обработка form-data запросов

### Сервер и деплой
- **Uvicorn 0.34.0** - ASGI сервер для разработки
- **Gunicorn** - production WSGI сервер
- **Docker** - контейнеризация приложения

### Frontend (опционально)
- **Vite** - сборщик frontend
- **React/Vue** - фреймворк интерфейса (настраивается отдельно)

---

## Структура зависимостей

```txt
requirements.txt
├── sqlalchemy==2.0.36          # ORM
├── fastapi==0.115.6            # Web framework
├── uvicorn[standard]==0.34.0   # ASGI server
├── pydantic==2.10.4            # Data validation
├── pydantic-settings==2.7.0    # Settings management
├── python-jose[cryptography]==3.4.0  # JWT
├── passlib[bcrypt]==1.7.4      # Password hashing
├── bcrypt==4.2.1               # Hash algorithm
├── python-multipart==0.0.20    # Form data
├── pandas==2.2.3               # Data processing
├── numpy==1.26.4               # Numeric operations
├── openpyxl==3.1.5             # Excel files
└── aiofiles==24.1.0            # Async file operations
```

---

## Версии и совместимость

| Компонент | Версия | Мин. Python | Примечание |
|-----------|--------|-------------|------------|
| Python | 3.12 | 3.11+ | Рекомендуется 3.12 |
| FastAPI | 0.115.6 | 3.8+ | Стабильная версия |
| SQLAlchemy | 2.0.36 | 3.7+ | Новая версия 2.x |
| Pydantic | 2.10.4 | 3.8+ | Версия 2.x с breaking changes |
| Pandas | 2.2.3 | 3.9+ | Совместима с NumPy 1.26 |
| NumPy | 1.26.4 | 3.9+ | Последняя стабильная 1.x |

---

## Почему выбраны эти версии?

### NumPy 1.26.4 вместо 2.x
- ✅ Полная совместимость с Pandas 2.2.3
- ✅ Стабильная версия без breaking changes
- ✅ Поддержка Python 3.11-3.13
- ❌ NumPy 2.x требует обновления многих зависимостей

### FastAPI 0.115.6 вместо latest
- ✅ Проверенная стабильная версия
- ✅ Все необходимые функции доступны
- ✅ Известные баги исправлены
- ❌ Latest может содержать нестабильные изменения

### SQLAlchemy 2.0.36
- ✅ Новый синтаксис 2.0
- ✅ Улучшенная производительность
- ✅ Долгосрочная поддержка
- ⚠️ Требует обновления кода с 1.x

---

## Альтернативные конфигурации

### Для production (PostgreSQL)
```txt
psycopg2-binary==2.9.9  # PostgreSQL драйвер
alembic==1.13.1         # Миграции БД
```

### Для расширенного мониторинга
```txt
prometheus-client==0.19.0  # Метрики
sentry-sdk==1.39.0         # Отслеживание ошибок
```

### Для тестирования
```txt
pytest==7.4.3              # Тестовый фреймворк
httpx==0.26.0              # Async HTTP клиент
pytest-asyncio==0.23.3     # Async тесты
```

---

## Требования к системе

### Минимальные
- CPU: 1 ядро
- RAM: 512 MB
- Disk: 1 GB
- OS: Linux/MacOS/Windows 10+

### Рекомендуемые
- CPU: 2 ядра
- RAM: 1 GB
- Disk: 5 GB
- OS: Ubuntu 22.04 LTS / Debian 12

---

## Установка на Windows

1. Установите Python 3.12 с [python.org](https://www.python.org/downloads/)
2. Создайте виртуальное окружение:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Установите зависимости:
   ```powershell
   pip install -r requirements.txt
   ```
4. Запустите сервер:
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## Обновление зависимостей

Проверяйте уязвимости регулярно:
```bash
pip install pip-audit
pip-audit -r requirements.txt
```

Обновляйте зависимости:
```bash
pip install --upgrade -r requirements.txt
```

---

**Примечание:** Версии зафиксированы для обеспечения стабильности. Обновляйте только после тестирования в development среде.
