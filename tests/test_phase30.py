from __future__ import annotations

import json

import pytest

from dataiku_codex_mcp.server import build_app_context, build_tool_registry, main


def test_run_rag_eval_returns_analysis_first_report(
    settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_run_rag_eval").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["execution_mode"] == "analysis_only"
    assert payload["data"]["benchmark_ready"] is False
    assert "vector_store" in payload["data"]["detected_components"]
    assert payload["data"]["overall_score"] <= 100


def test_compare_chunking_strategies_recommends_balanced_profile(
    settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_compare_chunking_strategies").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["current_strategy"]["chunk_size"] == 2500
    assert payload["data"]["recommended_strategy"] == "balanced_rag"
    assert payload["data"]["strategy_comparisons"][0]["score"] <= 100


def test_inspect_vector_store_detects_faiss_and_missing_normalization(
    settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_inspect_vector_store").handler("A")

    assert payload["ok"] is True
    assert "faiss" in payload["data"]["providers"]
    assert "IndexFlatIP" in payload["data"]["index_types"]
    assert payload["data"]["normalization_detected"] is False


def test_monitor_embedding_drift_flags_missing_lineage_fields(
    settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_monitor_embedding_drift").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["reference_dataset_name"] == "chunks"
    assert payload["data"]["tracking_coverage"]["embedding_model"] is False
    assert payload["data"]["risk_items"]


def test_audit_prompt_injection_reports_missing_guardrails(
    settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_audit_prompt_injection").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["risk_level"] == "high"
    assert payload["data"]["guardrails"]["content_sanitization"] is False
    assert payload["data"]["findings"]


def test_generate_architecture_diagram_returns_mermaid(
    settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_generate_architecture_diagram").handler("A")

    assert payload["ok"] is True
    assert "graph TD" in payload["data"]["mermaid"]
    assert "dataset: orders" in payload["data"]["mermaid"]
    assert "```mermaid" in payload["data"]["diagram_markdown"]


def test_score_project_quality_returns_weighted_breakdown(
    settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_score_project_quality").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["quality_score"] <= 100
    assert payload["data"]["quality_tier"] in {
        "excellent",
        "good",
        "needs_attention",
        "critical",
    }
    assert len(payload["data"]["breakdown"]) == 5


def test_prioritize_technical_debt_returns_sorted_backlog(
    settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_prioritize_technical_debt").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["backlog"]
    assert payload["data"]["backlog"][0]["priority_score"] >= (
        payload["data"]["backlog"][-1]["priority_score"]
    )


def test_run_rag_eval_cli_returns_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    settings: object,
    adapter: object,
) -> None:
    monkeypatch.setattr(
        "dataiku_codex_mcp.server.build_app_context",
        lambda settings: build_app_context(settings=settings, dataiku=adapter),
    )

    exit_code = main(
        [
            "--env-file",
            "examples/sample_env.example",
            "run-rag-eval",
            "A",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["execution_mode"] == "analysis_only"
