# Changelog

All notable changes to **TransformerForge** are documented in this file.

The project follows Semantic Versioning and the Keep a Changelog format.

## [Unreleased]

## [1.1.0] - 2026-08-22

### Added

- Python 3.10 and 3.11 CI matrix.
- API contract, validation, and deterministic fallback tests.
- Coverage XML and JUnit test artifacts.
- Container build and live health smoke testing.
- CodeQL, Gitleaks, Trivy, pip-audit, Dependabot, and CycloneDX SBOM automation.
- Reproducible deterministic benchmark protocol with machine-readable JSON/Markdown outputs.
- Verified architecture and request-lifecycle documentation.
- L6 engineering audit and evidence-boundary review.
- GitHub Release source archive, SHA-256 checksum, and GHCR image publishing.
- Manual release recovery for an existing semantic-version tag.

### Changed

- Hardened request validation with bounded input sizes and length constraints.
- Added deterministic lightweight inference for CI and constrained environments.
- Moved heavyweight transformer initialization behind a cached lazy loader.
- Reworked the runtime image into a multi-stage, non-root container.
- Replaced unsupported LLM/RAG quality and latency claims with a reproducible measurement contract.
- Updated README with an organized badge block, architecture/system-design diagrams, Quickstart, reproducibility, research-style benchmark interpretation, limitations, and technical Q&A.
- Clarified that the historical RAG prototype is not part of the verified `/summarize` serving path.

## [0.1.0] - 2025-07-01

### Added

- Initial public TransformerForge scaffold, API, dependency manifest, documentation, and CI foundation.

[Unreleased]: https://github.com/CoreyLeath-code/TransformerForge/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/CoreyLeath-code/TransformerForge/compare/v0.1.0...v1.1.0
[0.1.0]: https://github.com/CoreyLeath-code/TransformerForge/releases/tag/v0.1.0
