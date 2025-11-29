import requests
import json

# Замените на реальные значения API ZeroGPT
API_KEY = "dafeb81f-7b14-4011-811c-062835beb88e"
API_ENDPOINT = "https://api.zerogpt.com/api/detect/detectText" # АДРЕС может отличаться

text_to_analyze = """
Этот текст был сгенерирован или написан человеком?
Нейронные сети обладают способностью к генерации связного и стилистически
корректного текста, что затрудняет его обнаружение.
"""

# Настройка заголовков (метод Bearer)
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}" # Если используется метод Bearer
}

# Тело запроса
data = {
    "text": text_to_analyze,
    "source": "api" # Возможно, требуется для идентификации источника
}

try:
    # Отправка POST-запроса
    response = requests.post(API_ENDPOINT, headers=headers, data=json.dumps(data))
    response.raise_for_status() # Вызывает ошибку, если статус 4xx или 5xx
    
    # Получение результата
    result = response.json()
    
    ## 4. Интерпретация Результата
    
    print("✅ Ответ от ZeroGPT API:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Здесь нужно анализировать формат ответа (например, 'ai_score', 'human_percentage' и т.п.)
    
except requests.exceptions.RequestException as e:
    print(f"❌ Ошибка при выполнении API-запроса: {e}")