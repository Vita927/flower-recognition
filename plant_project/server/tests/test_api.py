import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)


def make_image(fmt="JPEG", size=(64, 64), color=(30, 160, 60)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format=fmt)
    return buf.getvalue()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["model_loaded"] is True


def test_classes():
    body = client.get("/classes").json()
    assert body["count"] == len(body["classes"]) > 0
    assert [c["id"] for c in body["classes"]] == list(range(body["count"]))


def test_predict_ok():
    r = client.post("/predict?top_k=3", files={"file": ("a.jpg", make_image(), "image/jpeg")})
    assert r.status_code == 200
    preds = r.json()["predictions"]
    assert len(preds) == 3
    confs = [p["confidence"] for p in preds]
    assert confs == sorted(confs, reverse=True)
    assert all(0 <= c <= 1 for c in confs)


def test_predict_png_ok():
    r = client.post("/predict", files={"file": ("a.png", make_image("PNG"), "image/png")})
    assert r.status_code == 200
    assert len(r.json()["predictions"]) == 5


def test_not_an_image():
    r = client.post("/predict", files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_image"


def test_unsupported_format():
    r = client.post("/predict", files={"file": ("a.gif", make_image("GIF"), "image/gif")})
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "unsupported_type"


def test_missing_file():
    r = client.post("/predict")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "missing_file"


@pytest.mark.parametrize("top_k", [0, 11, "abc"])
def test_bad_top_k(top_k):
    r = client.post(f"/predict?top_k={top_k}", files={"file": ("a.jpg", make_image(), "image/jpeg")})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_params"


def test_same_image_same_answer():
    img = make_image()
    a = client.post("/predict", files={"file": ("a.jpg", img, "image/jpeg")}).json()["predictions"]
    b = client.post("/predict", files={"file": ("a.jpg", img, "image/jpeg")}).json()["predictions"]
    assert a == b
