# Dataiku DSS Copilot Plugin Bundle

This folder is the repo-local Codex UI plugin bundle for the Dataiku DSS Copilot project.

The intended split is:

- the Codex plugin handles UI, prompts and discoverability
- the MCP server executes reusable commands
- Dataiku native visual components are preferred over ad-hoc generated code

It is designed to be discovered from:

- [`.agents/plugins/marketplace.json`](../../.agents/plugins/marketplace.json)
- [`plugins/dataiku-dss-copilot/.codex-plugin/plugin.json`](./.codex-plugin/plugin.json)

The plugin launches the repository MCP server through:

- [`scripts/run-stdio.ps1`](./scripts/run-stdio.ps1)
- [`scripts/run-http.ps1`](./scripts/run-http.ps1)

Before enabling it in Codex UI, make sure the repository virtual environment exists and the package is installed:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

The wrapper reads the repo root `.env` by default. You can override it with `DATAIKU_CODEX_ENV_FILE`.
