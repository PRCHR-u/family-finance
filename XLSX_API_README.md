# XLSX Interpreter API

Интеграция интерпретатора XLSX файлов в приложение Family Finance.

## Обзор

Добавлен набор REST API эндпоинтов для работы с XLSX файлами через функционал, аналогичный утилите `xlsx_interpreter.py`.

## Новые эндпоинты

### 1. Загрузка и информация о файле

**POST /xlsx/upload**

Загрузка XLSX файла и получение информации о нём.

**Параметры:**
- `file` (UploadFile): XLSX файл для загрузки

**Ответ:**
```json
{
  "filename": "example.xlsx",
  "sheet_count": 2,
  "sheets": ["Sheet1", "Sheet2"]
}
```

---

### 2. Чтение данных из листа

**POST /xlsx/read**

Чтение данных из указанного листа XLSX файла.

**Параметры:**
- `file` (UploadFile): XLSX файл
- `sheet_name` (query, optional): Имя листа (по умолчанию первый)
- `head` (query, optional): Количество строк для чтения

**Ответ:**
```json
{
  "name": "Sheet1",
  "columns": ["Date", "Amount", "Description"],
  "data": [
    {"Date": "2024-01-01", "Amount": 1000, "Description": "Payment"},
    {"Date": "2024-01-02", "Amount": 2000, "Description": "Refund"}
  ]
}
```

---

### 3. Конвертация в JSON

**POST /xlsx/to-json**

Конвертация XLSX листа в JSON формат.

**Параметры:**
- `file` (UploadFile): XLSX файл
- `sheet_name` (query, optional): Имя листа

**Ответ:** JSON документ с данными листа

**Content-Type:** `application/json`

---

### 4. Конвертация в CSV

**POST /xlsx/to-csv**

Конвертация XLSX листа в CSV формат.

**Параметры:**
- `file` (UploadFile): XLSX файл
- `sheet_name` (query, optional): Имя листа

**Ответ:** CSV файл для скачивания

**Content-Type:** `text/csv`  
**Content-Disposition:** `attachment; filename=<original_name>.csv`

---

### 5. Информация о файле на сервере

**GET /xlsx/info/{filename:path}**

Получение информации о XLSX файле, расположенном на сервере.

**Параметры:**
- `filename` (path): Путь к файлу на сервере

**Ответ:**
```json
{
  "filename": "ДОЛГИ.xlsx",
  "sheet_count": 1,
  "sheets": ["Sheet1"]
}
```

---

### 6. Чтение файла с сервера

**GET /xlsx/read/{filename:path}**

Чтение данных из XLSX файла на сервере.

**Параметры:**
- `filename` (path): Путь к файлу на сервере
- `sheet_name` (query, optional): Имя листа
- `head` (query, optional): Количество строк для чтения

**Ответ:** Данные листа в формате XLSXSheetData

---

## Примеры использования

### cURL

#### Загрузка файла и получение информации:
```bash
curl -X POST "http://localhost:8000/xlsx/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@ДОЛГИ.xlsx"
```

#### Чтение первых 10 строк:
```bash
curl -X POST "http://localhost:8000/xlsx/read?head=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@ДОЛГИ.xlsx"
```

#### Конвертация в JSON:
```bash
curl -X POST "http://localhost:8000/xlsx/to-json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@ДОЛГИ.xlsx" > output.json
```

#### Конвертация в CSV:
```bash
curl -X POST "http://localhost:8000/xlsx/to-csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@ДОЛГИ.xlsx" > output.csv
```

#### Чтение файла с сервера:
```bash
curl -X GET "http://localhost:8000/xlsx/read/ДОЛГИ.xlsx?head=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Python (requests)

```python
import requests

TOKEN = "YOUR_ACCESS_TOKEN"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Загрузка файла
with open("ДОЛГИ.xlsx", "rb") as f:
    response = requests.post(
        "http://localhost:8000/xlsx/upload",
        files={"file": f},
        headers=headers
    )
    print(response.json())

# Чтение данных
with open("ДОЛГИ.xlsx", "rb") as f:
    response = requests.post(
        "http://localhost:8000/xlsx/read",
        params={"head": 10},
        files={"file": f},
        headers=headers
    )
    data = response.json()
    for row in data["data"]:
        print(row)

# Конвертация в JSON
with open("ДОЛГИ.xlsx", "rb") as f:
    response = requests.post(
        "http://localhost:8000/xlsx/to-json",
        files={"file": f},
        headers=headers
    )
    with open("output.json", "w") as out:
        out.write(response.text)
```

---

## Модели данных

### XLSXFileInfo
```python
class XLSXFileInfo(BaseModel):
    filename: str          # Имя файла
    sheet_count: int       # Количество листов
    sheets: List[str]      # Список имён листов
```

### XLSXSheetData
```python
class XLSXSheetData(BaseModel):
    name: str              # Имя листа
    columns: List[str]     # Названия колонок
    data: List[Dict]       # Данные в виде списка словарей
```

---

## Обработка ошибок

API возвращает стандартные HTTP коды ошибок:

- **400 Bad Request**: Некорректный формат файла или параметров
- **401 Unauthorized**: Требуется авторизация
- **404 Not Found**: Файл не найден (для эндпоинтов с путём к серверу)

Пример ответа при ошибке:
```json
{
  "detail": "Файл должен быть в формате XLSX"
}
```

---

## Требования

- Python 3.12+
- pandas
- openpyxl
- python-multipart (для обработки загружаемых файлов)

Все зависимости установлены в проекте.
