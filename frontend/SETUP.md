# Frontend Setup Guide

## 📋 Требования

- Node.js 18+ 
- npm или yarn
- Запущенный бэкенд на http://localhost:8000

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd frontend
npm install
```

### 2. Конфигурация

Файл `.env` уже создан с настройками по умолчанию:

```env
VITE_API_URL=http://localhost:8000
```

При необходимости измените URL API.

### 3. Запуск в режиме разработки

```bash
npm run dev
```

Приложение будет доступно по адресу: **http://localhost:5173**

Vite автоматически настроил proxy для всех API endpoints, поэтому CORS ошибок не будет.

### 4. Сборка для продакшена

```bash
npm run build
```

Билд собирается в папку `../static` для интеграции с FastAPI.

## 📁 Структура API клиентов

Все API сервисы находятся в `src/api/services.js`:

- `authService` - аутентификация и регистрация
- `userService` - управление пользователями
- `debtService` - долги и платежи
- `expenseService` - расходы
- `incomeService` - доходы
- `creditCardService` - кредитные карты
- `repaymentService` - подтверждения платежей
- `analyticsService` - аналитика и отчеты
- `auditLogService` - логи аудита
- `creditorService` - кредиторы
- `creditCardIssuerService` - эмитенты карт
- `debtHistoryService` - история долгов
- `importService` - импорт из Excel
- `recordService` - финансовые записи

## 🔧 Proxy конфигурация

В `vite.config.js` настроены proxy для всех endpoints:

- `/auth/*` → http://localhost:8000/auth/*
- `/users/*` → http://localhost:8000/users/*
- `/debts/*` → http://localhost:8000/debts/*
- `/expenses/*` → http://localhost:8000/expenses/*
- `/incomes/*` → http://localhost:8000/incomes/*
- `/credit-cards/*` → http://localhost:8000/credit-cards/*
- `/analytics/*` → http://localhost:8000/analytics/*
- и другие...

## 🎨 Стек технологий

- **React 19** - UI библиотека
- **Vite** - сборщик
- **TailwindCSS 4** - стилизация
- **React Router v7** - роутинг
- **React Query** - работа с серверным состоянием
- **Axios** - HTTP клиент

## 🔐 Аутентификация

Токен сохраняется в `localStorage` и автоматически добавляется ко всем запросам через axios interceptor.

При получении 401 ошибки пользователь перенаправляется на страницу логина.

## 📝 Учетные данные для тестирования

После запуска бэкенда используйте:

- Email: `admin@example.com`
- Пароль: `ChangeMe123!`

Или зарегистрируйте нового пользователя через форму регистрации.
