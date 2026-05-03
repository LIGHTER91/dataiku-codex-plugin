# Master Prompt for Codex

You are building the project **Dataiku DSS Copilot for Codex**.

This is a complete Codex plugin for Dataiku DSS. It is not a small MVP.

## Read first

Read these files before coding:

- README.md
- PROJECT_BRIEF.md
- PRODUCT_REQUIREMENTS.md
- FUNCTIONAL_SPEC.md
- TECHNICAL_ARCHITECTURE.md
- CODEX_PLUGIN_SPEC.md
- MCP_SERVER_SPEC.md
- TOOL_CATALOG.md
- SECURITY_MODEL.md
- PERMISSION_MODEL.md
- CONFIGURATION_SPEC.md
- TEST_STRATEGY.md
- TOOL_IMPLEMENTATION_ORDER.md

## Build principles

- Implement foundation first.
- Implement read-only tools before write tools.
- Enforce permissions in the MCP server.
- Redact secrets.
- Never log API keys.
- Keep outputs JSON-serializable.
- Write tests for every tool.
- Do not assume Managed Folders are local paths.
- Avoid destructive actions.

## First coding task

Create the repository structure and implement:

1. `pyproject.toml`
2. `plugin.json`
3. MCP server entrypoint.
4. config loader.
5. Dataiku API client wrapper.
6. permission guard.
7. redaction utility.
8. error normalizer.
9. `dataiku_ping`
10. `dataiku_list_projects`
11. tests for all of the above.

## Quality bar

The code should be production-oriented, typed, modular and secure by default.
