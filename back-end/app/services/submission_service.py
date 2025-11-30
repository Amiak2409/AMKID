# app/services/submission_service.py

import uuid
import os
from pydantic import BaseModel
from typing import Any, Dict
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
    metadata = {}

    return {
        "fake_probability": 1.0 - (trust_score / 100.0), # Инвертируем trust_score для fake_probability
        "verdict": verdict,
        "ai_metadata": metadata
    }


# app/services/submission_service.py

def process_text_submission(db: Session, user_id: str, content_text: str) -> TextAnalyzeResponse:
    try:
        # 1. Анализ ИИ (делаем это СНАЧАЛА, чтобы если ИИ упал, мы даже не трогали базу)
        ai_response: TextAnalyzeResponse = analyze_text(content_text)

        # === ВРЕМЕННЫЙ БЛОК ЛОГИРОВАНИЯ В ФАЙЛ ===
        PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) 
        log_path = os.path.join(PROJECT_ROOT, 'ai_response_log.json')
        logger.debug(f"DEBUG: Полный путь для записи AI-ответа: {log_path}")
        
        try:
            data_to_log = ai_response.model_dump() 
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_log, f, ensure_ascii=False, indent=4)
            logger.debug("DEBUG: Файл успешно записан.")

        except Exception as e:
        # Используем logger.error, чтобы гарантировать, что ошибка будет видна
        logger.error(f"🚨 ОШИБКА ЛОГИРОВАНИЯ ФАЙЛА: {e}", exc_info=True)
        # ========================================
        
        # 2. Форматирование результатов
        db_data = _format_ai_response_to_db(ai_response)

        print(f"DEBUG: AI Score: {db_data['fake_probability']}, Metadata keys: {db_data['ai_metadata'].keys()}")

        # 3. Открываем транзакцию. 
        # Создаем заявку (Submission)
        submission: Submission = create_submission(
            db, 
            user_id=uuid.UUID(user_id),
            media_type='text', 
            content_text=content_text, 
            media_url='n/a'
        )
        
        # 4. Вставка TrustScore
        create_trust_score(
            db, 
            submission_id=submission.id,
            fake_probability=db_data['fake_probability'],
            verdict=db_data['verdict'],
            ai_metadata=db_data['ai_metadata'], # Передаем как dict!
            commit=False # Пока не коммитим
        )
        
        # 5. Обновляем статус и делаем ОДИН общий коммит
        submission.status = 'completed'
        db.commit() # Сохраняем все сразу (и заявку, и скор)
        print("DEBUG: Успешно сохранено в БД.")

        return ai_response

    except Exception as e:
        print(f"🚨 Ошибка обработки текста: {e}")
        db.rollback() 
        raise e

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