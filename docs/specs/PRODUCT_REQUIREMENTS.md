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
