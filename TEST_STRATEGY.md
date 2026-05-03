# Test Strategy

## Goals

Ensure the plugin is:

- safe.
- reliable.
- deterministic.
- testable without a real DSS instance.
- compatible with real DSS integration tests.
- resistant to secret leakage.

## Unit tests

Test:

- config loading.
- missing env variables.
- invalid mode.
- allowlist/blocklist parsing.
- permission guard.
- redaction.
- error normalization.
- Dataiku client wrapper.
- graph builder.
- file read limits.
- log truncation.
- RAG detection heuristics.
- recipe code review heuristics.

## MCP tool tests

Every MCP tool must have:

- input schema test.
- output schema test.
- permission test.
- success test.
- error case test.
- redaction test where relevant.

## Integration tests with mocks

Use mocked Dataiku API responses for:

- project listing.
- project summary.
- dataset schema.
- recipe details.
- Managed Folder listing.
- folder file read.
- scenario runs.
- logs.
- code envs.

## Optional real integration tests

Run only if:

```env
DATAIKU_INTEGRATION_TESTS=true
```

Real tests must be read-only by default.

## Security tests

Required:

- API key does not appear in logs.
- secrets are redacted from recipe code.
- secrets are redacted from logs.
- write tools fail in readonly mode.
- execute tools fail in readonly mode.
- blocked project is rejected.
- blocked tool is rejected.
- file too large is rejected.
- dataset preview is capped.

## Golden fixtures

Create fixtures for:

1. simple ETL project.
2. project with Python recipes.
3. project with Managed Folder on non-local backend.
4. project with malformed JSONL files.
5. failed scenario.
6. RAG pipeline project.
7. code env with missing package.
8. recipe with hardcoded secret.

## Acceptance test examples

- `dataiku_ping` returns reachable or normalized error.
- `dataiku_list_projects` returns list or permission error.
- `dataiku_get_project_summary` returns object counts.
- `dataiku_review_recipe_code` flags bad `get_path()` usage.
- `dataiku_managed_folder_doctor` warns on non-local path assumption.
- `dataiku_audit_rag_pipeline` produces a structured report.
