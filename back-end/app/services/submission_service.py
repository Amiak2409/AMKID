# app/services/submission_service.py

import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session

# Импортируем CRUD функции и модели
from app.models.database_ops import create_submission, create_trust_score, Submission
# Импортируем схемы для ответа
from app.models.schemas import TextAnalyzeResponse, ImageAnalyzeResponse 
# Импортируем AI сервисы
from app.services.ai_service import analyze_text, analyze_image # <--- Ваши существующие функции

# --- Вспомогательная функция для преобразования ответа AI в TrustScore ---
def _format_ai_response_to_db(ai_response: BaseModel) -> Dict[str, Any]:
    """Преобразует ответ AI (TextAnalyzeResponse/ImageAnalyzeResponse) в словарь для TrustScore."""
    
    # Выбираем поле, которое будет общим 'trust_score'
    trust_score = getattr(ai_response, 'trust_score', 0)
    
    # Определяем вердикт на основе score (пример)
    if trust_score > 80:
        verdict = "REAL"
    elif trust_score < 30:
        verdict = "FAKE"
    else:
        verdict = "MIXED"

    # Остальные данные упаковываем в ai_metadata
    metadata = ai_response.model_dump(exclude={'trust_score'})

    return {
        "fake_probability": 1.0 - (trust_score / 100.0), # Инвертируем trust_score для fake_probability
        "verdict": verdict,
        "ai_metadata": metadata
    }


def process_text_submission(db: Session, user_id: str, content_text: str) -> TextAnalyzeResponse:
    """
    Основная логика для текстовой заявки: DB -> AI -> DB -> API Response.
    """
    # 1. Вставка Submission (с дефолтным статусом 'pending')
    submission: Submission = create_submission(
        db, 
        user_id=uuid.UUID(user_id),
        media_type='text', 
        content_text=content_text, 
        media_url='n/a' # Для текста URL не требуется
    )
    
    # 2. Анализ ИИ (вызываем ваш существующий сервис)
    ai_response: TextAnalyzeResponse = analyze_text(content_text)
    
    # 3. Форматирование результатов для БД
    db_data = _format_ai_response_to_db(ai_response)
    
    # 4. Вставка TrustScore и обновление Submission
    create_trust_score(
        db, 
        submission_id=submission.id,
        fake_probability=db_data['fake_probability'],
        verdict=db_data['verdict'],
        ai_metadata=db_data['ai_metadata']
    )
    # Обновляем статус Submission до 'completed'
    submission.status = 'completed'
    db.commit()

    # 5. Возвращаем ответ API
    return ai_response

def process_image_submission(db: Session, user_id: str, image_bytes: bytes, filename: str) -> ImageAnalyzeResponse:
    """
    Основная логика для заявки изображения: DB -> AI -> DB -> API Response.
    """
    # 1. Вставка Submission (media_url будет заглушкой, в реальном мире - это ссылка на S3)
    media_url = f"s3://uploads/{filename}"
    submission: Submission = create_submission(
        db, 
        user_id=uuid.UUID(user_id),
        media_type='image', 
        media_url=media_url
    )
    
    # 2. Анализ ИИ (вызываем ваш существующий сервис)
    ai_response: ImageAnalyzeResponse = analyze_image(image_bytes)
    
    # 3. Форматирование результатов для БД
    db_data = _format_ai_response_to_db(ai_response)
    
    # 4. Вставка TrustScore и обновление Submission
    create_trust_score(
        db, 
        submission_id=submission.id,
        fake_probability=db_data['fake_probability'],
        verdict=db_data['verdict'],
        ai_metadata=db_data['ai_metadata']
    )
    # Обновляем статус Submission до 'completed'
    submission.status = 'completed'
    db.commit()

    # 5. Возвращаем ответ API
    return ai_response