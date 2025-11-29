from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai_routes import router as ai_router

app = FastAPI(title="AI Identifier API", version="0.1")

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

# Подключаем роуты анализа текста и изображений
app.include_router(ai_router)
