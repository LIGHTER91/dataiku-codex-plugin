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
