import logging
from typing import Tuple

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoConfig, AutoModel, PreTrainedModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ID модели на HuggingFace
MODEL_ID = "desklib/ai-text-detector-v1.01"
MAX_LEN = 768

# ===== Определяем класс модели (как в README на HuggingFace) =====


class DesklibAIDetectionModel(PreTrainedModel):
    """
    Модель из README HuggingFace:
    https://huggingface.co/desklib/ai-text-detector-v1.01
    """

    config_class = AutoConfig

    def __init__(self, config):
        super().__init__(config)
        # Базовая DeBERTa-модель
        self.model = AutoModel.from_config(config)
        # Классификатор: один логит = вероятность "AI-текст"
        self.classifier = nn.Linear(config.hidden_size, 1)
        self.init_weights()

    def forward(self, input_ids, attention_mask=None, labels=None):
        outputs = self.model(input_ids, attention_mask=attention_mask)
        last_hidden_state = outputs[0]

        # Mean pooling по маске
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
        )
        sum_embeddings = torch.sum(last_hidden_state * input_mask_expanded, dim=1)
        sum_mask = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
        pooled_output = sum_embeddings / sum_mask

        # Логиты
        logits = self.classifier(pooled_output)

        loss = None
        if labels is not None:
            loss_fct = nn.BCEWithLogitsLoss()
            loss = loss_fct(logits.view(-1), labels.float())

        output = {"logits": logits}
        if loss is not None:
            output["loss"] = loss
        return output


# ===== Глобальная инициализация токенизатора и модели =====

logger.info("Загружаю HuggingFace модель детектора: %s", MODEL_ID)
_tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
_config = AutoConfig.from_pretrained(MODEL_ID)
_model = DesklibAIDetectionModel.from_pretrained(MODEL_ID, config=_config)

_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model.to(_device)
_model.eval()

logger.info("Модель детектора загружена на устройство: %s", _device)


def _predict_probability(text: str) -> float:
    """
    Внутренняя функция: возвращает вероятность (0..1), что текст ИИ.
    """
    text = text or ""
    if not text.strip():
        return 0.0

    encoded = _tokenizer(
        text,
        padding="max_length",
        truncation=True,
        max_length=MAX_LEN,
        return_tensors="pt",
    )

    input_ids = encoded["input_ids"].to(_device)
    attention_mask = encoded["attention_mask"].to(_device)

    with torch.no_grad():
        outputs = _model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs["logits"]  # shape [1, 1]
        prob = torch.sigmoid(logits).item()

    # safety clamp
    prob = float(max(0.0, min(1.0, prob)))
    return prob


def detect_ai_probability(text: str) -> float:
    """
    Публичная функция: вероятность (0..1), что текст сгенерирован ИИ.
    """
    try:
        return _predict_probability(text)
    except Exception as e:
        logger.exception("Ошибка при локальном детекте AI-текста: %s", e)
        # Если что-то пошло не так — лучше вернуть 0, чем уронить API
        return 0.0


def detect_ai_label(text: str, threshold: float = 0.5) -> Tuple[bool, float]:
    """
    Публичная функция:
      - is_ai: True/False по порогу
      - prob: вероятность (0..1) ИИ-текста

    threshold=0.5 — можно подкрутить.
    """
    prob = detect_ai_probability(text)
    is_ai = prob >= threshold
    return is_ai, prob
