import pytest
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta
# Импортируем все необходимые функции
from app.models.database_ops import create_user, create_submission, create_trust_score 
from app.services.user_service import get_user_history_submissions_optimized 


def test_history_retrieval_success(db: Session, test_user):
    """Проверяет, что история пользователя извлекается корректно и в правильном порядке."""
    
    # 1. Создаем заявки для основного пользователя (test_user)
    # Старая заявка
    sub_old = create_submission(db, user_id=test_user.id, media_type='image', media_url='old.jpg')
    sub_old.created_at = datetime.now() - timedelta(minutes=5)
    db.flush() # Фиксируем изменение времени
    
    # Создаем TrustScore для старой заявки
    create_trust_score(db, sub_old.id, fake_probability=0.2, verdict="REAL", commit=False)

    # Новая заявка
    sub_new = create_submission(db, user_id=test_user.id, media_type='video', media_url='new.mp4')
    sub_new.created_at = datetime.now() 
    db.flush() # Фиксируем изменение времени

    # Создаем TrustScore для новой заявки
    create_trust_score(db, sub_new.id, fake_probability=0.8, verdict="FAKE", commit=False)

    db.commit() # Один коммит для всех изменений

    # 2. Создаем заявку для другого пользователя (не должна попасть в историю)
    other_user = create_user(db, username=f"other_{uuid.uuid4()}")
    other_sub = create_submission(db, user_id=other_user.id, media_type='text', media_url='other.txt')
    create_trust_score(db, other_sub.id, fake_probability=0.5, verdict="MIXED", commit=True)

    # 3. Вызываем функцию
    history = get_user_history_submissions_optimized(db, test_user.id)
    
    # 4. Проверки
    assert len(history) == 2, "Должно быть ровно 2 заявки."
    
    # Проверка сортировки: самая новая заявка должна быть первой
    assert history[0]['submission_id'] == sub_new.id
    assert history[1]['submission_id'] == sub_old.id
    
    # Проверка данных, включая media_url и final_verdict
    assert history[0]['media_url'] == 'new.mp4'
    assert history[0]['final_verdict'] == 'FAKE'
    assert history[1]['final_verdict'] == 'REAL'


def test_history_retrieval_no_submissions(db: Session, test_user):
    """Проверяет, что для пользователя без заявок возвращается пустой список."""
    
    history = get_user_history_submissions_optimized(db, test_user.id)
    assert history == []


def test_history_retrieval_user_not_found(db: Session):
    """Проверяет, что для несуществующего пользователя возвращается пустой список."""
    
    # ИСПРАВЛЕНИЕ: Используем несуществующий UUID
    non_existent_id = uuid.uuid4() 
    history = get_user_history_submissions_optimized(db, non_existent_id)
    assert history == []