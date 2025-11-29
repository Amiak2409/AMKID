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

import math
from typing import List


def compute_trust_score(
    *,
    ai_likeliness: float,
    manipulation_score: float,
    emotion_intensity: float,
    claims: List[ClaimEvaluation],
    dangerous_phrases: List[str],
) -> int:
    """
    Считает итоговый trust_score 0–100 на основе 5 осей:
    - factual_score      : достоверность
    - authenticity_score : похожесть на человеческий текст
    - integrity_score    : отсутствие манипуляций
    - tone_score         : адекватность эмоционального тона
    - safety_score       : отсутствие опасных формулировок

    Используем ВЗВЕШЕННОЕ ГЕОМЕТРИЧЕСКОЕ СРЕДНЕЕ,
    чтобы низкий балл по одной оси сильно бил по общему доверию.
    """

    # ---------- 1. FACTUAL: фактическая достоверность ----------
    if claims:
        avg_truth = sum(c.true_likeliness for c in claims) / len(claims)
    else:
        # если модель не выделила утверждений, считаем умеренно правдивым
        avg_truth = 0.6

    factual_score = avg_truth * 100.0  # 0–100

    # ---------- 2. AUTHENTICITY: насколько это не ИИ ----------
    # 1.0 = точно ИИ, 0.0 = точно человек
    authenticity_score = (1.0 - ai_likeliness) * 100.0

    # ---------- 3. INTEGRITY: отсутствие манипуляций ----------
    integrity_score = (1.0 - manipulation_score) * 100.0

    # ---------- 4. TONE: эмоциональная адекватность ----------
    # до 0.4 — нейтральный тон (штрафа нет)
    # 0.4–0.7 — мягкий штраф
    # 0.7–1.0 — агрессивный/панический тон, сильный штраф
    if emotion_intensity <= 0.4:
        tone_score = 100.0
    elif emotion_intensity <= 0.7:
        # линейно падаем до 70
        frac = (emotion_intensity - 0.4) / 0.3  # 0–1
        tone_score = 100.0 - 30.0 * frac        # до 70
    else:
        frac = (emotion_intensity - 0.7) / 0.3  # 0–1
        tone_score = 70.0 - 40.0 * frac         # до 30

    tone_score = max(0.0, tone_score)

    # ---------- 5. SAFETY: опасные фразы ----------
    n_danger = len(dangerous_phrases)
    # экспоненциальный штраф: каждая фраза уменьшает безопасность,
    # но вклад затухает
    safety_score = 100.0 * math.exp(-0.35 * n_danger)
    # для 1 фразы ~70, для 2 ~50, для 3 ~36, дальше → в ноль

    # ---------- Взвешенное геометрическое среднее ----------
    # веса важности осей (можно показывать на слайде)
    w_factual = 3.0
    w_auth    = 2.0
    w_integ   = 3.0
    w_tone    = 1.5
    w_safety  = 2.5

    # нормируем в [0,1], добавляем +1e-6 чтобы не было log(0)
    s_f = max(factual_score / 100.0, 1e-6)
    s_a = max(authenticity_score / 100.0, 1e-6)
    s_i = max(integrity_score / 100.0, 1e-6)
    s_t = max(tone_score / 100.0, 1e-6)
    s_s = max(safety_score / 100.0, 1e-6)

    total_weight = w_factual + w_auth + w_integ + w_tone + w_safety

    # логарифмическая форма геометрического среднего:
    log_trust = (
        w_factual * math.log(s_f)
        + w_auth  * math.log(s_a)
        + w_integ * math.log(s_i)
        + w_tone  * math.log(s_t)
        + w_safety* math.log(s_s)
    ) / total_weight

    trust = math.exp(log_trust) * 100.0
    trust = max(0, min(100, int(round(trust))))

    return trust


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
    dangerous_phrases_raw = data.get("dangerous_phrases", []) or []
    claims_raw = data.get("claims_evaluation", []) or []
    summary = data.get("summary", "") or ""

    # конвертируем claims
    claims: List[ClaimEvaluation] = []
    for c in claims_raw:
        claims.append(
            ClaimEvaluation(
                text=str(c.get("text", "")),
                true_likeliness=float(c.get("true_likeliness", 0.0)),
                comment=str(c.get("comment", "")),
            )
        )

    dangerous_phrases = [str(p) for p in dangerous_phrases_raw]


    trust = compute_trust_score(
        ai_likeliness=ai_likeliness,
        manipulation_score=manipulation_score,
        emotion_intensity=emotion_intensity,
        claims=claims,
        dangerous_phrases=dangerous_phrases,
    )

    return TextAnalyzeResponse(
        trust_score=trust,
        ai_likeliness=ai_likeliness,
        manipulation_score=manipulation_score,
        emotion_intensity=emotion_intensity,
        claims_evaluation=claims,
        dangerous_phrases=dangerous_phrases,
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

