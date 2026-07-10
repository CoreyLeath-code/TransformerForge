# TransformerForge L6 Nine-Tier Deployment Hygiene

This document defines the repository's engineering maturity baseline and the automated evidence produced for each tier.

## Tier 1 — Source Hygiene

- Python syntax compilation.
- High-confidence Ruff correctness gates.
- Explicit request models and bounded inputs.
- Reproducible runtime and development dependency manifests.

## Tier 2 — Test Engineering

- Python 3.10 and 3.11 compatibility matrix.
- API root, health, metrics, summarization, and validation contract tests.
- Deterministic lightweight inference for CI without external model downloads.
- Coverage XML and JUnit artifacts.

## Tier 3 — Static Quality

- Ruff correctness checks.
- CodeQL analysis.
- Compile-time syntax validation.
- Typed FastAPI and Pydantic contracts.

## Tier 4 — Security Engineering

- Gitleaks current-tree secret scanning.
- Trivy filesystem vulnerability scanning.
- SARIF upload to GitHub code scanning.
- Responsible vulnerability disclosure guidance.

## Tier 5 — Supply-Chain Hygiene

- Dependabot for Python, GitHub Actions, and Docker.
- pip-audit reports.
- CycloneDX SBOM generation.
- Pinned dependency versions.

## Tier 6 — Reproducible Runtime

- Multi-stage Docker build.
- Minimal Python runtime image.
- Non-root runtime identity.
- Explicit health check.
- Lazy transformer initialization and lightweight fallback mode.

## Tier 7 — Continuous Delivery

- Pull-request and main-branch validation.
- Superseded-run cancellation.
- Multi-version test matrix.
- Live container health smoke testing.
- Release-readiness contract.

## Tier 8 — Release Engineering

- Semantic version tag trigger.
- GitHub Release source archives.
- Generated release notes.
- GHCR container publishing.

## Tier 9 — Operational Governance

- `SECURITY.md` disclosure process.
- `CONTRIBUTING.md` validation and review standard.
- Semantic changelog.
- Auditable CI evidence for tests, coverage, dependency findings, and SBOMs.
- Prometheus metrics and health endpoints.

## Promotion Standard

A change is release-ready when compatibility tests, static analysis, container health validation, security workflows, and release metadata checks are green. Advisory findings should become focused remediation work rather than being hidden or ignored.
