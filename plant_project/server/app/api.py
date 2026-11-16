"""REST API распознавания растений (контракт v1.0, см. API_CONTRACT.md)."""
from __future__ import annotations

import io
import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, File, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from .schemas import (
    ClassesResponse,
    ClassInfo,
    HealthResponse,
    Prediction,
    PredictResponse,
)
from .stub_model import StubModel

API_VERSION = "1.0"
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 МБ
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

# <корень репозитория>/shared/classes.json (можно переопределить переменной PLANT_CLASSES)
ROOT = Path(__file__).resolve().parents[2]
CLASSES_PATH = Path(os.getenv("PLANT_CLASSES", ROOT / "shared" / "classes.json"))


class ApiError(Exception):
    """Ошибка в формате контракта: {"error": {"code": ..., "message": ...}}."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def _error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message}},
    )


def load_classes(path: Path) -> list[ClassInfo]:
    data = json.loads(path.read_text(encoding="utf-8"))
    result = [ClassInfo(**c) for c in data["classes"]]
    if [c.id for c in result] != list(range(len(result))):
        raise ValueError("id классов должны идти подряд, начиная с 0")
    return result


# --- Инициализация (один раз при старте) -----------------------------------
classes: list[ClassInfo] = load_classes(CLASSES_PATH)
# Когда появится настоящая модель, заменить на: model = OnnxModel("models/model.onnx")
model = StubModel(num_classes=len(classes))

app = FastAPI(title="Plant Recognition API", version=API_VERSION)


# --- Обработчики ошибок -----------------------------------------------------
@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return _error_response(exc.status, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    fields = {str(part) for err in exc.errors() for part in err["loc"]}
    if "file" in fields:
        return _error_response(400, "missing_file", "В запросе нет поля file с изображением")
    return _error_response(422, "invalid_params", "Неверные параметры запроса (top_k: от 1 до 10)")


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    return _error_response(500, "internal_error", "Внутренняя ошибка сервера")


# --- Эндпоинты --------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        model_loaded=model is not None,
        api_version=API_VERSION,
        model_version=model.version if model else "none",
    )


@app.get("/classes", response_model=ClassesResponse)
def get_classes():
    return ClassesResponse(count=len(classes), classes=classes)


@app.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    top_k: int = Query(5, ge=1, le=10),
):
    if model is None:
        raise ApiError(503, "model_not_ready", "Модель ещё не загружена")

    data = await file.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ApiError(413, "file_too_large", "Файл больше 10 МБ")

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ApiError(400, "invalid_image", "Файл не является изображением")

    if image.format not in ALLOWED_FORMATS:
        raise ApiError(415, "unsupported_type", "Поддерживаются только JPEG, PNG и WEBP")

    image = image.convert("RGB")

    started = time.perf_counter()
    top = await run_in_threadpool(model.predict, image, min(top_k, len(classes)))
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    predictions = [
        Prediction(
            class_id=cid,
            label=classes[cid].label,
            name_ru=classes[cid].name_ru,
            confidence=round(prob, 4),
        )
        for cid, prob in top
    ]
    return PredictResponse(
        predictions=predictions,
        inference_ms=elapsed_ms,
        model_version=model.version,
    )
