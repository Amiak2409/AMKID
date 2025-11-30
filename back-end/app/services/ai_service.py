import os
import json
import logging
import math
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv
from openai import OpenAI

from app.models.schemas import (
    TextAnalyzeResponse,
    ImageAnalyzeResponse,
    ClaimEvaluation,
)

# ----------------- ЛОГИ -----------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ----------------- ENV -----------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
zerogpt_api_key = os.getenv("ZEROGPT_API_KEY")
hf_api_key = os.getenv("HF_API_KEY")
HF_IMAGE_MODEL_URL = "https://api-inference.huggingface.co/models/falconsai/Detect-Fake-Image-Using-ResNet50"



if not api_key:
    raise RuntimeError("OPENAI_API_KEY не найден. Проверь файл .env в корне проекта.")

client = OpenAI(api_key=api_key)


# =====================================================================
#                       ZeroGPT интеграция
# =====================================================================

ZEROGPT_ENDPOINT = "https://api.zerogpt.com/api/detect/detectText"


def check_text_with_zerogpt(text: str) -> Optional[float]:
    """
    Отправляет текст в ZeroGPT и возвращает оценку ИИ-контента в диапазоне [0.0, 1.0],
    либо None в случае ошибки.

    В реальном ответе ZeroGPT (по логам) структура такая:

    {
      "success": true,
      "code": 200,
      "message": "...",
      "data": {
        "isHuman": 0,
        "fakePercentage": 100.0,
        ...
      }
    }

    Здесь fakePercentage — это вероятность AI-текста (0–100).
    """

    if not zerogpt_api_key:
        logger.info("ZEROGPT_API_KEY не задан. Пропускаю проверку ZeroGPT.")
        return None

    headers = {
        "ApiKey": zerogpt_api_key,
        "Content-Type": "application/json",
    }
    payload = {"input_text": text}

    try:
        resp = requests.post(
            ZEROGPT_ENDPOINT,
            headers=headers,
            data=json.dumps(payload),
            timeout=15,
        )
        resp.raise_for_status()
        outer: Dict[str, Any] = resp.json()
    except requests.exceptions.RequestException as e:
        logger.warning("Не удалось обратиться к ZeroGPT: %s", e)
        return None
    except json.JSONDecodeError as e:
        logger.warning("ZeroGPT вернул не-JSON: %s", e)
        return None

    # Проверяем общую «успешность»
    if not outer.get("success", False):
        logger.warning("ZeroGPT success=False: %r", outer)
        return None

    data = outer.get("data") or {}

    # Основное поле: fakePercentage (0–100)
    ai_percent = data.get("fakePercentage")

    # На всякий случай оставим бэкап-пути
    if ai_percent is None:
        for key in ("ai_percentage", "ai_score", "aiProbability", "ai_probability"):
            if key in outer:
                ai_percent = outer[key]
                break

    if ai_percent is None:
        logger.warning("ZeroGPT ответ без понятного поля процента AI: %r", outer)
        return None

    try:
        ai_percent = float(ai_percent)
    except (TypeError, ValueError):
        logger.warning("ai_percent из ZeroGPT не число: %r", ai_percent)
        return None

    ai_likelihood = max(0.0, min(1.0, ai_percent / 100.0))
    logger.info("ZeroGPT ai_likelihood=%.3f (из %s%%)", ai_likelihood, ai_percent)
    return ai_likelihood



# =====================================================================
#                "Крутой" алгоритм расчета trust_score
# =====================================================================


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
    if emotion_intensity <= 0.4:
        tone_score = 100.0
    elif emotion_intensity <= 0.7:
        frac = (emotion_intensity - 0.4) / 0.3  # 0–1
        tone_score = 100.0 - 30.0 * frac        # до 70
    else:
        frac = (emotion_intensity - 0.7) / 0.3  # 0–1
        tone_score = 70.0 - 40.0 * frac         # до 30

    tone_score = max(0.0, tone_score)

    # ---------- 5. SAFETY: опасные фразы ----------
    n_danger = len(dangerous_phrases)
    safety_score = 100.0 * math.exp(-0.35 * n_danger)

    # ---------- Взвешенное геометрическое среднее ----------
    w_factual = 3.0
    w_auth    = 2.0
    w_integ   = 3.0
    w_tone    = 1.5
    w_safety  = 2.5

    s_f = max(factual_score / 100.0, 1e-6)
    s_a = max(authenticity_score / 100.0, 1e-6)
    s_i = max(integrity_score / 100.0, 1e-6)
    s_t = max(tone_score / 100.0, 1e-6)
    s_s = max(safety_score / 100.0, 1e-6)

    total_weight = w_factual + w_auth + w_integ + w_tone + w_safety

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


# =====================================================================
#                            OpenAI анализ текста
# =====================================================================


def analyze_text(content: str) -> TextAnalyzeResponse:
    """
    Анализ текста через OpenAI + (опционально) ZeroGPT.
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
        '  \"summary\": строка краткого объяснения, обьяснение преимущественно давай на английском, но если текст на русском или словацком то на этих языках\n'
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

    # ---------- ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА ЧЕРЕЗ ZeroGPT ----------
    zerogpt_ai = check_text_with_zerogpt(content)
    if zerogpt_ai is not None:
        # комбинируем оценки: 60% доверия ZeroGPT, 40% — OpenAI
        combined_ai = 0.6 * zerogpt_ai + 0.4 * ai_likeliness
        logger.info(
            "Комбинированный ai_likeliness: openai=%.3f, zerogpt=%.3f -> combined=%.3f",
            ai_likeliness,
            zerogpt_ai,
            combined_ai,
        )
        ai_likeliness = combined_ai
    else:
        logger.info("Используем только ai_likeliness от OpenAI: %.3f", ai_likeliness)

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


# =====================================================================
#                          Анализ изображения
# =====================================================================

import base64

def detect_ai_image_hf(image_bytes: bytes) -> Optional[float]:
    """
    Вызывает HuggingFace модель falconsai/Detect-Fake-Image-Using-ResNet50
    и возвращает вероятность того, что картинка ИИ (0.0–1.0),
    либо None, если не удалось.
    """

    if not hf_api_key:
        logger.info("HF_API_KEY не задан. Пропускаю детектор изображения HuggingFace.")
        return None

    headers = {"Authorization": f"Bearer {hf_api_key}"}

    try:
        resp = requests.post(
            HF_IMAGE_MODEL_URL,
            headers=headers,
            data=image_bytes,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.warning("Ошибка запроса к HuggingFace image-detector: %s", e)
        return None
    except json.JSONDecodeError as e:
        logger.warning("HuggingFace вернул не-JSON для image-detector: %s", e)
        return None

    # Ожидаемый формат: [{"label": "real"/"fake", "score": 0.xx}, ...]
    if not isinstance(data, list) or not data:
        logger.warning("Неожиданный ответ от HF image-detector: %r", data)
        return None

    fake_score = None
    real_score = None
    for item in data:
        label = str(item.get("label", "")).lower()
        score = float(item.get("score", 0.0))
        if "fake" in label or "ai" in label:
            fake_score = max(fake_score or 0.0, score)
        if "real" in label:
            real_score = max(real_score or 0.0, score)

    ai_likelihood = None
    if fake_score is not None:
        ai_likelihood = fake_score
    elif real_score is not None:
        ai_likelihood = 1.0 - real_score

    if ai_likelihood is None:
        logger.warning("Не удалось выделить fake/real score из HF ответа: %r", data)
        return None

    ai_likelihood = max(0.0, min(1.0, ai_likelihood))
    logger.info("HF image-detector ai_likeliness=%.3f", ai_likelihood)
    return ai_likelihood


def analyze_image_with_openai(image_bytes: bytes) -> Dict[str, Any]:
    """
    Анализ изображения через OpenAI Vision (gpt-4.1-mini / gpt-4o-mini).
    Возвращает dict с полями:
    {
      "ai_likeliness": float 0-1,
      "manipulation_risk": float 0-1,
      "realism": float 0-1,
      "anomalies": [строки],
      "summary": строка
    }
    либо дефолт, если что-то пошло не так.
    """

    # Базовый дефолт, если что-то сломалось
    default = {
        "ai_likeliness": 0.5,
        "manipulation_risk": 0.3,
        "realism": 0.8,
        "anomalies": [],
        "summary": "Не удалось провести полноценный анализ изображения.",
    }

    # Кодируем картинку в base64 для data URL
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    image_url = f"data:image/jpeg;base64,{b64}"

    system_prompt = (
        "Ты модуль анализа доверия к изображению. "
        "Твоя задача — оценить несколько метрик и вернуть СТРОГО JSON:\n"
        "{\n"
        '  \"ai_likeliness\": float от 0 до 1,  // вероятность, что картинка сгенерирована ИИ\n'
        '  \"manipulation_risk\": float от 0 до 1,  // риск, что изображение было отредактировано / подделано\n'
        '  \"realism\": float от 0 до 1,  // насколько картинка выглядит визуально реалистичной\n'
        '  \"anomalies\": [строки],  // перечень заметных аномалий (например, странные руки, тени, текст)\n'
        '  \"summary\": строка краткого объяснения, обьяснение преимущественно давай на английском, но если текст на русском или словацком то на этих языках\n'
        "}\n"
        "Не добавляй никакого текста вокруг JSON."
    )

    user_content = [
        {
            "type": "image_url",
            "image_url": {"url": image_url},
        },
        {
            "type": "text",
            "text": (
                "Проанализируй это изображение: реалистичность, возможные манипуляции, "
                "вероятность ИИ-генерации и перечисли визуальные аномалии, если они есть."
            ),
        },
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",  # или gpt-4o-mini, если доступен
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as e:
        logger.exception("Ошибка при обращении к OpenAI Vision: %s", e)
        return default

    raw = completion.choices[0].message.content
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.exception("Не удалось распарсить JSON от OpenAI Vision. raw=%r", raw)
        return default

    try:
        return {
            "ai_likeliness": float(data.get("ai_likeliness", default["ai_likeliness"])),
            "manipulation_risk": float(data.get("manipulation_risk", default["manipulation_risk"])),
            "realism": float(data.get("realism", default["realism"])),
            "anomalies": data.get("anomalies", []) or [],
            "summary": str(data.get("summary", default["summary"])),
        }
    except Exception:
        logger.exception("Ошибка при приведении типов метрик изображения: %r", data)
        return default


def compute_image_trust_score(
    *,
    ai_likeliness: float,
    manipulation_risk: float,
    realism: float,
    anomalies: List[str],
) -> int:
    """
    Аналог продвинутого trust-score, но для изображений.
    Оси:
      - authenticity_score : похожесть на человеческое фото (1 - ai_likeliness)
      - integrity_score    : отсутствие манипуляций     (1 - manipulation_risk)
      - realism_score      : визуальная реалистичность  (realism)
      - anomaly_score      : отсутствие заметных аномалий (чем больше аномалий, тем хуже)

    Используем взвешенное геометрическое среднее.
    """

    authenticity_score = (1.0 - ai_likeliness) * 100.0
    integrity_score = (1.0 - manipulation_risk) * 100.0
    realism_score = realism * 100.0

    n_anom = len(anomalies)
    anomaly_score = 100.0 * math.exp(-0.5 * n_anom)  # при 0 аномалий = 100, при 1 ~60, при 2 ~37

    w_auth = 3.0
    w_integ = 3.0
    w_real = 2.0
    w_anom = 2.0

    s_a = max(authenticity_score / 100.0, 1e-6)
    s_i = max(integrity_score / 100.0, 1e-6)
    s_r = max(realism_score / 100.0, 1e-6)
    s_n = max(anomaly_score / 100.0, 1e-6)

    total_weight = w_auth + w_integ + w_real + w_anom

    log_trust = (
        w_auth * math.log(s_a)
        + w_integ * math.log(s_i)
        + w_real * math.log(s_r)
        + w_anom * math.log(s_n)
    ) / total_weight

    trust = math.exp(log_trust) * 100.0
    trust = max(0, min(100, int(round(trust))))
    return trust


def analyze_image(image_bytes: bytes) -> ImageAnalyzeResponse:
    """
    Анализ изображения:
      1. HuggingFace детектор falconsai/Detect-Fake-Image-Using-ResNet50
      2. OpenAI Vision (gpt-4.1-mini)
      3. Комбинированный ai_likeliness и продвинутый trust_score.
    """

    # 1) HF детектор
    hf_ai = detect_ai_image_hf(image_bytes)

    # 2) OpenAI Vision
    vision_metrics = analyze_image_with_openai(image_bytes)
    vision_ai = vision_metrics["ai_likeliness"]
    manipulation_risk = vision_metrics["manipulation_risk"]
    realism = vision_metrics["realism"]
    anomalies = [str(a) for a in (vision_metrics["anomalies"] or [])]
    summary = vision_metrics["summary"]

    # 3) Комбинируем оценки AI-картинки
    if hf_ai is not None and vision_ai is not None:
        ai_likeliness = 0.6 * hf_ai + 0.4 * vision_ai
        logger.info(
            "Комбинированный image ai_likeliness: HF=%.3f, Vision=%.3f -> %.3f",
            hf_ai,
            vision_ai,
            ai_likeliness,
        )
    elif hf_ai is not None:
        ai_likeliness = hf_ai
        logger.info("Используем только HF ai_likeliness для изображения: %.3f", ai_likeliness)
    else:
        ai_likeliness = vision_ai
        logger.info("Используем только OpenAI Vision ai_likeliness для изображения: %.3f", ai_likeliness)

    # 4) Итоговый trust-score
    trust_score = compute_image_trust_score(
        ai_likeliness=ai_likeliness,
        manipulation_risk=manipulation_risk,
        realism=realism,
        anomalies=anomalies,
    )

    return ImageAnalyzeResponse(
        trust_score=trust_score,
        ai_likeliness=ai_likeliness,
        manipulation_risk=manipulation_risk,
        realism=realism,
        anomalies=anomalies,
        summary=summary,
    )