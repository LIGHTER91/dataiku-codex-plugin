# Technical Architecture

## High-level architecture

```text
Codex Plugin
|-- plugin.json or .codex-plugin/plugin.json
|-- skills/
|-- .mcp.json or mcp/*.json
|-- hooks/
`-- assets/

MCP Server
|-- transport layer
|-- command catalog
|-- blueprint resolver
|-- Dataiku API adapter
|-- tool registry
|-- permission guard
|-- redaction layer
|-- error normalizer
|-- audit logger
`-- tests

Dataiku Layer
|-- DSSClient
|-- DSSProject
|-- DSSDataset
|-- DSSRecipe
|-- DSSManagedFolder
|-- DSSScenario
|-- DSSJob
|-- DSSCodeEnv
`-- Visual ML tasks
```

## Product split

The intended split is:

- plugin UI for discoverability, prompts, skills and presentation
- MCP server for fast command execution
- Dataiku-native assets for durable project mutations

The server should prefer:

- command catalog entries
- reusable blueprints
- Prepare recipes
- Visual ML tasks
- scenario templates

The server should avoid generating new setup scripts for recurring workflows.

Direct code generation or code editing should be reserved for:

- recipe fixes
- variable renames
- narrowly scoped maintenance patches
- edge cases where no native Dataiku or catalog path exists

## Runtime options

### Option A - Local STDIO MCP server

Codex starts the MCP server locally.

Best for:

- developer laptop
- secure internal network
- simple setup
- private DSS access through VPN

### Option B - Remote HTTP MCP server

Codex connects to a deployed MCP server.

Best for:

- enterprise deployment
- team-wide access
- central auditing
- centralized policy enforcement
- OAuth or Bearer-token access

## Python package architecture

```text
src/dataiku_codex_mcp/
|-- __init__.py
|-- __main__.py
|-- server.py
|-- config.py
|-- client.py
|-- permissions.py
|-- redaction.py
|-- errors.py
|-- logging_utils.py
|-- audit.py
|-- identity.py
|-- policy.py
|-- remote_auth.py
|-- models/
|   `-- common.py
|-- tools/
|   |-- instance.py
|   |-- projects.py
|   |-- flow.py
|   |-- datasets.py
|   |-- recipes.py
|   |-- managed_folders.py
|   |-- scenarios.py
|   |-- code_envs.py
|   |-- rag.py
|   |-- documentation.py
|   |-- ml.py
|   `-- write_safety.py
`-- analyzers/
    |-- code_review.py
    |-- flow_graph.py
    |-- folder_doctor.py
    |-- rag_audit.py
    |-- log_analysis.py
    |-- ml_bootstrap.py
    `-- ml_commands.py
```

## Core services

### Config service

Loads:

- DSS URL
- API key
- mode
- allowlists
- max limits
- redaction settings
- auth and policy settings

### Command catalog

Maps recurring user intents to reusable operations such as:

- `xgboost_prediction_flow`
- `lightgbm_prediction_flow`
- `random_forest_prediction_flow`
- `logistic_regression_prediction_flow`

The catalog is the preferred execution path for repeated ML setup.

### Blueprint resolver

Converts a catalog command into:

- target selection
- naming plan
- Prepare recipe creation plan
- Visual ML task configuration

### Dataiku client wrapper

Wraps Dataiku API calls and returns normalized objects.

Rules:

- never expose raw API keys
- normalize Dataiku exceptions
- return JSON-serializable data
- keep methods small and testable

### Permission guard

Checks whether a tool is allowed under the current mode.

Modes:

- `readonly`
- `write`
- `execute`
- `admin`

### Redaction layer

Redacts:

- API keys
- tokens
- passwords
- connection strings
- private keys
- secrets in logs
- sensitive columns if configured

### Error normalizer

Converts raw exceptions to a stable structured payload.

### Audit logger

Logs:

- tool name
- command name when relevant
- project key
- mode
- operation type
- timestamp
- success or failure

It must never log secrets or full data payloads.

## Data flow

```text
User request
  ->
Plugin UI and skill selection
  ->
MCP tool call
  ->
Permission guard
  ->
Command catalog and blueprint resolver
  ->
Dataiku API wrapper
  ->
Result normalization
  ->
Redaction
  ->
Structured result to Codex
  ->
Codex explanation, plan or report
```

## Safety architecture

The server must enforce safety independently of Codex.

Codex skills may guide behavior, but the MCP server must still block unsafe operations.

## Dependency choices

Recommended:

- Python 3.10+
- `dataiku-api-client`
- `fastmcp`
- `pydantic`
- `python-dotenv`
- `pytest`
- `ruff`
- `mypy`
- `networkx` for Flow graphs

## Packaging

Use `pyproject.toml`.

CLI examples:

```bash
dataiku-codex-mcp --stdio
dataiku-codex-mcp list-ml-commands
dataiku-codex-mcp plan-ml-command TEST flight_data xgb
```
