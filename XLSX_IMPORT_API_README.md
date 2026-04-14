# XLSX Import API - Импорт данных из Excel в базу

## Обзор

Новый эндпоинт `/xlsx/import` позволяет загружать данные из XLSX файлов напрямую в базу данных приложения. Поддерживается автоматическое определение типа данных и маппинг колонок с различными названиями (на русском и английском языках).

## Эндпоинт

```
POST /xlsx/import
```

### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| file | File | Да | XLSX файл для импорта |
| sheet_name | Query | Нет | Имя листа (по умолчанию первый лист) |
| entity_type | Query | Нет | Тип данных: `debt`, `income`, `expense`, `credit_card`, `auto` (по умолчанию) |

### Поддерживаемые типы сущностей

#### 1. Debt (Долги)
**Колонки для маппинга:**
- `creditor_name`: creditor, кредитор, название_кредитора
- `principal_amount`: principal, сумма_долга, основной_долг, тело_долга
- `start_date`: date, дата_начала, дата
- `planned_payoff_date`: planned_date, дата_погашения, плановая_дата
- `interest_rate`: interest, ставка, процентная_ставка
- `comment`: comments, комментарий, примечание
- `current_balance`: balance, текущий_баланс, остаток

#### 2. Income (Доходы)
**Колонки для маппинга:**
- `amount`: сумма, доход
- `income_date`: date, дата_дохода, дата
- `category`: категория (salary, bonus, scholarship, gift, investment, freelance, other)
- `description`: desc, описание, комментарий
- `is_actual`: actual, актуальный

#### 3. Expense (Расходы)
**Колонки для маппинга:**
- `amount`: сумма, расход
- `due_date`: date, дата_расхода, дата, срок_оплаты
- `category`: категория (rent, utilities, food, transport, entertainment, education, medical, gifts, loan_repayment, other)
- `description`: desc, описание, комментарий
- `is_mandatory`: mandatory, обязательный
- `is_completed`: completed, выполнен

#### 4. CreditCard (Кредитные карты)
**Колонки для маппинга:**
- `card_name`: card, название_карты, карта
- `grace_start_date`: grace_start, дата_начала_льготного, дата_начала
- `grace_period_days`: grace_period, льготный_период, дней_льготного
- `current_debt`: debt, текущий_долг, долг
- `comment`: comments, комментарий, примечание

### Автоматическое определение типа

При `entity_type=auto` (по умолчанию) система пытается определить тип данных по:
1. Названию листа (например, "Debts", "Долги", "Income", "Доходы")
2. Названиям колонок в файле

## Примеры использования

### cURL

#### Импорт долгов
```bash
curl -X POST "http://localhost:8000/xlsx/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@debts.xlsx" \
  -F "sheet_name=Sheet1" \
  -F "entity_type=debt"
```

#### Импорт с автоопределением
```bash
curl -X POST "http://localhost:8000/xlsx/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@data.xlsx"
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/xlsx/import"
headers = {"Authorization": f"Bearer {YOUR_TOKEN}"}
files = {"file": open("debts.xlsx", "rb")}
params = {
    "sheet_name": "Sheet1",
    "entity_type": "debt"
}

response = requests.post(url, headers=headers, files=files, params=params)
result = response.json()

print(f"Всего строк: {result['total_rows']}")
print(f"Добавлено: {result['inserted']}")
print(f"Обновлено: {result['updated']}")
print(f"Пропущено: {result['skipped']}")
if result['errors']:
    print("Ошибки:", result['errors'])
```

### JavaScript (fetch)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('sheet_name', 'Sheet1');
formData.append('entity_type', 'debt');

const response = await fetch('/xlsx/import', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`
    },
    body: formData
});

const result = await response.json();
console.log(result);
```

## Формат ответа

```json
{
    "filename": "debts.xlsx",
    "sheet_name": "Sheet1",
    "total_rows": 100,
    "inserted": 95,
    "updated": 3,
    "skipped": 2,
    "errors": [
        {
            "row": 15,
            "error": "Отсутствуют обязательные поля (кредитор, сумма, дата начала)"
        },
        {
            "row": 47,
            "error": "неверный формат даты"
        }
    ]
}
```

## Обработка ошибок

### Статусы HTTP

- `200 OK` - Успешный импорт
- `400 Bad Request` - Ошибка в формате файла или данных
- `401 Unauthorized` - Требуется авторизация
- `404 Not Found` - Файл не найден (для серверных файлов)

### Модерация

- Записи, созданные обычными пользователями, получают статус `PENDING`
- Записи, созданные администраторами, автоматически получают статус `APPROVED`

## Требования к файлу

1. Формат: `.xlsx`
2. Кодировка: UTF-8 (рекомендуется)
3. Первая строка должна содержать заголовки колонок
4. Обязательные поля должны быть заполнены

## Примечания

- При импорте проверяются дубликаты (для долгов: по кредитору и дате начала)
- Даты поддерживаются в различных форматах (ISO, Excel date serial)
- Числовые значения могут содержать запятую или точку как разделитель
- Пустые значения интерпретируются как `NULL`
