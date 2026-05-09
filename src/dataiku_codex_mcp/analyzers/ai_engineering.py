"""Advanced AI engineering analyzers for V3.0 roadmap features."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

_BENCHMARK_QUERY_COLUMNS = {"question", "query", "prompt", "user_query"}
_BENCHMARK_ANSWER_COLUMNS = {"answer", "expected_answer", "ground_truth", "label"}
_SOURCE_METADATA_COLUMNS = {"source", "source_path", "document_id", "doc_id", "uri"}
_HIERARCHY_METADATA_COLUMNS = {"page", "section", "heading", "title"}
_TRACKING_COLUMNS = {"embedding_model", "embedding_version", "indexed_at", "content_hash"}
_EMBEDDING_PATTERNS = {
    "sentence_transformers": r"SentenceTransformer",
    "openai_embeddings": r"OpenAIEmbeddings|text-embedding",
    "cohere_embeddings": r"Cohere",
    "huggingface_embeddings": r"HuggingFaceEmbeddings|transformers",
}
_VECTOR_STORE_PATTERNS = {
    "faiss": r"\bfaiss\b|IndexFlatIP|IndexFlatL2|IndexIVF",
    "weaviate": r"\bweaviate\b",
    "chroma": r"\bchroma\b",
    "elasticsearch": r"\belasticsearch\b",
}
_INDEX_PATTERNS = (
    r"IndexFlatIP",
    r"IndexFlatL2",
    r"IndexIVF\w+",
    r"HNSW",
)
_DEFAULT_CHUNKING_STRATEGIES: dict[str, dict[str, Any]] = {
    "balanced_rag": {
        "chunk_size": 800,
        "chunk_overlap": 80,
        "top_k": 8,
        "best_for": "General-purpose answer quality with manageable prompt size.",
        "tradeoffs": "Balanced recall and cost; a good default when current chunks are too large.",
    },
    "high_recall": {
        "chunk_size": 1200,
        "chunk_overlap": 200,
        "top_k": 12,
        "best_for": "Long-form documents where missing context is more costly than latency.",
        "tradeoffs": "Higher prompt cost and more duplicate context during retrieval.",
    },
    "low_latency": {
        "chunk_size": 400,
        "chunk_overlap": 40,
        "top_k": 5,
        "best_for": "Fast interactive experiences or constrained context windows.",
        "tradeoffs": "May reduce recall on cross-section answers or longer explanations.",
    },
    "citation_focused": {
        "chunk_size": 600,
        "chunk_overlap": 120,
        "top_k": 6,
        "best_for": "Grounded answers that need stronger citation fidelity.",
        "tradeoffs": "Slightly more indexing volume in exchange for better provenance.",
    },
}


def run_rag_evaluation(
    *,
    project_key: str,
    detection: Mapping[str, Any],
    rag_audit: Mapping[str, Any],
    datasets: Sequence[Mapping[str, Any]],
    dataset_schemas: Mapping[str, Mapping[str, Any]],
    recipe_details: Sequence[Mapping[str, Any]],
    benchmark_dataset_name: str | None = None,
) -> dict[str, Any]:
    """Build an analysis-first RAG evaluation report from project signals."""

    risk_categories = _risk_categories(rag_audit)
    benchmark_candidates = _find_benchmark_candidates(dataset_schemas)
    resolved_benchmark = benchmark_dataset_name or (
        benchmark_candidates[0]["dataset_name"] if benchmark_candidates else None
    )
    benchmark_ready = resolved_benchmark is not None
    detected_components = {
        str(component) for component in detection.get("detected_components", [])
    }
    column_names = _collect_column_names(dataset_schemas)
    combined_code = _combine_recipe_code(recipe_details)

    retrieval_score = 35
    retrieval_evidence: list[str] = []
    if "chunking" in detected_components:
        retrieval_score += 18
        retrieval_evidence.append("Chunking logic is present in recipe code.")
    if "embeddings" in detected_components:
        retrieval_score += 16
        retrieval_evidence.append("Embedding generation is configured.")
    if "vector_store" in detected_components:
        retrieval_score += 16
        retrieval_evidence.append("A vector store backend is referenced.")
    if "retrieval" in detected_components:
        retrieval_score += 10
        retrieval_evidence.append("Retrieval parameters such as top_k are configured.")
    retrieval_score -= _penalty_for_risks(
        risk_categories,
        {
            "missing_overlap": 12,
            "high_top_k": 6,
            "vector_normalization": 18,
        },
    )
    if benchmark_ready:
        retrieval_score += 5
        retrieval_evidence.append("A benchmark dataset is available for regression testing.")
    else:
        retrieval_evidence.append("No benchmark dataset was detected for retrieval checks.")

    grounding_score = 45
    grounding_evidence = []
    if _has_any(column_names, _SOURCE_METADATA_COLUMNS):
        grounding_score += 20
        grounding_evidence.append("Source metadata exists in dataset schemas.")
    else:
        grounding_evidence.append("Source metadata is missing from chunk-level schemas.")
    if _has_any(column_names, _HIERARCHY_METADATA_COLUMNS):
        grounding_score += 10
        grounding_evidence.append("Hierarchy metadata is available for citation context.")
    if "generation" in detected_components:
        grounding_score += 10
        grounding_evidence.append("A generation stage is present in the pipeline.")
    grounding_score -= _penalty_for_risks(
        risk_categories,
        {
            "missing_source_metadata": 18,
            "limited_hierarchy_metadata": 8,
            "missing_evaluation": 10,
        },
    )

    safety_score = 60
    safety_evidence = []
    if _contains_any(
        combined_code,
        ("sanitize", "allowlist", "citation", "prompt injection", "guardrail"),
    ):
        safety_score += 8
        safety_evidence.append("Some safety or guardrail language is present in code.")
    else:
        safety_evidence.append("No obvious guardrail logic was detected in recipe code.")
    if "api_key" in combined_code.lower():
        safety_score -= 8
        safety_evidence.append("Code appears to manipulate raw API key strings.")
    safety_score -= _penalty_for_risks(
        risk_categories,
        {
            "missing_prompt_injection_mitigation": 25,
            "missing_source_metadata": 8,
        },
    )

    observability_score = 55
    observability_evidence = []
    if benchmark_ready:
        observability_score += 20
        observability_evidence.append("A benchmark dataset can anchor regression checks.")
    if "missing_evaluation" not in risk_categories:
        observability_score += 12
        observability_evidence.append("Evaluation metrics are referenced in code.")
    else:
        observability_evidence.append("No retrieval or answer-quality metrics were detected.")
    observability_score -= _penalty_for_risks(risk_categories, {"missing_evaluation": 25})

    dimensions = [
        _dimension("retrieval", retrieval_score, retrieval_evidence),
        _dimension("grounding", grounding_score, grounding_evidence),
        _dimension("safety", safety_score, safety_evidence),
        _dimension("observability", observability_score, observability_evidence),
    ]
    overall_score = round(sum(dimension["score"] for dimension in dimensions) / len(dimensions))
    next_actions = _deduplicated_strings(
        [
            *[str(item) for item in rag_audit.get("recommendations", [])],
            "Create a benchmark dataset with query, expected_answer and expected_source columns."
            if not benchmark_ready
            else "",
        ]
    )[:5]

    return {
        "project_key": project_key,
        "execution_mode": "analysis_only",
        "benchmark_dataset_name": resolved_benchmark,
        "benchmark_ready": benchmark_ready,
        "benchmark_candidates": benchmark_candidates,
        "detected_components": sorted(detected_components),
        "dimensions": dimensions,
        "overall_score": _clamp_score(overall_score),
        "dataset_count": len(datasets),
        "next_actions": next_actions,
        "summary": (
            f"RAG evaluation readiness for {project_key} is "
            f"{_status_from_score(overall_score)} at {overall_score}/100."
        ),
    }


def compare_chunking_strategies(
    *,
    project_key: str,
    recipe_details: Sequence[Mapping[str, Any]],
    dataset_name: str | None = None,
    strategies: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Compare reusable chunking profiles against the current implementation."""

    combined_code = _combine_recipe_code(recipe_details)
    current_strategy = {
        "splitter": _detect_splitter(combined_code),
        "chunk_size": _extract_int(combined_code, r"chunk_size\s*=\s*(\d+)"),
        "chunk_overlap": _extract_int(combined_code, r"chunk_overlap\s*=\s*(\d+)"),
        "top_k": _extract_int(combined_code, r"top_k\s*=\s*(\d+)"),
    }
    selected_strategy_names = _resolve_strategy_names(strategies)
    recommended_strategy = _recommend_chunking_strategy(current_strategy)

    comparisons: list[dict[str, Any]] = []
    for strategy_name in selected_strategy_names:
        blueprint = dict(_DEFAULT_CHUNKING_STRATEGIES[strategy_name])
        prompt_pressure = blueprint["chunk_size"] * blueprint["top_k"]
        score = 88 if strategy_name == recommended_strategy else 74
        if current_strategy["chunk_size"] is not None:
            current_chunk_size = int(current_strategy["chunk_size"])
            if abs(current_chunk_size - int(blueprint["chunk_size"])) <= 250:
                score += 4
        comparisons.append(
            {
                "strategy_name": strategy_name,
                "chunk_size": blueprint["chunk_size"],
                "chunk_overlap": blueprint["chunk_overlap"],
                "recommended_top_k": blueprint["top_k"],
                "best_for": blueprint["best_for"],
                "tradeoffs": blueprint["tradeoffs"],
                "estimated_prompt_pressure": prompt_pressure,
                "score": _clamp_score(score),
            }
        )

    return {
        "project_key": project_key,
        "dataset_name": dataset_name,
        "current_strategy": current_strategy,
        "recommended_strategy": recommended_strategy,
        "strategy_comparisons": comparisons,
        "summary": (
            f"Compared {len(comparisons)} chunking strategies for {project_key} and "
            f"recommend {recommended_strategy}."
        ),
    }


def inspect_vector_store(
    *,
    project_key: str,
    rag_audit: Mapping[str, Any],
    dataset_schemas: Mapping[str, Mapping[str, Any]],
    recipe_details: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Inspect vector-store implementation details and associated risks."""

    combined_code = _combine_recipe_code(recipe_details)
    providers = [
        provider
        for provider, pattern in _VECTOR_STORE_PATTERNS.items()
        if re.search(pattern, combined_code, flags=re.IGNORECASE)
    ]
    index_types = _detect_index_types(combined_code)
    column_names = _collect_column_names(dataset_schemas)
    risk_categories = _risk_categories(rag_audit)
    health_score = 75
    if not providers:
        health_score = 25
    if "vector_normalization" in risk_categories:
        health_score -= 25
    if "missing_source_metadata" in risk_categories:
        health_score -= 15
    if "limited_hierarchy_metadata" in risk_categories:
        health_score -= 8

    findings = []
    if "vector_normalization" in risk_categories:
        findings.append(
            {
                "severity": "high",
                "category": "vector_normalization",
                "message": "Inner-product vector search appears to lack embedding normalization.",
            }
        )
    if not _has_any(column_names, _SOURCE_METADATA_COLUMNS):
        findings.append(
            {
                "severity": "medium",
                "category": "source_metadata",
                "message": "Chunk schemas do not expose strong source provenance metadata.",
            }
        )

    return {
        "project_key": project_key,
        "providers": providers,
        "index_types": index_types,
        "normalization_detected": "normalize" in combined_code.lower(),
        "approximate_search_detected": _contains_any(combined_code, ("hnsw", "ivf", "ann")),
        "metadata_fields": sorted(
            field
            for field in column_names
            if field in _SOURCE_METADATA_COLUMNS | _HIERARCHY_METADATA_COLUMNS | _TRACKING_COLUMNS
        ),
        "health_score": _clamp_score(health_score),
        "findings": findings,
        "summary": (
            f"Vector store inspection for {project_key} found "
            f"{len(providers) or 1} backend signal(s) with score {_clamp_score(health_score)}/100."
        ),
    }


def monitor_embedding_drift(
    *,
    project_key: str,
    dataset_schemas: Mapping[str, Mapping[str, Any]],
    recipe_details: Sequence[Mapping[str, Any]],
    reference_dataset_name: str | None = None,
    current_dataset_name: str | None = None,
) -> dict[str, Any]:
    """Estimate embedding drift readiness from metadata and model signals."""

    combined_code = _combine_recipe_code(recipe_details)
    providers = [
        provider
        for provider, pattern in _EMBEDDING_PATTERNS.items()
        if re.search(pattern, combined_code, flags=re.IGNORECASE)
    ]
    model_names = _extract_embedding_model_names(combined_code)
    dataset_names = list(dataset_schemas)
    resolved_reference = reference_dataset_name or _choose_embedding_dataset(dataset_names)
    resolved_current = current_dataset_name or resolved_reference
    column_names = _collect_column_names(dataset_schemas)

    tracking_coverage = {
        field: field in column_names
        for field in sorted(_TRACKING_COLUMNS | _SOURCE_METADATA_COLUMNS)
    }
    risk_items = []
    drift_score = 72 if providers else 35
    if not any(tracking_coverage.values()):
        drift_score -= 24
        risk_items.append(
            {
                "severity": "high",
                "category": "missing_embedding_lineage",
                "message": "No embedding lineage fields were detected in dataset schemas.",
            }
        )
    if len(set(model_names)) > 1:
        drift_score -= 12
        risk_items.append(
            {
                "severity": "medium",
                "category": "multiple_embedding_models",
                "message": (
                    "Multiple embedding models are referenced without explicit "
                    "drift guards."
                ),
            }
        )
    if "indexed_at" not in column_names:
        drift_score -= 10
        risk_items.append(
            {
                "severity": "medium",
                "category": "missing_timestamp",
                "message": "Chunk or embedding timestamp metadata is missing.",
            }
        )

    monitoring_plan = [
        "Track embedding_model, embedding_version and indexed_at on every chunk row.",
        "Keep a reference query set and compare recall against each re-indexing run.",
        "Capture content_hash to distinguish document drift from model drift.",
    ]

    return {
        "project_key": project_key,
        "reference_dataset_name": resolved_reference,
        "current_dataset_name": resolved_current,
        "embedding_providers": providers,
        "embedding_model_names": model_names,
        "tracking_coverage": tracking_coverage,
        "drift_score": _clamp_score(drift_score),
        "risk_items": risk_items,
        "monitoring_plan": monitoring_plan,
        "summary": (
            f"Embedding drift readiness for {project_key} is "
            f"{_status_from_score(drift_score)} at {_clamp_score(drift_score)}/100."
        ),
    }


def audit_prompt_injection(
    *,
    project_key: str,
    dataset_schemas: Mapping[str, Mapping[str, Any]],
    recipe_details: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Audit prompt-injection guardrails from code and metadata signals."""

    combined_code = _combine_recipe_code(recipe_details)
    column_names = _collect_column_names(dataset_schemas)
    guardrails = {
        "content_sanitization": _contains_any(
            combined_code,
            ("sanitize", "bleach", "strip_html", "escape", "allowlist"),
        ),
        "prompt_delimiters": _contains_any(
            combined_code,
            ("system prompt", "delimiter", "trusted context", "untrusted"),
        ),
        "citation_requirement": _contains_any(
            combined_code,
            ("citation", "cite", "source_path", "grounded"),
        )
        or _has_any(column_names, _SOURCE_METADATA_COLUMNS),
        "source_filtering": _contains_any(
            combined_code,
            ("regex", "filter", "blocklist", "denylist"),
        ),
    }

    findings = []
    if not guardrails["content_sanitization"]:
        findings.append(
            {
                "severity": "high",
                "category": "missing_content_sanitization",
                "message": "Retrieved content is not obviously sanitized before generation.",
            }
        )
    if not guardrails["prompt_delimiters"]:
        findings.append(
            {
                "severity": "medium",
                "category": "missing_prompt_boundaries",
                "message": (
                    "Prompt boundaries between system instructions and retrieved "
                    "content are unclear."
                ),
            }
        )
    if not guardrails["citation_requirement"]:
        findings.append(
            {
                "severity": "medium",
                "category": "missing_citations",
                "message": "The pipeline does not clearly require citations or source references.",
            }
        )
    if not guardrails["source_filtering"]:
        findings.append(
            {
                "severity": "medium",
                "category": "missing_source_filtering",
                "message": "No allowlist or filtering stage was detected for retrieved sources.",
            }
        )

    risk_level = "low"
    if any(item["severity"] == "high" for item in findings):
        risk_level = "high"
    elif findings:
        risk_level = "medium"

    return {
        "project_key": project_key,
        "risk_level": risk_level,
        "guardrails": guardrails,
        "findings": findings,
        "recommended_controls": [
            "Strip or escape untrusted markup before prompt assembly.",
            "Use explicit delimiters between system instructions and retrieved passages.",
            "Require citations or source IDs in final answers.",
            "Filter retrieved sources with allowlists or content policy checks.",
        ],
        "summary": (
            f"Prompt-injection audit for {project_key} is {risk_level} risk "
            f"with {len(findings)} control gap(s)."
        ),
    }


def generate_architecture_diagram(
    *,
    project_key: str,
    flow_graph: Mapping[str, Any],
    detection: Mapping[str, Any],
) -> dict[str, Any]:
    """Generate a Mermaid architecture diagram from project dependencies."""

    nodes = flow_graph.get("nodes", [])
    edges = flow_graph.get("edges", [])
    lines = ["graph TD"]
    rendered_nodes: set[str] = set()

    if isinstance(nodes, Sequence):
        for raw_node in nodes:
            if not isinstance(raw_node, Mapping):
                continue
            node_id = str(raw_node.get("id") or "")
            node_name = str(raw_node.get("name") or node_id)
            node_type = str(raw_node.get("type") or "node")
            if not node_id:
                continue
            rendered_id = _mermaid_id(node_id)
            if rendered_id in rendered_nodes:
                continue
            rendered_nodes.add(rendered_id)
            label = _mermaid_label(node_type, node_name)
            lines.append(f"    {rendered_id}{label}")

    if isinstance(edges, Sequence):
        for raw_edge in edges:
            if not isinstance(raw_edge, Mapping):
                continue
            source = raw_edge.get("source")
            target = raw_edge.get("target")
            if not isinstance(source, str) or not isinstance(target, str):
                continue
            lines.append(f"    {_mermaid_id(source)} --> {_mermaid_id(target)}")

    components = [
        str(component) for component in detection.get("detected_components", []) if component
    ]
    for component in components:
        component_id = _mermaid_id(f"rag:{component}")
        lines.append(f'    {component_id}{{"RAG: {component}"}}')

    mermaid = "\n".join(lines)
    diagram_markdown = "\n".join(["```mermaid", mermaid, "```"])
    return {
        "project_key": project_key,
        "mermaid": mermaid,
        "diagram_markdown": diagram_markdown,
        "rag_components": components,
        "summary": (
            f"Generated an architecture diagram for {project_key} with "
            f"{len(rendered_nodes)} node(s)."
        ),
    }


def score_project_quality(
    *,
    project_key: str,
    project_summary: Mapping[str, Any],
    flow_health: Mapping[str, Any],
    rag_audit: Mapping[str, Any],
    readiness_report: Mapping[str, Any],
    code_env_update_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Aggregate project signals into one weighted quality score."""

    flow_score = _score_from_issue_list(flow_health.get("issues", []))
    rag_score = _score_from_issue_list(rag_audit.get("main_risks", []))
    ops_score = int(readiness_report.get("score", 70) or 70)
    env_score = _score_code_env_plan(code_env_update_plan)
    documentation_score = 88
    if project_summary.get("warnings"):
        documentation_score -= 10
    if int(project_summary.get("scenarios_count", 0) or 0) == 0:
        documentation_score -= 6

    weights = {
        "flow": 0.24,
        "rag": 0.24,
        "operations": 0.22,
        "code_envs": 0.18,
        "documentation": 0.12,
    }
    weighted_score = round(
        flow_score * weights["flow"]
        + rag_score * weights["rag"]
        + ops_score * weights["operations"]
        + env_score * weights["code_envs"]
        + documentation_score * weights["documentation"]
    )
    breakdown = [
        {"dimension": "flow", "score": flow_score},
        {"dimension": "rag", "score": rag_score},
        {"dimension": "operations", "score": ops_score},
        {"dimension": "code_envs", "score": env_score},
        {"dimension": "documentation", "score": documentation_score},
    ]
    quality_tier = _quality_tier(weighted_score)

    return {
        "project_key": project_key,
        "quality_score": _clamp_score(weighted_score),
        "quality_tier": quality_tier,
        "breakdown": breakdown,
        "summary": (
            f"Project quality for {project_key} is {quality_tier} at "
            f"{_clamp_score(weighted_score)}/100."
        ),
    }


def prioritize_technical_debt(
    *,
    project_key: str,
    flow_health: Mapping[str, Any],
    rag_audit: Mapping[str, Any],
    readiness_report: Mapping[str, Any],
    code_env_update_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge project issues into a prioritized technical-debt backlog."""

    backlog_items: list[dict[str, Any]] = []

    for issue in flow_health.get("issues", []):
        if not isinstance(issue, Mapping):
            continue
        backlog_items.append(
            _debt_item(
                source="flow",
                category=str(issue.get("category", "flow_issue")),
                severity=str(issue.get("severity", "low")),
                message=str(issue.get("message", "Flow issue detected.")),
            )
        )

    rag_recommendations = [
        str(item) for item in rag_audit.get("recommendations", []) if isinstance(item, str)
    ]
    for issue in rag_audit.get("main_risks", []):
        if not isinstance(issue, Mapping):
            continue
        backlog_items.append(
            _debt_item(
                source="rag",
                category=str(issue.get("category", "rag_risk")),
                severity=str(issue.get("severity", "medium")),
                message=str(issue.get("message", "RAG risk detected.")),
                recommendation=_match_recommendation(
                    rag_recommendations,
                    str(issue.get("category", "")),
                ),
            )
        )

    for issue in readiness_report.get("findings", []):
        if not isinstance(issue, Mapping):
            continue
        backlog_items.append(
            _debt_item(
                source="operations",
                category=str(issue.get("category", "ops_finding")),
                severity=str(issue.get("severity", "low")),
                message=str(issue.get("message", "Operational issue detected.")),
            )
        )

    for env_entry in code_env_update_plan.get("environments", []):
        if not isinstance(env_entry, Mapping):
            continue
        priority_score = int(env_entry.get("priority_score", 0) or 0)
        if priority_score <= 0:
            continue
        severity = "high" if priority_score >= 4 else "medium"
        backlog_items.append(
            _debt_item(
                source="code_env",
                category="dependency_cleanup",
                severity=severity,
                message=(
                    f"Code env {env_entry.get('environment')} needs dependency cleanup "
                    f"before the next production iteration."
                ),
                effort="medium",
                owner_hint="platform_ops",
                impact_bonus=priority_score,
            )
        )

    ordered_items = sorted(
        backlog_items,
        key=lambda item: (-int(item["priority_score"]), str(item["source"]), str(item["title"])),
    )
    return {
        "project_key": project_key,
        "backlog": ordered_items,
        "summary": (
            f"Prioritized {len(ordered_items)} technical-debt item(s) for {project_key}."
        ),
    }


def _combine_recipe_code(recipe_details: Sequence[Mapping[str, Any]]) -> str:
    return "\n".join(
        str(recipe.get("code"))
        for recipe in recipe_details
        if isinstance(recipe.get("code"), str)
    )


def _find_benchmark_candidates(
    dataset_schemas: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for dataset_name, schema in dataset_schemas.items():
        column_names = _column_names(schema)
        if column_names & _BENCHMARK_QUERY_COLUMNS and column_names & _BENCHMARK_ANSWER_COLUMNS:
            candidates.append(
                {
                    "dataset_name": dataset_name,
                    "query_columns": sorted(column_names & _BENCHMARK_QUERY_COLUMNS),
                    "answer_columns": sorted(column_names & _BENCHMARK_ANSWER_COLUMNS),
                }
            )
    return candidates


def _column_names(schema: Mapping[str, Any]) -> set[str]:
    columns = schema.get("columns", [])
    if not isinstance(columns, Sequence) or isinstance(columns, (str, bytes)):
        return set()
    return {
        str(column.get("name")).lower()
        for column in columns
        if isinstance(column, Mapping) and column.get("name")
    }


def _collect_column_names(dataset_schemas: Mapping[str, Mapping[str, Any]]) -> set[str]:
    column_names: set[str] = set()
    for schema in dataset_schemas.values():
        column_names.update(_column_names(schema))
    return column_names


def _risk_categories(rag_audit: Mapping[str, Any]) -> set[str]:
    categories: set[str] = set()
    risks = rag_audit.get("main_risks", [])
    if not isinstance(risks, Sequence) or isinstance(risks, (str, bytes)):
        return categories
    for risk in risks:
        if isinstance(risk, Mapping) and risk.get("category"):
            categories.add(str(risk["category"]))
    return categories


def _penalty_for_risks(categories: set[str], penalty_map: Mapping[str, int]) -> int:
    return sum(penalty for category, penalty in penalty_map.items() if category in categories)


def _dimension(name: str, score: int, evidence: Sequence[str]) -> dict[str, Any]:
    normalized_score = _clamp_score(score)
    return {
        "name": name,
        "score": normalized_score,
        "status": _status_from_score(normalized_score),
        "evidence": [item for item in evidence if item],
    }


def _status_from_score(score: int) -> str:
    if score >= 80:
        return "strong"
    if score >= 60:
        return "usable"
    if score >= 40:
        return "fragile"
    return "at_risk"


def _quality_tier(score: int) -> str:
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "good"
    if score >= 55:
        return "needs_attention"
    return "critical"


def _clamp_score(score: int) -> int:
    return max(0, min(score, 100))


def _deduplicated_strings(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _resolve_strategy_names(strategies: Sequence[str] | None) -> list[str]:
    if not strategies:
        return list(_DEFAULT_CHUNKING_STRATEGIES)
    aliases = {
        "balanced": "balanced_rag",
        "balanced_rag": "balanced_rag",
        "high_recall": "high_recall",
        "recall": "high_recall",
        "low_latency": "low_latency",
        "latency": "low_latency",
        "citation": "citation_focused",
        "citation_focused": "citation_focused",
    }
    resolved: list[str] = []
    for strategy in strategies:
        canonical = aliases.get(strategy.lower())
        if canonical and canonical not in resolved:
            resolved.append(canonical)
    return resolved or list(_DEFAULT_CHUNKING_STRATEGIES)


def _recommend_chunking_strategy(current_strategy: Mapping[str, Any]) -> str:
    chunk_size = current_strategy.get("chunk_size")
    top_k = current_strategy.get("top_k")
    if isinstance(chunk_size, int) and chunk_size > 1800:
        return "balanced_rag"
    if isinstance(top_k, int) and top_k > 20:
        return "low_latency"
    if current_strategy.get("chunk_overlap") in {0, None}:
        return "citation_focused"
    return "high_recall"


def _extract_int(text: str, pattern: str) -> int | None:
    match = re.search(pattern, text)
    if match is None:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _detect_splitter(text: str) -> str | None:
    splitter_patterns = (
        ("recursive_character", r"RecursiveCharacterTextSplitter"),
        ("token", r"TokenTextSplitter"),
        ("markdown", r"MarkdownHeaderTextSplitter"),
        ("semantic", r"semantic"),
    )
    for splitter_name, pattern in splitter_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return splitter_name
    return None


def _detect_index_types(text: str) -> list[str]:
    detected: list[str] = []
    for pattern in _INDEX_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            if match not in detected:
                detected.append(match)
    return detected


def _extract_embedding_model_names(text: str) -> list[str]:
    patterns = (
        r"SentenceTransformer\(\s*[\"']([^\"']+)[\"']",
        r"model(?:_name)?\s*=\s*[\"']([^\"']+)[\"']",
        r"text-embedding-[A-Za-z0-9-]+",
    )
    model_names: list[str] = []
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if isinstance(matches, str):
            matches = [matches]
        for match in matches:
            candidate = match if isinstance(match, str) else ""
            if candidate and candidate not in model_names:
                model_names.append(candidate)
    return model_names


def _choose_embedding_dataset(dataset_names: Sequence[str]) -> str | None:
    lowered_pairs = [(name, name.lower()) for name in dataset_names]
    for original, lowered in lowered_pairs:
        if "chunk" in lowered or "embedding" in lowered:
            return original
    return dataset_names[0] if dataset_names else None


def _contains_any(text: str, tokens: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in tokens)


def _has_any(values: set[str], candidates: set[str]) -> bool:
    return bool(values & candidates)


def _mermaid_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def _mermaid_label(node_type: str, node_name: str) -> str:
    label = f"{node_type}: {node_name}"
    if node_type == "recipe":
        return f'("{label}")'
    if node_type == "managed_folder":
        return f'[["{label}"]]'
    if node_type == "scenario":
        return f'{{"{label}"}}'
    return f'["{label}"]'


def _score_from_issue_list(raw_issues: Any) -> int:
    if not isinstance(raw_issues, Sequence) or isinstance(raw_issues, (str, bytes)):
        return 100
    penalties = {"high": 20, "medium": 10, "low": 4}
    total_penalty = 0
    for issue in raw_issues:
        if not isinstance(issue, Mapping):
            continue
        severity = str(issue.get("severity", "low"))
        total_penalty += penalties.get(severity, 4)
    return _clamp_score(100 - total_penalty)


def _score_code_env_plan(code_env_update_plan: Mapping[str, Any]) -> int:
    environments = code_env_update_plan.get("environments", [])
    if not isinstance(environments, Sequence) or isinstance(environments, (str, bytes)):
        return 100
    penalty = sum(
        int(environment.get("priority_score", 0) or 0) * 5
        for environment in environments
        if isinstance(environment, Mapping)
    )
    return _clamp_score(100 - penalty)


def _debt_item(
    *,
    source: str,
    category: str,
    severity: str,
    message: str,
    recommendation: str | None = None,
    effort: str | None = None,
    owner_hint: str | None = None,
    impact_bonus: int = 0,
) -> dict[str, Any]:
    severity_weights = {"high": 9, "medium": 6, "low": 3}
    default_effort = {"high": "medium", "medium": "small", "low": "small"}
    owner_by_source = {
        "flow": "data_engineering",
        "rag": "ml_platform",
        "operations": "platform_ops",
        "code_env": "platform_ops",
    }
    priority_score = severity_weights.get(severity, 3) + impact_bonus
    title = category.replace("_", " ").strip().title()
    priority_bucket = "now" if priority_score >= 9 else "next" if priority_score >= 6 else "later"
    return {
        "title": title,
        "source": source,
        "category": category,
        "severity": severity,
        "priority_score": priority_score,
        "priority_bucket": priority_bucket,
        "effort": effort or default_effort.get(severity, "small"),
        "owner_hint": owner_hint or owner_by_source.get(source, "project_owner"),
        "message": message,
        "recommendation": recommendation or message,
    }


def _match_recommendation(recommendations: Sequence[str], category: str) -> str | None:
    normalized_category = category.replace("_", " ").lower()
    for recommendation in recommendations:
        if normalized_category.split(" ")[0] in recommendation.lower():
            return recommendation
    return recommendations[0] if recommendations else None
