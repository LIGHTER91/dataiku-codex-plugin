# Codex Prompt 01 — Generate Architecture

Implement the technical architecture described in `TECHNICAL_ARCHITECTURE.md`.

Create:

- `src/dataiku_codex_mcp/config.py`
- `src/dataiku_codex_mcp/client.py`
- `src/dataiku_codex_mcp/permissions.py`
- `src/dataiku_codex_mcp/redaction.py`
- `src/dataiku_codex_mcp/errors.py`
- `src/dataiku_codex_mcp/logging_utils.py`
- `src/dataiku_codex_mcp/audit.py`
- `src/dataiku_codex_mcp/server.py`
- `src/dataiku_codex_mcp/tools/`
- `src/dataiku_codex_mcp/models/`
- `tests/`

Requirements:

- Use pydantic for config validation.
- Use `dataikuapi.DSSClient`.
- All tools must return JSON-serializable objects.
- All errors must be normalized.
- API keys must never be logged.
- Permission checks must happen before Dataiku API calls.
- Redaction must happen before returning output.
