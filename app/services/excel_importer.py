import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

# Импорт моделей из основного файла models.py
from app.models import (
    User, DebtHistory,
    Income, Expense, IncomeCategory, ExpenseCategory,
    CreditCard, WeeklyBudgetPlan, SeasonSummary, YearSummary
)
import re

class ExcelImporter:
    def __init__(self, db: Session, file_path: str):
        self.db = db
        self.file_path = file_path
        
    def normalize_date(self, date_val) -> Optional[datetime]:
        """Преобразует различные форматы дат из Excel в datetime"""
        if pd.isna(date_val):
            return None
        
        if isinstance(date_val, datetime):
            return date_val
            
        if isinstance(date_val, str):
            date_val = date_val.strip()
            # Формат "до 31.05" или "31.05"
            match = re.match(r'(?:до\s*)?(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?', date_val)
            if match:
                day, month, year = match.groups()
                year = int(year) if year else datetime.now().year
                try:
                    return datetime(year, int(month), int(day))
                except ValueError:
                    return None
            # ISO формат
            try:
                return datetime.fromisoformat(date_val)
            except ValueError:
                pass
                
        return None

    def normalize_creditor_name(self, name: str) -> str:
        """Нормализует имена кредиторов"""
        if pd.isna(name):
            return "Unknown"
        name = str(name).strip().upper()
        # Убираем лишние слова
        name = re.sub(r'\s*\(.*?\)\s*', '', name)
        name = re.sub(r'\s+', ' ', name)
        return name

    def clear_existing_data(self):
        """Очищает существующие данные перед импортом"""
        self.db.query(WeeklyBudgetPlan).delete()
        self.db.query(SeasonSummary).delete()
        self.db.query(YearSummary).delete()
        self.db.query(Income).delete()
        self.db.query(Expense).delete()
        self.db.query(DebtHistory).delete()
        self.db.query(CreditCard).delete()
        self.db.commit()

    def import_sheet1_debts(self, df: pd.DataFrame):
        """
        Импортирует историю долгов из листа Sheet1 со специфической структурой:
        - Строка 0: NaT | СБЕР | ОЛЯ т-банк | Оля СБЕР | Т-БАНК | ... (названия кредиторов)
        - Строка 1: 2025-12-23 | 415705.44 | 15714.24 | ... (значения сумм)
        - Строка 2: NaT | СБЕР | Т-БАНК | ... (новые названия, если меняются)
        - Строка 3: 2026-01-20 | 430716.51 | ... (значения сумм)
        
        Модель DebtHistory имеет поля: creditor, amount, record_date, debt_change
        Каждая запись - это долг одного кредитора на конкретную дату.
        """
        print(f"Импорт долгов из {len(df)} строк (специфический формат)...")
        
        # Преобразуем DataFrame в список строк для удобной обработки
        rows_list = []
        for idx, row in df.iterrows():
            # Берём первые 8 колонок (основные данные)
            row_data = []
            for i in range(min(8, len(row))):
                val = row.iloc[i]
                row_data.append(val)
            rows_list.append(row_data)
        
        # Парсим структуру: чередование строк с названиями и строк с данными
        current_creditor_names = None
        records_created = 0
        
        # Словарь для отслеживания предыдущего общего долга по датам
        prev_total_by_date = {}
        
        for i, row_data in enumerate(rows_list):
            # Первая колонка - потенциальная дата или NaT
            first_val = row_data[0] if len(row_data) > 0 else None
            
            # Проверяем, является ли первая колонка датой
            date_val = self.normalize_date(first_val)
            
            if date_val:
                # Это строка с датой и суммами по кредиторам
                # current_creditor_names должна быть установлена из предыдущей строки
                if not current_creditor_names:
                    print(f"  ⚠️ Предупреждение: нет названий кредиторов для даты {date_val}")
                    continue
                
                # Сначала собираем все долги на эту дату для расчёта total_debt
                debts_to_create = []
                total_debt = 0.0
                
                for j in range(1, len(row_data)):  # Начинаем с 1, т.к. 0 - это дата
                    amount_val = row_data[j]
                    if j >= len(current_creditor_names):
                        break
                    
                    creditor_name = current_creditor_names[j]
                    if not creditor_name:
                        continue
                    
                    # Парсим сумму
                    if pd.isna(amount_val):
                        continue
                    
                    try:
                        amount_str = str(amount_val).replace(',', '.').replace(' ', '')
                        amount = float(amount_str)
                    except (ValueError, TypeError):
                        continue
                    
                    # Пропускаем нулевые значения
                    if amount == 0:
                        continue
                    
                    # Нормализуем имя кредитора
                    norm_name = self.normalize_creditor_name(creditor_name)
                    
                    debts_to_create.append({
                        'creditor': norm_name,
                        'amount': amount,
                    })
                    total_debt += amount
                
                # Вычисляем изменение долга относительно предыдущей даты
                sorted_dates = sorted(prev_total_by_date.keys())
                prev_total = None
                for d in sorted_dates:
                    if d < date_val:
                        prev_total = prev_total_by_date[d]
                
                debt_change = None
                if prev_total is not None:
                    debt_change = total_debt - prev_total
                
                # Сохраняем общий долг для этой даты
                prev_total_by_date[date_val] = total_debt
                
                # Создаём записи для каждого кредитора
                for debt_info in debts_to_create:
                    record = DebtHistory(
                        creditor=debt_info['creditor'],
                        amount=debt_info['amount'],
                        record_date=date_val,
                        debt_change=debt_change
                    )
                    self.db.add(record)
                    records_created += 1
            else:
                # Это строка с названиями кредиторов (или служебная строка)
                # Проверяем, есть ли в строке названия (не NaN, не числа)
                creditor_names = []
                has_valid_names = False
                
                for j, val in enumerate(row_data):
                    if pd.isna(val) or (isinstance(val, float) and val != val):  # NaN check
                        creditor_names.append(None)
                    elif isinstance(val, (int, float)):
                        # Это число, а не название - пропускаем эту строку
                        creditor_names.append(None)
                    else:
                        name_str = str(val).strip().upper()
                        # Пропускаем служебные названия
                        if any(keyword in name_str for keyword in ['ВСЕГО', 'РАЗНИЦА', 'ИЗМЕНЕНИЕ', 'ДОЛГ', 'ВЕСНУ', 'Unnamed']):
                            creditor_names.append(None)
                        else:
                            creditor_names.append(name_str)
                            has_valid_names = True
                
                if has_valid_names:
                    current_creditor_names = creditor_names
        
        self.db.commit()
        print(f"✅ Импортировано {records_created} записей о долгах")

    def import_income_sheet(self, df: pd.DataFrame):
        """
        Импортирует доходы из листа 'доход'.
        Структура: Доход | сколько | когда | ...
        Пример: лиза долг | 22533 | до 13.05
        
        Модель Income имеет поля: user_id, amount, income_date, category, description, is_actual
        """
        print(f"Импорт доходов из {len(df)} строк...")
        
        incomes_created = 0
        
        # Получаем ID первого пользователя (администратора)
        from app.models import User
        admin_user = self.db.query(User).first()
        user_id = admin_user.id if admin_user else 1
        
        for _, row in df.iterrows():
            # Получаем значения из первых трёх колонок
            if len(row) < 3:
                continue
                
            source = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            amount_val = row.iloc[1] if len(row) > 1 else None
            date_val_raw = row.iloc[2] if len(row) > 2 else None
            
            # Пропускаем пустые строки
            if not source or pd.isna(amount_val):
                continue
            
            # Парсим сумму
            try:
                amount_str = str(amount_val).replace(',', '.').replace(' ', '')
                amount = float(amount_str)
            except (ValueError, TypeError):
                continue
            
            if amount <= 0:
                continue
            
            # Парсим дату
            date_val = self.normalize_date(date_val_raw)
            if not date_val:
                continue
            
            # Определяем категорию по названию источника
            source_lower = source.lower()
            category = IncomeCategory.OTHER
            
            if 'стипенд' in source_lower:
                category = IncomeCategory.SCHOLARSHIP
            elif 'зарплат' in source_lower or 'аванс' in source_lower or 'склад' in source_lower:
                category = IncomeCategory.SALARY
            elif 'подар' in source_lower or 'др' in source_lower:
                category = IncomeCategory.GIFT
            elif 'отец' in source_lower or 'мама' in source_lower or 'долг' in source_lower:
                category = IncomeCategory.GIFT
            elif 'занят' in source_lower or 'урок' in source_lower:
                category = IncomeCategory.FREELANCE
            
            income = Income(
                user_id=user_id,
                amount=amount,
                income_date=date_val,
                category=category,
                description=source,
                is_actual=True
            )
            self.db.add(income)
            incomes_created += 1
        
        self.db.commit()
        print(f"✅ Импортировано {incomes_created} доходов")

    def import_expenses_sheet(self, df: pd.DataFrame):
        """
        Импортирует траты из листа 'траты'.
        Структура: ОБЯЗАТЕЛЬНЫЕ ТРАТЫ | СКОЛЬКО | ДАТА | ВСЕГО
        Пример: Оля врачи | 10000 | NaN | 13500
        
        Модель Expense имеет поля: user_id, amount, due_date, category, description, is_mandatory, is_completed
        """
        print(f"Импорт расходов из {len(df)} строк...")
        
        expenses_created = 0
        
        # Получаем ID первого пользователя (администратора)
        from app.models import User
        admin_user = self.db.query(User).first()
        user_id = admin_user.id if admin_user else 1
        
        for _, row in df.iterrows():
            # Пропускаем строки с менее чем 3 колонками
            if len(row) < 3:
                continue
            
            name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            amount_val = row.iloc[1] if len(row) > 1 else None
            date_val_raw = row.iloc[2] if len(row) > 2 else None
            
            # Пропускаем пустые строки или заголовки
            if not name or pd.isna(amount_val):
                continue
            
            # Парсим сумму
            try:
                amount_str = str(amount_val).replace(',', '.').replace(' ', '')
                amount = float(amount_str)
            except (ValueError, TypeError):
                continue
            
            if amount <= 0:
                continue
            
            # Парсим дату - может быть в любой колонке
            date_val = self.normalize_date(date_val_raw)
            
            # Если дата не найдена во второй колонке, проверяем другие
            if not date_val:
                for i in range(2, min(len(row), 5)):
                    date_val = self.normalize_date(row.iloc[i])
                    if date_val:
                        break
            
            # Если даты нет вообще - пропускаем (например, TOEFL с датой "неизвестно")
            if not date_val:
                continue
            
            # Определяем категорию и обязательность по названию
            name_lower = name.lower()
            category = ExpenseCategory.OTHER
            is_mandatory = True
            
            if 'аренд' in name_lower:
                category = ExpenseCategory.RENT
            elif 'коммунал' in name_lower or 'свет' in name_lower or 'вода' in name_lower:
                category = ExpenseCategory.UTILITIES
            elif 'врач' in name_lower or 'мед' in name_lower or 'зуб' in name_lower or 'оля врач' in name_lower:
                category = ExpenseCategory.MEDICAL
            elif 'подар' in name_lower or 'др' in name_lower:
                category = ExpenseCategory.GIFTS
                is_mandatory = False
            elif 'toefl' in name_lower or 'курс' in name_lower or 'учеб' in name_lower:
                category = ExpenseCategory.EDUCATION
            elif 'продукт' in name_lower or 'еда' in name_lower:
                category = ExpenseCategory.FOOD
            
            expense = Expense(
                user_id=user_id,
                amount=amount,
                due_date=date_val,
                category=category,
                description=name,
                is_mandatory=is_mandatory,
                is_completed=False
            )
            self.db.add(expense)
            expenses_created += 1
        
        self.db.commit()
        print(f"✅ Импортировано {expenses_created} расходов")

    def import_credit_cards_sheet(self, df: pd.DataFrame):
        """
        Импортирует льготные периоды.
        Структура: min (дата) | Т-банк | СБЕР | ... | TOTAL
        Пример: 2026-05-17 | 78144.0 | NaN | 78144.00
        """
        print(f"Импорт кредитных карт из {len(df)} строк...")

        cards_created = 0 
        for idx, row in df.iterrows():
                        # Первая колонка - дата или название месяца
            date_val_raw = row.iloc[0] if len(row) > 0 else None
            date_val = self.normalize_date(date_val_raw)

            # Если это месяц (МАЙ, ИЮНЬ и т.д.), пропускаем - это итоговая строка
            if date_val is None and isinstance(date_val_raw, str):
                month_str = str(date_val_raw).strip().upper()
                if any(m in month_str for m in ['МАЙ', 'ИЮН', 'ИЮЛ', 'АВГ', 'СЕН', 'ОКТ', 'НОЯ', 'ДЕК', 'ЯНВ', 'ФЕВ', 'МАР', 'АПР']):
                    continue
            
            # Последняя колонка - TOTAL (сумма к погашению)
            total_col_idx = len(row) - 1
            repayment = 0.0
            try:
                val = row.iloc[total_col_idx]
                if not pd.isna(val):
                    repayment = float(str(val).replace(',', '.').replace(' ', ''))
            except (ValueError, TypeError):
                pass
            
            if repayment <= 0:
                continue

            # Проходим по всем колонкам между датой и TOTAL
            for col_idx in range(1, total_col_idx):
                card_name_raw = df.columns[col_idx] if col_idx < len(df.columns) else None
                amount_val = row.iloc[col_idx]

                if pd.isna(card_name_raw) or pd.isna(amount_val):
                    continue

                card_name = str(card_name_raw).strip()
                if not card_name or card_name.lower() in ['min', 'total', 'unnamed']:
                    continue

                try:
                    amount = float(str(amount_val).replace(',', '.').replace(' ', ''))
                except (ValueError, TypeError):
                    continue

                if amount <= 0:
                    continue

                # Нормализуем имя карты (верхний регистр для консистентности)
                norm_name = card_name.upper()

                # Проверяем дубликат по имени карты и дате
                existing = self.db.query(CreditCard).filter(
                    CreditCard.card_name == norm_name
                ).first()

                if existing:
                    # Обновляем существующую запись
                    existing.planned_repayment_amount = repayment
                          if date_val:
                        existing.grace_end_date = date_val.date()
                else:
                    # Создаём новую запись
                    card = CreditCard(
                        user_id=1,
                        card_name=norm_name,
                        grace_start_date=datetime.now().date(),
                        grace_period_days=50,
                        current_debt=amount,
                        planned_repayment_amount=repayment
                    )
                    if date_val:
                        card.grace_end_date = date_val.date()                    
                    self.db.add(card)
                    cards_created += 1

        self.db.commit()
        print(f"✅ Импортировано {cards_created} кредитных карт")

    def import_weekly_budget_sheet(self, df: pd.DataFrame):
        """
        Импортирует недельный бюджет из листа 'Суммы для трат'.
        Структура файла (при чтении с заголовком):
        - Заголовок: МАЙ | Unnamed: 1 | Unnamed: 2 | Unnamed: 3
        - Строка 0: 48853.22 | 8866 | 5032.29 | NaN (суммы по неделям)
        - Строка 1: NaN | NaN | NaN | NaN (пустая)
        - Строка 2: 01.05-10.05 | 11.05-17.05 | ... (диапазоны дат)

        Модель WeeklyBudgetPlan имеет поля: user_id, month, year, week_number, planned_amount
        """
        print(f"Импорт недельного бюджета...")
        
        # Получаем ID первого пользователя (администратора)
        from app.models import User
        admin_user = self.db.query(User).first()
        user_id = admin_user.id if admin_user else 1
        
        plans_created = 0
        current_month = None
        current_year = datetime.now().year

        # Извлекаем месяц из заголовка первой колонки
        first_col_name = str(df.columns[0]).strip()
        month_lower = first_col_name.lower()

        if 'май' in month_lower or 'may' in month_lower:
            current_month = 5
        elif 'июн' in month_lower or 'jun' in month_lower:
            current_month = 6
        elif 'июл' in month_lower or 'jul' in month_lower:
            current_month = 7
        elif 'авг' in month_lower or 'aug' in month_lower:
            current_month = 8
        elif 'сен' in month_lower or 'sep' in month_lower:
            current_month = 9
        elif 'окт' in month_lower or 'oct' in month_lower:
            current_month = 10
        elif 'ноя' in month_lower or 'nov' in month_lower:
            current_month = 11
        elif 'дек' in month_lower or 'dec' in month_lower:
            current_month = 12
        elif 'янв' in month_lower or 'jan' in month_lower:
            current_month = 1
        elif 'фев' in month_lower or 'feb' in month_lower:
            current_month = 2
                    elif 'мар' in month_lower or 'mar' in month_lower:
            current_month = 3
        elif 'апр' in month_lower or 'apr' in month_lower:
            current_month = 4

        # Проверяем год в названии
        year_match = re.search(r'(20\d{2})', first_col_name)
        if year_match:
            current_year = int(year_match.group(1))

        if not current_month:
            print(f"  ⚠️ Не удалось определить месяц из заголовка: {first_col_name}")
            return

        # Берём первую строку данных (индекс 0) - там суммы по неделям
        first_row = df.iloc[0]

        # Парсим суммы по неделям из колонок 0, 1, 2 (индексы), что соответствует неделям 1, 2, 3
        for week_num in range(1, 5):
            col_idx = week_num - 1  # Индекс колонки (0-based)
            if len(first_row) <= col_idx:
                continue
            
            amount_val = first_row.iloc[col_idx]

            if pd.isna(amount_val):
                continue

            try:
                amount = float(str(amount_val).replace(',', '.').replace(' ', ''))
                if amount <= 0:
                    continue

                plan = WeeklyBudgetPlan(
                    user_id=user_id,
                    month=current_month,
                    year=current_year,
                    week_number=week_num,
                    planned_amount=amount
                )
                self.db.add(plan)
                plans_created += 1
            except (ValueError, TypeError):
                pass
        
        self.db.commit()
        print(f"✅ Импортировано {plans_created} недельных планов")

    def run_full_import(self):
        """Запускает полный импорт всех листов"""
        try:
            xls = pd.ExcelFile(self.file_path)
            sheet_names = xls.sheet_names
            print(f"Найдены листы: {sheet_names}")
            
            # Sheet1 или Долги
            if 'Sheet1' in sheet_names:
                df = pd.read_excel(xls, sheet_name='Sheet1')
                self.import_sheet1_debts(df)
            elif 'Долги' in sheet_names:
                df = pd.read_excel(xls, sheet_name='Долги')
                self.import_sheet1_debts(df)
            
            # Доход
            if 'доход' in sheet_names:
                df = pd.read_excel(xls, sheet_name='доход')
                self.import_income_sheet(df)
            
            # Траты
            if 'траты' in sheet_names:
                df = pd.read_excel(xls, sheet_name='траты')
                self.import_expenses_sheet(df)
            
            # Льготные периоды
            if 'льготные периоды' in sheet_names:
                df = pd.read_excel(xls, sheet_name='льготные периоды')
                self.import_credit_cards_sheet(df)
            
            # Суммы для трат (недельный бюджет)
            budget_sheet = next((s for s in sheet_names if 'сумм' in s.lower() or 'бюджет' in s.lower()), None)
            if budget_sheet:
                df = pd.read_excel(xls, sheet_name=budget_sheet)
                self.import_weekly_budget_sheet(df)
            
            print("🎉 Импорт успешно завершен!")
            return {"status": "success", "message": "Data imported successfully"}
            
        except Exception as e:
            print(f"❌ Ошибка импорта: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            if 'xls' in locals():
                xls.close()
