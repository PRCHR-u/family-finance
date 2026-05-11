import pandas as pd
from datetime import datetime
from app.database import get_db, engine, Base
from app.models import DebtHistory
from sqlalchemy.orm import sessionmaker
import re

def clean_value(val):
    """Очистка значения от лишних символов"""
    if pd.isna(val) or val == '':
        return None
    if isinstance(val, (int, float)):
        if pd.isna(val):
            return None
        return float(val)
    # Удаляем пробелы и заменяем запятую на точку
    val_str = str(val).strip().replace(',', '.').replace(' ', '')
    # Пробуем преобразовать в число
    try:
        return float(val_str)
    except (ValueError, TypeError):
        return None

def parse_date(val):
    """Парсинг даты из различных форматов"""
    if pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        val = val.strip()
        # Пробуем различные форматы
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']:
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return None

def import_debts_from_excel(file_path: str = 'ДОЛГИ.xlsx'):
    """Импорт данных о долгах из Excel файла"""
    
    # Читаем Excel файл без заголовков, так как структура сложная
    df = pd.read_excel(file_path, header=None)
    
    # Создаем сессию базы данных
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Очищаем существующие данные (опционально)
        db.query(DebtHistory).delete()
        
        imported_count = 0
        
        # Определяем строки-заголовки (где в колонке 1 текст "СБЕР" и т.д.)
        header_row_indices = []
        for idx, row in df.iterrows():
            first_col_val = row.iloc[1] if len(row) > 1 else None
            if isinstance(first_col_val, str) and first_col_val.strip() == 'СБЕР':
                header_row_indices.append(idx)
        
        # Проходим по секциям: заголовок -> данные до следующего заголовка
        current_header_row = None
        creditor_columns_map = {}
        
        for section_idx, header_idx in enumerate(header_row_indices):
            # Определяем конец текущей секции (следующий заголовок или конец файла)
            if section_idx + 1 < len(header_row_indices):
                end_idx = header_row_indices[section_idx + 1]
            else:
                end_idx = len(df)
            
            # Читаем заголовок текущей секции
            current_header_row = df.iloc[header_idx]
            creditor_columns_map = {}
            for col_idx in range(1, min(8, len(current_header_row))):
                header_val = current_header_row.iloc[col_idx]
                if isinstance(header_val, str):
                    header_val = header_val.strip()
                    # Пропускаем служебные колонки: "ВСЕГО", "разница", "изменение долга..."
                    if header_val in ['ВСЕГО', 'разница'] or 'изменение долга' in header_val.lower():
                        continue
                    # Преобразуем имена кредиторов при необходимости
                    # "ОЛЯ т-банк" -> "ОЛЯ" (отдельный кредитор)
                    if 'ОЛЯ' in header_val.upper() and 'т-банк' in header_val.lower():
                        creditor_name = 'ОЛЯ'
                    else:
                        creditor_name = header_val
                    creditor_columns_map[col_idx] = creditor_name
            
            # Обрабатываем строки с данными после заголовка до следующего заголовка
            for data_idx in range(header_idx + 1, end_idx):
                row = df.iloc[data_idx]
                date_val = parse_date(row.iloc[0])
                if date_val is not None:
                    count = process_data_row(db, row, creditor_columns_map, date_col_idx=0)
                    imported_count += count
        
        db.commit()
        print(f"Успешно импортировано {imported_count} записей о долгах")
        return imported_count
        
    except Exception as e:
        db.rollback()
        print(f"Ошибка при импорте: {e}")
        raise
    finally:
        db.close()


def process_data_row(db, row, creditor_columns_map, date_col_idx=0):
    """Обработка одной строки с данными"""
    from sqlalchemy import func
    
    date_val = parse_date(row.iloc[date_col_idx])
    if date_val is None:
        return 0
    
    imported_count = 0
    
    # Проходим по колонкам с долгами используя текущий маппинг
    for col_idx, creditor_name in creditor_columns_map.items():
        if col_idx < len(row):
            debt_value = clean_value(row.iloc[col_idx])
            
            if debt_value is not None:
                # Копилка и копилка Оли - это активы (отрицательный долг)
                if creditor_name in ['копилка', 'копилка Оли']:
                    # Преобразуем в отрицательное значение
                    debt_value = -abs(debt_value)
                
                # Создаем запись истории долга
                if debt_value != 0:
                    debt_record = DebtHistory(
                        creditor=creditor_name,
                        amount=debt_value,
                        record_date=date_val
                    )
                    db.add(debt_record)
                    imported_count += 1
    
    return imported_count

if __name__ == '__main__':
    import_debts_from_excel()
