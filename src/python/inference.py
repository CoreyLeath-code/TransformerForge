"""Production-oriented FastAPI inference service for TransformerForge.

The service keeps heavyweight model loading lazy, validates request bounds, and
supports a deterministic extractive fallback for tests and constrained runtimes.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Final

import prometheus_client as prom
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import Counter, Summary
from pydantic import BaseModel, Field, model_validator

APP_VERSION: Final[str] = "1.1.0"
DEFAULT_MODEL: Final[str] = "facebook/bart-large-cnn"
MAX_INPUT_CHARACTERS: Final[int] = 20_000

REQ_COUNTER = Counter("inference_total", "Total inference requests")
ERROR_COUNTER = Counter("inference_errors_total", "Total failed inference requests")
LATENCY_SUM = Summary("inference_latency_seconds", "Inference latency in seconds")

app = FastAPI(
    title="TransformerForge API",
    description="Validated transformer summarization and observability service.",
    version=APP_VERSION,
)


def _configure_tracing() -> None:
    """Enable OpenTelemetry only when its optional dependencies are available."""

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return

    provider = TracerProvider()
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)


_configure_tracing()


class TextIn(BaseModel):
    """Validated summarization request."""

    text: str = Field(min_length=1, max_length=MAX_INPUT_CHARACTERS)
    max_length: int = Field(default=128, ge=8, le=512)
    min_length: int = Field(default=1, ge=1, le=256)

    @model_validator(mode="after")
    def validate_lengths(self) -> "TextIn":
        if self.min_length > self.max_length:
            raise ValueError("min_length must be less than or equal to max_length")
        if not self.text.strip():
            raise ValueError("text must contain non-whitespace characters")
        return self


@lru_cache(maxsize=1)
def _get_summarizer():
    """Load and cache the configured Hugging Face summarization pipeline."""

    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
    import torch

    model_name = os.getenv("BASE_MODEL", DEFAULT_MODEL)
    device = 0 if torch.cuda.is_available() else -1
    return pipeline(
        "summarization",
        model=AutoModelForSeq2SeqLM.from_pretrained(model_name),
        tokenizer=AutoTokenizer.from_pretrained(model_name),
        device=device,
    )


def _fallback_summary(text: str, max_length: int) -> str:
    """Return a deterministic extractive summary without model downloads."""

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]
    if not sentences:
        return text.strip()[:max_length]

    summary = sentences[0]
    for sentence in sentences[1:]:
        candidate = f"{summary} {sentence}"
        if len(candidate) > max_length:
            break
        summary = candidate
    return summary[:max_length].strip()


def _summarize_text(payload: TextIn) -> tuple[str, str]:
    """Run model inference or a deterministic fallback when configured."""

    if os.getenv("TRANSFORMERFORGE_LIGHTWEIGHT_MODE", "false").lower() in {"1", "true", "yes"}:
        return _fallback_summary(payload.text, payload.max_length), "extractive-fallback"

    result = _get_summarizer()(
        payload.text,
        max_length=payload.max_length,
        min_length=payload.min_length,
        truncation=True,
    )[0]["summary_text"]
    return str(result).strip(), "transformer"


@app.get("/")
def root() -> dict[str, str]:
    """Return service identity and readiness metadata."""

    return {"status": "ok", "service": "TransformerForge", "version": APP_VERSION}


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight liveness response for orchestrators."""

    return {"status": "healthy", "service": "transformerforge-api", "version": APP_VERSION}


@app.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics in the standard text format."""

    return Response(prom.generate_latest(), media_type=prom.CONTENT_TYPE_LATEST)


@app.post("/summarize")
@LATENCY_SUM.time()
def summarize(payload: TextIn) -> dict[str, str]:
    """Summarize validated input and identify the execution backend."""

    REQ_COUNTER.inc()
    try:
        summary, backend = _summarize_text(payload)
    except Exception as exc:
        ERROR_COUNTER.inc()
        raise HTTPException(status_code=503, detail="Inference backend unavailable") from exc

    if not summary:
        ERROR_COUNTER.inc()
        raise HTTPException(status_code=500, detail="Inference backend returned an empty summary")
    return {"summary": summary, "backend": backend}
