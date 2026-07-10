# Contributing to TransformerForge

## Development setup

```bash
git clone https://github.com/CoreyLeath-code/TransformerForge.git
cd TransformerForge
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

## Required validation

```bash
ruff check src tests --select E9,F63,F7,F82
python -m compileall -q src tests
TRANSFORMERFORGE_LIGHTWEIGHT_MODE=true pytest tests -v --cov=src
docker build -t transformerforge:local .
```

## Pull-request standard

- Use focused branches and conventional commit messages.
- Explain the problem, design decision, test evidence, operational impact, and rollback plan.
- Add tests for behavior changes.
- Do not commit credentials, `.env` files, generated model artifacts, or production data.
- Keep API contracts backward compatible unless a migration path is documented.

## Review criteria

Reviewers should assess correctness, security, model reproducibility, failure behavior, observability, performance, maintainability, deployment impact, and rollback safety.
