from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import (
    TextAnalyzeRequest,
    TextAnalyzeResponse,
    ImageAnalyzeResponse,
)
from app.services.ai_service import analyze_text, analyze_image


app = FastAPI(title="AI Identifier API", version="0.1")


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
async def analyze_text_endpoint(payload: TextAnalyzeRequest):
    """
    Принимает текст и возвращает результат анализа (пока мок).
    """
    return analyze_text(payload.content)


@app.post("/analyze-image", response_model=ImageAnalyzeResponse)
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """
    Принимает изображение и возвращает результат анализа (пока мок).
    """
    image_bytes = await file.read()
    return analyze_image(image_bytes)