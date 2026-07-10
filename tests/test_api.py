"""Contract and failure-mode tests for the TransformerForge API."""

import importlib

import pytest
from fastapi.testclient import TestClient

app_module = importlib.import_module("src.python.inference")
client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def lightweight_inference(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep CI deterministic and independent of external model downloads."""

    monkeypatch.setenv("TRANSFORMERFORGE_LIGHTWEIGHT_MODE", "true")


def test_root_contract() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "TransformerForge"
    assert "version" in response.json()


def test_health_contract() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_metrics_endpoint() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "inference_total" in response.text


def test_lightweight_summarization_contract() -> None:
    response = client.post(
        "/summarize",
        json={
            "text": "TransformerForge validates requests. It supports deterministic CI execution.",
            "min_length": 5,
            "max_length": 90,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]
    assert payload["backend"] == "extractive-fallback"


def test_blank_input_is_rejected() -> None:
    response = client.post("/summarize", json={"text": "   "})

    assert response.status_code == 422


def test_invalid_length_bounds_are_rejected() -> None:
    response = client.post(
        "/summarize",
        json={"text": "Valid content.", "min_length": 100, "max_length": 20},
    )

    assert response.status_code == 422


def test_oversized_input_is_rejected() -> None:
    response = client.post("/summarize", json={"text": "x" * 20_001})

    assert response.status_code == 422
