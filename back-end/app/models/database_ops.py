import os
import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, DateTime, ForeignKey, Text, desc # <-- desc добавлен
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session, joinedload # <-- joinedload добавлен
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.exc import OperationalError

load_dotenv()

# НАСТРОЙКА ПОДКЛЮЧЕНИЯ
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Строка для SQLAlchemy
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
except Exception as e:
    print(f"❌ Ошибка создания движка: {e}")
    exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    """Таблица users (Пользователи)"""
    __tablename__ = "users"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: str = Column(String(100), unique=True, nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.now)

    # Отношение: Один пользователь может иметь много заявок (обратная связь)
    submissions = relationship("Submission", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
    
class Submission(Base):
    """Таблица submissions (Входящие данные)"""
    __tablename__ = "submissions"

    # id UUID PRIMARY KEY DEFAULT gen_random_uuid()
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # user_id UUID
    user_id: Optional[UUID] = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)    
    
    # media_type VARCHAR(10) NOT NULL
    media_type: str = Column(String(10), nullable=False) 
    
    # content_text TEXT
    content_text: Optional[str] = Column(Text, nullable=True) 
    
    # media_url TEXT
    media_url: str = Column(Text, nullable=False)
    
    # status VARCHAR(20) DEFAULT 'pending'
    status: str = Column(String(20), default='pending', nullable=False)
    
    # created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.now)
    updated_at: datetime = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    # Связь с результатами
    user = relationship("User", back_populates="submissions")
    trust_score = relationship("TrustScore", back_populates="submission", uselist=False)

    def __repr__(self):
        return f"<Submission(id={self.id}, type={self.media_type}, status={self.status})>"

    
class TrustScore(Base):
    """Таблица trust_scores (Результаты ИИ)"""
    __tablename__ = "trust_scores"

    # id UUID PRIMARY KEY DEFAULT gen_random_uuid()
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # submission_id UUID NOT NULL REFERENCES submissions(id)
    submission_id: UUID = Column(UUID(as_uuid=True), ForeignKey('submissions.id'), nullable=False)
    
    # fake_probability FLOAT NOT NULL
    fake_probability: float = Column(Float, nullable=False)
    
    # verdict VARCHAR(50)
    verdict: str = Column(String(50), nullable=True)
    
    # model_version VARCHAR(50)
    model_version: str = Column(String(50), default='v1.0')

    # ai_metadata JSONB
    ai_metadata: Dict[str, Any] = Column(JSONB, default={})
    
    # created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.now)

    # связь с заявкой
    submission = relationship("Submission", back_populates="trust_score")

    def __repr__(self):
        return f"<TrustScore(id={self.id}, fake_prob={self.fake_probability})>"


# CRUD

def create_db_and_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Структура базы данных успешно создана (или уже существует).")
    except OperationalError as e:
        print(f"❌ Ошибка подключения к базе данных. Проверьте настройки в .env и запущен ли PostgreSQL.")
        print(f"Детали ошибки: {e}")
        exit(1)

# --- НОВАЯ ФУНКЦИЯ: CREATE_USER ---
def create_user(db: Session, username: str) -> User:
    """Создает нового пользователя."""
    new_user = User(username=username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def create_submission(db: Session, media_type: str, media_url: str, user_id: Optional[UUID] = None, content_text: Optional[str] = None) -> Submission:
    """Создает новую заявку в таблице submissions."""
    new_submission = Submission(
        user_id=user_id,
        media_type=media_type,
        content_text=content_text,
        media_url=media_url
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)
    return new_submission

def get_user_history_submissions_optimized(db: Session, user_id: int):
    """
    Оптимизированный запрос: получает все заявки пользователя
    за ОДИН SQL-запрос, избегая проблемы N+1.
    """
    
    # Мы запрашиваем Submission, а не User, так как нам нужен список Submission
    submissions = (
        db.query(Submission)
        .filter(Submission.user_id == user_id)
        # ОПЦИЯ: Предзагрузка TrustScore, чтобы избежать N+1 при доступе к вердикту
        .options(joinedload(Submission.trust_score)) 
        # Сортировка по дате создания
        .order_by(desc(Submission.created_at)) 
        .all()
    )
    
    # Дальнейшая обработка и форматирование (как в предыдущем ответе)
    history_data = [
        {
            "submission_id": sub.id,
            "status": sub.status,
            "created_at": sub.created_at.isoformat(),
            # TrustScore уже загружен (благодаря joinedload), обращение к нему быстрое
            "final_verdict": sub.trust_score.verdict if sub.trust_score else "PENDING"
        } 
        for sub in submissions
    ]
    
    return history_data

def get_pending_submissions(db: Session, limit: int = 10) -> List[Submission]:
    """Извлекает заявки со статусом 'pending' для обработки ML-воркером."""
    return db.query(Submission).filter(Submission.status == 'pending').limit(limit).all()


def update_submission_status(db: Session, submission_id: UUID, new_status: str, commit: bool = True) -> Optional[Submission]:
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

def create_trust_score(db: Session, submission_id: UUID, fake_probability: float, verdict: str, ai_metadata: Dict[str, Any] = None, commit: bool = True) -> TrustScore:
    """Создает запись результата анализа в таблице trust_scores."""
    new_score = TrustScore(
        submission_id=submission_id,
        fake_probability=fake_probability,
        verdict=verdict,
        ai_metadata=ai_metadata if ai_metadata is not None else {}
    )
    db.add(new_score)
    db.commit()
    db.refresh(new_score)
    return new_score

def get_submission_with_score(db: Session, submission_id: UUID) -> Optional[Submission]:
    """Извлекает заявку вместе с ее результатом (если он есть)."""
    return db.query(Submission).filter(Submission.id == submission_id).first()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()