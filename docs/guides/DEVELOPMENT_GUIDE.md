# Development Guide

## Local development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Recommended tooling

- pytest
- ruff
- mypy
- pydantic
- pytest-mock
- pre-commit

## Code style

- typed Python.
- small modules.
- small functions.
- Pydantic models for input/output.
- no raw dicts for complex outputs.
- no secret logging.
- no broad exceptions without normalization.
- no write operation without permission guard.

## Test commands

```bash
pytest
ruff check .
mypy src
```

## Implementation order

1. config loader.
2. Dataiku client wrapper.
3. permission guard.
4. redaction utility.
5. error normalizer.
6. MCP server bootstrap.
7. read-only tools.
8. analysis tools.
9. documentation tools.
10. write tools.

## Mocking Dataiku

Most tests should not require a real DSS instance.

Use mocked objects for:

- projects.
- datasets.
- recipes.
- Managed Folders.
- scenarios.
- jobs.
- code envs.

## Real integration tests

Real DSS integration tests should be optional and gated by:

```env
DATAIKU_INTEGRATION_TESTS=true
```

## Security development rules

- never print environment variables.
- never log API key.
- redact before returning outputs.
- keep read limits enforced at tool level.
- test permission failures.
