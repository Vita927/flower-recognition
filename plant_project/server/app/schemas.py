"""Pydantic-модели ответов. Должны совпадать с API_CONTRACT.md."""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    api_version: str
    model_version: str


class ClassInfo(BaseModel):
    id: int
    label: str
    name_ru: str


class ClassesResponse(BaseModel):
    count: int
    classes: list[ClassInfo]


class Prediction(BaseModel):
    class_id: int
    label: str
    name_ru: str
    confidence: float = Field(ge=0.0, le=1.0)


class PredictResponse(BaseModel):
    predictions: list[Prediction]
    inference_ms: int
    model_version: str
