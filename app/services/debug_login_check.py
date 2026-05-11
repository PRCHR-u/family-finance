import asyncio
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from app.database import SessionLocal
from app.models import User
from datetime import timedelta

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Эмуляция endpoint'а для проверки данных
@app.post("/test-login")
async def test_login(request: Request):
    # Получаем сырое тело запроса
    body = await request.body()
    print(f"--- RAW BODY ---\n{body.decode('utf-8')}\n----------------")
    
    # Пробуем распарсить как форму (стандарт OAuth2)
    try:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
        print(f"--- PARSED FORM ---\nUsername: {username}\nPassword: {'*' * len(password) if password else 'None'}\n----------------")
        
        if not username or not password:
            return {"error": "Missing username or password in form data"}
            
        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()
        db.close()
        
        if not user:
            return {"error": "User not found"}
            
        is_valid = pwd_context.verify(password, user.hashed_password)
        return {
            "user_found": True,
            "username": user.username,
            "password_matches": is_valid,
            "stored_hash_start": user.hashed_password[:20] + "..."
        }
    except Exception as e:
        return {"error": f"Parse error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    print("Запуск тестового сервера на порту 8001...")
    print("Откройте http://localhost:8001/docs и попробуйте отправить запрос на /test-login")
    print("Или используйте curl/Postman")
    uvicorn.run(app, host="0.0.0.0", port=8001)
