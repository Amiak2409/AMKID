from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.models.database_ops import create_db_and_tables # <-- ВАЖНЫЙ ИМПОРТ

from app.models.schemas import (
    TextAnalyzeRequest,
    TextAnalyzeResponse,
    ImageAnalyzeResponse,
)
from app.services.ai_service import analyze_text, analyze_image
from app.models.database_ops import get_db 
from app.services.submission_service import process_text_submission_fixed 
from app.models.schemas import TextAnalyzeRequest, TextAnalyzeResponse



app = FastAPI(title="AI Identifier API", version="0.1")

@app.on_event("startup")
def on_startup():
    """
    Создает таблицы в базе данных при запуске приложения, если они не существуют.
    """
    print("Инициализация БД: Создание таблиц...")
    create_db_and_tables() 
    print("Инициализация БД завершена.")

# Разрешаем фронту к нам ходить (для хакатона ок так)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analyze-text", response_model=TextAnalyzeResponse)
async def analyze_text_endpoint(payload: TextAnalyzeRequest,
                                db: Session = Depends((get_db))):
    """
    Принимает текст и возвращает результат анализа (пока мок).
    """
    TEST_USER_ID_STR = "06090171-4660-4b5b-b181-e793ee2a3173" 
    
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
        raise HTTPException(
            status_code=500, 
            detail="Internal Server Error during AI processing and DB transaction."
        )


@app.post("/analyze-image", response_model=ImageAnalyzeResponse)
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """
    Принимает изображение и возвращает результат анализа (пока мок).
    """
    image_bytes = await file.read()
    return analyze_image(image_bytes)