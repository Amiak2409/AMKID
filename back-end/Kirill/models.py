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

