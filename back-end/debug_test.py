import sys
import os
import uuid
import random
from app.models.database_ops import SessionLocal, create_user, create_submission, create_trust_score, User, Submission, Base, engine, create_db_and_tables

# Проверяем и создаем структуру БД, если нужно
create_db_and_tables()

# ----- ТЕСТОВАЯ ФУНКЦИЯ -----
def run_isolated_test():
    """Проверяет возможность вставки в submissions и trust_scores."""
    db = None
    try:
        db = SessionLocal()
        
        # 1. Обеспечиваем наличие пользователя (чтобы избежать Foreign Key Error)
        # Используем существующий или создаем нового
        test_user = db.query(User).filter(User.username == "isolated_tester").first()
        if not test_user:
            test_user = create_user(db, "isolated_tester")
            print(f"✅ Создан новый тестовый пользователь с ID: {test_user.id}")
        else:
            print(f"✅ Используется существующий пользователь: {test_user.id}")

        # 2. Создаем Submission
        print("➡️ Попытка создания Submission...")
        submission: Submission = create_submission(
            db=db,
            user_id=test_user.id,
            media_type='text',
            content_text='Это тестовый текст для проверки вставки в базу.',
            media_url=f'test_url_{random.randint(100, 999)}'
        )
        # В этом месте данные ДОЛЖНЫ быть во flushed (но не committed) состоянии.
        print(f"✅ Submission создан (ID: {submission.id}). Данные во временной транзакции.")

        # 3. Создаем TrustScore
        print("➡️ Попытка создания TrustScore...")
        create_trust_score(
            db=db,
            submission_id=submission.id,
            fake_probability=random.random(), # Случайное число 0..1
            verdict="TEST_VERDICT",
            ai_metadata={'test_key': 'test_value', 'score_breakdown': [10, 20]} # Чистый словарь
        )
        print("✅ TrustScore создан.")
        
        # 4. Финальный коммит
        db.commit()
        print(f"🎉 Успех! Обе записи (Submission и TrustScore) зафиксированы.")
        print("----------------------------------------------------------------")

    except Exception as e:
        # Выводим полную трассировку, чтобы понять причину!
        db.rollback()
        print("\n" + "="*50)
        print("❌ КРИТИЧЕСКАЯ ОШИБКА БАЗЫ ДАННЫХ. Транзакция откачена.")
        print(f"ОШИБКА: {e}")
        # Вывод детальной трассировки ошибок (Traceback)
        import traceback
        traceback.print_exc()
        print("="*50 + "\n")

    finally:
        if db:
            db.close()
            
if __name__ == "__main__":
    run_isolated_test()