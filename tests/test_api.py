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

    assert response.status_code == 200, response.text
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


@pytest.mark.parametrize(
    "payload",
    [
        {"text": "Valid content.", "max_length": "128"},
        {"text": "Valid content.", "min_length": True},
    ],
)
def test_length_controls_require_native_json_integers(payload: dict[str, object]) -> None:
    response = client.post("/summarize", json=payload)

    assert response.status_code == 422


def test_oversized_input_is_rejected() -> None:
    response = client.post("/summarize", json={"text": "x" * 20_001})

    assert response.status_code == 422


def test_undeclared_request_fields_are_rejected() -> None:
    response = client.post(
        "/summarize",
        json={"text": "Valid content.", "model_override": "untrusted-model"},
    )

    assert response.status_code == 422


def test_tracing_is_disabled_without_an_explicit_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)

    assert app_module._configure_tracing() is None



def test_summary_metadata_marks_the_fallback_as_not_calibrated() -> None:
    response = client.post("/summarize", json={"text": "A deterministic summary is available."})

    assert response.status_code == 200, response.text
    metadata = response.json()["metadata"]
    assert metadata == {
        "execution_mode": "extractive-fallback",
        "model_id": None,
        "confidence_status": "not-calibrated",
        "validation_status": "passed",
    }


def test_transformer_metadata_includes_the_configured_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRANSFORMERFORGE_LIGHTWEIGHT_MODE", raising=False)
    monkeypatch.setenv("BASE_MODEL", "reviewed-transformer")
    monkeypatch.setattr(app_module, "_get_summarizer", lambda: lambda *_args, **_kwargs: [{"summary_text": "Model output."}])

    response = client.post("/summarize", json={"text": "Input for the model."})

    assert response.status_code == 200, response.text
    assert response.json()["metadata"] == {
        "execution_mode": "transformer",
        "model_id": "reviewed-transformer",
        "confidence_status": "not-calibrated",
        "validation_status": "passed",
    }
