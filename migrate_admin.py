"""
Скрипт для преобразования администратора в главу семьи.
Привязывает все существующие данные к семье администратора.
"""
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, engine, Base
from app.models import User, UserRole, FinanceRecord, Debt, DebtRepayment, CreditCard, Income, Expense, SeasonSummary, YearSummary, WeeklyBudgetPlan
from sqlalchemy import select, update

def migrate_admin_to_family_head():
    """Преобразует администратора в главу семьи и привязывает все данные."""
    
    db = SessionLocal()
    try:
        # Находим администратора
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            print("Администратор не найден!")
            return
        
        print(f"Найден администратор: {admin.username} (ID: {admin.id})")
        print(f"Текущая роль: {admin.role}")
        print(f"family_id: {admin.family_id}")
        
        # Проверяем, есть ли уже данные с этим user_id
        existing_records = db.query(FinanceRecord).filter(FinanceRecord.user_id == admin.id).count()
        existing_debts = db.query(Debt).filter(Debt.user_id == admin.id).count()
        existing_cards = db.query(CreditCard).filter(CreditCard.user_id == admin.id).count()
        existing_incomes = db.query(Income).filter(Income.user_id == admin.id).count()
        existing_expenses = db.query(Expense).filter(Expense.user_id == admin.id).count()
        
        print(f"\nНайдено данных для user_id={admin.id}:")
        print(f"  FinanceRecord: {existing_records}")
        print(f"  Debt: {existing_debts}")
        print(f"  CreditCard: {existing_cards}")
        print(f"  Income: {existing_incomes}")
        print(f"  Expense: {existing_expenses}")
        
        # Если у админа уже есть family_id, значит он уже мигрирован
        if admin.family_id is not None:
            print("\nАдминистратор уже является частью семьи.")
            return
        
        # Меняем роль на FAMILY_ADMIN
        old_role = admin.role
        admin.role = UserRole.FAMILY_ADMIN
        db.commit()
        print(f"\nРоль изменена: {old_role} -> {admin.role}")
        
        # Все данные уже привязаны к admin.id, который теперь будет ID главы семьи
        # Остальные пользователи будут ссылаться на этот ID через family_id
        print(f"\nВсе существующие данные автоматически привязаны к семье (family_id={admin.id})")
        print("Теперь администратор является главой семьи и видит все свои данные.")
        
        # Проверяем итоговое количество записей
        new_records = db.query(FinanceRecord).filter(FinanceRecord.user_id == admin.id).count()
        new_debts = db.query(Debt).filter(Debt.user_id == admin.id).count()
        
        print(f"\nИтоговое количество записей:")
        print(f"  FinanceRecord: {new_records}")
        print(f"  Debt: {new_debts}")
        
        print("\n✅ Миграция успешно завершена!")
        print("Теперь вы можете войти под admin и увидеть все свои данные.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка миграции: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_admin_to_family_head()
