import pytest
from unittest.mock import MagicMock, patch
# Обратите внимание: импорт должен быть корректным после исправления путей
from app.services.metrics_assembler import TrustScoreAssembler 

# -----------------------------------------------------------
# ФИКСАТУРЫ (Заглушки для изоляции)
# -----------------------------------------------------------

class MockSubmission:
    """Простая заглушка для объекта Submission, нужного для инициализации."""
    def __init__(self, id):
        self.id = id

@pytest.fixture
def mock_submission():
    """Создает заглушку объекта Submission с ID 456."""
    return MockSubmission(id=456)

@pytest.fixture
def assembler(mock_submission):
    """Создает экземпляр TrustScoreAssembler для каждого теста."""
    return TrustScoreAssembler(mock_submission)

# -----------------------------------------------------------
# ТЕСТЫ ЛОГИКИ СБОРКИ
# -----------------------------------------------------------

def test_initialization(assembler):
    """Проверяет, что объект инициализируется с корректными пустыми значениями."""
    assert assembler.submission.id == 456
    assert assembler.assemble() == {}
    assert assembler._verdict is None
    assert assembler._fake_probability == 0.0

def test_add_metric_result_success(assembler):
    """Проверяет успешное добавление нескольких метрик."""
    
    ai_data = {"model_version": "v1.2", "confidence": 0.98}
    hate_data = {"is_sexist": True, "score": 0.65}
    
    assembler.add_metric_result("ai_detection", ai_data)
    assembler.add_metric_result("hate_speech", hate_data)
    
    expected_metrics = {
        "ai_detection": {"model_version": "v1.2", "confidence": 0.98},
        "hate_speech": {"is_sexist": True, "score": 0.65}
    }
    assert assembler.assemble() == expected_metrics

def test_add_metric_result_invalid_data_is_ignored(assembler):
    """Проверяет, что пустые словари или не-словари игнорируются."""
    
    initial_valid_data = {"initial_check": {"status": "ok"}}
    assembler.add_metric_result("initial_check", initial_valid_data["initial_check"])
    
    # Попытка добавить невалидные данные
    assembler.add_metric_result("empty_data", {})
    assembler.add_metric_result("none_data", None)
    assembler.add_metric_result("non_dict_data", "some string value")
    
    # Убеждаемся, что только валидные данные сохранились
    assert assembler.assemble() == initial_valid_data
    assert "empty_data" not in assembler.assemble()

def test_set_overall_score(assembler):
    """Проверяет корректность установки общего вердикта и вероятности."""
    
    assembler.set_overall_score("REAL", 0.15)
    
    assert assembler._verdict == "REAL"
    assert assembler._fake_probability == 0.15
    
# -----------------------------------------------------------
# ТЕСТЫ ВЗАИМОДЕЙСТВИЯ С БАЗОЙ ДАННЫХ
# -----------------------------------------------------------

def test_save_to_db_calls_create_trust_score_correctly(assembler):
    """
    Проверяет, что save_to_db вызывает функцию БД с собранными данными.
    Используем patch для подмены реальной функции БД.
    """
    mock_db_session = MagicMock()
    
    # 1. Подготовка данных в Assembler
    assembler.add_metric_result("check_1", {"data": 1})
    assembler.add_metric_result("check_2", {"data": 2})
    assembler.set_overall_score("MIXED", 0.5)
    
    # 2. Имитация вызова функции create_trust_score из database_ops
    with patch('app.services.metrics_assembler.create_trust_score') as mock_create: 
        assembler.save_to_db(mock_db_session)
        
        # 3. Проверка: функция должна быть вызвана ровно один раз
        mock_create.assert_called_once()
        
        # 4. Проверка: аргументы вызова должны быть корректными
        call_kwargs = mock_create.call_args.kwargs

        assert call_kwargs['db'] == mock_db_session
        assert call_kwargs['submission_id'] == 456
        assert call_kwargs['verdict'] == "MIXED"
        assert call_kwargs['fake_probability'] == 0.5
        assert call_kwargs['metrics_data'] == {"check_1": {"data": 1}, "check_2": {"data": 2}}

def test_save_to_db_raises_error_if_verdict_missing(assembler):
    """Проверяет, что если общий вердикт не установлен, будет поднято исключение."""
    mock_db_session = MagicMock()
    
    # Добавляем метрики, но НЕ устанавливаем общий вердикт
    assembler.add_metric_result("test_metric", {"data": "ok"})
    
    # Ожидаем, что будет поднята ошибка ValueError с нужным сообщением
    with pytest.raises(ValueError, match="Overall verdict and probability must be set before saving"):
        assembler.save_to_db(mock_db_session)