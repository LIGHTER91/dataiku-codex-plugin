"""RAG detection and audit heuristics."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

_SIGNAL_PATTERNS = {
    "chunking": [r"RecursiveCharacterTextSplitter", r"chunk_size", r"chunk_overlap"],
    "embeddings": [r"SentenceTransformer", r"embeddings?", r"OpenAIEmbeddings"],
    "vector_store": [r"faiss", r"IndexFlatIP", r"weaviate", r"chroma", r"elasticsearch"],
    "retrieval": [r"top_k", r"retriev", r"search"],
    "reranking": [r"rerank", r"cross-encoder", r"bm25"],
    "generation": [r"prompt", r"llm", r"chatcompletion"],
}


def detect_rag_pipeline(recipe_details: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect common RAG pipeline signals in recipe code."""

    components: dict[str, list[str]] = defaultdict(list)
    evidence: list[dict[str, str]] = []

    for recipe in recipe_details:
        recipe_name = str(recipe.get("name") or "unknown")
        raw_code = recipe.get("code")
        code = raw_code if isinstance(raw_code, str) else ""
        for component, patterns in _SIGNAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, code, flags=re.IGNORECASE):
                    if recipe_name not in components[component]:
                        components[component].append(recipe_name)
                    evidence.append(
                        {
                            "recipe": recipe_name,
                            "component": component,
                            "signal": pattern,
                        }
                    )
                    break

    detected_components = sorted(
        component
        for component, component_recipes in components.items()
        if component_recipes
    )
    return {
        "is_rag_pipeline": len(detected_components) >= 2,
        "detected_components": detected_components,
        "matching_recipes": components,
        "evidence": evidence,
    }


def audit_rag_pipeline(
    *,
    recipe_details: list[dict[str, Any]],
    datasets: list[dict[str, Any]],
    dataset_schemas: dict[str, dict[str, Any]],
    deep: bool = False,
) -> dict[str, Any]:
    """Audit RAG design choices from code and metadata heuristics."""

    detection = detect_rag_pipeline(recipe_details)
    risks: list[dict[str, str]] = []
    recommendations: list[str] = []

    code_chunks = [
        recipe["code"]
        for recipe in recipe_details
        if isinstance(recipe.get("code"), str)
    ]
    combined_code = "\n".join(code_chunks)

    chunk_size = _extract_int(combined_code, r"chunk_size\s*=\s*(\d+)")
    overlap = _extract_int(combined_code, r"chunk_overlap\s*=\s*(\d+)")
    top_k = _extract_int(combined_code, r"top_k\s*=\s*(\d+)")

    if chunk_size is not None and chunk_size > 2000:
        risks.append(
            _risk(
                "medium",
                "chunk_size",
                "Chunk size appears quite large and may dilute retrieval precision.",
            )
        )
        recommendations.append("Reduce chunk_size or justify it with retrieval benchmarks.")
    if overlap is not None and overlap == 0:
        risks.append(
            _risk(
                "medium",
                "missing_overlap",
                "Chunk overlap is missing, which may hurt recall at boundaries.",
            )
        )
        recommendations.append("Add a non-zero chunk_overlap for long-form documents.")
    if "IndexFlatIP" in combined_code and "normalize" not in combined_code.lower():
        risks.append(
            _risk(
                "high",
                "vector_normalization",
                "FAISS inner-product search is used without obvious embedding normalization.",
            )
        )
        recommendations.append(
            "Normalize embeddings before indexing or switch to a better-aligned metric."
        )
    if "rerank" not in combined_code.lower() and "cross-encoder" not in combined_code.lower():
        risks.append(
            _risk("medium", "missing_reranker", "No reranking stage was detected.")
        )
        recommendations.append(
            "Add a reranker if answer quality depends on tight relevance ordering."
        )
    if top_k is not None and top_k > 30:
        risks.append(
            _risk(
                "low",
                "high_top_k",
                "top_k appears relatively high and may bloat prompt context.",
            )
        )
        recommendations.append(
            "Benchmark lower top_k values and measure answer relevance vs. context cost."
        )
    if "recall@" not in combined_code.lower() and "mrr" not in combined_code.lower():
        risks.append(
            _risk(
                "high",
                "missing_evaluation",
                "No explicit retrieval evaluation metrics were detected.",
            )
        )
        recommendations.append("Track Recall@K, MRR and citation accuracy on a held-out query set.")
    if "prompt injection" not in combined_code.lower():
        risks.append(
            _risk(
                "medium",
                "missing_prompt_injection_mitigation",
                "No prompt-injection mitigation was detected.",
            )
        )
        recommendations.append("Sanitize retrieved content and add prompt-injection guardrails.")

    schema_columns = {
        column.get("name")
        for schema in dataset_schemas.values()
        for column in schema.get("columns", [])
        if column.get("name")
    }
    if "source_path" not in schema_columns and "source" not in schema_columns:
        risks.append(
            _risk(
                "medium",
                "missing_source_metadata",
                "Source metadata fields were not detected in dataset schemas.",
            )
        )
        recommendations.append("Add source identifiers and hierarchy metadata to chunk records.")
    if "page" not in schema_columns and "section" not in schema_columns:
        risks.append(
            _risk(
                "low",
                "limited_hierarchy_metadata",
                "Document hierarchy metadata appears limited.",
            )
        )
        recommendations.append(
            "Capture page, section or heading metadata for better filtering and citations."
        )

    return {
        "deep": deep,
        "detected_components": detection["detected_components"],
        "evidence": detection["evidence"],
        "main_risks": risks,
        "recommendations": recommendations,
        "dataset_count": len(datasets),
    }


def _extract_int(text: str, pattern: str) -> int | None:
    match = re.search(pattern, text)
    if match is None:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _risk(severity: str, category: str, message: str) -> dict[str, str]:
    return {"severity": severity, "category": category, "message": message}
