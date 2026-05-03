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
