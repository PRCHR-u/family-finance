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
        header_row_indices = set()
        for idx, row in df.iterrows():
            first_col_val = row.iloc[1] if len(row) > 1 else None
            if isinstance(first_col_val, str) and first_col_val.strip() in ['СБЕР', 'ВСЕГО', 'разница', 'копилка', 'копилка Оли']:
                header_row_indices.add(idx)
        
        # Для каждой строки с данными определяем, какой заголовок ей предшествует
        # чтобы понять структуру колонок
        current_header_row = None
        creditor_columns_map = {}
        
        # Проходим по каждой строке
        for idx, row in df.iterrows():
            # Проверяем, является ли строка заголовком
            if idx in header_row_indices:
                # Сохраняем эту строку как текущий заголовок
                current_header_row = row
                continue
            
            # Получаем дату из первой колонки (индекс 0)
            date_val = parse_date(row.iloc[0])
            
            if date_val is None:
                continue
            
            # Определяем маппинг колонок на основе последнего заголовка
            # или используем стандартный, если заголовка не было
            if current_header_row is not None:
                # Строим маппинг на основе заголовка
                creditor_columns_map = {}
                for col_idx in range(1, min(8, len(current_header_row))):
                    header_val = current_header_row.iloc[col_idx]
                    if isinstance(header_val, str):
                        header_val = header_val.strip()
                        # Определяем имя кредитора по заголовку
                        # Пропускаем служебные колонки: "ВСЕГО", "разница", "копилка", "копилка Оли"
                        if header_val == 'СБЕР':
                            creditor_columns_map[col_idx] = 'СБЕР'
                        elif header_val == 'Т-БАНК':
                            creditor_columns_map[col_idx] = 'Т-БАНК'
                        elif header_val == 'Оля СБЕР':
                            creditor_columns_map[col_idx] = 'Оля СБЕР'
                        elif 'ОЛЯ' in header_val.upper() and 'т-банк' in header_val.lower():
                            # "ОЛЯ т-банк" - это отдельный кредитор ОЛЯ
                            creditor_columns_map[col_idx] = 'ОЛЯ'
                        # Игнорируем: ВСЕГО, разница, копилка, копилка Оли
            
            # Если маппинг пустой, используем значения по умолчанию для первых строк
            if not creditor_columns_map:
                creditor_columns_map = {
                    1: 'СБЕР',
                    2: 'ОЛЯ',
                    3: 'Оля СБЕР',
                    4: 'Т-БАНК'
                }
            
            # Проходим по колонкам с долгами
            for col_idx, creditor_name in creditor_columns_map.items():
                if col_idx < len(row):
                    debt_value = clean_value(row.iloc[col_idx])
                    
                    # Пропускаем отрицательные значения (это изменения долга, а не сам долг)
                    if debt_value is not None and debt_value > 0:
                        # Создаем запись истории долга
                        debt_record = DebtHistory(
                            creditor=creditor_name,
                            amount=debt_value,
                            record_date=date_val
                        )
                        db.add(debt_record)
                        imported_count += 1
        
        db.commit()
        print(f"Успешно импортировано {imported_count} записей о долгах")
        return imported_count
        
    except Exception as e:
        db.rollback()
        print(f"Ошибка при импорте: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    import_debts_from_excel()
