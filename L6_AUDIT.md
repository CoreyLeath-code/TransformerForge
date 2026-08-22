# TransformerForge L6 Engineering Audit

## Executive assessment

TransformerForge has a credible engineering foundation for a portfolio summarization service: strict request contracts, a deterministic CI-safe execution mode, lazy heavyweight model loading, metrics/tracing hooks, container health validation, and multiple security workflows. Its strongest differentiator is that the verified path can be reproduced without silently downloading a model.

The largest risk was documentation drift: `Metrics.MD` previously described Llama 3, RAG, LangChain, ~25 ms retrieval, high grounding, reduced hallucination, and an L7 production-readiness level without a versioned experiment establishing those claims. The v1.1.0 release baseline removes those unsupported assertions and aligns the documentation with the code actually exercised by CI.

## What the verified runtime actually is

The public service path is `src/python/inference.py`:

1. FastAPI receives `POST /summarize`.
2. Pydantic rejects unknown fields, blank text, oversized input, and invalid length relationships.
3. In lightweight mode, a deterministic extractive helper generates the output.
4. Otherwise a cached Hugging Face summarization pipeline is loaded lazily from `BASE_MODEL`.
5. Responses include execution-mode provenance and deliberately report confidence as `not-calibrated`.
6. Prometheus counters/latency summaries are exposed; OpenTelemetry export is opt-in.

The historical RAG code is separate from this verified path and should remain documented as experimental until it has integration and retrieval-evaluation evidence.

## Strengths

### Contract discipline

The request model has explicit size and range bounds and rejects extra fields. This prevents unsupported inference controls from becoming accidental API surface area.

### Reproducible CI path

The deterministic mode avoids external model downloads and makes API, container, and benchmark checks reproducible on standard GitHub-hosted runners.

### Heavy dependency isolation

The transformer stack is loaded lazily and the optional LLM/RAG dependencies are separated from the lightweight runtime dependency set.

### Observability boundary

Prometheus instrumentation is always local to the service, while OTLP export requires explicit endpoint configuration rather than exporting by default.

### Packaging

The Dockerfile uses a multi-stage Python 3.11 build, a non-root runtime user, and a live health check. The release workflow publishes both source/checksum artifacts and a GHCR image.

## Priority gaps

### P0 — model-quality evidence

There is no committed, versioned evaluation corpus or acceptance protocol for summarization quality. Before publishing ROUGE, BERTScore, factuality, hallucination, preference, or grounding claims, add:

- exact dataset/version/license;
- deterministic split definition;
- exact model revision and decoding settings;
- metric implementation/version;
- repeated-trial/seed policy where applicable;
- machine-readable raw outputs and aggregate report;
- failure taxonomy and representative qualitative cases.

### P0 — readiness semantics

`/health` is a lightweight liveness endpoint and does not prove the transformer backend is loaded or usable. A deployed full-model mode should expose separate liveness/readiness semantics and fail readiness if required model artifacts are unavailable.

### P1 — load and capacity evaluation

The current benchmark is intentionally in-process and single-threaded. Add a separate load-test protocol using a real bound HTTP server, controlled concurrency, warm/cold model states, disclosed hardware, error-rate tracking, and p50/p95/p99 latency under saturation.

### P1 — exact model provenance

`BASE_MODEL` is a model identifier, not necessarily an immutable revision. Full-model experiments and deployments should pin an exact revision/commit and record tokenizer/model configuration hashes.

### P1 — threat model and abuse controls

Before internet exposure, define authentication, authorization, request budgets, rate limits, payload logging/redaction, prompt/data retention, network boundary, and denial-of-service assumptions.

### P1 — RAG separation

The RAG prototype should have its own contract tests and evaluation dataset. Retrieval metrics should include at least recall@k / nDCG / MRR or another task-appropriate relevance measure, plus corpus/version provenance.

### P2 — supply-chain provenance

The repository already has SBOM/security automation. The release line can be strengthened with image digest capture, attestations/signing, action pinning by commit SHA, and artifact provenance.

### P2 — native/experimental components

Attention/training/native-acceleration experiments should be benchmarked and documented independently from the serving path. Avoid implying a performance advantage until equivalent-workload measurements establish one.

## Benchmark interpretation

`benchmarks/benchmark_lightweight.py` uses 1,000 warm-up operations per workload and measures deterministic fallback, Pydantic validation, and in-process FastAPI request handling. It records mean, median, p95, p99, population standard deviation, and derived operations/second.

That is useful regression evidence, but it excludes model download, transformer inference, network transport, concurrency, accelerator behavior, and model quality. Any future README number should identify the exact workflow/commit and environment that produced it.

## Release acceptance criteria

For the v1.1.0 baseline:

- CI matrix passes on Python 3.10 and 3.11.
- API contract tests pass in lightweight mode.
- Docker image builds and `/health` succeeds in CI.
- Security workflows remain enabled.
- README and Metrics documentation contain no unsupported model-quality or production-capacity numbers.
- Release workflow supports semantic tag push and manual recovery for an existing semantic tag.
- Release publishes a source archive, SHA-256 checksum, and GHCR image.

## Recommended next milestone

A strong v1.2.0 would focus on scientific model evaluation rather than additional platform surface area: pin one exact summarization model revision, commit a small legally distributable evaluation set, add ROUGE plus a factuality/error rubric, publish raw outputs, and keep that evaluation separate from deterministic API microbenchmarks.
