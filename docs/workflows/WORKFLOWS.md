# Workflows

## Workflow 1 - Full project audit

1. User provides project key.
2. Codex calls `dataiku_get_project_summary`.
3. Codex calls `dataiku_get_flow_graph`.
4. Codex calls `dataiku_analyze_flow_health`.
5. Codex inspects datasets, recipes, Managed Folders and scenarios.
6. Codex produces audit report.

## Workflow 2 - Managed Folder debugging

1. User describes folder or file error.
2. Codex lists Managed Folders.
3. Codex inspects folder metadata.
4. Codex lists files.
5. Codex inspects relevant recipes.
6. Codex detects path, stream or encoding issues.
7. Codex proposes fix.

## Workflow 3 - RAG audit

1. Codex detects RAG pipeline.
2. Codex inspects ingestion recipes.
3. Codex inspects chunking logic.
4. Codex inspects metadata.
5. Codex detects embedding or vector store usage.
6. Codex checks retrieval and reranking.
7. Codex generates evaluation plan.

## Workflow 4 - Scenario failure

1. User gives project key and scenario ID.
2. Codex retrieves recent scenario runs.
3. Codex reads relevant logs.
4. Codex identifies error class.
5. Codex inspects linked recipe, dataset or folder if needed.
6. Codex proposes fix and retry strategy.

## Workflow 5 - Controlled recipe update

1. Codex reviews a recipe.
2. Codex proposes a patch.
3. Codex shows a dry-run summary.
4. User approves.
5. MCP server verifies mode and approval.
6. The tool applies the update.
7. The audit log records the action.

## Workflow 6 - ML command catalog

1. User asks for a reusable ML setup such as XGBoost, LightGBM or Random Forest.
2. Codex resolves the matching catalog command.
3. MCP server suggests likely prediction targets if the user did not provide one.
4. MCP server returns a structured plan with the target, algorithm and Dataiku assets to create.
5. User approves.
6. MCP server creates a standard Prepare recipe and a Visual ML task through Dataiku-native APIs.
7. The audit log records the command execution.

## Workflow 7 - Code generation fallback

1. User asks for a change that cannot be expressed through a catalog command or Dataiku-native asset.
2. Codex checks whether the request is a narrow maintenance edit such as a rename or patch.
3. If yes, Codex can generate or modify code directly.
4. If not, prefer plans, reports, visual outputs or new catalog commands instead of ad-hoc setup scripts.
