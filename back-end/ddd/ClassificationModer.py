import json
import os
import random

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
import joblib

DATA_PATHS = ["dataset_5000.json", "dataset_10000.json"]
MODEL_PATH = "sentiment_tfidf_logreg.joblib"

# ===== 1. Загружаем данные =====
data = []
for path in DATA_PATHS:
    if not os.path.exists(path):
        print(f"⚠️ Файл {path} не найден, пропускаю")
        continue
    with open(path, "r", encoding="utf-8") as f:
        part = json.load(f)
        data.extend(part)

print(f"Всего примеров после загрузки: {len(data)}")

texts = [item["text"] for item in data]
labels = [item["label"] for item in data]

# ===== 2. Перемешиваем и создаём train/valid/test =====
train_texts, temp_texts, train_labels, temp_labels = train_test_split(
    texts, labels, test_size=0.2, random_state=42, shuffle=True
)

val_texts, test_texts, val_labels, test_labels = train_test_split(
    temp_texts, temp_labels, test_size=0.5, random_state=42, shuffle=True
)

print(f"Train: {len(train_texts)}, Validation: {len(val_texts)}, Test: {len(test_texts)}")

# ===== 3. Pipeline: TF-IDF + Logistic Regression =====
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),       # униграммы + биграммы
        max_features=100000,       # увеличил для больших данных
        sublinear_tf=True,         # улучшение качества
    )),
    ("clf", LogisticRegression(
        max_iter=500,
        n_jobs=-1,                 # использовать все CPU ядра
        C=2.0,                     # немного сильнее регуляризация
    )),
])

# ===== 4. Обучение =====
print("Обучение модели...")
pipeline.fit(train_texts, train_labels)

# ===== 5. Оценка (Validation) =====
print("\n📊 Validation results:")
val_preds = pipeline.predict(val_texts)
print(classification_report(val_labels, val_preds))

# ===== 6. Финальная оценка (Test) =====
print("\n🧪 Test results:")
test_preds = pipeline.predict(test_texts)
print(classification_report(test_labels, test_preds))

# ===== 7. Сохранение =====
joblib.dump(pipeline, MODEL_PATH)
print(f"\n✅ Модель сохранена в {MODEL_PATH}")
