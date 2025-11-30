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

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(UserCreate):
    # Используем UserCreate, так как поля те же (username, password)
    pass

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserInDB(UserBase):
    # Модель для чтения из БД
    id: uuid.UUID
    hashed_password: str
    is_active: bool

    class Config:
        from_attributes = True
