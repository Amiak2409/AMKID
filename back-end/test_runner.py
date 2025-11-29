import uuid
import json
from typing import Dict, Any, List

from db_ops import (
    SessionLocal,
    create_db_and_tables,
    create_submission,
    update_submission_status,
    create_trust_score,
    get_pending_submissions,
    get_submission_with_score,
    Submission
)

class DatabaseTester:
    """
    Класс для имитации и проверки базового цикла работы
    системы: Frontend -> DB -> Worker -> DB -> Frontend.
    """
    def __init__(self):
        self.test_submission_ids: List[uuid.UUID] = []

    def _simulate_frontend_uploads(self) -> uuid.UUID:
        """Имитирует загрузку нескольких файлов с веб-интерфейса."""
        
        # Текстовая заявка
        text_sub = create_submission(
            SessionLocal(), 
            media_type='text', 
            content_text='Актер сделал политическое заявление.', 
            media_url='n/a'
        )
        self.test_submission_ids.append(text_sub.id)
        print(f"➕ [Frontend] Создана заявка TEXT: {text_sub.id}")

        # Видео-заявка (для обработки)
        video_sub = create_submission(
            SessionLocal(), 
            media_type='video', 
            media_url='s3://test/video_001.mp4'
        )
        self.test_submission_ids.append(video_sub.id)
        print(f"➕ [Frontend] Создана заявка VIDEO: {video_sub.id}")
        
        return video_sub.id # Возвращаем ID для дальнейшей обработки


    def _simulate_ml_worker_process(self, task_id: uuid.UUID):
        """Имитирует работу ML-воркера: берет задачу, обрабатывает, сохраняет результат."""
        
        # Смена статуса на 'processing'
        with SessionLocal() as db:
            update_submission_status(db, task_id, 'processing')
            print(f"🔄 [ML Worker] Статус заявки {task_id} изменен на 'processing'.")
            
            # Имитация результата от нейросети
            fake_prob: float = 0.98
            verdict: str = "HIGH_RISK_DEEPFAKE"
            metadata: Dict[str, Any] = {
                "face_count": 1,
                "fake_frame_indices": [12, 14, 150],
                "model_version": "DeepFakeDetector_v2.1"
            }

            # Сохранение результата в trust_scores
            score = create_trust_score(
                db, 
                task_id, 
                fake_prob, 
                verdict, 
                ai_metadata=metadata
            )
            print(f"➕ [ML Worker] Создан результат в TrustScore: {score.id}")
            
            # Смена статуса на 'completed'
            update_submission_status(db, task_id, 'completed')
            print(f"✅ [ML Worker] Обработка завершена, статус 'completed'.")


    def _simulate_frontend_query(self, task_id: uuid.UUID):
        """Имитирует запрос фронтенда для получения финального результата."""
        print(f"\n--- 4. Имитация Frontend: Запрос результата для {task_id} ---")
        with SessionLocal() as db:
            final_submission: Submission = get_submission_with_score(db, task_id)
            
            if final_submission and final_submission.trust_score:
                print(f"🔎 Заявка ID: {final_submission.id}")
                print(f"   Тип медиа: {final_submission.media_type}")
                print(f"   Финальный статус: {final_submission.status}")
                print(f"   Процент фейка: {final_submission.trust_score.fake_probability:.2f}")
                print(f"   Вердикт: {final_submission.trust_score.verdict}")
                
                print(f"   Метаданные ИИ: \n{json.dumps(final_submission.trust_score.ai_metadata, indent=2, ensure_ascii=False)}")
            else:
                print("❌ Не удалось найти финальный результат.")


    def run_all_tests(self):
        """Запускает полный цикл тестирования системы."""
        
        print("--- 🚀 СТАРТ ТЕСТИРОВАНИЯ БАЗЫ ДАННЫХ ---")
        
        # Шаг 0: Создание таблиц
        create_db_and_tables()

        # Шаг 1: Имитация загрузки с фронтенда
        print("\n--- 1. Создание тестовых данных ---")
        video_task_id = self._simulate_frontend_uploads()
        
        # Шаг 2: Имитация проверки ML-воркером
        print("\n--- 2. Имитация обработки ML-воркером ---")
        self._simulate_ml_worker_process(video_task_id)
        
        # Шаг 3: Имитация запроса результата с фронтенда
        self._simulate_frontend_query(video_task_id)

        print("\n--- ✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО ---")


if __name__ == "__main__":
    tester = DatabaseTester()
    tester.run_all_tests()