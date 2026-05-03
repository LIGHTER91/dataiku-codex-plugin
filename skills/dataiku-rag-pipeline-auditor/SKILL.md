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
