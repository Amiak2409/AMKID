import hashlib
import uuid
from typing import List as TypingList

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Depends,
    HTTPException,
    Header,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.database_ops import (
    create_db_and_tables,
    get_db,
    User,
    create_history_record,
    get_user_history,
    delete_history_item,
    delete_all_history_for_user,
)
from app.models.schemas import (
    TextAnalyzeRequest,
    TextAnalyzeResponse,
    ImageAnalyzeResponse,
    HistoryItem,
)
from app.services.ai_service import analyze_image
from app.services.submission_service import process_text_submission_fixed


app = FastAPI(title="AI Identifier API", version="0.1")


@app.on_event("startup")
def on_startup():
    """
    Создает таблицы в базе данных при запуске приложения, если они не существуют.
    """
    print("Инициализация БД: Создание таблиц...")
    create_db_and_tables()
    print("Инициализация БД завершена.")


# Разрешаем фронту к нам ходить (для хакатона ок так)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ==========================
#  AUTH: модели и утилиты
# ==========================


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


def hash_password(password: str) -> str:
    """Простое хеширование пароля (для хакатона ок)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password


def get_current_user_id(authorization: str = Header(None)) -> uuid.UUID:
    """
    Достаёт user_id из токена формата:
      Authorization: Bearer fake-<uuid>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        scheme, token = authorization.split()
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    if not token.startswith("fake-"):
        raise HTTPException(status_code=401, detail="Invalid token format")

    user_id_str = token[5:]
    try:
        return uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user id in token")


# ==========================
#  AUTH: эндпоинты /register и /login
# ==========================


@app.post("/register", response_model=Token)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация пользователя.
    - username = email (на фронте мы так и шлём)
    - пароль хешируется и сохраняется в hashed_password
    - сразу возвращаем access_token (простой строковый токен)
    """
    # Проверка на дубликат
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Создаём пользователя
    db_user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Простой "токен" (не настоящий JWT, но фронту всё равно)
    access_token = f"fake-{db_user.id}"

    return Token(access_token=access_token, token_type="bearer")


@app.post("/login", response_model=Token)
def login_for_access_token(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Логин:
    - ищем пользователя по username
    - сверяем пароль
    - возвращаем тот же формат токена
    """
    db_user = db.query(User).filter(User.username == user_data.username).first()

    if not db_user or not verify_password(user_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    access_token = f"fake-{db_user.id}"
    return Token(access_token=access_token, token_type="bearer")


# ==========================
#   ANALYZE TEXT / IMAGE
# ==========================


@app.post("/analyze-text", response_model=TextAnalyzeResponse)
async def analyze_text_endpoint(
    payload: TextAnalyzeRequest,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Принимает текст, запускает анализ, пишет результат в submissions/trust_scores
    И ДОПОЛНИТЕЛЬНО создаёт запись в history.
    """
    try:
        # 1. Анализ + запись в submissions/trust_scores (как было)
        ai_response = process_text_submission_fixed(
            db=db,
            user_id=str(user_id),  # внутри он приводит к UUID
            content=payload.content,
        )

        # 2. Запись в history
        create_history_record(
            db=db,
            user_id=user_id,
            question=payload.content,
            raw_response=ai_response.dict(),  # полный JSON ответа модели
            kind="text",
        )

        return ai_response

    except Exception:
        # Если сервис упал (и уже сделал rollback), возвращаем 500 ошибку
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error during AI processing and DB transaction.",
        )


@app.post("/analyze-image", response_model=ImageAnalyzeResponse)
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Принимает изображение, анализирует его
    и сохраняет историю (kind='image').
    """
    image_bytes = await file.read()
    ai_response = analyze_image(image_bytes)

    # Сохраняем в history: вопросом считаем имя файла
    filename = file.filename or "uploaded_image"
    create_history_record(
        db=db,
        user_id=user_id,
        question=filename,
        raw_response=ai_response.dict(),
        kind="image",
    )

    return ai_response


# ==========================
#     HISTORY ENDPOINTS
# ==========================


@app.get("/history", response_model=TypingList[HistoryItem])
def get_history_endpoint(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Возвращает историю ТОЛЬКО текущего пользователя (по токену).
    """
    records = get_user_history(db, user_id)
    return records


@app.delete("/history/{history_id}", status_code=204)
def delete_history_item_endpoint(
    history_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Удаляет одну запись истории этого пользователя.
    """
    deleted = delete_history_item(db, user_id, history_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History item not found")
    return


@app.delete("/history", status_code=204)
def delete_all_history_endpoint(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Удаляет ВСЮ историю текущего пользователя.
    """
    delete_all_history_for_user(db, user_id)
    return
