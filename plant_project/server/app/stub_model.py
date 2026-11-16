"""Модель-заглушка: возвращает правдоподобные случайные предсказания.

Нужна, чтобы мобильное приложение разрабатывалось, пока настоящая модель обучается.
Один и тот же снимок всегда даёт один и тот же ответ (seed считается по картинке).

Интерфейс, который должна повторять настоящая модель (OnnxModel):
    version: str
    predict(image: PIL.Image (RGB), top_k: int) -> list[tuple[class_id, probability]]
"""
import hashlib
import random
import time

from PIL import Image


class StubModel:
    version = "stub-0.1"

    def __init__(self, num_classes: int):
        self.num_classes = num_classes

    def predict(self, image: Image.Image, top_k: int) -> list[tuple[int, float]]:
        time.sleep(0.15)  # имитация времени работы нейросети

        small = image.resize((16, 16)).tobytes()
        seed = int.from_bytes(hashlib.md5(small).digest()[:8], "big")
        rng = random.Random(seed)

        weights = [rng.random() ** 4 for _ in range(self.num_classes)]
        total = sum(weights)
        probs = [w / total for w in weights]

        ranked = sorted(enumerate(probs), key=lambda p: p[1], reverse=True)
        return ranked[:top_k]
