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
    
    # Читаем Excel файл
    df = pd.read_excel(file_path)
    
    # Определяем колонки с кредиторами
    creditor_columns = ['СБЕР', 'АЛЬФА', 'МТС1', 'МТС2', 'Т-БАНК', 'ОЛЯ', 'КРЕДИТ']
    
    # Создаем сессию базы данных
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Очищаем существующие данные (опционально)
        db.query(DebtHistory).delete()
        
        imported_count = 0
        
        # Проходим по каждой строке
        for idx, row in df.iterrows():
            # Получаем дату из первой колонки
            date_val = parse_date(row.iloc[0])
            
            if date_val is None:
                continue
            
            # Проходим по каждому кредитору
            for creditor in creditor_columns:
                if creditor in df.columns:
                    debt_value = clean_value(row.get(creditor))
                    
                    if debt_value is not None and debt_value > 0:
                        # Создаем запись истории долга
                        debt_record = DebtHistory(
                            creditor=creditor,
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
