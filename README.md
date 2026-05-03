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

See [examples/sample_env.example](examples/sample_env.example) for the full configuration template.

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

To build Python distribution artifacts:

```powershell
.\.venv\Scripts\python -m build
```

The source distribution manifest is defined in [MANIFEST.in](MANIFEST.in).

## Repository map

- [src/dataiku_codex_mcp](src/dataiku_codex_mcp)
- [tests](tests)
- [plugin.json](plugin.json)
- [mcp/dataiku.mcp.json](mcp/dataiku.mcp.json)
- [examples/sample_env.example](examples/sample_env.example)
- [ALL_DOCUMENTATION.md](ALL_DOCUMENTATION.md)
