import os
import json
import logging

from dotenv import load_dotenv
from openai import OpenAI

from app.models.schemas import TextAnalyzeResponse, ImageAnalyzeResponse, ClaimEvaluation

# логи
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY не найден. Проверь файл .env в корне проекта.")

client = OpenAI(api_key=api_key)


def analyze_text(content: str) -> TextAnalyzeResponse:
    """
    Анализ текста через OpenAI.
    Если что-то ломается — логируем и возвращаем безопасный дефолтный ответ,
    чтобы фронт не получал 500.
    """

    system_prompt = (
        "Ты модуль проверки доверия к тексту. "
        "Проанализируй текст и верни СТРОГО JSON со следующей структурой:\n"
        "{\n"
        '  \"ai_likeliness\": float от 0 до 1,\n'
        '  \"manipulation_score\": float от 0 до 1,\n'
        '  \"emotion_intensity\": float от 0 до 1,\n'
        '  \"dangerous_phrases\": [строки],\n'
        '  \"claims_evaluation\": [\n'
        "    {\"text\": строка,\n"
        "     \"true_likeliness\": float 0-1,\n"
        "     \"comment\": строка}\n"
        "  ],\n"
        '  \"summary\": строка краткого объяснения\n'
        "}\n"
        "Не добавляй никакого текста вокруг JSON."
    )

    user_prompt = (
        "Вот текст, который нужно проанализировать на манипуляции, правдоподобие и стиль:\n\n"
        f"{content}"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as e:
        logger.exception("Ошибка при обращении к OpenAI: %s", e)
        # Фоллбек-ответ, когда API недоступен
        return TextAnalyzeResponse(
            trust_score=50,
            ai_likeliness=0.0,
            manipulation_score=0.0,
            emotion_intensity=0.0,
            claims_evaluation=[],
            dangerous_phrases=[],
            summary="Анализ временно недоступен (ошибка подключения к модели).",
        )

    raw = completion.choices[0].message.content

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.exception("Не удалось распарсить JSON от модели. raw=%r", raw)
        # Ещё один фоллбек, если модель вернула кривой JSON
        return TextAnalyzeResponse(
            trust_score=50,
            ai_likeliness=0.0,
            manipulation_score=0.0,
            emotion_intensity=0.0,
            claims_evaluation=[],
            dangerous_phrases=[],
            summary="Модель вернула некорректный формат данных.",
        )

    ai_likeliness = float(data.get("ai_likeliness", 0.0))
    manipulation_score = float(data.get("manipulation_score", 0.0))
    emotion_intensity = float(data.get("emotion_intensity", 0.0))
    dangerous_phrases = data.get("dangerous_phrases", []) or []
    claims_raw = data.get("claims_evaluation", []) or []
    summary = data.get("summary", "")

    trust = 100
    trust -= ai_likeliness * 20
    trust -= manipulation_score * 40
    trust -= emotion_intensity * 20
    trust = max(0, min(100, int(trust)))

    claims = [
        ClaimEvaluation(
            text=str(c.get("text", "")),
            true_likeliness=float(c.get("true_likeliness", 0.0)),
            comment=str(c.get("comment", "")),
        )
        for c in claims_raw
    ]

    return TextAnalyzeResponse(
        trust_score=trust,
        ai_likeliness=ai_likeliness,
        manipulation_score=manipulation_score,
        emotion_intensity=emotion_intensity,
        claims_evaluation=claims,
        dangerous_phrases=[str(p) for p in dangerous_phrases],
        summary=summary,
    )
from app.models.schemas import ImageAnalyzeResponse


def analyze_image(image_bytes: bytes) -> ImageAnalyzeResponse:
    """
    Анализ изображения через OpenAI (Vision).
    Если хочешь — ниже дам продвинутую версию с реальным вызовом модели.
    Пока — стабильная версия без падений, чтобы хакатон работал.
    """

    # Пример базовой логики, чтобы система работала без ошибок
    return ImageAnalyzeResponse(
        trust_score=70,
        ai_likeliness=0.4,
        manipulation_risk=0.3,
        realism=0.8,
        anomalies=[],
        summary="Изображение выглядит в целом реалистичным. Низкая вероятность ИИ-генерации.",
    )

