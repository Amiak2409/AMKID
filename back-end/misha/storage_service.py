import os
import uuid
from typing import BinaryIO
import boto3
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()

# --- КОНФИГУРАЦИЯ R2 ---
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_APPLICATION_KEY = os.getenv("R2_SECRET_APPLICATION_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

s3_client = None 

try:
    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_APPLICATION_KEY,
    )
    print("✅ Boto3 клиент для R2 успешно инициализирован.")
except Exception as e:
    # Здесь s3_client остается равным None, но он существует.
    print(f"❌ Ошибка инициализации Boto3: {e}")

# --- ФУНКЦИИ ХРАНИЛИЩА ---

def upload_media_file(file_stream: BinaryIO, original_filename: str, content_type: str) -> str:
    """
    Загружает файл в Backblaze R2.
    
    :param file_stream: Поток данных файла (полученный, например, от FastAPI UploadFile).
    :param original_filename: Имя файла для определения расширения.
    :param content_type: MIME-тип файла (например, 'image/jpeg').
    :return: Ключ файла в хранилище (S3 Key), который мы сохраним в DB.
    """
    
    # Генерируем уникальный ключ, чтобы избежать конфликтов имен
    file_extension = os.path.splitext(original_filename)[1]
    s3_key = f"submissions/{uuid.uuid4()}{file_extension}"
    
    try:
        s3_client.upload_fileobj(
            file_stream,
            R2_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ContentType': content_type
            }
        )
        # В БД мы сохраняем ключ (s3_key), а не полный URL
        return s3_key 
    except Exception as e:
        print(f"❌ Ошибка загрузки файла в R2: {e}")
        # Если загрузка не удалась, возвращаем пустую строку или вызываем исключение
        return ""

def get_file_url(s3_key: str) -> str:
    """Генерирует публичный URL для доступа к файлу."""
    # Замените домен на ваш публичный URL для корзины R2 (если настроено CDN)
    return f"{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/{s3_key}"


def download_media_file(s3_key: str) -> bytes | None:
    """
    Скачивает файл из Backblaze R2 по его S3-ключу.
    
    :param s3_key: Ключ файла в хранилище (например, submissions/uuid.jpg).
    :return: Содержимое файла в виде байтов (bytes) или None в случае ошибки.
    """
    if s3_client is None:
        print("🛑 Клиент R2 не инициализирован, скачивание невозможно.")
        return None
        
    try:
        # Используем get_object для получения ответа, содержащего данные файла
        response = s3_client.get_object(
            Bucket=R2_BUCKET_NAME,
            Key=s3_key
        )
        
        # Читаем содержимое файла в байты
        file_content = response['Body'].read()
        return file_content
        
    except Exception as e:
        print(f"❌ Ошибка скачивания файла из R2 (ключ: {s3_key}): {e}")
        return None
    
# --- ПРОВЕРКА (ОПЦИОНАЛЬНО) ---
# Если нужно проверить, что клиент работает:
def check_connection():
    try:
        s3_client.list_buckets()
        print("✅ Успешное подключение к Backblaze R2.")
        return True
    except Exception as e:
        print(f"❌ Ошибка: Не удалось подключиться к R2. Проверьте ключи и Endpoint. {e}")
        return False

if __name__ == '__main__':
    
    # 1. Проверяем, что клиент R2/S3 инициализирован
    if s3_client is None:
        print("🛑 Клиент R2 не инициализирован. Проверьте переменные окружения.")
    else:
        check_connection()
        
        # 2. Создаем фиктивный файл в памяти
        import io
        
        # Файл-поток с фиктивным содержимым
        TEST_CONTENT = b"This is a test file for R2 upload and download."
        fake_file_content = b"This is a test file for R2 upload."
        fake_file_stream = io.BytesIO(fake_file_content)
        
        original_filename = "test_data.txt"
        content_type = "text/plain"
        
        print(f"\n🚀 Пытаемся загрузить '{original_filename}'...")
        
        # 3. Вызываем нашу функцию
        s3_key = upload_media_file(fake_file_stream, original_filename, content_type)
        
        if s3_key:
            full_url = get_file_url(s3_key)
            print(f"🎉 Успех! Файл загружен с ключом: {s3_key}")
            print(f"🔗 Полный URL: {full_url}")
        else:
            print("🛑 Загрузка не удалась. Смотрите ошибки выше.")

        # 1. ЗАГРУЗКА
        fake_file_stream = io.BytesIO(TEST_CONTENT)
        print(f"\n🚀 Пытаемся загрузить '{original_filename}'...")
        s3_key = upload_media_file(fake_file_stream, original_filename, content_type)
        
        if s3_key:
            print(f"🎉 Успех загрузки! Ключ: {s3_key}")
            
            # 2. СКАЧИВАНИЕ
            print(f"⬇️ Пытаемся скачать файл по ключу: {s3_key}")
            downloaded_content = download_media_file(s3_key)
            
            if downloaded_content is not None:
                print("✅ Успех скачивания!")
                
                # 3. ПРОВЕРКА СООТВЕТСТВИЯ
                if downloaded_content == TEST_CONTENT:
                    print("✨ **Проверка пройдена:** Содержимое загруженного и скачанного файла совпадает!")
                else:
                    print("❌ **Ошибка проверки:** Содержимое не совпадает.")
                    
                # ОПЦИОНАЛЬНО: УДАЛЕНИЕ ФАЙЛА (Для чистки бакета)
                # s3_client.delete_object(Bucket=R2_BUCKET_NAME, Key=s3_key)
                # print(f"🗑️ Файл {s3_key} удален.")
            else:
                print("🛑 Скачивание не удалось.")
        else:
            print("🛑 Загрузка не удалась, невозможно протестировать скачивание.")