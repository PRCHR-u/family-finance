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
        """Импортирует историю долгов из листа Sheet1"""
        print(f"Импорт долгов из {len(df)} строк...")
        
        # Определяем колонки динамически
        date_col = None
        for col in df.columns:
            if 'дата' in str(col).lower() or 'date' in str(col).lower():
                date_col = col
                break
        
        if not date_col:
            print("❌ Не найдена колонка с датой")
            return

        creditors = [c for c in df.columns if c != date_col and not pd.isna(c)]
        
        for _, row in df.iterrows():
            date_val = self.normalize_date(row[date_col])
            if not date_val:
                continue
                
            total_debt = 0.0
            debts_data = []
            
            for creditor in creditors:
                val = row.get(creditor)
                if pd.isna(val):
                    continue
                    
                try:
                    amount = float(str(val).replace(',', '.').replace(' ', ''))
                except ValueError:
                    continue
                
                if amount == 0:
                    continue
                    
                norm_name = self.normalize_creditor_name(creditor)
                
                debts_data.append({
                    'creditor_name': norm_name,
                    'amount': amount,
                })
                total_debt += amount

            # Вычисляем изменение долга
            prev_record = self.db.query(DebtHistory).filter(
                DebtHistory.record_date < date_val
            ).order_by(DebtHistory.record_date.desc()).first()
            
            debt_change = None
            if prev_record:
                debt_change = total_debt - prev_record.total_debt

            record = DebtHistory(
                record_date=date_val,
                total_debt=total_debt,
                debt_change=debt_change,
                details=debts_data
            )
            self.db.add(record)
        
        self.db.commit()
        print(f"✅ Импортировано записей о долгах")

    def import_income_sheet(self, df: pd.DataFrame):
        """Импортирует доходы из листа 'доход'"""
        print(f"Импорт доходов из {len(df)} строк...")
        
        # Ожидаемая структура: Дата | Категория | Сумма | Комментарий
        # Или: Дата | Стипендия | Зарплата | ...
        
        for _, row in df.iterrows():
            date_val = None
            amount = 0.0
            category = ExpenseCategory.OTHER
            comment = ""
            
            # Пытаемся найти дату в первой колонке
            first_col = df.columns[0]
            date_val = self.normalize_date(row[first_col])
            
            if not date_val:
                continue
                
            # Если структура широкая (колонки это категории)
            for col in df.columns[1:]:
                val = row[col]
                if pd.isna(val):
                    continue
                try:
                    amt = float(str(val).replace(',', '.').replace(' ', ''))
                    if amt > 0:
                        amount = amt
                        col_lower = str(col).lower()
                        if 'стипендия' in col_lower:
                            category = IncomeCategory.SCHOLARSHIP
                        elif 'зарплат' in col_lower or 'работа' in col_lower:
                            category = IncomeCategory.SALARY
                        elif 'подар' in col_lower:
                            category = IncomeCategory.GIFT
                        elif 'отец' in col_lower or 'мама' in col_lower:
                            category = IncomeCategory.GIFT
                        comment = str(col)
                        break
                except ValueError:
                    pass
            
            if amount > 0 and date_val:
                income = Income(
                    transaction_date=date_val,
                    amount=amount,
                    category=category,
                    description=comment,
                    status='actual' # По умолчанию факт
                )
                self.db.add(income)
        
        self.db.commit()
        print(f"✅ Импортировано доходов")

    def import_expenses_sheet(self, df: pd.DataFrame):
        """Импортирует траты из листа 'траты'"""
        print(f"Импорт расходов из {len(df)} строк...")
        
        for _, row in df.iterrows():
            date_val = None
            amount = 0.0
            category = ExpenseCategory.OTHER
            is_mandatory = True # По умолчанию обязательные
            
            first_col = df.columns[0]
            date_val = self.normalize_date(row[first_col])
            
            if not date_val:
                continue
            
            # Парсим колонки
            for col in df.columns[1:]:
                val = row[col]
                if pd.isna(val):
                    continue
                try:
                    amt = float(str(val).replace(',', '.').replace(' ', ''))
                    if amt > 0:
                        amount = amt
                        col_lower = str(col).lower()
                        
                        if 'аренд' in col_lower:
                            category = ExpenseCategory.RENT
                        elif 'коммунал' in col_lower or 'свет' in col_lower or 'вода' in col_lower:
                            category = ExpenseCategory.UTILITIES
                        elif 'врач' in col_lower or 'мед' in col_lower or 'зуб' in col_lower:
                            category = ExpenseCategory.MEDICAL
                        elif 'подар' in col_lower:
                            category = ExpenseCategory.GIFTS
                            is_mandatory = False
                        elif 'toefl' in col_lower or 'курс' in col_lower or 'учеб' in col_lower:
                            category = ExpenseCategory.EDUCATION
                        elif 'продукт' in col_lower or 'еда' in col_lower:
                            category = ExpenseCategory.FOOD
                            
                        break
                except ValueError:
                    pass
            
            if amount > 0 and date_val:
                expense = Expense(
                    transaction_date=date_val,
                    amount=amount,
                    category=category,
                    description=str(col) if 'col' in locals() else "Расход",
                    is_mandatory=is_mandatory
                )
                self.db.add(expense)
        
        self.db.commit()
        print(f"✅ Импортировано расходов")

    def import_credit_cards_sheet(self, df: pd.DataFrame):
        """Импортирует льготные периоды"""
        print(f"Импорт кредитных карт из {len(df)} строк...")
        
        # Ожидаем структуру: Карта | Лимит | Потрачено | Срок | Сумма к погашению
        for idx, row in df.iterrows():
            name = str(row.iloc[0]).strip() if len(row) > 0 else "Unknown"
            if pd.isna(name) or name == "":
                continue
            
            # Пытаемся найти сумму к погашению (последняя колонка обычно)
            repayment = 0.0
            if len(row) > 4:
                try:
                    val = row.iloc[-1] # Последняя колонка - TOTAL
                    repayment = float(str(val).replace(',', '.').replace(' ', ''))
                except (ValueError, TypeError):
                    pass
            
            # Проверяем дубликат
            existing = self.db.query(CreditCard).filter(CreditCard.card_name == name).first()
            if existing:
                if repayment > 0:
                    existing.planned_repayment_amount = repayment
            else:
                # Создаём новую запись с минимальными данными
                # Для полноценного импорта нужны дополнительные данные из файла
                if repayment > 0:
                    card = CreditCard(
                        user_id=1, # Default user
                        card_name=name,
                        grace_start_date=datetime.now().date(),
                        grace_period_days=50,
                        current_debt=0.0,
                        planned_repayment_amount=repayment
                    )
                    self.db.add(card)
                
        self.db.commit()
        print(f"✅ Импортировано кредитных карт")

    def import_weekly_budget_sheet(self, df: pd.DataFrame):
        """Импортирует недельный бюджет"""
        print(f"Импорт недельного бюджета...")
        
        # Структура: Месяц | Неделя 1 | Неделя 2 | ...
        for _, row in df.iterrows():
            month_str = str(row.iloc[0]).strip()
            if pd.isna(month_str) or len(month_str) < 3:
                continue
            
            # Парсим месяц (например, "Май 2026")
            try:
                month_date = datetime.strptime(month_str, "%B %Y")
            except ValueError:
                try:
                    month_date = datetime.strptime(month_str, "%b %Y")
                except ValueError:
                    month_date = datetime.now()
            
            for i in range(1, 5): # 4 недели
                if len(row) > i:
                    try:
                        amount = float(str(row.iloc[i]).replace(',', '.').replace(' ', ''))
                        plan = WeeklyBudgetPlan(
                            month=month_date,
                            week_number=i,
                            planned_amount=amount
                        )
                        self.db.add(plan)
                    except (ValueError, TypeError):
                        pass
        
        self.db.commit()
        print(f"✅ Импортировано недельных планов")

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
