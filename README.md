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
- advanced AI engineering reports for RAG evaluation, chunking comparison, vector-store inspection, embedding drift, prompt-injection audit, architecture diagrams, project quality scoring and debt prioritization
- reusable ML command catalog
- guided prediction target discovery
- command-driven Visual ML bootstrap for XGBoost, LightGBM, Random Forest and Logistic Regression
- Visual ML task lifecycle commands for list, train, inspect trained models and deploy-to-flow
- saved model inspection, scoring recipe creation and model evaluation flows
- natural-language ML intent routing to reusable commands
- code environment diagnostics
- plugin inventory, scenario dependency mapping, code env update planning and production readiness reports
- cost/performance monitoring, production readiness checklists and governance documentation
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

## Product direction

The preferred architecture is:

- Codex plugin for UI, prompts, skills and discoverability
- MCP server for executing standardized commands
- Dataiku-native assets for the actual workflow mutations

The preferred behavior is:

- use reusable command catalog entries and blueprints whenever possible
- avoid generating new ad-hoc setup scripts for recurring tasks
- reserve direct code edits for narrow maintenance work such as renames, patches or recipe fixes
- prefer Dataiku visual components such as Prepare recipes, Visual ML tasks and scenario steps over custom Python when a native component exists
- return plans, reports and UI-visible structured outputs before raw code whenever code generation is not required

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

List the ML command catalog:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env list-ml-commands
```

Plan a reusable ML command:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env plan-ml-command TEST flight_data xgb
```

Run a reusable ML command after approval:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env run-ml-command TEST flight_data xgb --approved --approval-reason "Bootstrap ML demo"
```

List Visual ML tasks:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env list-ml-tasks TEST
```

Train a Visual ML task after approval:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env train-ml-task TEST <ANALYSIS_ID> <ML_TASK_ID> --approved --approval-reason "Train ML task"
```

Deploy a trained model to the Flow:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env deploy-trained-model-to-flow TEST <ANALYSIS_ID> <ML_TASK_ID> --model-id <MODEL_ID> --approved --approval-reason "Deploy trained model"
```

List deployed saved models:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env list-saved-models TEST
```

Create a prediction scoring recipe from a saved model:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env create-prediction-scoring-recipe TEST <SAVED_MODEL_ID> flight_data score_flights flight_data_scored --approved --approval-reason "Create scoring recipe"
```

Create and run a model evaluation:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env create-model-evaluation TEST <SAVED_MODEL_ID> flight_data --recipe-name evaluate_flights_model --scored-output-dataset flight_data_eval_scored --metrics-output-dataset flight_data_eval_metrics --metrics accuracy auc --run-immediately --approved --approval-reason "Run model evaluation"
```

Route a natural-language ML request to the command catalog:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env route-ml-intent "setup xgboost on project TEST using dataset flight_data for Cancelled"
```

Generate an ops readiness report:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env generate-production-readiness-report TEST
```

Generate the remaining V4.0 ops reports:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env generate-cost-performance-report TEST
.\.venv\Scripts\dataiku-codex-mcp --env-file .env generate-production-readiness-checklist TEST
.\.venv\Scripts\dataiku-codex-mcp --env-file .env generate-governance-documentation TEST
```

Run the V3.0 RAG engineering reports:

```powershell
.\.venv\Scripts\dataiku-codex-mcp --env-file .env run-rag-eval TEST
.\.venv\Scripts\dataiku-codex-mcp --env-file .env compare-chunking-strategies TEST
.\.venv\Scripts\dataiku-codex-mcp --env-file .env inspect-vector-store TEST
.\.venv\Scripts\dataiku-codex-mcp --env-file .env audit-prompt-injection TEST
.\.venv\Scripts\dataiku-codex-mcp --env-file .env generate-architecture-diagram TEST
.\.venv\Scripts\dataiku-codex-mcp --env-file .env score-project-quality TEST
.\.venv\Scripts\dataiku-codex-mcp --env-file .env prioritize-technical-debt TEST
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
- ML command catalog write-path with native Prepare recipe creation, dataset materialization and Visual ML task bootstrap

The latest repo-only validation also confirms:

- dead code audit completed for the ML command layer
- removal of obsolete helper functions replaced by the generic command catalog
- scoring, evaluation, routed ML intents and ops commands covered by automated tests
- V3.0 advanced AI engineering analyzers covered by automated tests and CLI smoke checks

The current DSS trial URL saved in `.env` no longer resolves to a live instance, so new remote smoke tests require the refreshed trial URL before rerunning end-to-end validation.

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

## Recommended next development

The next recommended sequence is:

1. Refresh the DSS trial URL in `.env` and rerun the real end-to-end ML lifecycle on a live instance.
2. Re-run the V3.0 AI engineering reports on a live DSS project with richer benchmark datasets.
3. Extend the live DSS smoke tests to the new V4.0 cost/perf and governance outputs on a richer project.

This keeps the product aligned with its intended operating model:

- Codex plugin for UI and intent capture
- MCP server for standardized command execution
- native DSS visual assets for repeated ML workflows
- direct code edits only for narrow maintenance work such as renames, patches or recipe fixes

## Repository map

- [src/dataiku_codex_mcp](src/dataiku_codex_mcp)
- [tests](tests)
- [plugin.json](plugin.json)
- [mcp/dataiku.mcp.json](mcp/dataiku.mcp.json)
- [examples/sample_env.example](examples/sample_env.example)
- [ALL_DOCUMENTATION.md](ALL_DOCUMENTATION.md)
