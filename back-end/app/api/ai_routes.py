from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import logging
from sqlalchemy.orm import Session
import uuid

from app.models.schemas import (
    TextAnalyzeRequest,
    TextAnalyzeResponse,
    ImageAnalyzeResponse,
)
from app.services.ai_service import analyze_text, analyze_image
from app.models.database_ops import get_db 
from app.services.submission_service import process_text_submission_fixed 

router = APIRouter()

@router.post("/analyze-text", response_model=TextAnalyzeResponse)
async def analyze_text_endpoint(payload: TextAnalyzeRequest):
    """
    Принимает текст и возвращает результат анализа.
    Логика полностью делегирована в сервис analyze_text.
    """
    return analyze_text(payload.content)

@router.post("/analyze-image", response_model=ImageAnalyzeResponse)
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """
    Принимает изображение и возвращает результат анализа.
    Логика полностью делегирована в сервис analyze_image.
    """
    image_bytes = await file.read()
    return analyze_image(image_bytes)

router = APIRouter(tags=["AI"])
logger = logging.getLogger(name)

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    
    # Проверка на дубликат
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    # Хеширование пароля
    hashed_password = get_password_hash(user_data.password)

    # Создание пользователя в БД
    db_user = User(
        username=user_data.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Создание JWT-токена для немедленного логина
    access_token = create_access_token(
        data={"sub": db_user.username, "user_id": str(db_user.id)},
        expires_delta=timedelta(minutes=60)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 2. Логин (получение токена)
@router.post("/login", response_model=Token)
def login_for_access_token(user_data: UserLogin, db: Session = Depends(get_db)):
    
    # 1. Поиск и проверка пользователя
    db_user = db.query(User).filter(User.username == user_data.username).first()
    
    if not db_user or not verify_password(user_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Создание JWT-токена
    access_token = create_access_token(
        data={"sub": db_user.username, "user_id": str(db_user.id)},
        expires_delta=timedelta(minutes=60)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}