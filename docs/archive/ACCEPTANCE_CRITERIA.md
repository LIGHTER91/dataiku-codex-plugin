# Acceptance Criteria

## Plugin packaging

- `plugin.json` exists and is valid JSON.
- skills are present and documented.
- MCP config is present.
- README explains setup.
- example `.env` exists.
- install guide exists.

## MCP server

- server starts in STDIO mode.
- `dataiku-codex-mcp --stdio` works.
- `dataiku-codex-mcp validate-config` works.
- `dataiku-codex-mcp ping` works or returns normalized error.
- tools are registered.
- tool list is available.

## Dataiku connectivity

- ping works.
- projects can be listed.
- project summary works.
- datasets can be listed.
- dataset schema can be read.
- recipes can be listed.
- recipe details can be read.
- Managed Folders can be listed.
- folder files can be listed.
- scenarios can be listed.

## Safety

- readonly mode blocks all write tools.
- readonly mode blocks execute tools.
- secrets are redacted.
- large file reads are blocked.
- dataset previews are limited.
- blocked projects are rejected.
- destructive operations are disabled by default.

## RAG audit

- plugin detects RAG patterns.
- plugin detects chunking code.
- plugin detects vector store usage.
- plugin detects embedding usage.
- plugin produces structured audit report.
- plugin identifies at least 10 common RAG issues.

## Documentation

- plugin can generate project README.
- plugin can generate Flow documentation.
- plugin can generate troubleshooting report.
- plugin can generate RAG audit report.

## Tests

- all unit tests pass.
- all permission tests pass.
- all redaction tests pass.
- all mocked integration tests pass.
- optional real integration tests are skipped unless explicitly enabled.

## Quality

- code is typed.
- ruff passes.
- mypy passes or documented exceptions exist.
- no hardcoded secrets.
- no unsafe default write mode.
