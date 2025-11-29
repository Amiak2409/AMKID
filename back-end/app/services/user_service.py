import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

# Импортируем модели из app.models.database_ops (предполагаем, что они доступны)
from app.models.database_ops import Submission, TrustScore 

def get_user_history_submissions_optimized(db: Session, user_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Оптимизированный запрос: получает все заявки пользователя с результатами.
    Исправлены импорты (joinedload, desc) и тип user_id (UUID).
    """
    
    # Защита от передачи не-UUID (актуально для тестового ID 999999)
    if not isinstance(user_id, uuid.UUID):
        return []

    submissions = (
        db.query(Submission)
        .filter(Submission.user_id == user_id)
        # Оптимизация: Предзагрузка TrustScore для избежания N+1
        .options(joinedload(Submission.trust_score)) 
        # Сортировка: Самая новая в начале
        .order_by(desc(Submission.created_at)) 
        .all()
    )
    
    history_data = [
        {
            "submission_id": sub.id,
            "status": sub.status,
            "created_at": sub.created_at.isoformat(),
            "media_url": sub.media_url, # Добавлено для прохождения теста
            "final_verdict": sub.trust_score.verdict if sub.trust_score else "PENDING"
        } 
        for sub in submissions
    ]
    
    return history_data