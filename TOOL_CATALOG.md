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
