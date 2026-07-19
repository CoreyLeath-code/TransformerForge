"""Reproducible lightweight-path benchmarks for TransformerForge.

The suite deliberately excludes model download and transformer inference. It
measures the deterministic code paths used by CI and constrained deployments.
"""

from __future__ import annotations

import json
import math
import os
import platform
import statistics
import time
from pathlib import Path
from typing import Callable

os.environ["TRANSFORMERFORGE_LIGHTWEIGHT_MODE"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from fastapi.testclient import TestClient

from src.python.inference import TextIn, _fallback_summary, app

WARMUP_ITERATIONS = 1_000
OUTPUT_DIRECTORY = Path("benchmark-results")
SAMPLE_TEXT = (
    "TransformerForge validates bounded requests. "
    "It exposes deterministic inference for reproducible tests. "
    "Production deployments can enable the transformer backend."
)


def _percentile(samples: list[int], percentile: float) -> float:
    ordered = sorted(samples)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return float(ordered[index])


def _measure(name: str, operation: Callable[[], object], iterations: int) -> dict[str, float | int | str]:
    for _ in range(WARMUP_ITERATIONS):
        operation()

    samples: list[int] = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        result = operation()
        finished = time.perf_counter_ns()
        if result is None:
            raise RuntimeError(f"{name} returned no result")
        samples.append(finished - started)

    mean_ns = statistics.fmean(samples)
    return {
        "workload": name,
        "iterations": iterations,
        "mean_ns": round(mean_ns, 2),
        "median_ns": round(statistics.median(samples), 2),
        "p95_ns": round(_percentile(samples, 0.95), 2),
        "p99_ns": round(_percentile(samples, 0.99), 2),
        "stddev_ns": round(statistics.pstdev(samples), 2),
        "throughput_ops_per_second": round(1_000_000_000 / mean_ns, 2),
    }


def main() -> None:
    client = TestClient(app)
    payload = {"text": SAMPLE_TEXT, "min_length": 8, "max_length": 128}

    def api_request() -> str:
        response = client.post("/summarize", json=payload)
        response.raise_for_status()
        return str(response.json()["summary"])

    results = [
        _measure(
            "fallback_summary",
            lambda: _fallback_summary(SAMPLE_TEXT, 128),
            20_000,
        ),
        _measure(
            "request_validation",
            lambda: TextIn(**payload),
            20_000,
        ),
        _measure("api_summarize_request", api_request, 3_000),
    ]

    report = {
        "schema_version": 1,
        "mode": "deterministic-lightweight",
        "timer": "time.perf_counter_ns",
        "warmup_iterations_per_workload": WARMUP_ITERATIONS,
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "processor": platform.processor() or "not-reported",
        },
        "results": results,
    }

    OUTPUT_DIRECTORY.mkdir(exist_ok=True)
    (OUTPUT_DIRECTORY / "benchmark-results.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# TransformerForge lightweight benchmark",
        "",
        f"- Python: {report['environment']['python']}",
        f"- Platform: {report['environment']['platform']}",
        f"- Warmup operations/workload: {WARMUP_ITERATIONS:,}",
        "",
        "| Workload | Iterations | Mean | Median | p95 | p99 | Throughput |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            "| {workload} | {iterations:,} | {mean_ns:,.2f} ns | "
            "{median_ns:,.2f} ns | {p95_ns:,.2f} ns | {p99_ns:,.2f} ns | "
            "{throughput_ops_per_second:,.2f} ops/s |".format(**result)
        )

    markdown = "\n".join(lines) + "\n"
    (OUTPUT_DIRECTORY / "benchmark-results.md").write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
