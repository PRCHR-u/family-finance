from app.database import SessionLocal
from app.schemas import UserLogin
from passlib.context import CryptContext

db = SessionLocal()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Ищем пользователя
username = "admin"
user = db.query(type('User', (), {}).__class__).filter(type('User', (), {}).__class__.username == username).first() if False else None
# Правильный запрос:
from app.models import User
user = db.query(User).filter(User.username == username).first()

if not user:
    print(f"❌ Пользователь '{username}' НЕ найден в базе!")
else:
    print(f"✅ Пользователь '{username}' найден.")
    print(f"   Hash в БД: {user.hashed_password[:20]}...")
    
    # Пробуем проверить пароль вручную
    password = "ChangeMe123!"
    is_valid = pwd_context.verify(password, user.hashed_password)
    print(f"   Пароль '{password}' верен? {is_valid}")
    
    if not is_valid:
        print("   ⚠️ Попробуем создать новый хэш и проверить его...")
        new_hash = pwd_context.hash(password)
        print(f"   Новый хэш: {new_hash[:20]}...")
        print(f"   Проверка нового хэша: {pwd_context.verify(password, new_hash)}")

db.close()
'@ | Out-File -FilePath debug_login.py -Encoding UTF8

python debug_login.py
