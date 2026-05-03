# Codex Prompt 07 — Implement RAG Auditor

Implement RAG detection and audit tools.

Read:

- `FUNCTIONAL_SPEC.md`
- `TOOL_CATALOG.md`
- `skills/dataiku-rag-pipeline-auditor/SKILL.md`

Implement:

- `dataiku_detect_rag_pipeline`
- `dataiku_audit_rag_pipeline`
- `dataiku_generate_rag_evaluation_plan`
- `dataiku_generate_rag_audit_report`

Detection signals:

- FAISS.
- Weaviate.
- Chroma.
- vector store.
- embeddings.
- chunking.
- RecursiveCharacterTextSplitter.
- reranker.
- BM25.
- metadata.
- LLM connector.
- prompt.
- top_k.
- cosine similarity.
- normalization.

Output must include:

- detected components.
- evidence.
- risks.
- recommendations.
- evaluation plan.

Add tests with fake recipe code.
