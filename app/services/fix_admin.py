from app.database import SessionLocal, engine
from app.models import User, Base
from passlib.context import CryptContext

# Создаем таблицы, если их нет
Base.metadata.create_all(bind=engine)

db = SessionLocal()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Проверяем существующего админа
admin = db.query(User).filter(User.username == "admin").first()

if admin:
    print(f"Пользователь admin найден. Обновляем пароль...")
    admin.hashed_password = pwd_context.hash("ChangeMe123!")
    admin.is_active = True
    admin.is_superuser = True
else:
    print("Создаем нового пользователя admin...")
    admin = User(
        username="admin",
        hashed_password=pwd_context.hash("ChangeMe123!"),
        is_active=True,
        is_superuser=True
    )
    db.add(admin)

db.commit()
print("Готово! Теперь попробуйте войти: login='admin', password='ChangeMe123!'")
db.close()
