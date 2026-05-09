# Dataiku DSS Copilot for Codex — All Documentation



---

# File: `ACCEPTANCE_CRITERIA.md`


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



---

# File: `CODEX_PLUGIN_SPEC.md`


# Codex Plugin Specification

## Purpose

Define how the Dataiku DSS Copilot plugin is packaged for Codex.

## Plugin components

The plugin contains:

- `plugin.json`
- `skills/`
- MCP configuration
- optional hooks
- assets
- installation docs
- examples

## Expected plugin manifest

```json
{
  "name": "dataiku-dss-copilot",
  "version": "1.0.0",
  "description": "Codex plugin for inspecting, auditing, debugging and improving Dataiku DSS projects.",
  "author": "Lucien Lachaud",
  "license": "Apache-2.0",
  "keywords": ["dataiku", "dss", "codex", "mcp", "rag", "mlops"],
  "skills": [
    "./skills/dataiku-project-auditor",
    "./skills/dataiku-managed-folder-debugger",
    "./skills/dataiku-rag-pipeline-auditor",
    "./skills/dataiku-recipe-reviewer",
    "./skills/dataiku-flow-architect",
    "./skills/dataiku-scenario-debugger",
    "./skills/dataiku-code-env-doctor"
  ],
  "mcpServers": "./mcp/dataiku.mcp.json",
  "hooks": "./hooks/hooks.json",
  "interface": {
    "displayName": "Dataiku DSS Copilot",
    "shortDescription": "Inspect, audit and debug Dataiku DSS projects from Codex.",
    "longDescription": "A Codex plugin that connects to Dataiku DSS through MCP and provides expert skills for Flow analysis, recipe debugging, Managed Folder inspection, RAG pipeline auditing and documentation generation.",
    "developerName": "Lucien Lachaud",
    "category": "Developer Tools",
    "capabilities": ["Dataiku DSS", "MCP", "RAG", "MLOps", "Project Audit"]
  }
}
```

## Skill list

### dataiku-project-auditor

For project summaries, audits and architecture understanding.

### dataiku-managed-folder-debugger

For Managed Folder, file access, JSONL/CSV/PDF/DOCX, S3/HDFS/GCS path issues.

### dataiku-rag-pipeline-auditor

For RAG ingestion, chunking, metadata, embeddings, vector stores, retrieval and evaluation.

### dataiku-recipe-reviewer

For Python, SQL, PySpark and visual recipe analysis.

### dataiku-flow-architect

For Flow graph, object dependencies, modularity and architecture recommendations.

### dataiku-scenario-debugger

For failed scenarios, jobs and automation debugging.

### dataiku-code-env-doctor

For code environment dependency issues.

## MCP configuration

The plugin should include a local STDIO MCP configuration by default.

Example:

```json
{
  "mcp_servers": {
    "dataiku-dss": {
      "command": "dataiku-codex-mcp",
      "args": ["--stdio"],
      "env": {
        "DATAIKU_DSS_URL": "${DATAIKU_DSS_URL}",
        "DATAIKU_API_KEY": "${DATAIKU_API_KEY}",
        "DATAIKU_MODE": "readonly"
      }
    }
  }
}
```

## Hook policy

Hooks are optional.

Potential hooks:

- pre-tool-call safety logging.
- post-tool-call redaction validation.
- pre-write dry-run generation.
- post-write audit logging.

No hook should bypass the MCP server permission guard.

## Plugin installation docs

The plugin must provide:

- setup guide.
- environment variables.
- MCP configuration examples.
- read-only test command.
- troubleshooting section.



---

# File: `CONFIGURATION_SPEC.md`


# Configuration Specification

## Required environment variables

```env
DATAIKU_DSS_URL=https://dss.company.com
DATAIKU_API_KEY=changeme
```

## Optional environment variables

```env
DATAIKU_DEFAULT_PROJECT=
DATAIKU_PROJECT_ALLOWLIST=
DATAIKU_PROJECT_BLOCKLIST=
DATAIKU_TOOL_ALLOWLIST=
DATAIKU_TOOL_BLOCKLIST=
DATAIKU_MODE=readonly
DATAIKU_MAX_PREVIEW_ROWS=20
DATAIKU_MAX_FILE_READ_BYTES=500000
DATAIKU_MAX_LOG_LINES=1000
DATAIKU_MAX_LISTED_FILES=1000
DATAIKU_REDACT_SECRETS=true
DATAIKU_ENABLE_WRITE_TOOLS=false
DATAIKU_ENABLE_EXECUTE_TOOLS=false
DATAIKU_ENABLE_ADMIN_TOOLS=false
DATAIKU_DEBUG=false
```

## Modes

Allowed values:

```text
readonly
write
execute
admin
```

## Example `.env`

```env
DATAIKU_DSS_URL=https://dss.company.com
DATAIKU_API_KEY=replace-me
DATAIKU_MODE=readonly
DATAIKU_PROJECT_ALLOWLIST=PROJECT_A,PROJECT_B
DATAIKU_MAX_PREVIEW_ROWS=20
DATAIKU_MAX_FILE_READ_BYTES=500000
DATAIKU_MAX_LOG_LINES=1000
DATAIKU_REDACT_SECRETS=true
DATAIKU_ENABLE_WRITE_TOOLS=false
DATAIKU_ENABLE_EXECUTE_TOOLS=false
DATAIKU_ENABLE_ADMIN_TOOLS=false
```

## Config validation

The server must validate:

- DSS URL is set.
- API key is set.
- mode is valid.
- numeric limits are positive.
- write tools are disabled unless explicitly enabled.
- execute tools are disabled unless explicitly enabled.
- admin tools are disabled unless explicitly enabled.

## Safe defaults

If optional values are missing:

- use readonly mode.
- enable redaction.
- disable write tools.
- disable execute tools.
- disable admin tools.
- keep preview/file/log limits small.



---

# File: `DATAIKU_API_MAPPING.md`


# Dataiku API Mapping

This document maps the intended MCP tools to likely Dataiku Python API concepts.

Exact method names must be verified during implementation against the installed Dataiku API client version.

## Client

### Purpose

Connect to Dataiku DSS.

### Likely API object

- `dataikuapi.DSSClient`

### Plugin wrapper

- `DataikuClientFactory`
- `DataikuDSSAdapter`

## Projects

### MCP tools

- `dataiku_list_projects`
- `dataiku_get_project_summary`
- `dataiku_generate_project_map`

### Likely API objects

- `DSSClient`
- `DSSProject`

### Required data

- project key.
- project name.
- owner.
- metadata.
- variables if permitted.
- tags if available.

## Flow

### MCP tools

- `dataiku_get_flow_graph`
- `dataiku_analyze_flow_health`

### Likely API objects

- `DSSProject`
- project Flow accessors.
- recipes/datasets/folders/model handles.

### Implementation note

If a direct Flow graph API is not sufficient, reconstruct graph from recipe inputs and outputs.

## Datasets

### MCP tools

- `dataiku_list_datasets`
- `dataiku_get_dataset_schema`
- `dataiku_preview_dataset`
- `dataiku_analyze_dataset_quality`

### Likely API objects

- `DSSDataset`
- dataset schema methods.
- dataset settings methods.
- dataset data preview methods where supported.

### Safety

Default preview limit must be small.

## Recipes

### MCP tools

- `dataiku_list_recipes`
- `dataiku_get_recipe_details`
- `dataiku_review_recipe_code`
- `dataiku_update_recipe_code`
- `dataiku_create_python_recipe`

### Likely API objects

- `DSSRecipe`
- project recipe listings.
- recipe settings.
- recipe code accessors for code recipes.

### Safety

Updating code requires write mode and explicit approval.

## Managed Folders

### MCP tools

- `dataiku_list_managed_folders`
- `dataiku_get_managed_folder_info`
- `dataiku_list_folder_files`
- `dataiku_read_folder_file`
- `dataiku_managed_folder_doctor`
- `dataiku_upload_file_to_folder`
- `dataiku_create_managed_folder`

### Likely API objects

- `DSSManagedFolder`
- in-DSS `dataiku.Folder` concepts.
- file listing APIs.
- download/upload stream APIs.

### Critical implementation rule

Never assume a Managed Folder is a local filesystem directory. Use stream APIs for non-local backends.

## Scenarios / Jobs / Logs

### MCP tools

- `dataiku_list_scenarios`
- `dataiku_get_scenario_runs`
- `dataiku_run_scenario`
- `dataiku_get_job_logs`
- `dataiku_explain_failure`

### Likely API objects

- `DSSScenario`
- scenario runs.
- job handles/log access.

### Safety

Running scenarios requires execute mode and explicit approval.

## Code Environments

### MCP tools

- `dataiku_list_code_envs`
- `dataiku_get_code_env_details`
- `dataiku_code_env_doctor`

### Likely API objects

- client/admin-level code env APIs if permission allows.

### Safety

Code env modification is not part of v1 write tools.

## Plugins

### Possible future tools

- `dataiku_list_installed_plugins`
- `dataiku_get_plugin_info`

### Safety

Read-only only in early versions.

## Connections

### Possible future tools

- `dataiku_list_connections`
- `dataiku_get_connection_summary`

### Safety

Never request sensitive info by default. Never return credentials.

## Limitations

Some Dataiku objects may require admin permissions. The plugin must degrade gracefully when permissions are insufficient.



---

# File: `DATA_PRIVACY_SPEC.md`


# Data Privacy Specification

## Privacy goals

The plugin must avoid exposing sensitive data from Dataiku DSS.

## Default behavior

- Return metadata, not full data.
- Preview small samples only.
- Redact secrets.
- Limit file reads.
- Limit logs.
- Avoid connection details.
- Never request sensitive info by default.

## Dataset privacy

Dataset preview must:

- use a small default row limit.
- support maximum configured limit.
- redact sensitive-looking columns.
- avoid returning large text blobs by default.
- avoid returning binary content.
- warn the user if data may contain PII.

## Sensitive column names

The redaction layer should treat these as sensitive by default:

- password
- passwd
- token
- api_key
- secret
- access_key
- private_key
- email
- phone
- address
- ssn
- iban
- credit_card
- card_number
- user_id if configured
- employee_id if configured

## Logs privacy

Logs may contain secrets. The plugin must:

- redact tokens.
- redact credentials.
- redact connection strings.
- truncate long logs.
- avoid returning environment dumps.

## Recipe code privacy

Recipe code may contain hardcoded secrets. The plugin must:

- detect secret-looking assignments.
- redact values.
- keep line numbers if possible.
- report that a secret may exist without revealing the secret.

## Managed Folder privacy

File reading must:

- be size-limited.
- detect binary files.
- support explicit max bytes.
- redact secrets in text files.
- avoid returning full datasets stored as files.

## Audit privacy

Audit logs must not contain:

- API keys.
- data rows.
- file contents.
- raw logs.
- secret-looking values.
- credentials.



---

# File: `DEVELOPMENT_GUIDE.md`


# Development Guide

## Local development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Recommended tooling

- pytest
- ruff
- mypy
- pydantic
- pytest-mock
- pre-commit

## Code style

- typed Python.
- small modules.
- small functions.
- Pydantic models for input/output.
- no raw dicts for complex outputs.
- no secret logging.
- no broad exceptions without normalization.
- no write operation without permission guard.

## Test commands

```bash
pytest
ruff check .
mypy src
```

## Implementation order

1. config loader.
2. Dataiku client wrapper.
3. permission guard.
4. redaction utility.
5. error normalizer.
6. MCP server bootstrap.
7. read-only tools.
8. analysis tools.
9. documentation tools.
10. write tools.

## Mocking Dataiku

Most tests should not require a real DSS instance.

Use mocked objects for:

- projects.
- datasets.
- recipes.
- Managed Folders.
- scenarios.
- jobs.
- code envs.

## Real integration tests

Real DSS integration tests should be optional and gated by:

```env
DATAIKU_INTEGRATION_TESTS=true
```

## Security development rules

- never print environment variables.
- never log API key.
- redact before returning outputs.
- keep read limits enforced at tool level.
- test permission failures.



---

# File: `ERROR_HANDLING_SPEC.md`


# Error Handling Specification

## Goals

Errors must be:

- safe.
- readable.
- actionable.
- normalized.
- testable.
- free of secrets.

## Standard error response

```json
{
  "ok": false,
  "error": {
    "type": "ErrorType",
    "message": "Human-readable explanation.",
    "details": {},
    "suggested_fix": "Recommended next step."
  }
}
```

## Error categories

### ConfigurationError

Examples:

- missing `DATAIKU_DSS_URL`.
- missing `DATAIKU_API_KEY`.
- invalid mode.
- invalid allowlist.

### DataikuConnectionError

Examples:

- DSS unreachable.
- DNS failure.
- SSL error.
- timeout.

### DataikuAuthenticationError

Examples:

- invalid API key.
- expired token.
- insufficient auth.

### PermissionDeniedError

Examples:

- tool not allowed in mode.
- project not allowed.
- write operation in readonly mode.
- missing approval.

### DataikuObjectNotFoundError

Examples:

- project not found.
- dataset not found.
- recipe not found.
- Managed Folder not found.
- scenario not found.

### DataikuAPIError

Examples:

- unexpected Dataiku API response.
- unsupported operation.
- client version mismatch.

### FileTooLargeError

Examples:

- requested Managed Folder file exceeds max bytes.
- logs exceed line limit.

### BinaryFileError

Examples:

- attempted to read binary file as text.

### RedactionError

Examples:

- output contains unredacted secret-looking value.
- redaction failed.

### UnsupportedOperationError

Examples:

- requested API not supported by current Dataiku version.
- operation not implemented yet.

## Implementation requirements

- Catch Dataiku-specific exceptions.
- Map exceptions to normalized errors.
- Remove credentials from exception messages.
- Do not include raw stack traces in normal output.
- Keep stack traces only in debug logs, with redaction.
- Include suggested fixes.

## Example

```json
{
  "ok": false,
  "error": {
    "type": "PermissionDeniedError",
    "message": "The tool dataiku_update_recipe_code is not allowed in readonly mode.",
    "details": {
      "mode": "readonly",
      "required_mode": "write"
    },
    "suggested_fix": "Set DATAIKU_MODE=write and DATAIKU_ENABLE_WRITE_TOOLS=true, then explicitly approve the operation."
  }
}
```



---

# File: `FUNCTIONAL_SPEC.md`


# Functional Specification

## Module 1 — Instance Discovery

The plugin must detect:

- DSS availability.
- DSS version if available.
- current user if available.
- accessible projects.
- global feature availability where permitted.
- installed plugins where permitted.
- code environments where permitted.

### Expected user requests

- "Check if my Dataiku instance is reachable."
- "List my Dataiku projects."
- "What Dataiku version am I connected to?"

## Module 2 — Project Understanding

For a given `project_key`, the plugin must retrieve:

- project metadata.
- datasets.
- recipes.
- Managed Folders.
- scenarios.
- jobs/runs where available.
- project variables where permitted.
- project library/code assets where permitted.
- Flow zones if available.
- models and saved models if available.

### Output requirements

Project summaries must include:

- object counts.
- important objects.
- detected technical stack.
- potential risks.
- missing documentation.
- recommended next analysis steps.

## Module 3 — Flow Analysis

The plugin must build a graph representation of:

- datasets.
- recipes.
- Managed Folders.
- model objects.
- scenario dependencies where possible.
- recipe inputs and outputs.
- upstream/downstream dependencies.

### Graph output format

Return a JSON object with:

- `nodes`
- `edges`
- `topological_order`
- `orphan_nodes`
- `warnings`
- `summary`

### Health checks

The plugin must detect:

- orphan datasets.
- recipes without outputs.
- unused datasets.
- duplicated transformations.
- missing Flow zones.
- naming inconsistencies.
- objects with poor descriptions.
- potentially unstable dependencies.

## Module 4 — Recipe Analysis

The plugin must inspect:

- Python recipes.
- SQL recipes.
- PySpark recipes if accessible.
- visual recipes metadata.
- input/output bindings.
- recipe code.
- recipe settings.

### Python recipe checks

Detect:

- use of `get_path()` on Managed Folders without checking backend.
- hardcoded absolute paths.
- full-file reads for large files.
- unsafe JSONL parsing.
- missing UTF-8 decoding handling.
- missing schema management.
- missing logging.
- missing exception handling.
- unpinned package assumptions.
- vector index dimension mismatch patterns.
- embedding normalization mistakes.
- batch processing issues.
- memory-heavy pandas usage.
- non-streaming processing for large files.

### SQL recipe checks

Detect:

- `SELECT *` anti-patterns.
- missing filters on large tables.
- inconsistent naming.
- fragile date parsing.
- duplicated logic.
- possible schema drift.

## Module 5 — Managed Folder Analysis

The plugin must:

- list Managed Folders.
- retrieve folder metadata.
- list files safely.
- read small files through Dataiku APIs.
- detect backend/path constraints.
- avoid local path assumptions.
- inspect file formats when safe.
- detect malformed JSONL.
- detect encoding problems.
- detect oversized files.
- detect empty folders.
- detect partitioning confusion.

### Supported file types

Priority:

- `.jsonl`
- `.json`
- `.csv`
- `.txt`
- `.md`
- `.parquet` when supported
- `.pdf` metadata or text extraction when safe
- `.docx` metadata or text extraction when safe

## Module 6 — Scenario and Job Debugging

The plugin must:

- list scenarios.
- inspect scenario settings if available.
- inspect recent scenario runs.
- retrieve logs with line limits.
- identify failed steps.
- normalize errors.
- suggest probable causes.
- propose next debugging actions.

### Failure categories

- permission error.
- missing dataset.
- missing Managed Folder file.
- code environment error.
- package import error.
- schema mismatch.
- memory error.
- timeout.
- invalid credentials.
- API error.
- vector store error.
- LLM connector error.

## Module 7 — Code Environment Doctor

The plugin must:

- list code envs if allowed.
- retrieve code env settings if allowed.
- detect Python version issues.
- detect missing packages.
- detect package version conflicts.
- detect native dependency issues.
- detect offline installation risks.
- suggest installation steps.
- suggest reproducibility improvements.

## Module 8 — RAG Pipeline Auditor

The plugin must detect and analyze:

- document ingestion.
- text cleaning.
- chunking.
- metadata extraction.
- embedding generation.
- vector store creation.
- vector store querying.
- metadata filtering.
- sparse/dense retrieval.
- reranking.
- answer generation.
- prompt templates.
- evaluation.

### RAG-specific risks

- chunks too large or too small.
- missing overlap.
- missing source identifiers.
- poor metadata normalization.
- no document/page/section hierarchy.
- embedding dimension mismatch.
- missing vector normalization for cosine search.
- no reranking.
- top-k too low or too high.
- context window overload.
- no citation policy.
- no evaluation dataset.
- no Recall@K/MRR/nDCG checks.
- hallucination risk.
- no prompt injection mitigation.

## Module 9 — Documentation Generator

The plugin must generate:

- project README.
- Flow architecture report.
- dataset dictionary.
- recipe documentation.
- Managed Folder inventory.
- scenario/runbook documentation.
- RAG architecture report.
- troubleshooting report.
- technical debt report.

## Module 10 — Controlled Modification

After safety layers are implemented, the plugin may:

- create recipes.
- update recipe code.
- create datasets.
- create Managed Folders.
- upload files.
- run scenarios.
- update project documentation.
- add generated README content to project files/wiki if available.

All write/execute operations require:

- write or execute mode.
- explicit user approval.
- dry-run summary before execution.
- audit log entry.
- rollback guidance where possible.



---

# File: `INSTALLATION_GUIDE.md`


# Installation Guide

## Requirements

- Python 3.10+
- Codex CLI or Codex IDE integration
- Access to a Dataiku DSS instance
- Dataiku API key
- Network access to DSS
- `pip`

## Installation

Clone or create the repository.

```bash
git clone <repository-url>
cd dataiku-dss-copilot
```

Create virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install.

```bash
pip install -e ".[dev]"
```

## Configure environment

```bash
cp examples/sample_env.example .env
```

Edit `.env`:

```env
DATAIKU_DSS_URL=https://dss.company.com
DATAIKU_API_KEY=replace-me
DATAIKU_MODE=readonly
```

## Test connection

```bash
dataiku-codex-mcp validate-config
dataiku-codex-mcp ping
```

## Run MCP server locally

```bash
dataiku-codex-mcp --stdio
```

## Configure Codex

Use the provided MCP config:

```json
{
  "mcp_servers": {
    "dataiku-dss": {
      "command": "dataiku-codex-mcp",
      "args": ["--stdio"],
      "env": {
        "DATAIKU_DSS_URL": "${DATAIKU_DSS_URL}",
        "DATAIKU_API_KEY": "${DATAIKU_API_KEY}",
        "DATAIKU_MODE": "readonly"
      }
    }
  }
}
```

## First test requests

- "Ping my Dataiku instance."
- "List my accessible Dataiku projects."
- "Summarize project PROJECT_KEY."
- "List recipes in project PROJECT_KEY."
- "Inspect Managed Folders in project PROJECT_KEY."

## Troubleshooting

### DSS unreachable

Check:

- `DATAIKU_DSS_URL`
- VPN/network access
- proxy settings
- SSL certificates

### Authentication error

Check:

- API key validity
- API key permissions
- Dataiku user permissions

### Tool denied

Check:

- `DATAIKU_MODE`
- tool permission level
- project allowlist/blocklist
- write/execute enable flags

### Managed Folder path issue

Do not assume the folder is local. Use file listing and stream APIs.



---

# File: `MCP_SERVER_SPEC.md`


# MCP Server Specification

## Purpose

Expose Dataiku DSS functionality as MCP tools usable by Codex.

## Supported transports

The server should support:

- STDIO transport for local usage.
- Streamable HTTP transport for enterprise deployment.

## Server layers

1. Transport layer.
2. Tool registry.
3. Input validation.
4. Permission guard.
5. Dataiku API adapter.
6. Result serializer.
7. Redaction layer.
8. Error normalization.
9. Audit logging.

## Python dependencies

Recommended:

```text
mcp
dataiku-api-client
pydantic
python-dotenv
pytest
pytest-mock
networkx
ruff
mypy
```

Optional:

```text
fastmcp
orjson
rich
pandas
pyarrow
python-magic
```

## Tool design rules

Every tool must:

- have typed input models.
- have typed output models where useful.
- return JSON-serializable output.
- have clear permission level.
- call the permission guard.
- apply redaction.
- handle Dataiku exceptions.
- include tests.

## Permission levels

- `read`: metadata, schemas, small previews, recipe code, logs.
- `write`: create/update non-destructive objects.
- `execute`: run scenarios/jobs.
- `admin`: inspect admin-level settings where API key allows.
- `dangerous`: delete or destructive operations. Disabled by default.

## Tool registration categories

- instance
- projects
- flow
- datasets
- recipes
- Managed Folders
- scenarios/jobs/logs
- code environments
- RAG audit
- documentation
- write actions

## Server CLI

Required:

```bash
dataiku-codex-mcp --stdio
```

Recommended:

```bash
dataiku-codex-mcp ping
dataiku-codex-mcp validate-config
dataiku-codex-mcp list-tools
dataiku-codex-mcp list-projects
```

## Error response format

```json
{
  "ok": false,
  "error": {
    "type": "DataikuConnectionError",
    "message": "Could not connect to Dataiku DSS.",
    "details": {
      "url": "redacted"
    },
    "suggested_fix": "Check DATAIKU_DSS_URL, network access and API key."
  }
}
```

## Success response format

```json
{
  "ok": true,
  "data": {},
  "warnings": [],
  "metadata": {
    "tool": "dataiku_list_projects",
    "mode": "readonly"
  }
}
```



---

# File: `PACK_CONTENTS.md`


# Pack Contents

This downloadable pack contains:

## Root specifications

- README.md
- PROJECT_BRIEF.md
- PRODUCT_REQUIREMENTS.md
- FUNCTIONAL_SPEC.md
- TECHNICAL_ARCHITECTURE.md
- CODEX_PLUGIN_SPEC.md
- MCP_SERVER_SPEC.md
- DATAIKU_API_MAPPING.md
- TOOL_CATALOG.md
- SECURITY_MODEL.md
- PERMISSION_MODEL.md
- ERROR_HANDLING_SPEC.md
- DATA_PRIVACY_SPEC.md
- CONFIGURATION_SPEC.md
- INSTALLATION_GUIDE.md
- DEVELOPMENT_GUIDE.md
- TEST_STRATEGY.md
- ACCEPTANCE_CRITERIA.md
- RELEASE_PLAN.md
- ROADMAP.md
- TOOL_IMPLEMENTATION_ORDER.md

## Codex prompts

- codex_prompts/00_bootstrap_project.md
- codex_prompts/01_generate_architecture.md
- codex_prompts/02_generate_mcp_server.md
- codex_prompts/03_generate_skills.md
- codex_prompts/04_generate_tests.md
- codex_prompts/05_security_review.md
- codex_prompts/06_final_packaging.md
- codex_prompts/07_implement_rag_auditor.md
- codex_prompts/08_implement_managed_folder_doctor.md

## Skills

- skills/dataiku-project-auditor/SKILL.md
- skills/dataiku-managed-folder-debugger/SKILL.md
- skills/dataiku-rag-pipeline-auditor/SKILL.md
- skills/dataiku-recipe-reviewer/SKILL.md
- skills/dataiku-flow-architect/SKILL.md
- skills/dataiku-scenario-debugger/SKILL.md
- skills/dataiku-code-env-doctor/SKILL.md

## MCP docs

- mcp/README.md
- mcp/SERVER_DESIGN.md
- mcp/TOOLS_SPEC.md
- mcp/RESOURCES_SPEC.md
- mcp/PROMPTS_SPEC.md
- mcp/SAFETY_RULES.md
- mcp/dataiku.mcp.json

## Extra docs

- docs/use_cases/USE_CASES.md
- docs/user_stories/USER_STORIES.md
- docs/workflows/WORKFLOWS.md
- docs/diagrams/ARCHITECTURE.md
- docs/prompts/MASTER_CODEX_PROMPT.md
- docs/examples/EXAMPLE_REPORTS.md
- docs/decisions/*.md

## Examples

- examples/sample_plugin.json
- examples/sample_mcp.json
- examples/sample_env.example
- examples/sample_user_requests.md
- examples/sample_prompts.md



---

# File: `PERMISSION_MODEL.md`


# Permission Model

## Modes

## readonly

Can inspect:

- projects.
- Flow metadata.
- datasets metadata.
- dataset schemas.
- small dataset previews.
- recipes and recipe code.
- Managed Folder metadata.
- small files through safe read APIs.
- scenarios metadata.
- recent runs/logs.
- code env metadata if allowed.

Cannot:

- modify objects.
- run scenarios.
- upload files.
- delete anything.

## write

Includes readonly capabilities and can:

- create recipes.
- update recipe code.
- create Managed Folders.
- upload files.
- write generated documentation.

Requires:

- `DATAIKU_ENABLE_WRITE_TOOLS=true`
- explicit approval per operation.

## execute

Includes readonly capabilities and can:

- run scenarios.
- run jobs if implemented.

Requires:

- `DATAIKU_ENABLE_EXECUTE_TOOLS=true`
- explicit approval per operation.

## admin

Can inspect admin-level objects where the API key allows.

Possible capabilities:

- code environments.
- plugins.
- connections metadata without secrets.
- global settings summaries.

Requires:

- `DATAIKU_ENABLE_ADMIN_TOOLS=true`

## dangerous

Reserved for destructive operations.

Should remain disabled unless a future version implements strong safeguards.

## Project allowlist

Environment variable:

```env
DATAIKU_PROJECT_ALLOWLIST=PROJECT_A,PROJECT_B
```

If set, the server must reject all project operations outside this list.

## Project blocklist

Environment variable:

```env
DATAIKU_PROJECT_BLOCKLIST=SECRET_PROJECT,HR_PROJECT
```

If set, the server must reject operations on these projects.

## Tool allowlist/blocklist

Optional environment variables:

```env
DATAIKU_TOOL_ALLOWLIST=dataiku_ping,dataiku_list_projects
DATAIKU_TOOL_BLOCKLIST=dataiku_preview_dataset,dataiku_read_folder_file
```

## Approval input pattern

Write/execute tools should include:

```json
{
  "approved": true,
  "approval_reason": "User explicitly approved this action."
}
```

If `approved` is missing or false, the server must reject the operation and return a dry-run summary if possible.

## Permission test requirements

Every tool must have tests for:

- allowed mode.
- denied mode.
- blocked project.
- blocked tool.
- missing approval for write/execute.



---

# File: `PRODUCT_REQUIREMENTS.md`


# Product Requirements

## Goals

The plugin must allow Codex to:

1. Connect to Dataiku DSS using a configurable API client.
2. Inspect accessible Dataiku projects.
3. Understand project Flow structure.
4. Analyze datasets, schemas, recipes, scenarios, jobs and Managed Folders.
5. Debug common Dataiku issues.
6. Review Python/SQL recipes.
7. Audit RAG and LLM pipelines built inside Dataiku.
8. Diagnose code environment problems.
9. Generate useful project documentation.
10. Propose safe modifications.
11. Apply controlled modifications only after explicit approval and permission checks.

## Non-goals

The plugin must not:

- Replace the Dataiku DSS UI.
- Bypass Dataiku permissions.
- Expose credentials or secrets.
- Read full datasets by default.
- Run destructive operations without explicit approval.
- Assume Managed Folders are accessible through local filesystem paths.
- Depend on a specific company-internal Dataiku configuration.
- Require admin access for normal read-only usage.
- Execute arbitrary user code unless explicitly enabled.

## Product modes

### 1. Read-only audit mode

Default mode. Allows inspection, summaries, schema reading, recipe reading, logs reading and safe previews.

### 2. Assisted write mode

Allows non-destructive write operations after explicit approval.

### 3. Execute mode

Allows running scenarios or jobs after explicit approval.

### 4. Admin mode

Allows inspecting admin-level objects if the API key already has those permissions.

### 5. RAG expert mode

Specialized analysis of ingestion, chunking, embeddings, vector stores, rerankers, prompts and evaluation.

### 6. Documentation mode

Generates README files, architecture docs, Flow summaries, troubleshooting reports and RAG audit reports.

## Core capabilities

### Instance discovery

- Ping DSS.
- Retrieve version if possible.
- List accessible projects.
- Detect user permissions if available.

### Project understanding

- List datasets.
- List recipes.
- List Managed Folders.
- List scenarios.
- List jobs/runs.
- Retrieve project metadata.
- Retrieve project variables if allowed.
- Build a project map.

### Flow analysis

- Build dependency graph.
- Identify orphan objects.
- Identify missing documentation.
- Identify risky architecture patterns.
- Identify duplicated logic.

### Recipe analysis

- Inspect recipe code and settings.
- Detect bad Dataiku API usage.
- Detect hardcoded paths.
- Detect memory-heavy patterns.
- Detect missing error handling and logging.

### Managed Folder analysis

- List folders and files.
- Detect backend/path assumptions.
- Read small files safely through APIs.
- Analyze JSONL/CSV/Markdown/PDF/DOCX when supported.
- Detect malformed files.

### Scenario and job debugging

- List scenarios.
- Retrieve recent runs.
- Retrieve logs.
- Explain failure root cause.
- Suggest fixes.

### Code environment diagnosis

- Inspect code envs if allowed.
- Detect missing or incompatible packages.
- Suggest package installation actions.
- Support offline-install-oriented advice.

### RAG pipeline audit

- Detect RAG components.
- Analyze chunking.
- Analyze metadata.
- Analyze embeddings.
- Analyze vector store usage.
- Analyze reranking.
- Analyze evaluation strategy.
- Detect hallucination risks.

### Documentation generation

- Generate project README.
- Generate Flow documentation.
- Generate troubleshooting reports.
- Generate RAG audit reports.
- Generate dataset dictionaries.

## Success metrics

- Time to understand a Dataiku project reduced significantly.
- Common Managed Folder bugs detected automatically.
- RAG pipeline weaknesses identified clearly.
- Read-only mode never performs write operations.
- Tests cover every MCP tool.
- Outputs are useful to both technical and non-technical stakeholders.



---

# File: `PROJECT_BRIEF.md`


# Project Brief — Dataiku DSS Copilot for Codex

## Vision

Build a complete Codex plugin that connects Codex to Dataiku DSS and allows developers, data scientists, AI engineers and MLOps teams to inspect, audit, debug, document and safely modify Dataiku projects.

## Product name

Dataiku DSS Copilot for Codex

## Product category

Developer tool / Data platform assistant / AI engineering assistant / MCP connector.

## Core idea

The plugin combines:

- Codex skills for Dataiku-specific reasoning.
- An MCP server exposing Dataiku DSS API tools.
- A Dataiku API client wrapper.
- A security and permission layer.
- A redaction layer.
- A test suite.
- Documentation and examples.

## Main users

- AI engineers
- Data scientists
- Data engineers
- MLOps engineers
- Dataiku administrators
- RAG engineers
- Enterprise data teams
- Technical project leads

## Main value

Reduce the time needed to understand and debug complex Dataiku DSS projects, especially projects involving Python recipes, Managed Folders, scenario automation, LLM connectors, RAG pipelines, vector databases and large document ingestion.

## Product promise

Give Codex enough Dataiku-specific context and tools to answer questions such as:

- "Analyze this Dataiku project and explain the Flow architecture."
- "Find why my Python recipe fails when reading a Managed Folder."
- "Audit my RAG pipeline: chunking, metadata, embeddings, vector store and reranking."
- "Inspect the latest scenario failure and explain the root cause."
- "Generate a technical README for this project."
- "Review my recipes for unsafe Dataiku API usage."

## Key differentiator

This is not just "Codex inside Dataiku". It is a Codex plugin that can understand and operate on a Dataiku DSS instance from Codex through a structured, safe and testable MCP server.



---

# File: `README.md`


# Dataiku DSS Copilot for Codex — Documentation Pack

This repository contains the full documentation needed to ask Codex to build a complete Codex plugin for Dataiku DSS.

The intended product is not a small MVP. It is a maximal plugin architecture combining:

- Codex plugin packaging
- Codex skills
- MCP server integration
- Dataiku DSS Python/API client
- Read-only project inspection
- Controlled write operations
- RAG/LLM pipeline auditing
- Managed Folder debugging
- Scenario/job/log analysis
- Code environment diagnosis
- Security, privacy and permission controls
- Test strategy and acceptance criteria

## Recommended build order

1. Read `PROJECT_BRIEF.md`
2. Read `PRODUCT_REQUIREMENTS.md`
3. Read `FUNCTIONAL_SPEC.md`
4. Read `TECHNICAL_ARCHITECTURE.md`
5. Read `CODEX_PLUGIN_SPEC.md`
6. Read `MCP_SERVER_SPEC.md`
7. Read `TOOL_CATALOG.md`
8. Read `SECURITY_MODEL.md`
9. Read `TEST_STRATEGY.md`
10. Start with `codex_prompts/00_bootstrap_project.md`

## Core idea

Dataiku DSS Copilot for Codex gives Codex a deep, safe and structured way to inspect, audit, debug and improve Dataiku DSS projects.

It should be especially strong for:

- Python recipes
- SQL recipes
- Managed Folders
- scenarios and jobs
- code environments
- RAG pipelines
- vector stores
- embedding pipelines
- metadata quality
- documentation generation

## Non-negotiable principles

- Read-only by default.
- No secret exfiltration.
- Explicit approval for write or execution operations.
- No destructive operation by default.
- Do not assume Managed Folders are local paths.
- Do not dump full datasets by default.
- Every MCP tool must have tests.
- Every output must be JSON-serializable.
- Errors must be normalized and useful.



---

# File: `RELEASE_PLAN.md`


# Release Plan

## Alpha

Goal: internal developer testing with mocked Dataiku API.

Scope:

- local STDIO MCP server.
- read-only tools.
- skills.
- tests.
- mocked fixtures.

Exit criteria:

- all read-only tool tests pass.
- plugin can be loaded locally.
- no secret leakage in tests.

## Beta

Goal: test with a real Dataiku DSS instance in read-only mode.

Scope:

- project inspection.
- recipe reading.
- Managed Folder listing.
- scenario listing.
- logs.
- RAG audit.

Exit criteria:

- works on at least 2 real projects.
- handles permission errors gracefully.
- no write operations possible.

## Release Candidate

Goal: hardening and packaging.

Scope:

- documentation finalization.
- installation guide.
- security review.
- acceptance criteria validation.
- versioned release notes.

Exit criteria:

- tests pass.
- docs complete.
- security review completed.
- plugin package ready.

## Stable

Goal: public or private enterprise release.

Scope:

- version tag.
- changelog.
- installation package.
- demo examples.
- known limitations.

## Post-stable

- controlled write tools.
- remote MCP deployment.
- enterprise policy engine.



---

# File: `ROADMAP.md`


# Roadmap

## Version 1.0 — Read-only foundation

- Codex plugin structure.
- MCP server STDIO.
- config loading.
- permission guard.
- redaction.
- error normalization.
- Dataiku client wrapper.
- project listing.
- project summaries.
- dataset listing/schema.
- recipe listing/details.
- Managed Folder listing/files.
- scenario listing.
- basic logs.
- all skills.

## Version 1.5 — Analysis layer

- Flow graph reconstruction.
- Flow health analysis.
- recipe code reviewer.
- Managed Folder doctor.
- scenario failure explainer.
- code env doctor.
- RAG pipeline detector.
- RAG audit report.
- project README generation.

## Version 2.0 — Controlled actions

- create Python recipe.
- update recipe code.
- create Managed Folder.
- upload file to Managed Folder.
- run scenario.
- write generated documentation.
- approval flow.
- dry-run output.

## Version 2.5 — Enterprise hardening

- remote HTTP MCP server.
- OAuth/Bearer auth.
- centralized audit logs.
- policy engine.
- team allowlists.
- per-tool RBAC.
- stricter PII detection.
- deployment guide.

## Version 3.0 — Advanced AI engineering

- RAG eval runner.
- chunking comparison runner.
- FAISS/Weaviate inspector.
- embedding drift monitor.
- prompt injection audit.
- automatic architecture diagrams.
- project quality score.
- technical debt prioritization.

## Version 4.0 — Dataiku platform operations

- code env update planning.
- plugin inventory.
- scenario dependency map.
- cost/performance monitoring.
- production readiness checklist.
- governance documentation generator.



---

# File: `SECURITY_MODEL.md`


# Security Model

## Security principles

- Least privilege.
- Read-only by default.
- Explicit approval for write operations.
- Explicit approval for execute operations.
- No secret exfiltration.
- No credentials in logs.
- No full dataset dumps by default.
- No destructive actions by default.
- No arbitrary code execution unless explicitly enabled.
- No `sensitive_info=True` by default.
- User permissions in Dataiku must be respected.
- MCP server must enforce security independently from Codex.

## Data redaction

The plugin must redact:

- API keys.
- passwords.
- bearer tokens.
- private keys.
- OAuth tokens.
- connection strings.
- database credentials.
- secret environment variables.
- sensitive values in logs.
- PII-like fields if configured.

## Secret patterns

The redaction layer should detect patterns such as:

- `api_key=...`
- `password=...`
- `token=...`
- `Authorization: Bearer ...`
- `-----BEGIN PRIVATE KEY-----`
- AWS keys.
- GCP service account keys.
- Azure credentials.
- JDBC URLs with passwords.

## Dangerous operations

The following operations require explicit approval:

- update recipe code.
- create recipe.
- create dataset.
- create Managed Folder.
- upload files.
- run scenario.
- run job.
- update documentation.
- change project variables.
- change code env settings.
- inspect admin-level connections.

## Disabled by default

The following should be disabled unless explicitly implemented safely:

- delete project objects.
- delete datasets.
- delete recipes.
- delete Managed Folders.
- delete project.
- modify connections.
- retrieve connection credentials.
- run arbitrary code on DSS.
- export full datasets.

## Read limits

Default limits:

- max dataset preview rows: 20.
- max file read bytes: 500,000.
- max log lines: 1,000.
- max listed files: 1,000.

These must be configurable.

## Audit logging

Every tool call should log:

- timestamp.
- tool name.
- mode.
- project key if any.
- object name if any.
- success/failure.
- error type if any.

Never log:

- API keys.
- full data rows.
- file contents.
- credentials.
- secret values.

## Approval model

Before write/execute operations, Codex must show:

- what will be changed.
- target project.
- target object.
- risk level.
- rollback possibility.
- exact operation.

The MCP server must reject the operation unless the request includes an explicit approved flag or equivalent confirmed mechanism.

## Safe defaults

Default environment:

```env
DATAIKU_MODE=readonly
DATAIKU_ENABLE_WRITE_TOOLS=false
DATAIKU_ENABLE_EXECUTE_TOOLS=false
DATAIKU_ENABLE_ADMIN_TOOLS=false
DATAIKU_REDACT_SECRETS=true
```



---

# File: `TECHNICAL_ARCHITECTURE.md`


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



---

# File: `TEST_STRATEGY.md`


# Test Strategy

## Goals

Ensure the plugin is:

- safe.
- reliable.
- deterministic.
- testable without a real DSS instance.
- compatible with real DSS integration tests.
- resistant to secret leakage.

## Unit tests

Test:

- config loading.
- missing env variables.
- invalid mode.
- allowlist/blocklist parsing.
- permission guard.
- redaction.
- error normalization.
- Dataiku client wrapper.
- graph builder.
- file read limits.
- log truncation.
- RAG detection heuristics.
- recipe code review heuristics.

## MCP tool tests

Every MCP tool must have:

- input schema test.
- output schema test.
- permission test.
- success test.
- error case test.
- redaction test where relevant.

## Integration tests with mocks

Use mocked Dataiku API responses for:

- project listing.
- project summary.
- dataset schema.
- recipe details.
- Managed Folder listing.
- folder file read.
- scenario runs.
- logs.
- code envs.

## Optional real integration tests

Run only if:

```env
DATAIKU_INTEGRATION_TESTS=true
```

Real tests must be read-only by default.

## Security tests

Required:

- API key does not appear in logs.
- secrets are redacted from recipe code.
- secrets are redacted from logs.
- write tools fail in readonly mode.
- execute tools fail in readonly mode.
- blocked project is rejected.
- blocked tool is rejected.
- file too large is rejected.
- dataset preview is capped.

## Golden fixtures

Create fixtures for:

1. simple ETL project.
2. project with Python recipes.
3. project with Managed Folder on non-local backend.
4. project with malformed JSONL files.
5. failed scenario.
6. RAG pipeline project.
7. code env with missing package.
8. recipe with hardcoded secret.

## Acceptance test examples

- `dataiku_ping` returns reachable or normalized error.
- `dataiku_list_projects` returns list or permission error.
- `dataiku_get_project_summary` returns object counts.
- `dataiku_review_recipe_code` flags bad `get_path()` usage.
- `dataiku_managed_folder_doctor` warns on non-local path assumption.
- `dataiku_audit_rag_pipeline` produces a structured report.



---

# File: `TOOL_CATALOG.md`


# MCP Tool Catalog

This is the main implementation reference for Codex.

Every tool must have:

- stable name.
- description.
- input schema.
- output schema.
- permission level.
- safety rules.
- tests.

## Naming convention

All tools use the prefix:

```text
dataiku_
```

---

# A. Instance tools

## dataiku_ping

Check if the DSS instance is reachable.

### Inputs

None.

### Output

```json
{
  "reachable": true,
  "dss_url": "https://...",
  "version": "optional",
  "user": "optional"
}
```

### Permission

`read`

---

## dataiku_get_instance_info

Retrieve high-level instance metadata.

### Inputs

None.

### Output

```json
{
  "version": "optional",
  "node_type": "optional",
  "user": "optional",
  "features": []
}
```

### Permission

`read`

---

# B. Project tools

## dataiku_list_projects

List accessible projects.

### Inputs

```json
{
  "include_archived": false
}
```

### Output

```json
{
  "projects": [
    {
      "project_key": "PROJECT",
      "name": "Project name",
      "owner": "optional",
      "tags": [],
      "status": "optional"
    }
  ]
}
```

### Permission

`read`

---

## dataiku_get_project_summary

Get detailed project metadata.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Output

```json
{
  "project_key": "PROJECT",
  "name": "Project name",
  "datasets_count": 0,
  "recipes_count": 0,
  "managed_folders_count": 0,
  "scenarios_count": 0,
  "warnings": []
}
```

### Permission

`read`

---

## dataiku_generate_project_map

Generate a high-level project map.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Output

```json
{
  "nodes": [],
  "edges": [],
  "summary": "text",
  "warnings": []
}
```

### Permission

`read`

---

# C. Flow tools

## dataiku_get_flow_graph

Return the dependency graph of the project Flow.

### Inputs

```json
{
  "project_key": "PROJECT",
  "include_recipes": true,
  "include_folders": true,
  "include_models": true,
  "include_zones": true
}
```

### Output

```json
{
  "nodes": [],
  "edges": [],
  "topological_order": [],
  "orphan_nodes": [],
  "warnings": []
}
```

### Permission

`read`

---

## dataiku_analyze_flow_health

Analyze the Flow for structural issues.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Checks

- orphan datasets.
- recipes without outputs.
- unmanaged dependencies.
- duplicated logic.
- missing documentation.
- naming inconsistencies.
- missing Flow zones.
- unclear architecture boundaries.

### Permission

`read`

---

# D. Dataset tools

## dataiku_list_datasets

List datasets in a project.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Output

```json
{
  "datasets": [
    {
      "name": "dataset_name",
      "type": "optional",
      "connection": "optional",
      "schema_columns_count": 0,
      "tags": []
    }
  ]
}
```

### Permission

`read`

---

## dataiku_get_dataset_schema

Retrieve dataset schema.

### Inputs

```json
{
  "project_key": "PROJECT",
  "dataset_name": "dataset"
}
```

### Output

```json
{
  "columns": [
    {
      "name": "column",
      "type": "string",
      "meaning": "optional",
      "nullable": "optional"
    }
  ]
}
```

### Permission

`read`

---

## dataiku_preview_dataset

Preview first rows safely.

### Inputs

```json
{
  "project_key": "PROJECT",
  "dataset_name": "dataset",
  "limit": 20
}
```

### Safety

- default limit <= 20.
- hard max configured by `DATAIKU_MAX_PREVIEW_ROWS`.
- redact sensitive-looking fields.
- never dump full dataset.

### Permission

`read`

---

## dataiku_analyze_dataset_quality

Analyze dataset quality.

### Inputs

```json
{
  "project_key": "PROJECT",
  "dataset_name": "dataset",
  "sample_size": 1000
}
```

### Checks

- null rates.
- duplicate rows.
- type inconsistencies.
- suspicious columns.
- possible PII.
- schema drift.
- high-cardinality identifiers.
- constant columns.

### Permission

`read`

---

# E. Recipe tools

## dataiku_list_recipes

List project recipes.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Output

```json
{
  "recipes": [
    {
      "name": "recipe",
      "type": "python",
      "inputs": [],
      "outputs": [],
      "last_modified": "optional"
    }
  ]
}
```

### Permission

`read`

---

## dataiku_get_recipe_details

Retrieve recipe settings and code.

### Inputs

```json
{
  "project_key": "PROJECT",
  "recipe_name": "recipe"
}
```

### Output

```json
{
  "name": "recipe",
  "type": "python",
  "inputs": [],
  "outputs": [],
  "settings": {},
  "code": "optional"
}
```

### Permission

`read`

---

## dataiku_review_recipe_code

Review recipe code for quality and Dataiku-specific issues.

### Inputs

```json
{
  "project_key": "PROJECT",
  "recipe_name": "recipe"
}
```

### Checks

- bad use of `get_path()`.
- missing stream APIs.
- hardcoded paths.
- missing schema handling.
- memory-heavy dataframe loading.
- bad JSONL handling.
- bad exception handling.
- missing logging.
- embedding dimension mismatch.
- no vector normalization.
- fragile dependencies.

### Permission

`read`

---

## dataiku_update_recipe_code

Update recipe code.

### Inputs

```json
{
  "project_key": "PROJECT",
  "recipe_name": "recipe",
  "new_code": "...",
  "reason": "..."
}
```

### Permission

`write`

### Safety

- explicit approval required.
- create backup if possible.
- dry run summary required.
- never auto-update in readonly mode.

---

## dataiku_create_python_recipe

Create a Python recipe.

### Inputs

```json
{
  "project_key": "PROJECT",
  "recipe_name": "new_recipe",
  "inputs": [],
  "outputs": [],
  "code": "..."
}
```

### Permission

`write`

### Safety

- explicit approval required.
- validate inputs/outputs.
- do not overwrite existing recipe.

---

# F. Managed Folder tools

## dataiku_list_managed_folders

List Managed Folders.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Output

```json
{
  "folders": [
    {
      "folder_id": "id",
      "name": "folder",
      "type": "optional",
      "connection": "optional",
      "partitioning": "optional"
    }
  ]
}
```

### Permission

`read`

---

## dataiku_get_managed_folder_info

Retrieve Managed Folder metadata.

### Inputs

```json
{
  "project_key": "PROJECT",
  "folder_id": "folder"
}
```

### Output

```json
{
  "folder_id": "folder",
  "name": "folder",
  "backend_type": "optional",
  "local_path_available": false,
  "warnings": []
}
```

### Permission

`read`

---

## dataiku_list_folder_files

List files in a Managed Folder.

### Inputs

```json
{
  "project_key": "PROJECT",
  "folder_id": "folder",
  "path": "/",
  "recursive": false,
  "limit": 100
}
```

### Output

```json
{
  "files": [
    {
      "path": "file.jsonl",
      "size": 123,
      "last_modified": "optional"
    }
  ],
  "truncated": false
}
```

### Permission

`read`

---

## dataiku_read_folder_file

Read a file through the proper Dataiku API.

### Inputs

```json
{
  "project_key": "PROJECT",
  "folder_id": "folder",
  "file_path": "file.jsonl",
  "max_bytes": 500000
}
```

### Safety

- default max bytes.
- reject huge files unless explicit override exists.
- redact secrets.
- detect binary content.
- do not assume local path.

### Permission

`read`

---

## dataiku_managed_folder_doctor

Detect common Managed Folder issues.

### Inputs

```json
{
  "project_key": "PROJECT",
  "folder_id": "optional"
}
```

### Checks

- `get_path()` used on non-local folder.
- encoding errors.
- JSONL malformed lines.
- oversized files.
- missing partitions.
- inaccessible files.
- folder id/name confusion.
- full-file memory reads.

### Permission

`read`

---

## dataiku_upload_file_to_folder

Upload a file to a Managed Folder.

### Inputs

```json
{
  "project_key": "PROJECT",
  "folder_id": "folder",
  "file_path": "target/path.txt",
  "content_base64": "..."
}
```

### Permission

`write`

### Safety

- explicit approval required.
- size limits.
- do not overwrite unless explicitly allowed.

---

## dataiku_create_managed_folder

Create a Managed Folder.

### Inputs

```json
{
  "project_key": "PROJECT",
  "folder_name": "folder",
  "connection": "optional"
}
```

### Permission

`write`

---

# G. Scenario / job / log tools

## dataiku_list_scenarios

List project scenarios.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Output

```json
{
  "scenarios": [
    {
      "scenario_id": "id",
      "name": "scenario",
      "active": true,
      "trigger_type": "optional"
    }
  ]
}
```

### Permission

`read`

---

## dataiku_get_scenario_runs

Get recent scenario runs.

### Inputs

```json
{
  "project_key": "PROJECT",
  "scenario_id": "scenario",
  "limit": 10
}
```

### Output

```json
{
  "runs": [
    {
      "run_id": "id",
      "outcome": "FAILED",
      "start_time": "optional",
      "duration": "optional",
      "failed_steps": []
    }
  ]
}
```

### Permission

`read`

---

## dataiku_run_scenario

Run a scenario.

### Inputs

```json
{
  "project_key": "PROJECT",
  "scenario_id": "scenario"
}
```

### Permission

`execute`

### Safety

- explicit approval required.
- show dry-run summary.
- respect allowlist.

---

## dataiku_get_job_logs

Retrieve logs for a job or scenario run.

### Inputs

```json
{
  "project_key": "PROJECT",
  "job_id": "optional",
  "run_id": "optional",
  "max_lines": 1000
}
```

### Output

```json
{
  "logs": "...",
  "detected_errors": [],
  "probable_root_cause": "optional"
}
```

### Permission

`read`

---

## dataiku_explain_failure

Explain a scenario/job failure.

### Inputs

```json
{
  "project_key": "PROJECT",
  "job_id": "optional",
  "run_id": "optional"
}
```

### Output

```json
{
  "symptoms": [],
  "root_causes": [],
  "evidence": [],
  "recommended_fixes": []
}
```

### Permission

`read`

---

# H. Code environment tools

## dataiku_list_code_envs

List code environments.

### Inputs

None.

### Output

```json
{
  "code_envs": [
    {
      "name": "env",
      "language": "python",
      "python_version": "optional",
      "packages_count": 0
    }
  ]
}
```

### Permission

`admin` or `read` if available to the user.

---

## dataiku_get_code_env_details

Retrieve code env settings.

### Inputs

```json
{
  "env_name": "code-env"
}
```

### Output

```json
{
  "name": "code-env",
  "language": "python",
  "python_version": "3.10",
  "packages": [],
  "settings": {}
}
```

### Permission

`admin` or `read` if available to the user.

---

## dataiku_code_env_doctor

Analyze code environment issues.

### Inputs

```json
{
  "env_name": "code-env"
}
```

### Checks

- missing packages.
- incompatible versions.
- package installed in wrong env.
- offline install problems.
- native dependency issues.
- Python version mismatch.
- local model path issues.

### Permission

`read`

---

# I. RAG / LLM pipeline tools

## dataiku_detect_rag_pipeline

Detect whether a project contains a RAG pipeline.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Signals

- embedding model usage.
- vector store usage.
- chunking code.
- LLM connector usage.
- FAISS / Weaviate / Chroma / Elasticsearch.
- JSONL chunks.
- metadata fields.
- reranker usage.

### Permission

`read`

---

## dataiku_audit_rag_pipeline

Audit RAG design.

### Inputs

```json
{
  "project_key": "PROJECT",
  "deep": false
}
```

### Checks

- chunk size.
- overlap.
- metadata quality.
- vector index dimension.
- embedding normalization.
- reranker usage.
- top-k.
- context window usage.
- source citation.
- hallucination risk.
- prompt injection risk.
- evaluation strategy.

### Permission

`read`

---

## dataiku_compare_chunking_strategies

Compare possible chunking strategies.

### Inputs

```json
{
  "project_key": "PROJECT",
  "source_recipe_or_folder": "optional",
  "strategies": [
    {
      "chunk_size": 800,
      "overlap": 100
    },
    {
      "chunk_size": 2500,
      "overlap": 300
    }
  ]
}
```

### Output

```json
{
  "comparison": [],
  "recommendation": "text",
  "risks": []
}
```

### Permission

`read`

---

## dataiku_generate_rag_evaluation_plan

Generate evaluation plan.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Metrics

- Recall@K.
- Precision@N.
- MRR.
- nDCG.
- faithfulness.
- answer relevance.
- source citation accuracy.

### Permission

`read`

---

# J. Documentation tools

## dataiku_generate_project_readme

Generate README for a Dataiku project.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Output

```json
{
  "markdown": "# Project README..."
}
```

### Permission

`read`

---

## dataiku_generate_flow_documentation

Generate Flow documentation.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Output

```json
{
  "markdown": "# Flow documentation..."
}
```

### Permission

`read`

---

## dataiku_generate_troubleshooting_report

Generate a debugging report.

### Inputs

```json
{
  "project_key": "PROJECT",
  "focus": "optional"
}
```

### Output

```json
{
  "markdown": "# Troubleshooting report..."
}
```

### Permission

`read`

---

## dataiku_generate_rag_audit_report

Generate a RAG audit report.

### Inputs

```json
{
  "project_key": "PROJECT"
}
```

### Output

```json
{
  "markdown": "# RAG audit report..."
}
```

### Permission

`read`

---

# K. Write action tools

## dataiku_create_project_documentation

Write generated documentation into the project if supported.

### Inputs

```json
{
  "project_key": "PROJECT",
  "target": "wiki_or_library_path",
  "markdown": "..."
}
```

### Permission

`write`

### Safety

- explicit approval required.
- do not overwrite unless explicitly allowed.
- keep backup if possible.

---

# L. Future tools

Future possible tools:

- `dataiku_list_plugins`
- `dataiku_list_connections`
- `dataiku_search_project_objects`
- `dataiku_find_objects_by_tag`
- `dataiku_export_project_summary`
- `dataiku_generate_mermaid_flow_diagram`
- `dataiku_generate_c4_context_diagram`
- `dataiku_detect_pii_in_dataset_preview`
- `dataiku_detect_secrets_in_recipes`
- `dataiku_prepare_offline_package_install_plan`



---

# File: `TOOL_IMPLEMENTATION_ORDER.md`


# Tool Implementation Order

## Phase 1 — Foundation

1. config loader.
2. Dataiku client wrapper.
3. permission guard.
4. redaction utility.
5. error normalizer.
6. audit logger.
7. MCP server bootstrap.
8. CLI entrypoint.
9. tests for all foundations.

## Phase 2 — Read-only core

1. `dataiku_ping`
2. `dataiku_get_instance_info`
3. `dataiku_list_projects`
4. `dataiku_get_project_summary`
5. `dataiku_list_datasets`
6. `dataiku_get_dataset_schema`
7. `dataiku_list_recipes`
8. `dataiku_get_recipe_details`
9. `dataiku_list_managed_folders`
10. `dataiku_get_managed_folder_info`
11. `dataiku_list_folder_files`

## Phase 3 — Analysis tools

1. `dataiku_generate_project_map`
2. `dataiku_get_flow_graph`
3. `dataiku_analyze_flow_health`
4. `dataiku_review_recipe_code`
5. `dataiku_managed_folder_doctor`
6. `dataiku_code_env_doctor`
7. `dataiku_detect_rag_pipeline`
8. `dataiku_audit_rag_pipeline`

## Phase 4 — Logs and scenarios

1. `dataiku_list_scenarios`
2. `dataiku_get_scenario_runs`
3. `dataiku_get_job_logs`
4. `dataiku_explain_failure`

## Phase 5 — Documentation

1. `dataiku_generate_project_readme`
2. `dataiku_generate_flow_documentation`
3. `dataiku_generate_troubleshooting_report`
4. `dataiku_generate_rag_audit_report`

## Phase 6 — Write tools

Only after permission system, approval flow and tests are complete:

1. `dataiku_update_recipe_code`
2. `dataiku_create_python_recipe`
3. `dataiku_create_managed_folder`
4. `dataiku_upload_file_to_folder`
5. `dataiku_run_scenario`
6. `dataiku_create_project_documentation`

## Phase 7 — Enterprise features

1. HTTP MCP transport.
2. centralized audit logging.
3. OAuth/Bearer auth.
4. per-tool policies.
5. deployment guide.
6. production monitoring.



---

# File: `codex_prompts/00_bootstrap_project.md`


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



---

# File: `codex_prompts/01_generate_architecture.md`


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



---

# File: `codex_prompts/02_generate_mcp_server.md`


# Codex Prompt 02 — Generate MCP Server

Implement the MCP server.

Requirements:

- Support STDIO transport.
- Register tools from `TOOL_CATALOG.md`.
- Start with read-only tools.
- Add permission checks before each tool.
- Add redaction before returning output.
- Add structured logging.
- Add tests for all tools.

Do not implement destructive operations yet.

Initial tools:

1. `dataiku_ping`
2. `dataiku_get_instance_info`
3. `dataiku_list_projects`
4. `dataiku_get_project_summary`
5. `dataiku_list_datasets`
6. `dataiku_get_dataset_schema`
7. `dataiku_list_recipes`
8. `dataiku_get_recipe_details`
9. `dataiku_list_managed_folders`
10. `dataiku_list_folder_files`



---

# File: `codex_prompts/03_generate_skills.md`


# Codex Prompt 03 — Generate Skills

Generate Codex skill folders based on the skill specifications.

For each skill:

- create `SKILL.md`.
- include when to use it.
- include tool usage strategy.
- include safety rules.
- include expected report format.
- include examples of user requests.

Skills:

- `dataiku-project-auditor`
- `dataiku-managed-folder-debugger`
- `dataiku-rag-pipeline-auditor`
- `dataiku-recipe-reviewer`
- `dataiku-flow-architect`
- `dataiku-scenario-debugger`
- `dataiku-code-env-doctor`

Do not include secrets or environment-specific data.



---

# File: `codex_prompts/04_generate_tests.md`


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



---

# File: `codex_prompts/05_security_review.md`


# Codex Prompt 05 — Security Review

Perform a security review of the whole repository.

Check:

- no secrets in code.
- no credentials in logs.
- no unsafe file reads.
- no write operation without permission.
- no execute operation without permission.
- no destructive operation without confirmation.
- no `sensitive_info=True` by default.
- safe defaults in config.
- dataset previews are limited.
- file reads are limited.
- logs are limited.
- redaction tests exist.
- permission tests exist.

Create a `SECURITY_REVIEW_REPORT.md` with:

- findings.
- severity.
- affected files.
- recommended fixes.
- fixed/not fixed status.



---

# File: `codex_prompts/06_final_packaging.md`


# Codex Prompt 06 — Final Packaging

Prepare the plugin for distribution.

Check:

- `plugin.json` valid.
- MCP JSON valid.
- skills valid.
- README complete.
- INSTALLATION_GUIDE complete.
- examples complete.
- tests passing.
- release notes generated.
- safe defaults.
- no secrets.
- version set.

Create:

- `CHANGELOG.md`
- `RELEASE_NOTES.md`
- `PACKAGING_CHECKLIST.md`

Do not publish automatically.



---

# File: `codex_prompts/07_implement_rag_auditor.md`


# Codex Prompt 07 — Implement RAG Auditor

Implement RAG detection and audit tools.

Read:

- `FUNCTIONAL_SPEC.md`
- `TOOL_CATALOG.md`
- `skills/dataiku-rag-pipeline-auditor/SKILL.md`

Implement:

- `dataiku_detect_rag_pipeline`
- `dataiku_audit_rag_pipeline`
- `dataiku_generate_rag_evaluation_plan`
- `dataiku_generate_rag_audit_report`

Detection signals:

- FAISS.
- Weaviate.
- Chroma.
- vector store.
- embeddings.
- chunking.
- RecursiveCharacterTextSplitter.
- reranker.
- BM25.
- metadata.
- LLM connector.
- prompt.
- top_k.
- cosine similarity.
- normalization.

Output must include:

- detected components.
- evidence.
- risks.
- recommendations.
- evaluation plan.

Add tests with fake recipe code.



---

# File: `codex_prompts/08_implement_managed_folder_doctor.md`


# Codex Prompt 08 — Implement Managed Folder Doctor

Implement Managed Folder analysis tools.

Read:

- `TOOL_CATALOG.md`
- `skills/dataiku-managed-folder-debugger/SKILL.md`
- `docs/decisions/ADR-003-managed-folders-stream-first.md`

Implement:

- `dataiku_list_managed_folders`
- `dataiku_get_managed_folder_info`
- `dataiku_list_folder_files`
- `dataiku_read_folder_file`
- `dataiku_managed_folder_doctor`

Critical rule:

Do not assume Managed Folders are local filesystem paths.

Detect:

- `get_path()` usage.
- hardcoded paths.
- missing stream APIs.
- malformed JSONL.
- encoding errors.
- file size risks.
- binary files.

Add unit tests and mocked integration tests.



---

# File: `docs/decisions/ADR-001-plugin-plus-mcp.md`


# ADR-001 — Use Codex Plugin + MCP Server Architecture

## Status

Accepted.

## Context

The project needs to provide both behavior guidance to Codex and live interaction with Dataiku DSS.

Codex skills are useful for domain-specific reasoning, but they cannot directly access a Dataiku instance.

An MCP server can expose Dataiku API capabilities as structured tools.

## Decision

Use a Codex plugin containing:

- skills.
- MCP server configuration.
- documentation.
- optional hooks.

Use a Python MCP server to expose Dataiku DSS operations.

## Consequences

Positive:

- clean separation between reasoning and tool execution.
- testable Dataiku integration.
- security enforced server-side.
- extensible tool catalog.

Negative:

- more complex than a simple script.
- requires careful permission model.
- requires MCP packaging and config.



---

# File: `docs/decisions/ADR-002-readonly-by-default.md`


# ADR-002 — Read-only by Default

## Status

Accepted.

## Context

Dataiku DSS projects can contain production workflows, sensitive data, credentials and business-critical pipelines.

An AI assistant must not modify or execute workflows accidentally.

## Decision

The plugin is read-only by default.

Write and execute operations require:

- explicit mode activation.
- enable flags.
- explicit user approval.
- server-side permission check.

## Consequences

Positive:

- safer adoption.
- easier enterprise acceptance.
- lower risk during testing.

Negative:

- write workflows require extra setup.
- users may need to approve actions manually.



---

# File: `docs/decisions/ADR-003-managed-folders-stream-first.md`


# ADR-003 — Managed Folders Must Be Stream-First

## Status

Accepted.

## Context

Dataiku Managed Folders may be backed by local storage, S3, HDFS, GCS, FTP or other backends.

Local filesystem paths are not always available.

## Decision

The plugin must not assume local filesystem access for Managed Folders.

It should prefer file listing and stream-based read/write APIs.

## Consequences

Positive:

- works across backends.
- avoids common Dataiku bugs.
- safer for large files.

Negative:

- file access code is slightly more complex.
- some local-only optimizations cannot be assumed.



---

# File: `docs/diagrams/ARCHITECTURE.md`


# Architecture Diagrams

## High-level architecture

```mermaid
flowchart TD
    U[User] --> C[Codex]
    C --> S[Codex Skills]
    C --> MCP[MCP Server]
    MCP --> P[Permission Guard]
    P --> A[Dataiku API Adapter]
    A --> DSS[Dataiku DSS]
    A --> R[Result Normalizer]
    R --> X[Redaction Layer]
    X --> C
```

## Tool call flow

```mermaid
sequenceDiagram
    participant User
    participant Codex
    participant Skill
    participant MCP
    participant Guard
    participant Dataiku
    participant Redactor

    User->>Codex: Ask Dataiku question
    Codex->>Skill: Select relevant skill
    Codex->>MCP: Call tool
    MCP->>Guard: Check permission
    Guard-->>MCP: Allowed
    MCP->>Dataiku: API call
    Dataiku-->>MCP: Raw result
    MCP->>Redactor: Redact output
    Redactor-->>MCP: Safe output
    MCP-->>Codex: Tool result
    Codex-->>User: Explanation/report
```

## Permission model

```mermaid
flowchart LR
    Tool[Tool Request] --> Mode{Mode}
    Mode -->|readonly| Read[Read allowed]
    Mode -->|write| Write[Write requires approval]
    Mode -->|execute| Exec[Execute requires approval]
    Mode -->|admin| Admin[Admin requires explicit enable]
    Write --> Approval{Approved?}
    Exec --> Approval
    Approval -->|yes| Run[Run tool]
    Approval -->|no| Reject[Reject]
```

## RAG audit workflow

```mermaid
flowchart TD
    Project[Dataiku Project] --> Recipes[Recipes]
    Recipes --> Ingestion[Ingestion]
    Recipes --> Chunking[Chunking]
    Recipes --> Embeddings[Embeddings]
    Recipes --> VectorStore[Vector Store]
    Recipes --> Retrieval[Retrieval]
    Recipes --> Generation[LLM Generation]
    Ingestion --> Audit[RAG Audit Report]
    Chunking --> Audit
    Embeddings --> Audit
    VectorStore --> Audit
    Retrieval --> Audit
    Generation --> Audit
```



---

# File: `docs/examples/EXAMPLE_REPORTS.md`


# Example Reports

## Project audit report

```md
# Dataiku Project Audit — PROJECT_KEY

## Summary
The project contains 18 datasets, 12 recipes, 3 Managed Folders and 4 scenarios.

## Flow architecture
The Flow appears organized around ingestion, preprocessing, embedding generation and retrieval.

## Main risks
1. Several recipes use hardcoded paths.
2. Managed Folder access may fail on non-local backends.
3. RAG metadata is inconsistent.
4. No explicit RAG evaluation pipeline was detected.

## Recommendations
1. Replace local path access with stream APIs.
2. Normalize metadata fields.
3. Add Recall@K/MRR/nDCG evaluation.
4. Add project README and scenario runbook.
```

## Managed Folder debug report

```md
# Managed Folder Debug Report

## Symptom
Recipe `build_chunks` fails when reading files from folder `RAW_DOCS`.

## Evidence
The recipe uses `folder.get_path()` and then `open(path)`.

## Root cause
This pattern fails when the Managed Folder is not backed by a local filesystem.

## Fix
Use Dataiku folder stream APIs and process files line by line.
```

## RAG audit report

```md
# RAG Audit Report

## Detected components
- ingestion recipes.
- chunking recipe.
- embedding generation.
- FAISS index.
- reranking not detected.

## Main issues
- chunk size is not justified.
- metadata lacks document hierarchy.
- no embedding dimension validation.
- no reranker.
- no evaluation dataset.

## Recommended plan
1. Add metadata normalization.
2. Validate embedding dimension at index load.
3. Add reranking.
4. Build evaluation query set.
5. Track Recall@K and MRR.
```



---

# File: `docs/prompts/MASTER_CODEX_PROMPT.md`


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



---

# File: `docs/use_cases/USE_CASES.md`


# Use Cases

## UC-001 — Audit a Dataiku project

As an AI engineer, I want Codex to inspect a Dataiku project and explain its Flow, so that I can understand the architecture quickly.

## UC-002 — Debug a Managed Folder error

As a Dataiku developer, I want Codex to detect wrong Managed Folder usage, so that I can fix file access issues across local/S3/HDFS backends.

## UC-003 — Review Python recipes

As a developer, I want Codex to review Python recipes for Dataiku-specific bugs, so that I can improve reliability and maintainability.

## UC-004 — Audit a RAG pipeline

As a RAG engineer, I want Codex to inspect ingestion, chunking, metadata, embeddings and retrieval, so that I can identify weaknesses.

## UC-005 — Debug failed scenarios

As an MLOps engineer, I want Codex to inspect scenario runs and logs, so that I can understand failures faster.

## UC-006 — Generate documentation

As a project owner, I want Codex to generate README/Flow/RAG documentation, so that the project is easier to maintain.

## UC-007 — Diagnose code environment issues

As a data scientist, I want Codex to inspect code env dependencies, so that import/runtime errors can be fixed.

## UC-008 — Apply controlled fixes

As a developer, I want Codex to update recipes or create folders only after approval, so that changes are safe and traceable.



---

# File: `docs/user_stories/USER_STORIES.md`


# User Stories

## Project audit

As an AI engineer, I want to summarize a Dataiku project so that I can understand its purpose, structure and technical risks.

Acceptance criteria:

- project objects are listed.
- Flow dependencies are summarized.
- risks are identified.
- recommendations are produced.

## Managed Folder debugging

As a developer, I want to inspect Managed Folder usage so that I can detect path and stream bugs.

Acceptance criteria:

- folders are listed.
- file listing works.
- recipes using folders are inspected.
- bad `get_path()` usage is flagged.

## RAG audit

As a RAG engineer, I want to inspect a Dataiku RAG pipeline so that I can improve retrieval and answer quality.

Acceptance criteria:

- RAG signals are detected.
- chunking and metadata are reviewed.
- vector store and embeddings are reviewed.
- evaluation plan is generated.

## Scenario failure

As an MLOps engineer, I want to explain a failed scenario so that I can fix automation issues.

Acceptance criteria:

- recent runs are retrieved.
- logs are summarized.
- root cause is proposed.
- fix is suggested.

## Documentation generation

As a project lead, I want to generate documentation from the project so that onboarding is easier.

Acceptance criteria:

- README generated.
- Flow documentation generated.
- RAG audit documentation generated when applicable.

## Controlled write

As a user, I want write operations to require approval so that Codex does not accidentally modify Dataiku projects.

Acceptance criteria:

- write tools fail in readonly mode.
- write tools require approval.
- dry-run summary is shown.



---

# File: `docs/workflows/WORKFLOWS.md`


# Workflows

## Workflow 1 — Full project audit

1. User provides project key.
2. Codex calls `dataiku_get_project_summary`.
3. Codex calls `dataiku_get_flow_graph`.
4. Codex calls `dataiku_analyze_flow_health`.
5. Codex inspects datasets, recipes, Managed Folders and scenarios.
6. Codex produces audit report.

## Workflow 2 — Managed Folder debugging

1. User describes folder/file error.
2. Codex lists Managed Folders.
3. Codex inspects folder metadata.
4. Codex lists files.
5. Codex inspects relevant recipes.
6. Codex detects path/stream/encoding issues.
7. Codex proposes fix.

## Workflow 3 — RAG audit

1. Codex detects RAG pipeline.
2. Codex inspects ingestion recipes.
3. Codex inspects chunking logic.
4. Codex inspects metadata.
5. Codex detects embedding/vector store usage.
6. Codex checks retrieval/reranking.
7. Codex generates evaluation plan.

## Workflow 4 — Scenario failure

1. User gives project key and scenario ID.
2. Codex retrieves recent scenario runs.
3. Codex reads relevant logs.
4. Codex identifies error class.
5. Codex inspects linked recipe/dataset/folder if needed.
6. Codex proposes fix and retry strategy.

## Workflow 5 — Controlled recipe update

1. Codex reviews recipe.
2. Codex proposes patch.
3. Codex shows dry-run summary.
4. User approves.
5. MCP server verifies write mode and approval.
6. Tool applies update.
7. Audit log records action.



---

# File: `examples/sample_env.example`


```env
DATAIKU_DSS_URL=https://dss.company.com
DATAIKU_API_KEY=replace-me
DATAIKU_MODE=readonly
DATAIKU_PROJECT_ALLOWLIST=
DATAIKU_PROJECT_BLOCKLIST=
DATAIKU_MAX_PREVIEW_ROWS=20
DATAIKU_MAX_FILE_READ_BYTES=500000
DATAIKU_MAX_LOG_LINES=1000
DATAIKU_MAX_LISTED_FILES=1000
DATAIKU_REDACT_SECRETS=true
DATAIKU_ENABLE_WRITE_TOOLS=false
DATAIKU_ENABLE_EXECUTE_TOOLS=false
DATAIKU_ENABLE_ADMIN_TOOLS=false
DATAIKU_DEBUG=false

```



---

# File: `examples/sample_mcp.json`


```json
{
  "mcp_servers": {
    "dataiku-dss": {
      "command": "dataiku-codex-mcp",
      "args": [
        "--stdio"
      ],
      "env": {
        "DATAIKU_DSS_URL": "${DATAIKU_DSS_URL}",
        "DATAIKU_API_KEY": "${DATAIKU_API_KEY}",
        "DATAIKU_MODE": "readonly"
      }
    }
  }
}

```



---

# File: `examples/sample_plugin.json`


```json
{
  "name": "dataiku-dss-copilot",
  "version": "1.0.0",
  "description": "Codex plugin for inspecting, auditing, debugging and improving Dataiku DSS projects.",
  "author": "Lucien Lachaud",
  "license": "Apache-2.0",
  "keywords": [
    "dataiku",
    "dss",
    "codex",
    "mcp",
    "rag",
    "mlops"
  ],
  "skills": [
    "./skills/dataiku-project-auditor",
    "./skills/dataiku-managed-folder-debugger",
    "./skills/dataiku-rag-pipeline-auditor",
    "./skills/dataiku-recipe-reviewer",
    "./skills/dataiku-flow-architect",
    "./skills/dataiku-scenario-debugger",
    "./skills/dataiku-code-env-doctor"
  ],
  "mcpServers": "./mcp/dataiku.mcp.json",
  "hooks": "./hooks/hooks.json",
  "interface": {
    "displayName": "Dataiku DSS Copilot",
    "shortDescription": "Inspect, audit and debug Dataiku DSS projects from Codex.",
    "longDescription": "A Codex plugin that connects to Dataiku DSS through MCP and provides expert skills for Flow analysis, recipe debugging, Managed Folder inspection, RAG pipeline auditing and documentation generation.",
    "developerName": "Lucien Lachaud",
    "category": "Developer Tools",
    "capabilities": [
      "Dataiku DSS",
      "MCP",
      "RAG",
      "MLOps",
      "Project Audit"
    ]
  }
}

```



---

# File: `examples/sample_prompts.md`


# Sample Prompts

## Bootstrap

Use `codex_prompts/00_bootstrap_project.md`.

## Implement architecture

Use `codex_prompts/01_generate_architecture.md`.

## Implement MCP server

Use `codex_prompts/02_generate_mcp_server.md`.

## Generate skills

Use `codex_prompts/03_generate_skills.md`.

## Generate tests

Use `codex_prompts/04_generate_tests.md`.

## Security review

Use `codex_prompts/05_security_review.md`.

## Final packaging

Use `codex_prompts/06_final_packaging.md`.



---

# File: `examples/sample_user_requests.md`


# Example User Requests

## Project audit

Analyze my Dataiku project PROJECT_KEY and explain the Flow architecture.

## Managed folder debugging

Inspect the Managed Folders in PROJECT_KEY and tell me if any Python recipe incorrectly uses get_path().

## RAG audit

Audit the RAG pipeline in PROJECT_KEY. Check chunking, metadata, embeddings, vector store and reranking.

## Scenario debugging

Find why the latest run of scenario SCENARIO_ID failed.

## Documentation

Generate a README for project PROJECT_KEY.

## Code environment

Analyze the code environment used by my Python recipes and detect missing packages.

## Recipe review

Review recipe RECIPE_NAME in project PROJECT_KEY and propose improvements.

## Controlled write

Prepare a patch for recipe RECIPE_NAME, but do not apply it until I approve.



---

# File: `hooks/hooks.json`


```json
{
  "hooks": [],
  "notes": "Hooks are optional. Keep security enforcement in the MCP server."
}

```



---

# File: `mcp/PROMPTS_SPEC.md`


# MCP Prompts Specification

MCP prompts can provide reusable workflows for Codex.

## Prompt: audit_dataiku_project

Inputs:

- `project_key`

Behavior:

1. list project objects.
2. build Flow graph.
3. inspect recipes.
4. inspect Managed Folders.
5. detect RAG pipeline if present.
6. generate report.

## Prompt: debug_managed_folder_issue

Inputs:

- `project_key`
- optional `folder_id`
- optional `recipe_name`

Behavior:

1. inspect folder metadata.
2. inspect file list.
3. inspect recipe code.
4. detect path/stream issues.
5. propose fix.

## Prompt: audit_rag_pipeline

Inputs:

- `project_key`

Behavior:

1. detect RAG signals.
2. inspect ingestion.
3. inspect chunking.
4. inspect metadata.
5. inspect embeddings/vector store.
6. inspect retrieval/reranking.
7. produce evaluation plan.

## Prompt: explain_latest_scenario_failure

Inputs:

- `project_key`
- `scenario_id`

Behavior:

1. inspect recent runs.
2. select latest failure.
3. read logs.
4. identify root cause.
5. suggest fix.



---

# File: `mcp/README.md`


# MCP Documentation

This folder contains MCP-specific documentation for the Dataiku DSS Copilot for Codex project.

Read in this order:

1. `SERVER_DESIGN.md`
2. `TOOLS_SPEC.md`
3. `RESOURCES_SPEC.md`
4. `PROMPTS_SPEC.md`
5. `SAFETY_RULES.md`



---

# File: `mcp/RESOURCES_SPEC.md`


# MCP Resources Specification

MCP resources may expose read-only references to Dataiku objects.

## Possible resources

```text
dataiku://projects
dataiku://projects/{project_key}
dataiku://projects/{project_key}/flow
dataiku://projects/{project_key}/datasets
dataiku://projects/{project_key}/recipes
dataiku://projects/{project_key}/folders
dataiku://projects/{project_key}/scenarios
```

## Resource rules

- resources are read-only.
- resources must respect project allowlist/blocklist.
- resources must not expose secrets.
- resources must not return full datasets.
- resources should return summaries, not heavy content.

## Example

```text
dataiku://projects/PROJECT_KEY/flow
```

returns:

```json
{
  "project_key": "PROJECT_KEY",
  "nodes": [],
  "edges": []
}
```



---

# File: `mcp/SAFETY_RULES.md`


# MCP Safety Rules

## Global rules

- Read-only by default.
- Reject write tools unless write mode is enabled.
- Reject execute tools unless execute mode is enabled.
- Reject admin tools unless admin mode is enabled.
- Enforce project allowlist/blocklist.
- Enforce tool allowlist/blocklist.
- Redact secrets before returning outputs.
- Limit dataset previews.
- Limit file reads.
- Limit logs.

## Managed Folder rules

- Do not assume local filesystem access.
- Prefer stream APIs.
- Refuse huge reads by default.
- Detect binary files.
- Redact file contents.

## Recipe rules

- Redact hardcoded secrets.
- Do not run recipe code.
- Do not update recipe code without explicit approval.
- Create backup/dry-run if possible.

## Scenario rules

- Do not run scenarios in readonly mode.
- Running scenarios requires explicit approval.
- Explain potential impact before execution.

## Dataset rules

- No full export by default.
- Preview only small sample.
- Redact sensitive columns.
- Warn about PII risk.

## Admin rules

- Do not return credentials.
- Do not call sensitive info APIs unless explicitly allowed.
- Never expose connection passwords.



---

# File: `mcp/SERVER_DESIGN.md`


# MCP Server Design

## Server purpose

The MCP server exposes Dataiku DSS capabilities as structured tools for Codex.

## Responsibilities

- connect to DSS.
- register tools.
- validate tool inputs.
- enforce permissions.
- call Dataiku APIs.
- normalize results.
- redact sensitive data.
- normalize errors.
- log audit events.

## Transports

### STDIO

Default.

```bash
dataiku-codex-mcp --stdio
```

### Streamable HTTP

Future enterprise mode.

```bash
dataiku-codex-mcp --http --host 0.0.0.0 --port 8080
```

## Tool registration pattern

Each tool module should expose a function:

```python
def register_tools(server: MCPServer, context: AppContext) -> None:
    ...
```

## App context

The server should create an `AppContext` containing:

- settings.
- Dataiku client.
- permission guard.
- redactor.
- audit logger.

## Output wrapper

Every tool should return:

```json
{
  "ok": true,
  "data": {},
  "warnings": [],
  "metadata": {}
}
```

or:

```json
{
  "ok": false,
  "error": {}
}
```



---

# File: `mcp/TOOLS_SPEC.md`


# MCP Tools Specification

The canonical source for all tools is `../TOOL_CATALOG.md`.

## Implementation requirements

For each tool, implement:

1. Pydantic input model.
2. tool handler function.
3. permission check.
4. Dataiku adapter call.
5. output normalization.
6. redaction.
7. tests.

## Tool module split

```text
tools/
├── instance.py
├── projects.py
├── flow.py
├── datasets.py
├── recipes.py
├── managed_folders.py
├── scenarios.py
├── code_envs.py
├── rag.py
├── documentation.py
└── write_actions.py
```

## Tool handler pattern

```python
async def dataiku_list_projects(input: ListProjectsInput, ctx: AppContext) -> ToolResult:
    ctx.permissions.require("dataiku_list_projects", level="read")
    projects = ctx.dataiku.list_projects(include_archived=input.include_archived)
    return ok({"projects": projects})
```

## Tests

Every tool must have:

- success test.
- Dataiku API error test.
- permission denied test.
- redaction test if relevant.



---

# File: `mcp/dataiku.mcp.json`


```json
{
  "mcp_servers": {
    "dataiku-dss": {
      "command": "dataiku-codex-mcp",
      "args": [
        "--stdio"
      ],
      "env": {
        "DATAIKU_DSS_URL": "${DATAIKU_DSS_URL}",
        "DATAIKU_API_KEY": "${DATAIKU_API_KEY}",
        "DATAIKU_MODE": "readonly"
      }
    }
  }
}

```



---

# File: `plugin.json`


```json
{
  "name": "dataiku-dss-copilot",
  "version": "1.0.0",
  "description": "Codex plugin for inspecting, auditing, debugging and improving Dataiku DSS projects.",
  "author": "Lucien Lachaud",
  "license": "Apache-2.0",
  "keywords": [
    "dataiku",
    "dss",
    "codex",
    "mcp",
    "rag",
    "mlops"
  ],
  "skills": [
    "./skills/dataiku-project-auditor",
    "./skills/dataiku-managed-folder-debugger",
    "./skills/dataiku-rag-pipeline-auditor",
    "./skills/dataiku-recipe-reviewer",
    "./skills/dataiku-flow-architect",
    "./skills/dataiku-scenario-debugger",
    "./skills/dataiku-code-env-doctor"
  ],
  "mcpServers": "./mcp/dataiku.mcp.json",
  "hooks": "./hooks/hooks.json",
  "interface": {
    "displayName": "Dataiku DSS Copilot",
    "shortDescription": "Inspect, audit and debug Dataiku DSS projects from Codex.",
    "longDescription": "A Codex plugin that connects to Dataiku DSS through MCP and provides expert skills for Flow analysis, recipe debugging, Managed Folder inspection, RAG pipeline auditing and documentation generation.",
    "developerName": "Lucien Lachaud",
    "category": "Developer Tools",
    "capabilities": [
      "Dataiku DSS",
      "MCP",
      "RAG",
      "MLOps",
      "Project Audit"
    ]
  }
}

```



---

# File: `skills/dataiku-code-env-doctor/SKILL.md`


# Dataiku Code Environment Doctor

Use this skill for Python/R package, dependency, offline install, native library, model loading or code environment problems.

## Checks

- missing packages.
- incompatible versions.
- wrong Python version.
- native dependency errors.
- package installed outside code env.
- offline wheel issues.
- Hugging Face/local model path issues.
- CUDA/GPU package mismatch.
- imports failing in recipes.

## Tool strategy

Use:

1. `dataiku_list_code_envs`
2. `dataiku_get_code_env_details`
3. `dataiku_code_env_doctor`
4. `dataiku_get_recipe_details` if linked to a recipe failure.
5. `dataiku_get_job_logs` if linked to logs.

## Expected report format

```md
# Code Environment Diagnosis

## Environment
...

## Symptoms
...

## Dependency issues
...

## Recommended installation/fix
...

## Reproducibility recommendations
...
```



---

# File: `skills/dataiku-flow-architect/SKILL.md`


# Dataiku Flow Architect

Use this skill to reason about the architecture of a Dataiku Flow.

## Tasks

- build dependency graph.
- detect unnecessary complexity.
- suggest modularization.
- identify missing zones.
- separate ingestion, transformation, ML, RAG and reporting.
- recommend naming conventions.
- identify technical debt.
- recommend Flow documentation structure.

## Tool strategy

Use:

1. `dataiku_get_flow_graph`
2. `dataiku_analyze_flow_health`
3. `dataiku_generate_project_map`
4. `dataiku_generate_flow_documentation`

## Architecture smells

- too many objects in a single zone.
- unclear naming.
- duplicated processing branches.
- manual intermediate datasets.
- recipes with many inputs/outputs.
- missing final outputs.
- hidden dependencies.
- no clear RAG/ML boundary.

## Expected report format

```md
# Flow Architecture Review

## Current architecture
...

## Dependency graph summary
...

## Architecture issues
...

## Proposed restructuring
...

## Naming and zoning recommendations
...
```



---

# File: `skills/dataiku-managed-folder-debugger/SKILL.md`


# Dataiku Managed Folder Debugger

Use this skill when the user has issues with Dataiku Managed Folders, files, JSONL, CSV, S3, HDFS, GCS, FTP or local paths.

## Common issues

- `get_path()` used on non-local folder.
- file encoding errors.
- broken JSONL lines.
- large files read entirely into memory.
- missing upload/download stream usage.
- wrong folder id vs folder name.
- partition path confusion.
- missing files.
- binary file read as text.

## Tool strategy

Use:

1. `dataiku_list_managed_folders`
2. `dataiku_get_managed_folder_info`
3. `dataiku_list_folder_files`
4. `dataiku_read_folder_file` only if safe and needed.
5. `dataiku_list_recipes`
6. `dataiku_get_recipe_details`
7. `dataiku_managed_folder_doctor`
8. `dataiku_review_recipe_code`

## Preferred fixes

- Use download streams for reading.
- Use upload streams for writing.
- Avoid assuming local filesystem access.
- Stream JSONL line by line.
- Decode bytes safely.
- Add robust error reporting.
- Add file-size checks.

## Expected report format

```md
# Managed Folder Debug Report

## Symptom
...

## Evidence
...

## Root cause
...

## Fix
...

## Safer code pattern
...
```

## Example user requests

- "Why does my Managed Folder recipe fail on S3?"
- "Find recipes that incorrectly use get_path()."
- "Check if my JSONL files are malformed."



---

# File: `skills/dataiku-project-auditor/SKILL.md`


# Dataiku Project Auditor

Use this skill when the user asks to understand, audit or summarize a Dataiku DSS project.

## Responsibilities

- Inspect project structure.
- Summarize datasets, recipes, scenarios and Managed Folders.
- Build a mental model of the Flow.
- Identify risks and missing documentation.
- Produce clear reports.
- Recommend next debugging or documentation steps.

## Tool strategy

Use:

1. `dataiku_get_project_summary`
2. `dataiku_get_flow_graph`
3. `dataiku_list_datasets`
4. `dataiku_list_recipes`
5. `dataiku_list_managed_folders`
6. `dataiku_list_scenarios`
7. `dataiku_analyze_flow_health`

## Safety rules

- Prefer read-only tools.
- Do not modify anything.
- Do not preview data unless needed.
- Keep report evidence-based.
- Warn when permissions limit the analysis.

## Expected report format

```md
# Dataiku Project Audit

## Summary
...

## Flow architecture
...

## Main objects
...

## Risks
...

## Recommendations
...
```

## Example user requests

- "Analyze my Dataiku project PROJECT_KEY."
- "Explain the architecture of this Dataiku Flow."
- "Find technical debt in my Dataiku project."



---

# File: `skills/dataiku-rag-pipeline-auditor/SKILL.md`


# Dataiku RAG Pipeline Auditor

Use this skill when the project contains ingestion, chunking, embeddings, vector stores, reranking or LLM generation.

## Analyze

- source ingestion.
- cleaning.
- chunking.
- metadata.
- embedding model.
- vector store.
- retrieval configuration.
- reranker.
- prompt.
- evaluation.
- hallucination risks.
- prompt injection risks.

## Tool strategy

Use:

1. `dataiku_detect_rag_pipeline`
2. `dataiku_list_recipes`
3. `dataiku_get_recipe_details`
4. `dataiku_list_managed_folders`
5. `dataiku_managed_folder_doctor`
6. `dataiku_audit_rag_pipeline`
7. `dataiku_generate_rag_evaluation_plan`

## Risks to detect

- missing metadata.
- bad chunk size.
- embedding dimension mismatch.
- no vector normalization.
- no reranking.
- no source citation.
- hallucination risk.
- weak evaluation strategy.
- prompt injection vulnerabilities.
- no metadata filtering.
- top-k not justified.

## Expected report format

```md
# RAG Pipeline Audit

## Detected pipeline
...

## Ingestion
...

## Chunking
...

## Metadata
...

## Embeddings/vector store
...

## Retrieval/reranking
...

## Evaluation
...

## Main risks
...

## Recommended fixes
...
```

## Example user requests

- "Audit my RAG pipeline in Dataiku."
- "Check my chunking/embedding/vector store choices."
- "Generate an evaluation plan for my RAG project."



---

# File: `skills/dataiku-recipe-reviewer/SKILL.md`


# Dataiku Recipe Reviewer

Use this skill to review Python, SQL, PySpark or visual recipe settings.

## Review criteria

- correct use of Dataiku API.
- memory usage.
- logging.
- error handling.
- inputs/outputs.
- schema handling.
- code env dependencies.
- reproducibility.
- readability.
- maintainability.

## Tool strategy

Use:

1. `dataiku_list_recipes`
2. `dataiku_get_recipe_details`
3. `dataiku_review_recipe_code`
4. `dataiku_get_dataset_schema`
5. `dataiku_code_env_doctor` if dependency issue suspected.

## Dataiku-specific checks

- bad Managed Folder path assumptions.
- hardcoded project keys.
- hardcoded dataset names where avoidable.
- missing output schema handling.
- batch size too large.
- loading entire dataset in memory.
- improper use of Dataiku APIs.

## Expected report format

```md
# Recipe Review

## Recipe
...

## Strengths
...

## Issues
...

## Risk level
...

## Suggested patch
...
```

## Example user requests

- "Review this Python recipe."
- "Find bugs in recipe X."
- "Refactor my Dataiku recipe."



---

# File: `skills/dataiku-scenario-debugger/SKILL.md`


# Dataiku Scenario Debugger

Use this skill for failed scenarios, jobs and automation problems.

## Tasks

- inspect scenario runs.
- read logs.
- identify failed steps.
- explain root cause.
- suggest fix.
- recommend retry/rollback strategy.
- distinguish code, data, dependency and permission failures.

## Tool strategy

Use:

1. `dataiku_list_scenarios`
2. `dataiku_get_scenario_runs`
3. `dataiku_get_job_logs`
4. `dataiku_explain_failure`
5. related dataset/recipe/folder tools depending on failure.

## Common causes

- missing input dataset.
- schema mismatch.
- package missing in code env.
- Managed Folder file not found.
- permission issue.
- timeout.
- memory error.
- LLM connector failure.
- vector store failure.

## Expected report format

```md
# Scenario Failure Analysis

## Failed run
...

## Error summary
...

## Evidence from logs
...

## Probable root cause
...

## Fix
...

## Retry strategy
...
```
