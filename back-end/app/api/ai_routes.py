# app/routers/ai_routes.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

# Предполагаемые импорты:
from app.models.database_ops import get_db 
from app.models.schemas import TextAnalyzeRequest, TextAnalyzeResponse
from app.services.submission_service import process_text_submission_fixed 

router = APIRouter(tags=["AI"])
logger = logging.getLogger(__name__)

@router.post("/analyze-text", response_model=TextAnalyzeResponse)
async def analyze_text_endpoint(
    payload: TextAnalyzeRequest,
    # 🚨 Ключевой момент: FastAPI инжектирует сессию БД
    db: Session = Depends(get_db) 
):
    """
    Принимает текст, выполняет анализ AI и сохраняет результат в БД.
    """
    
    # ВРЕМЕННЫЙ ID (должен существовать в таблице users)
    TEST_USER_ID_STR = "e0e37a6c-f230-47b2-8414-b159f8069d3a" 
    
    try:
        # Передаем сессию БД в сервис
        ai_response = process_text_submission_fixed(
            db=db, 
            user_id=TEST_USER_ID_STR, 
            content=payload.content
        )
        return ai_response
    
    except Exception as e:
        # Если сервис упал (и уже сделал rollback), возвращаем 500 ошибку
        logger.error(f"Обработка запроса завершилась ошибкой в роутере: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal Server Error during AI processing and DB transaction."
        )
    
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