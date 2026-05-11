"""
Скрипт для привязки импортированных данных о долгах к пользователю admin.
Переносит данные из DebtHistory в Debt с привязкой к user_id администратора.
"""
from app.database import SessionLocal, Base, engine
from app.models import User, Debt, DebtStatus, DebtHistory
from datetime import date

def init_admin_debts():
    """Создает записи о долгах для администратора на основе импортированных данных."""
    
    db = SessionLocal()
    try:
        # Находим администратора
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            print("❌ Администратор не найден!")
            return
        
        print(f"Администратор: {admin.username} (ID={admin.id})")
        
        # Проверяем существующие долги
        existing_debts = db.query(Debt).filter(Debt.user_id == admin.id).all()
        if existing_debts:
            print(f"\nУ администратора уже есть {len(existing_debts)} записей о долгах.")
            response = input("Хотите пересоздать? (y/n): ").strip().lower()
            if response != 'y':
                return
            # Удаляем старые записи
            for debt in existing_debts:
                db.delete(debt)
            db.commit()
            print("Старые записи удалены.")
        
        # Получаем последние данные по каждому кредитору из DebtHistory
        creditors_data = {}
        all_history = db.query(DebtHistory).all()
        
        for record in all_history:
            creditor = record.creditor
            if creditor not in creditors_data:
                creditors_data[creditor] = []
            creditors_data[creditor].append(record)
        
        print(f"\nНайдено данных по {len(creditors_data)} кредиторам:")
        
        created_count = 0
        for creditor, records in creditors_data.items():
            # Сортируем по дате, чтобы найти первую и последнюю запись
            records.sort(key=lambda x: x.record_date)
            
            first_record = records[0]
            last_record = records[-1]
            
            # Создаем запись о долге
            debt = Debt(
                user_id=admin.id,
                creditor_name=creditor,
                principal_amount=first_record.amount,  # Начальная сумма долга
                current_balance=last_record.amount,    # Текущий баланс
                start_date=first_record.record_date,
                status=DebtStatus.ACTIVE,
                comment=f"Импортировано из ДОЛГИ.xlsx"
            )
            db.add(debt)
            created_count += 1
            
            print(f"  ✅ {creditor}: {first_record.amount} -> {last_record.amount}")
        
        db.commit()
        print(f"\n✅ Создано {created_count} записей о долгах для пользователя admin")
        
        # Проверка результата
        final_count = db.query(Debt).filter(Debt.user_id == admin.id).count()
        print(f"Всего долгов у admin: {final_count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_admin_debts()
