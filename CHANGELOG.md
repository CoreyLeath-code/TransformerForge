# Changelog

All notable changes to **TransformerForge** are documented in this file.

The project follows Semantic Versioning and the Keep a Changelog format.

## [Unreleased]

### Added

- Python 3.10 and 3.11 CI matrix.
- API contract, validation, and deterministic fallback tests.
- Coverage XML and JUnit test artifacts.
- Container build and live health smoke testing.
- CodeQL, Gitleaks, Trivy, pip-audit, Dependabot, and CycloneDX SBOM automation.
- GitHub Release source artifacts and GHCR image publishing.
- Security, contribution, release-readiness, and nine-tier deployment-hygiene documentation.
- Existing Helm, Ansible, dashboard, native acceleration, SageMaker, Snowflake, Terraform, and Docker Compose infrastructure remains part of the broader platform roadmap.

### Changed

- Hardened request validation with bounded input sizes and length constraints.
- Added deterministic lightweight inference for CI and constrained environments.
- Moved heavyweight transformer initialization behind a cached lazy loader.
- Reworked the production image into a multi-stage, non-root runtime.
- Pinned runtime and development dependencies for reproducibility.
- Updated repository links to the current `CoreyLeath-code` owner.

## [0.1.0] - 2025-07-01

### Added

- Initial public TransformerForge scaffold, API, dependency manifest, documentation, and CI foundation.

[Unreleased]: https://github.com/CoreyLeath-code/TransformerForge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/CoreyLeath-code/TransformerForge/releases/tag/v0.1.0
