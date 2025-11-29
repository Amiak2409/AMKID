from pydantic import BaseModel
from typing import List


class TextAnalyzeRequest(BaseModel):
    content: str


class ClaimEvaluation(BaseModel):
    text: str
    true_likeliness: float
    comment: str


class TextAnalyzeResponse(BaseModel):
    trust_score: int
    ai_likeliness: float
    manipulation_score: float
    emotion_intensity: float
    claims_evaluation: List[ClaimEvaluation]
    dangerous_phrases: List[str]
    summary: str


class ImageAnalyzeResponse(BaseModel):
    trust_score: int
    ai_likeliness: float
    manipulation_risk: float
    realism: float
    anomalies: List[str]
    summary: str

from pydantic import BaseModel


class AIDetectRequest(BaseModel):
    content: str


class AIDetectResponse(BaseModel):
    is_ai: bool          # True если считаем текст ИИ
    probability: float   # вероятность 0..1
    model_id: str        # какая модель использована
    threshold: float     # порог

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import AIDetectRequest, AIDetectResponse
from hf_ai_detector import detect_ai_label, MODEL_ID

app = FastAPI(title="AI Detector API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/detect-ai", response_model=AIDetectResponse)
async def detect_ai_endpoint(payload: AIDetectRequest):
    is_ai, prob = detect_ai_label(payload.content, threshold=0.5)
    return AIDetectResponse(
        is_ai=is_ai,
        probability=prob,
        model_id=MODEL_ID,
        threshold=0.5,
    )
