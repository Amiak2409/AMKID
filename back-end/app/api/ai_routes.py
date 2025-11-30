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