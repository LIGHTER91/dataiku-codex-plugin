# Dataiku DSS Copilot for Codex

This repository contains a working Codex plugin plus a Python MCP server for inspecting, auditing, debugging and selectively modifying Dataiku DSS projects.

The project is built around four pieces:

- a Codex plugin manifest in `plugin.json`
- domain skills under `skills/`
- an MCP server entrypoint in `mcp/dataiku.mcp.json`
- the Python implementation in `src/dataiku_codex_mcp`

## Current status

The repository is no longer only a documentation pack. It includes an implemented server, tests, CLI commands, guarded write and execute tools, and real validation against a Dataiku DSS cloud trial.

Implemented capability areas:

- instance and project inspection
- datasets, recipes and Managed Folders
- Flow analysis and health checks
- code environment diagnostics
- RAG pipeline detection and audit
- scenario runs, job logs and failure explanation
- documentation generation
- controlled write tools for recipes, folders and project docs
- controlled execute tools for scenario runs
- remote Streamable HTTP serving
- bearer or JWT-backed remote authentication
- config-driven policy rules, team allowlists and per-tool RBAC
- JSONL audit logging
- GitHub Actions CI for tests, lint, type-checks and packaging

## Safety model

The default posture is conservative:

- `readonly` by default
- explicit approval required for write and execute actions
- secret redaction enabled by default
- no destructive tool enabled by default
- Managed Folders are treated as remote objects, not local paths

Useful environment flags:

```env
DATAIKU_MODE=readonly
DATAIKU_ENABLE_WRITE_TOOLS=false
DATAIKU_ENABLE_EXECUTE_TOOLS=false
DATAIKU_ENABLE_ADMIN_TOOLS=false
```

For remote hardening, the repository also includes:

- [examples/sample_env.example](examples/sample_env.example)
- [examples/sample_policy.json](examples/sample_policy.json)
- [examples/sample_bearer_tokens.json](examples/sample_bearer_tokens.json)

## Quick start

Create a virtual environment, install the project, then validate the config:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\dataiku-codex-mcp --env-file examples/sample_env.example validate-config
```

Typical local checks:

```powershell
.\.venv\Scripts\pytest -q
.\.venv\Scripts\ruff check .
.\.venv\Scripts\mypy src
```

Run the MCP server over STDIO:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env --stdio
```

Run the MCP server over HTTP:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env serve-http --host 127.0.0.1 --port 8000 --path /mcp
```

## Real DSS validation

The implementation has been exercised on a real Dataiku DSS trial instance, including:

- read-only project inspection
- creation of a Managed Folder
- upload to a Managed Folder
- project library and wiki writes
- Python recipe creation and update
- recipe execution and failure diagnosis
- custom scenario creation and execution

This also drove compatibility fixes for real Dataiku API objects such as:

- cloud Managed Folder connections
- `list_contents()` fallback for folder file listing
- `CodeRecipeSettings` extraction for recipe details

## Packaging notes

This repository can be treated in two ways:

1. As a Codex plugin bundle rooted at `plugin.json`
2. As a Python package providing the `dataiku-codex-mcp` CLI

## Codex UI native plugin

The repository now also includes a native Codex UI plugin bundle in the format expected by local plugin marketplaces:

- [plugins/dataiku-dss-copilot/.codex-plugin/plugin.json](plugins/dataiku-dss-copilot/.codex-plugin/plugin.json)
- [plugins/dataiku-dss-copilot/.mcp.json](plugins/dataiku-dss-copilot/.mcp.json)
- [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json)

The bundle launches the repository virtualenv through:

- [plugins/dataiku-dss-copilot/scripts/run-stdio.ps1](plugins/dataiku-dss-copilot/scripts/run-stdio.ps1)
- [plugins/dataiku-dss-copilot/scripts/run-http.ps1](plugins/dataiku-dss-copilot/scripts/run-http.ps1)

To use it from this workspace, keep the repo as-is and make sure the virtualenv is installed:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Codex can then discover the plugin from the repo-local marketplace file:

- [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json)

If you want a home-local installation instead, copy:

- `plugins/dataiku-dss-copilot` to `~/plugins/dataiku-dss-copilot`
- `.agents/plugins/marketplace.json` entry to `~/.agents/plugins/marketplace.json`

The wrapper scripts read the repo root `.env` by default. Set `DATAIKU_CODEX_ENV_FILE` to point at another env file if needed. Set `DATAIKU_CODEX_REPO_ROOT` if you want a home-local plugin install to target a different checkout of this repository.

To build Python distribution artifacts:

```powershell
.\.venv\Scripts\python -m build
```

The source distribution manifest is defined in [MANIFEST.in](MANIFEST.in).

## CI

GitHub Actions CI is defined in [.github/workflows/ci.yml](.github/workflows/ci.yml) and runs:

- `pytest -q`
- `ruff check .`
- `mypy src`
- `python -m build`

## Repository map

- [src/dataiku_codex_mcp](src/dataiku_codex_mcp)
- [tests](tests)
- [plugin.json](plugin.json)
- [mcp/dataiku.mcp.json](mcp/dataiku.mcp.json)
- [examples/sample_env.example](examples/sample_env.example)
- [ALL_DOCUMENTATION.md](ALL_DOCUMENTATION.md)
