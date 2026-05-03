# Technical Architecture

## High-level architecture

```text
Codex Plugin
├── plugin.json
├── skills/
├── .mcp.json or mcp/*.json
├── hooks/
└── assets/

MCP Server
├── MCP transport layer
├── Dataiku API client wrapper
├── Tool registry
├── Pydantic input/output models
├── Permission guard
├── Redaction layer
├── Error normalizer
├── Audit logger
└── Tests

Dataiku Layer
├── DSSClient
├── DSSProject
├── DSSDataset
├── DSSRecipe
├── DSSManagedFolder
├── DSSScenario
├── DSSJob
├── DSSCodeEnv
└── DSSPlugin
```

## Runtime options

### Option A — Local STDIO MCP server

Codex starts the MCP server locally.

Best for:

- developer laptop.
- secure internal network.
- simple setup.
- private DSS access through VPN.

### Option B — Remote HTTP MCP server

Codex connects to a deployed MCP server.

Best for:

- enterprise deployment.
- team-wide access.
- central auditing.
- centralized policy enforcement.
- OAuth or Bearer-token access.

## Python package architecture

```text
src/dataiku_codex_mcp/
├── __init__.py
├── __main__.py
├── server.py
├── config.py
├── client.py
├── permissions.py
├── redaction.py
├── errors.py
├── logging_utils.py
├── audit.py
├── models/
│   ├── common.py
│   ├── projects.py
│   ├── datasets.py
│   ├── recipes.py
│   ├── folders.py
│   ├── scenarios.py
│   ├── code_envs.py
│   └── rag.py
├── tools/
│   ├── instance.py
│   ├── projects.py
│   ├── flow.py
│   ├── datasets.py
│   ├── recipes.py
│   ├── managed_folders.py
│   ├── scenarios.py
│   ├── code_envs.py
│   ├── rag.py
│   ├── documentation.py
│   └── write_actions.py
└── analyzers/
    ├── code_review.py
    ├── flow_graph.py
    ├── folder_doctor.py
    ├── rag_audit.py
    ├── data_quality.py
    └── log_analysis.py
```

## Core services

### Config service

Loads:

- DSS URL.
- API key.
- mode.
- allowlists.
- max limits.
- redaction settings.

### Dataiku client wrapper

Wraps Dataiku API calls and returns normalized objects.

Rules:

- never expose raw API key.
- normalize Dataiku exceptions.
- return JSON-serializable data.
- keep methods small and testable.

### Permission guard

Checks whether a tool is allowed under the current mode.

Modes:

- `readonly`
- `write`
- `execute`
- `admin`

### Redaction layer

Redacts:

- API keys.
- tokens.
- passwords.
- connection strings.
- private keys.
- secrets in logs.
- sensitive columns if configured.

### Error normalizer

Converts raw exceptions to:

```json
{
  "error_type": "PermissionDenied",
  "message": "Readable explanation",
  "details": {},
  "suggested_fix": "..."
}
```

### Audit logger

Logs:

- tool name.
- project key.
- mode.
- operation type.
- timestamp.
- success/failure.
- never logs secrets or full data payloads.

## Data flow

```text
User request
  ↓
Codex skill selection
  ↓
MCP tool call
  ↓
Permission guard
  ↓
Dataiku API wrapper
  ↓
Result normalization
  ↓
Redaction
  ↓
Structured result to Codex
  ↓
Codex explanation/report
```

## Safety architecture

The server must enforce safety independently of Codex.

Codex skills may guide behavior, but the MCP server must still block unsafe operations.

## Dependency choices

Recommended:

- Python 3.10+
- `dataiku-api-client`
- `mcp` or `fastmcp`
- `pydantic`
- `python-dotenv`
- `pytest`
- `pytest-mock`
- `ruff`
- `mypy`
- `networkx` for Flow graphs
- `orjson` optional for fast serialization
- `rich` optional for CLI diagnostics

## Packaging

Use `pyproject.toml`.

CLI command:

```bash
dataiku-codex-mcp --stdio
```

Optional commands:

```bash
dataiku-codex-mcp ping
dataiku-codex-mcp list-projects
dataiku-codex-mcp validate-config
```
