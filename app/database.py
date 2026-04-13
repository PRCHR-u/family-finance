import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Чтение переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./family_finance.db")

# Для SQLite важно правильно обрабатывать путь
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация базы данных и создание начальных данных"""
    from .models import User, UserRole, Creditor, CreditCardIssuer, ExpenseCategory, IncomeCategory
    from .auth import get_password_hash
    from sqlalchemy.orm import Session
    
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Создание администратора по умолчанию
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")
        
        admin = db.query(User).filter(User.username == admin_username).first()
        if not admin:
            admin = User(
                username=admin_username,
                hashed_password=get_password_hash(admin_password),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print(f"Администратор создан: {admin_username} ({admin_email})")
        
        # Инициализация справочников будет вызвана через API при первом запуске
        print("База данных инициализирована успешно")
    except Exception as e:
        db.rollback()
        print(f"Ошибка инициализации БД: {e}")
        raise
    finally:
        db.close()
