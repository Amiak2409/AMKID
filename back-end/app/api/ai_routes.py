from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Убедимся, что DEBUG-сообщения выводятся    

from app.models.database_ops import (
    get_db,
    Base,
    engine,
    User
)
from app.models.schemas import (
    TextAnalyzeRequest,
    TextAnalyzeResponse,
    ImageAnalyzeResponse,
)
from app.services.ai_service import analyze_text, analyze_image
from app.services.submission_service import (
    process_text_submission, 
    process_image_submission
)

router = APIRouter()

@router.post("/analyze-text", response_model=TextAnalyzeResponse)
async def analyze_text_endpoint(payload: TextAnalyzeRequest,
                                db: Session = Depends(get_db)):
    """
    Принимает текст и возвращает результат анализа.
    Логика полностью делегирована в сервис analyze_text.
    """

    user = db.query(User).first()
    real_user_id = user.id # Если user не None
    
    response = process_text_submission(
        db=db,
        user_id=str(real_user_id), # Передаем существующий ID
        content_text=payload.content
    )
    
    return response

@router.post("/analyze-image", response_model=ImageAnalyzeResponse)
async def analyze_image_endpoint(file: UploadFile = File(...),
                                 db: Session = Depends(get_db)):
    """
    Принимает изображение и возвращает результат анализа.
    Логика полностью делегирована в сервис analyze_image.
    """
    image_bytes = await file.read()
    
    # 🚨 ИСПРАВЛЕНИЕ: Вызываем process_image_submission, который сохраняет данные
    response = process_image_submission(
        db=db,
        user_id=USER_ID, # TODO: Заменить на реальный ID
        image_bytes=image_bytes,
        filename=file.filename
    )
    return response
