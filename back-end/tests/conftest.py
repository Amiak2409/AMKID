# conftest.py (в папке 'tests/')

import pytest
import sys
import os
from sqlalchemy.orm import Session
import uuid

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

from app.models.database_ops import SessionLocal, Base, engine, create_user, User 

# --- 1. Фикстура DB Session (db) ---
@pytest.fixture(scope="session")
def setup_db():
    """Создает таблицы один раз перед всеми тестами и удаляет их после."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Опционально: можно удалить таблицы после всех тестов, если не нужно сохранять состояние
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(setup_db):
    """Предоставляет сессию БД для каждого теста (транзакция с откатом)."""
    # Создаем новую сессию
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection)
    
    # Чтобы тесты не влияли друг на друга, используем откат
    try:
        yield db
    finally:
        db.close()
        transaction.rollback() # Откатываем все изменения
        connection.close()

# --- 2. Фикстура Test User (test_user) ---
@pytest.fixture(scope="function")
def test_user(db: Session) -> User:
    """Создает тестового пользователя для каждой функции."""
    user = create_user(db, username=f"test_user_{uuid.uuid4()}")
    # Нет необходимости в коммите/откате, так как это делает фикстура 'db'
    return user