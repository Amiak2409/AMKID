import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Any, Dict

# Импорты для работы с БД и ORM
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, DateTime, ForeignKey, Text, desc
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session, joinedload
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.exc import OperationalError
from faker import Faker

load_dotenv()
fake = Faker('ru_RU')

# ==========================================================
# 1. КОНФИГУРАЦИЯ И НАСТРОЙКА БД (Код из database_ops)
# ==========================================================

# НАСТРОЙКА ПОДКЛЮЧЕНИЯ
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Пробуем создать движок
try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
except Exception as e:
    print(f"❌ Ошибка создания движка: {e}")
    exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================================
# 2. МОДЕЛИ (Код из database_ops)
# ==========================================================

class User(Base):
    """Таблица users (Пользователи)"""
    __tablename__ = "users"
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: str = Column(String(100), unique=True, nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.now)
    submissions = relationship("Submission", back_populates="user")
    
class Submission(Base):
    """Таблица submissions (Входящие данные)"""
    __tablename__ = "submissions"
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Optional[UUID] = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)    
    media_type: str = Column(String(10), nullable=False) 
    content_text: Optional[str] = Column(Text, nullable=True) 
    media_url: str = Column(Text, nullable=False)
    status: str = Column(String(20), default='pending', nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.now)
    updated_at: datetime = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    user = relationship("User", back_populates="submissions")
    trust_score = relationship("TrustScore", back_populates="submission", uselist=False)

class TrustScore(Base):
    """Таблица trust_scores (Результаты ИИ)"""
    __tablename__ = "trust_scores"
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: UUID = Column(UUID(as_uuid=True), ForeignKey('submissions.id'), nullable=False)
    fake_probability: float = Column(Float, nullable=False)
    verdict: str = Column(String(50), nullable=True)
    model_version: str = Column(String(50), default='v1.0')
    ai_metadata: Dict[str, Any] = Column(JSONB, default={})
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.now)
    submission = relationship("Submission", back_populates="trust_score")

# ==========================================================
# 3. CRUD ФУНКЦИИ (Код из database_ops)
# ==========================================================

def create_db_and_tables():
    """Создает все таблицы. ВАЖНО: Не удаляет старые данные!"""
    try:
        # Для сида, возможно, нужно очистить старые данные, но здесь только создание.
        # Если нужно удаление: Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✅ Структура базы данных успешно создана (или уже существует).")
    except OperationalError as e:
        print(f"❌ Ошибка подключения к базе данных. Проверьте настройки в .env.")
        print(f"Детали ошибки: {e}")
        exit(1)

def create_user(db: Session, username: str) -> User:
    """Создает нового пользователя."""
    new_user = User(username=username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def create_submission(db: Session, media_type: str, media_url: str, user_id: Optional[uuid.UUID] = None, content_text: Optional[str] = None) -> Submission:
    """Создает новую заявку. Сохраняет сразу в БД."""
    new_submission = Submission(
        user_id=user_id,
        media_type=media_type,
        content_text=content_text,
        media_url=media_url
    )
    db.add(new_submission)
    db.commit() # <--- Коммит
    db.refresh(new_submission)
    return new_submission

def update_submission_status(db: Session, submission_id: uuid.UUID, new_status: str, commit: bool = True) -> Optional[Submission]:
    """Обновляет статус заявки."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if submission:
        submission.status = new_status
        submission.updated_at = datetime.now() 
        if commit:
            db.commit()
            db.refresh(submission)
        return submission
    return None

def create_trust_score(db: Session, submission_id: uuid.UUID, fake_probability: float, verdict: str, ai_metadata: Dict[str, Any] = None) -> TrustScore:
    """Создает запись результата анализа. Сохраняет сразу в БД."""
    new_score = TrustScore(
        submission_id=submission_id,
        fake_probability=fake_probability,
        verdict=verdict,
        ai_metadata=ai_metadata if ai_metadata is not None else {}
    )
    db.add(new_score)
    db.commit() # <--- Коммит
    db.refresh(new_score)
    return new_score

# ==========================================================
# 4. АССЕМБЛЕР (Прокси-класс для простоты сида)
# ==========================================================

class TrustScoreAssembler:
    """Имитация сервиса, который собирает метрики и сохраняет результат."""
    def __init__(self, submission: Submission):
        self.submission = submission
        self.fake_probability = 0.5
        self.verdict = "UNCLEAR"
        self.ai_metadata = {}

    def add_metric_result(self, metric_name: str, data: Dict[str, Any]):
        """Добавляет данные от ML-моделей в метаданные."""
        self.ai_metadata[metric_name] = data

    def set_overall_score(self, verdict: str, probability: float):
        """Устанавливает итоговый вердикт."""
        self.verdict = verdict
        self.fake_probability = probability

    def save_to_db(self, db: Session):
        """Создает TrustScore в БД."""
        # Используем функцию из CRUD, чтобы создать связанную запись
        create_trust_score(
            db, 
            submission_id=self.submission.id, 
            fake_probability=self.fake_probability, 
            verdict=self.verdict, 
            ai_metadata=self.ai_metadata
        )
        
# ==========================================================
# 5. ГЛАВНАЯ ФУНКЦИЯ СИДА
# ==========================================================

NUM_USERS = 5
SUBMISSIONS_PER_USER = 10
VERDICTS = ["REAL", "FAKE", "MIXED", "UNCLEAR"]

def seed_database(db: Session):
    """Основная функция для наполнения базы данных тестовыми данными."""
    
    print(">>> Запуск очистки и создания таблиц...")
    create_db_and_tables() 
    
    users = []
    
    # 1. Создание Пользователей
    print(f"--- Создание {NUM_USERS} пользователей... ---")
    for i in range(NUM_USERS):
        user = create_user(db, username=f"user_{i}_{fake.first_name().lower()}")
        users.append(user)
    
    # 2. Создание Заявок и Метрик
    print(f"--- Создание {NUM_USERS * SUBMISSIONS_PER_USER} заявок... ---")
    
    submissions_created = 0
    
    for user in users:
        for j in range(SUBMISSIONS_PER_USER):
            # Случайная дата создания
            created_at = datetime.now() - timedelta(days=fake.random_int(min=1, max=30))
            
            # 2.1 Создание Submission (коммитится с дефолтным created_at)
            sub = create_submission(
                db, 
                user_id=user.id, 
                media_type=fake.random_element(["video", "image", "text"]), 
                media_url=f"s3://content/{user.id}_{j}.mp4"
            )
            
            # 2.2 Обновляем created_at (требует дополнительного flush/commit, но мы его отложим)
            sub.created_at = created_at
            
            # 2.3 Создание Метрик
            assembler = TrustScoreAssembler(submission=sub)
            
            # Случайные метрики
            final_verdict = fake.random_element(VERDICTS)
            # Вероятность либо высокая (фейк), либо низкая (реальный)
            fake_prob = round(fake.random_element([fake.pyfloat(min_value=0.8, max_value=0.99), fake.pyfloat(min_value=0.01, max_value=0.2)]), 3)
            
            assembler.add_metric_result("ai_detection", {"score": fake_prob, "model": "v3"})
            assembler.add_metric_result("hate_speech", {"is_racist": fake.boolean(), "score": fake.pyfloat(min_value=0, max_value=1)})
            
            assembler.set_overall_score(verdict=final_verdict, probability=fake_prob)
            
            # 2.4 Сохранение TrustScore
            assembler.save_to_db(db) # Эта функция делает commit для TrustScore
            
            # 2.5 Обновление статуса Submission (и сохранение измененного created_at)
            # Используем update_submission_status, чтобы обновить статус до 'completed' 
            # и сохранить измененное sub.created_at, используя ее commit.
            update_submission_status(db, sub.id, new_status='completed', commit=True)
            
            submissions_created += 1
            if submissions_created % 25 == 0:
                print(f"   ... Обработано {submissions_created} заявок.")


    print("\n✅ Наполнение базы данных завершено.")
    print(f"Создано пользователей: {db.query(User).count()}")
    print(f"Создано заявок: {db.query(Submission).count()}")
    print(f"Создано результатов: {db.query(TrustScore).count()}")


if __name__ == "__main__":
    try:
        db = SessionLocal()
        seed_database(db)
    except Exception as e:
        # В случае ошибки делаем откат
        if 'db' in locals() and db:
            db.rollback() 
        print(f"\n❌ Ошибка при наполнении базы данных: {e}")
    finally:
        if 'db' in locals() and db:
            db.close()