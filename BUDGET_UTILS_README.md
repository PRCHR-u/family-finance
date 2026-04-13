# Утилиты анализа долгов и планирования бюджета

## Обзор

Добавлен новый модуль `app/budget_utils.py` с функциями для:
- Анализа прироста и уменьшения долга
- Планирования недельного бюджета
- Расчета ежедневного бюджета (по запросу)
- Сводной информации о бюджете

## Новые API эндпоинты

### 1. Анализ изменения долгов
**GET** `/analytics/debt-change`

**Параметры:**
- `period_from` (date) - начало периода
- `period_to` (date) - конец периода

**Возвращает:**
- `opening_debt` - долг на начало периода
- `closing_debt` - долг на конец периода
- `debt_change` - абсолютное изменение долга
- `new_debts` - список новых долгов в периоде
- `repayments` - список платежей по долгам
- `debt_increase` - сумма новых долгов
- `debt_decrease` - сумма погашений
- `net_change` - чистое изменение (увеличение - уменьшение)

### 2. Недельный бюджет
**GET** `/analytics/weekly-budget`

**Параметры:**
- `reference_date` (date, optional) - дата начала периода (по умолчанию сегодня)
- `weeks_ahead` (int, 1-12) - количество недель для планирования (по умолчанию 1)

**Возвращает:**
- `weekly_budget` - общий бюджет на неделю
- `daily_budget` - средний дневной бюджет
- `mandatory_expenses` - обязательные расходы (список и сумма)
- `planned_expenses` - средние плановые расходы
- `income` - доходы за период
- `available_income` - доступный доход
- `balance` - баланс (доходы - расходы)
- `recommendation` - рекомендация по бюджету

### 3. Ежедневный бюджет (по запросу)
**GET** `/analytics/daily-budget`

**Параметры:**
- `target_date` (date, optional) - дата расчета (по умолчанию сегодня)

**Возвращает:**
- `date` - дата расчета
- `mandatory_expenses` - обязательные расходы на день
- `base_daily_budget` - базовый дневной бюджет
- `discretionary_budget` - дискреционный бюджет (на необязательные траты)
- `total_budget` - общий бюджет на день
- `recommendations` - список рекомендаций

### 4. Сводка бюджета
**GET** `/analytics/budget-summary`

**Параметры:**
- `period_from` (date) - начало периода
- `period_to` (date) - конец периода

**Возвращает:**
- `period` - информация о периоде (даты, количество дней/недель)
- `debt_analysis` - анализ изменения долгов
- `budget_overview` - обзор бюджета (средние значения)
- `financial_health` - оценка финансового здоровья:
  - `debt_trend` - тренд долга (increasing/decreasing/stable)
  - `budget_balance` - баланс бюджета (surplus/deficit/balanced)

## Примеры использования

### Анализ долгов за месяц
```
GET /analytics/debt-change?period_from=2025-01-01&period_to=2025-01-31
```

### План бюджета на следующую неделю
```
GET /analytics/weekly-budget?reference_date=2025-01-20&weeks_ahead=1
```

### Ежедневный бюджет на завтра
```
GET /analytics/daily-budget?target_date=2025-01-16
```

### Сводка за квартал
```
GET /analytics/budget-summary?period_from=2025-01-01&period_to=2025-03-31
```

## Файлы изменений

1. **app/budget_utils.py** (новый файл) - основные функции утилит
2. **app/schemas.py** - добавлены схемы Pydantic:
   - `DebtChangeAnalysis`
   - `WeeklyBudgetResponse`
   - `DailyBudgetResponse`
   - `BudgetSummaryResponse`
3. **app/main.py** - добавлены 4 новых API эндпоинта

## Требования

Все зависимости уже установлены в проекте:
- SQLAlchemy
- Pydantic
- FastAPI
