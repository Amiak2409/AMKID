# app/services/ai_service.py

from typing import Dict, Any, List, Optional
from app.models.database_ops import create_trust_score, Submission # Предполагаем, что этот импорт нужен

class TrustScoreAssembler:
    """
    Сервис для централизованной сборки всех метрик контента 
    от различных ML-воркеров в единую структуру TrustScore.
    
    Это обеспечивает чистый интерфейс для процесса обработки.
    """
    
    def __init__(self, submission: Submission):
        """Инициализируем сервис, привязывая его к конкретной заявке."""
        self.submission = submission
        self._metrics: Dict[str, Any] = {}
        self._verdict: Optional[str] = None
        self._fake_probability: float = 0.0

    def add_metric_result(self, metric_name: str, data: Dict[str, Any]):
        """
        Добавляет результат от одного воркера/метрики.
        
        :param metric_name: Ключ для словаря (например, 'ai_detection').
        :param data: Словарь с результатами метрики.
        """
        if data and isinstance(data, dict):
            # Используем имя метрики как ключ верхнего уровня
            self._metrics[metric_name] = data
        else:
            print(f"Warning: Skipping empty or invalid data for metric '{metric_name}'")

    def set_overall_score(self, verdict: str, probability: float):
        """Устанавливает основной вердикт и вероятность."""
        self._verdict = verdict
        self._fake_probability = probability

    def assemble(self) -> Dict[str, Any]:
        """
        Возвращает финальный словарь metrics_data, готовый для сохранения в JSONB.
        """
        return self._metrics
    
    def save_to_db(self, db_session) -> None:
        """
        Сохраняет собранные метрики, вердикт и вероятность в базу данных.
        """
        if self._verdict is None:
            raise ValueError("Overall verdict and probability must be set before saving.")
        
        create_trust_score(
            db=db_session,
            submission_id=self.submission.id,
            verdict=self._verdict,
            fake_probability=self._fake_probability,
            metrics_data=self._metrics
        )
        print(f"✅ TrustScore для заявки {self.submission.id} сохранен.")


# --- Пример использования ---
def pipeline_example(db_session, submission_instance):
    """Имитация работы конвейера воркеров."""
    
    # 1. Инициализация сборщика
    assembler = TrustScoreAssembler(submission=submission_instance)
    
    # 2. Воркер 1: Обнаружение ИИ
    ai_result = {"score": 0.98, "model": "ZeroGPT-v3"}
    assembler.add_metric_result("ai_detection", ai_result)
    
    # 3. Воркер 2: Проверка на ненависть (может быть пустым, если не применимо)
    hate_result = {"is_sexist": True, "score": 0.75}
    assembler.add_metric_result("hate_speech", hate_result)
    
    # 4. Воркер 3: Неизвестная метрика (добавляется без изменения класса Assembler)
    spam_result = {"is_spam": False, "confidence": 0.9}
    assembler.add_metric_result("spam_detection", spam_result)
    
    # 5. Установка общего вердикта (основываясь на логике принятия решений)
    assembler.set_overall_score(verdict="FAKE", probability=0.98)
    
    # 6. Сохранение в БД
    assembler.save_to_db(db_session)
    
    print("\nФинальные собранные метрики:")
    print(assembler.assemble())