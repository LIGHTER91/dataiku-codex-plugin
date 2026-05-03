# Roadmap

## Version 1.0 - Read-only foundation

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

## Version 1.5 - Analysis layer

- Flow graph reconstruction.
- Flow health analysis.
- recipe code reviewer.
- Managed Folder doctor.
- scenario failure explainer.
- code env doctor.
- RAG pipeline detector.
- RAG audit report.
- project README generation.

## Version 2.0 - Controlled actions

- create Python recipe.
- update recipe code.
- create Managed Folder.
- upload file to Managed Folder.
- run scenario.
- write generated documentation.
- approval flow.
- dry-run output.

## Version 2.5 - Enterprise hardening

- remote HTTP MCP server.
- OAuth/Bearer auth.
- centralized audit logs.
- policy engine.
- team allowlists.
- per-tool RBAC.
- stricter PII detection.
- deployment guide.

## Version 3.0 - Advanced AI engineering

- RAG eval runner.
- chunking comparison runner.
- FAISS/Weaviate inspector.
- embedding drift monitor.
- prompt injection audit.
- automatic architecture diagrams.
- project quality score.
- technical debt prioritization.

## Version 3.5 - Guided ML bootstrap

- dataset prediction target discovery.
- candidate target ranking and explanation.
- target selection workflow from natural language requests.
- prediction task type inference: classification, regression, ranking.
- reusable blueprint engine for ML setup commands.
- prepare recipe generation from templates, not ad-hoc code generation.
- Visual ML task bootstrap for XGBoost-ready flows.
- one-command pipeline scaffolding for train, score and evaluate paths.
- dry-run plan before creating ML assets.
- approval flow for recipe/task creation and execution.
- reusable command patterns such as:
  - "set up xgboost on project X using dataset Y"
  - "show me what I can predict from dataset Y"
  - "prepare the flow for predicting column Z"

## Version 3.5.1 - ML command catalog

- reusable ML command catalog exposed by MCP tools and CLI.
- command aliases such as `xgb`, `lightgbm`, `rf`, `logit`.
- plan-first workflow before any ML asset creation.
- auto-select the best target when the user asks for speed and does not provide one.
- generic command runner for multiple algorithm families.
- keep XGBoost, LightGBM, Random Forest and Logistic Regression as standard baselines.
- prefer Dataiku Visual ML tasks and Prepare recipes over custom generated setup scripts.
- use direct code generation only for narrow maintenance work such as recipe fixes or variable renames.

## Version 4.0 - Dataiku platform operations

- code env update planning.
- plugin inventory.
- scenario dependency map.
- cost/performance monitoring.
- production readiness checklist.
- governance documentation generator.

## Product direction notes

- Prefer Dataiku-native assets and templates over generating new Python setup scripts for each request.
- Turn common intents into high-level tools and blueprints so repeated ML setup is fast, deterministic and reviewable.
- Keep Codex focused on orchestration, validation and explanation, while the MCP server executes standardized project mutations.
