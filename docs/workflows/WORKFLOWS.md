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
