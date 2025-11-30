from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database_ops import (
    get_db,
    Base,
    engine
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

USER_ID = "e0e37a6c-f230-47b2-8414-b159f8069d3a"

@router.post("/analyze-text", response_model=TextAnalyzeResponse)
async def analyze_text_endpoint(payload: TextAnalyzeRequest,
                                db: Session = Depends(get_db)):
    """
    Принимает текст и возвращает результат анализа.
    Логика полностью делегирована в сервис analyze_text.
    """

    response = process_text_submission(
        db=db,
        user_id=USER_ID, # TODO: Заменить на реальный ID из аутентификации
        content_text=payload.content
    )

    return response

@router.post("/analyze-image", response_model=ImageAnalyzeResponse)
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """
    Принимает изображение и возвращает результат анализа.
    Логика полностью делегирована в сервис analyze_image.
    """
    image_bytes = await file.read()
    return analyze_image(image_bytes)
