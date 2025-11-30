# app/services/submission_service.py

import uuid
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Для точного отлова ошибок БД

# Предполагаемые импорты:
# Убедитесь, что ваш database_ops содержит create_submission, create_trust_score, Submission
from app.models.database_ops import create_submission, create_trust_score, Submission 
from app.models.schemas import TextAnalyzeResponse, ClaimEvaluation
from app.services.ai_service import analyze_text # Ваша функция анализа

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) 

# --- Утилита для очистки JSONB ---
def to_clean_dict(claims: List[ClaimEvaluation]) -> List[Dict[str, Any]]:
    """
    Преобразует список Pydantic-объектов ClaimEvaluation в чистый список словарей Python.
    Это необходимо для надежной записи в колонку JSONB, чтобы избежать конфликтов ORM.
    """
    clean_claims = []
    for claim in claims:
        # Ручная сборка словаря, гарантируем чистые float и строки
        clean_claims.append({
            "text": claim.text,
            "true_likeliness": float(claim.true_likeliness), 
            "comment": claim.comment
        })
    return clean_claims

# --- Главная функция сервиса ---
def process_text_submission_fixed(db: Session, user_id: str, content: str) -> TextAnalyzeResponse:
    """
    Выполняет анализ текста AI и записывает данные в БД в одной транзакции.
    """
    
    # 1. Получение ответа AI
    try:
        ai_response: TextAnalyzeResponse = analyze_text(content)
    except Exception as e:
        logger.error(f"Ошибка при получении ответа от AI: {e}")
        raise e

    # 2. Форматирование данных для TrustScore
    trust_score = ai_response.trust_score
    fake_probability = 1.0 - (trust_score / 100.0) 
    verdict = "REAL" if trust_score > 80 else ("FAKE" if trust_score < 30 else "MIXED")
    
    # 🚨 Очистка данных для записи в JSONB
    clean_claims = to_clean_dict(ai_response.claims_evaluation)
    
    ai_metadata: Dict[str, Any] = {
        "ai_likeliness": ai_response.ai_likeliness,
        "manipulation_score": ai_response.manipulation_score,
        "emotion_intensity": ai_response.emotion_intensity,
        "dangerous_phrases": ai_response.dangerous_phrases,
        "claims_evaluation": clean_claims, # <-- ЧИСТЫЙ СПИСОК СЛОВАРЕЙ
        "summary": ai_response.summary,
    }
    
    # === НАЧАЛО ТРАНЗАКЦИИ ===
    try:
        # 3. Создаем Submission
        submission: Submission = create_submission(
            db, 
            user_id=uuid.UUID(user_id),
            media_type='text', 
            content_text=content, 
            media_url='n/a'
        )
        logger.debug(f"Submission {submission.id} создан.")
        
        # 4. Создаем TrustScore
        create_trust_score(
            db=db,
            submission_id=submission.id,
            fake_probability=fake_probability,
            verdict=verdict,
            ai_metadata=ai_metadata
        )
        logger.debug("TrustScore создан.")

        # 5. Фиксация транзакции
        submission.status = 'completed'
        db.commit()
        logger.info(f"🎉 УСПЕХ! Данные для Submission {submission.id} зафиксированы.")
        
        return ai_response

    except SQLAlchemyError as e:
        # Ловим ошибки БД и делаем откат
        logger.error(f"❌ SQLAlchemy Error: {e}", exc_info=True)
        db.rollback()
        raise e
    except Exception as e:
        # Ловим остальные ошибки и делаем откат
        logger.error(f"❌ Critical Error during transaction: {e}", exc_info=True)
        db.rollback()
        raise e