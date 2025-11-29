from fastapi import APIRouter, UploadFile, File

from app.models.schemas import (
    TextAnalyzeRequest,
    TextAnalyzeResponse,
    ImageAnalyzeResponse,
)
from app.services.ai_service import analyze_text, analyze_image

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
