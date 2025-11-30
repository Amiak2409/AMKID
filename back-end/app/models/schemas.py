from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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


class HistoryItem(BaseModel):
    """
    То, что отдаём на фронт в /history.
    """
    # Pydantic v2: включаем чтение из ORM-объектов
    model_config = ConfigDict(from_attributes=True)

    id: UUID               # <--- раньше было str
    question: str
    raw_response: Dict[str, Any]
    created_at: datetime
    kind: str
