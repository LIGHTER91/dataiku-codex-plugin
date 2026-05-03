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
