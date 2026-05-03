# Codex Prompt 04 — Generate Tests

Generate pytest tests for the MCP server.

Test:

- config loading.
- missing env variables.
- invalid mode.
- permission denied.
- project allowlist.
- tool blocklist.
- project listing.
- dataset listing.
- recipe inspection.
- Managed Folder listing.
- Managed Folder non-local get_path warning.
- redaction.
- error normalization.
- file read limits.
- log truncation.

Use mocks for Dataiku API.

Do not require a real DSS instance for normal test runs.
