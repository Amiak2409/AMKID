import pytest
import uuid
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy.orm import Session
from app.models.database_ops import (
    SessionLocal,
    create_db_and_tables,
    create_user,
    create_submission,
    create_trust_score,
    update_submission_status,
    get_pending_submissions,
    get_submission_with_score,
    User,
    Submission
)

# --- ФИКСАТУРЫ PYTEST (Транзакционный подход) ---

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Создает таблицы в базе данных один раз перед всеми тестами."""
    create_db_and_tables()

# Фикстура для каждой тестовой функции
@pytest.fixture
def db() -> Session:
    """
    Создает сессию, начинает транзакцию и ОТКАТЫВАЕТ ее после завершения теста.
    Дополнительно очищаем таблицу Submission перед запуском для надежности.
    """
    db = SessionLocal()
    
    # !!! ДОПОЛНИТЕЛЬНАЯ ОЧИСТКА ДАННЫХ ПЕРЕД ТЕСТОМ (Если откат не работает)
    # db.query(Submission).delete() 
    # db.query(User).delete()
    # db.commit() 
    # 
    # Вместо этого, давайте положимся на транзакцию и просто убедимся, что 
    # лишние заявки не были созданы в других тестах.
    
    # 1. Начинаем транзакцию
    db.begin()
    
    try:
        yield db # Передаем сессию тестовой функции
    finally:
        # 2. Откатываем транзакцию (Rollback), чтобы очистить изменения
        db.rollback() 
        db.close()

@pytest.fixture
def test_user(db: Session) -> User:
    """Создает и возвращает тестового пользователя для всех тестов."""
    return create_user(db, username=f"test_user_{uuid.uuid4()}")


# --- ТЕСТОВЫЕ ФУНКЦИИ ---

def test_user_creation_and_retrieval(db: Session):
    """Проверяет создание пользователя и уникальность."""
    username = f"unique_tester_{uuid.uuid4()}" 
    user = create_user(db, username=username)

    # Проверяем, что пользователь создан
    assert user.id is not None
    assert user.username == username
    
    # Проверяем, что можем найти его по ID
    retrieved_user = db.query(User).filter(User.id == user.id).first()
    assert retrieved_user.username == username


def test_submission_creation_and_user_link(db: Session, test_user: User):
    """Проверяет создание заявки и правильную установку внешнего ключа (FK)."""
    
    sub = create_submission(
        db, 
        user_id=test_user.id, 
        media_type='video', 
        media_url='s3://test/video_001.mp4' # Это будет наш S3-ключ
    )

    # Проверяем прямую привязку
    assert sub.user_id == test_user.id
    # Проверяем связь SQLAlchemy (Relationship)
    assert sub.user.username == test_user.username


def test_submission_status_updates(db: Session, test_user: User):
    """Проверяет корректное изменение статуса заявки."""
    sub = create_submission(db, user_id=test_user.id, media_type='image', media_url='s3/img.png')
    
    # Имитация воркера, берущего задачу
    update_submission_status(db, sub.id, 'processing')
    updated_sub = db.query(Submission).filter(Submission.id == sub.id).first()
    assert updated_sub.status == 'processing'

    # Имитация завершения задачи
    update_submission_status(db, sub.id, 'completed')
    completed_sub = db.query(Submission).filter(Submission.id == sub.id).first()
    assert completed_sub.status == 'completed'


def test_ml_worker_queue_management(db: Session, test_user: User):
    # ИСПРАВЛЕНИЕ: Добавляем обязательный аргумент media_url
    create_submission(db, user_id=test_user.id, media_type='text', 
                      content_text='News item', media_url='n/a') # <--- ИСПРАВЛЕНО
    
    # Completed task (не должна быть найдена)
    sub_completed = create_submission(db, user_id=test_user.id, media_type='video', media_url='s3/done.mp4')
    update_submission_status(db, sub_completed.id, 'completed', commit=False)
    db.commit()

    pending_tasks = get_pending_submissions(db, limit=10)
    
    assert len(pending_tasks) >= 1
    assert pending_tasks[0].media_type == 'text'


def test_full_result_retrieval(db: Session, test_user: User):
    """Проверяет создание и чтение связки Submission + TrustScore (с JSONB)."""
    
    sub = create_submission(db, user_id=test_user.id, media_type='image', media_url='s3/img.png')
    
    # Запись результата ML
    create_trust_score(
        db, 
        sub.id, 
        fake_probability=0.999, 
        verdict="FAKE", 
        ai_metadata={"model_version": "v2.1", "confidence": 0.999}
    )

    # Получение полной информации
    final_sub = get_submission_with_score(db, sub.id)
    
    assert final_sub is not None
    assert final_sub.trust_score.verdict == "FAKE"
    # Проверяем, что JSONB вернулся как словарь
    assert final_sub.trust_score.ai_metadata["model_version"] == "v2.1"