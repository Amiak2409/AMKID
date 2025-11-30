import os
import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict

from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    desc,
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session, joinedload
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
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.now)

    # Отношение: Один пользователь может иметь много заявок (обратная связь)
    submissions = relationship("Submission", back_populates="user")

    # История запросов (новая связь)
    history = relationship(
        "History",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def repr(self):
        return f"<User(id={self.id}, username={self.username})>"


class Submission(Base):
    """Таблица submissions (Входящие данные)"""
    __tablename__ = "submissions"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # user_id UUID
    user_id: Optional[UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    # media_type VARCHAR(10) NOT NULL
    media_type: str = Column(String(10), nullable=False)

    # content_text TEXT
    content_text: Optional[str] = Column(Text, nullable=True)

    # media_url TEXT
    media_url: Optional[str] = Column(Text, nullable=False)

    # status VARCHAR(20) DEFAULT 'pending'
    status: str = Column(String(20), default="pending", nullable=False)

    # created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.now)
    updated_at: datetime = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    # Связь с результатами
    user = relationship("User", back_populates="submissions")
    trust_score = relationship("TrustScore", back_populates="submission", uselist=False)

    def repr(self):
        return f"<Submission(id={self.id}, type={self.media_type}, status={self.status})>"


class TrustScore(Base):
    """Таблица trust_scores (Результаты ИИ)"""
    __tablename__ = "trust_scores"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # submission_id UUID NOT NULL REFERENCES submissions(id)
    submission_id: UUID = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)

    # fake_probability FLOAT NOT NULL
    fake_probability: float = Column(Float, nullable=True)

    # verdict VARCHAR(50)
    verdict: str = Column(String(50), nullable=True)

    # model_version VARCHAR(50)
    model_version: str = Column(String(50), default="v1.0")

    # ai_metadata JSONB
    ai_metadata: Dict[str, Any] = Column(JSONB, default={})

    # created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.now)

    # связь с заявкой
    submission = relationship("Submission", back_populates="trust_score")

    def repr(self):
        return f"<TrustScore(id={self.id}, fake_prob={self.fake_probability})>"


class History(Base):
    """
    Таблица history — история запросов пользователя.

    Поля:
    - id         — UUID записи
    - user_id    — владелец (FK на users.id)
    - question   — то, что ввёл пользователь (контент)
    - raw_response — полный JSON-ответ модели (TextAnalyzeResponse / ImageAnalyzeResponse)
    - created_at — когда запрос был сделан
    - kind       — тип ("text" / "image" и т.п.)
    """
    __tablename__ = "history"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    question: str = Column(Text, nullable=False)
    raw_response: Dict[str, Any] = Column(JSONB, nullable=False)

    created_at: datetime = Column(DateTime(timezone=True), default=datetime.now)
    kind: str = Column(String(20), nullable=False)

    user = relationship("User", back_populates="history")

    def repr(self):
        return f"<History(id={self.id}, user_id={self.user_id}, kind={self.kind})>"


# ---------------------- DB INIT ----------------------


def create_db_and_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Структура базы данных успешно создана (или уже существует).")
    except OperationalError as e:
        print("❌ Ошибка подключения к базе данных. Проверьте настройки в .env и запущен ли PostgreSQL.")
        print(f"Детали ошибки: {e}")
        exit(1)


# --- ПРИМЕР: CREATE_USER (старое) ---
def create_user(db: Session, username: str) -> User:
    """Создает нового пользователя."""
    new_user = User(username=username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def create_submission(
    db: Session,
    media_type: str,
    media_url: str,
    user_id: Optional[UUID] = None,
    content_text: Optional[str] = None,
) -> Submission:
    """Создает новую заявку в таблице submissions."""
    new_submission = Submission(
        user_id=user_id,
        media_type=media_type,
        content_text=content_text,
        media_url=media_url,
    )
    db.add(new_submission)
    db.flush()
    db.refresh(new_submission)
    return new_submission


def get_user_history_submissions_optimized(db: Session, user_id: uuid.UUID):
    """
    Старый (ML)-хистори по submissions — оставляю как есть.
    """
    submissions = (
        db.query(Submission)
        .filter(Submission.user_id == user_id)
        .options(joinedload(Submission.trust_score))
        .order_by(desc(Submission.created_at))
        .all()
    )

    history_data = [
        {
            "submission_id": sub.id,
            "status": sub.status,
            "created_at": sub.created_at.isoformat(),
            "final_verdict": sub.trust_score.verdict if sub.trust_score else "PENDING",
        }
        for sub in submissions
    ]

    return history_data


def get_pending_submissions(db: Session, limit: int = 10) -> List[Submission]:
    """Извлекает заявки со статусом 'pending' для обработки ML-воркером."""
    return db.query(Submission).filter(Submission.status == "pending").limit(limit).all()


def update_submission_status(
    db: Session,
    submission_id: UUID,
    new_status: str,
    commit: bool = True,
) -> Optional[Submission]:
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


def create_trust_score(
    db: Session,
    submission_id: UUID,
    fake_probability: float,
    verdict: str,
    ai_metadata: Dict[str, Any] = None,
) -> TrustScore:
    """Создает запись результата анализа в таблице trust_scores."""
    new_score = TrustScore(
        submission_id=submission_id,
        fake_probability=fake_probability,
        verdict=verdict,
        ai_metadata=ai_metadata if ai_metadata is not None else {},
    )
    db.add(new_score)
    db.flush()
    db.refresh(new_score)
    return new_score


def get_submission_with_score(db: Session, submission_id: UUID) -> Optional[Submission]:
    """Извлекает заявку вместе с ее результатом (если он есть)."""
    return db.query(Submission).filter(Submission.id == submission_id).first()


# ---------------------- HISTORY CRUD ----------------------


def create_history_record(
    db: Session,
    user_id: uuid.UUID,
    question: str,
    raw_response: Dict[str, Any],
    kind: str,
) -> History:
    """
    Создает одну запись истории.
    """
    record = History(
        user_id=user_id,
        question=question,
        raw_response=raw_response,
        kind=kind,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_user_history(db: Session, user_id: uuid.UUID) -> List[History]:
    """
    Возвращает все записи истории пользователя, отсортированные по дате (новые сверху).
    """
    return (
        db.query(History)
        .filter(History.user_id == user_id)
        .order_by(desc(History.created_at))
        .all()
    )


def delete_history_item(db: Session, user_id: uuid.UUID, history_id: uuid.UUID) -> bool:
    """
    Удаляет одну запись истории по id, гарантируя, что она принадлежит этому user_id.
    """
    record = (
        db.query(History)
        .filter(History.id == history_id, History.user_id == user_id)
        .first()
    )
    if not record:
        return False

    db.delete(record)
    db.commit()
    return True


def delete_all_history_for_user(db: Session, user_id: uuid.UUID) -> int:
    """
    Удаляет ВСЮ историю пользователя. Возвращает количество удалённых записей.
    """
    q = db.query(History).filter(History.user_id == user_id)
    count = q.count()
    q.delete(synchronize_session=False)
    db.commit()
    return count


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
