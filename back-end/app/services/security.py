# app/utils/security.py

from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError

# 🚨 Обязательно замените SECRET_KEY! Лучше загружать его из переменных окружения (.env)
SECRET_KEY = "YOUR_SUPER_SECRET_KEY" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Токен будет действовать 60 минут

# Инициализация контекста для bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Хеширование ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие открытого и хешированного паролей."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Возвращает хеш пароля."""
    return pwd_context.hash(password)

# --- JWT ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создает JWT-токен."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Устанавливаем срок действия
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "sub": "access_token"})
    
    # Кодируем токен
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt