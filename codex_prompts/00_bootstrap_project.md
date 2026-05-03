# Codex Prompt 00 — Bootstrap Project

You are coding the project "Dataiku DSS Copilot for Codex".

Read these files first:

- PROJECT_BRIEF.md
- PRODUCT_REQUIREMENTS.md
- TECHNICAL_ARCHITECTURE.md
- CODEX_PLUGIN_SPEC.md
- MCP_SERVER_SPEC.md
- TOOL_CATALOG.md
- SECURITY_MODEL.md
- TEST_STRATEGY.md
- TOOL_IMPLEMENTATION_ORDER.md

Your task:

1. Create the repository structure.
2. Create `plugin.json`.
3. Create the Python MCP server package.
4. Create the Dataiku client wrapper.
5. Implement read-only tools first.
6. Add tests for every implemented tool.
7. Do not implement write tools until the permission guard exists.
8. Never hardcode secrets.
9. Keep all code typed and modular.
10. Keep outputs JSON-serializable.

Start by implementing:

- `pyproject.toml`
- `src/dataiku_codex_mcp/config.py`
- `src/dataiku_codex_mcp/permissions.py`
- `src/dataiku_codex_mcp/redaction.py`
- `src/dataiku_codex_mcp/errors.py`
- `src/dataiku_codex_mcp/client.py`
- `src/dataiku_codex_mcp/server.py`
- `tests/test_config.py`
- `tests/test_permissions.py`
- `tests/test_redaction.py`
