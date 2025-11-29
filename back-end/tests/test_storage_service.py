import pytest
from unittest.mock import patch, MagicMock
import io
import os
from app.services.storage_service import (
    upload_media_file, 
    get_file_url,
    # ИСПРАВЛЕНИЕ #2: Импортируем переменные для теста URL
    R2_ENDPOINT_URL, 
    R2_BUCKET_NAME
)


# ИСПРАВЛЕНИЕ #1: Меняем мокирование с boto3 на s3_client
@patch('app.services.storage_service.s3_client')
def test_upload_media_file_success(mock_s3_client): # Теперь мы мокируем s3_client
    """Проверяет успешную загрузку файла и возвращение корректного S3-ключа."""

    # Настраивать mock_boto3.client.return_value больше не нужно.
    # mock_s3_client — это уже мок клиента.
    
    # Настройка: метод upload_fileobj должен быть вызван без ошибок
    # Этого достаточно, так как MagicMock по умолчанию не вызывает ошибок
    
    fake_file_stream = io.BytesIO(b"file content")
    original_filename = "test_image.jpg"
    content_type = "image/jpeg"

    s3_key = upload_media_file(fake_file_stream, original_filename, content_type)
    
    # Проверяем, что метод upload_fileobj был вызван на мок-клиенте
    mock_s3_client.upload_fileobj.assert_called_once()
    
    # Проверяем структуру ключа
    assert s3_key.startswith("submissions/")
    assert s3_key.endswith(".jpg")
    assert s3_key != ""

# ИСПРАВЛЕНИЕ #1: Меняем мокирование с boto3 на s3_client
@patch('app.services.storage_service.s3_client')
def test_upload_media_file_failure(mock_s3_client):
    """Проверяет, что при ошибке R2 функция возвращает пустую строку."""

    # Настраиваем мок-клиент, чтобы его метод upload_fileobj вызывал исключение
    mock_s3_client.upload_fileobj.side_effect = Exception("Simulated R2 error")

    fake_file_stream = io.BytesIO(b"file content")
    original_filename = "test_file.txt"
    content_type = "text/plain"

    s3_key = upload_media_file(fake_file_stream, original_filename, content_type)
    
    # Проверяем, что была попытка загрузки
    mock_s3_client.upload_fileobj.assert_called_once()
    
    # Проверяем, что функция вернула пустую строку, так как исключение было поймано
    assert s3_key == ""

# ИСПРАВЛЕНИЕ #2: Тест теперь работает, так как R2_ENDPOINT_URL и R2_BUCKET_NAME импортированы
def test_get_file_url_generation():
    """Проверяет корректное формирование публичного URL."""
    
    test_key = "submissions/12345-abcde.mp4"
    
    # R2_ENDPOINT_URL и R2_BUCKET_NAME доступны благодаря импорту.
    expected_url = f"{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/{test_key}"
    actual_url = get_file_url(test_key)
    
    assert actual_url == expected_url