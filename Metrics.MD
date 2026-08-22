# TransformerForge Metrics & Evaluation

TransformerForge publishes only measurements that can be reproduced from repository code or CI artifacts. This document intentionally avoids model-quality, retrieval-quality, production-capacity, and latency claims that are not backed by a versioned experiment.

## Evidence boundary

The reproducible benchmark path is `benchmarks/benchmark_lightweight.py`. It forces `TRANSFORMERFORGE_LIGHTWEIGHT_MODE=true`, disables telemetry export, warms each workload for 1,000 operations, and measures three deterministic workloads with `time.perf_counter_ns`:

| Workload | Timed iterations | What it measures |
|---|---:|---|
| `fallback_summary` | 20,000 | Pure deterministic extractive summarization helper |
| `request_validation` | 20,000 | Pydantic request construction and validation |
| `api_summarize_request` | 3,000 | In-process FastAPI `TestClient` request path |

Each workload records mean, median, p95, p99, population standard deviation, and derived single-thread operations/second. CI uploads the JSON/Markdown benchmark outputs as workflow artifacts on Python 3.11.

## What these benchmarks do **not** measure

- Hugging Face transformer download or inference latency.
- GPU/accelerator performance.
- Network latency, reverse proxies, TLS, or multi-process deployment.
- Concurrent request saturation or tail latency under load.
- RAG retrieval latency or retrieval quality.
- ROUGE, BERTScore, factuality, hallucination rate, calibration, or human preference.
- Cost, SLO attainment, availability, or production capacity.

## Model-quality status

No versioned evaluation corpus or accepted model-quality baseline is committed today. Therefore TransformerForge does **not** publish claims such as “high grounding,” “reduced hallucination rate,” or “production-grade LLM quality.” Those require an explicit dataset, metric definition, model revision, decoding configuration, seed policy, and reproducible evaluation command.

## Reproduce

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
TRANSFORMERFORGE_LIGHTWEIGHT_MODE=true python benchmarks/benchmark_lightweight.py
```

Outputs:

```text
benchmark-results/benchmark-results.json
benchmark-results/benchmark-results.md
```

Treat the generated results as environment-specific regression evidence. For research reporting, record the commit SHA, Python version, operating system/runner, processor description, warm-up count, timed iteration count, and whether the measurement is in-process or over a real network boundary.
