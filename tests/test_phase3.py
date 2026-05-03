from __future__ import annotations

import json

import pytest

from dataiku_codex_mcp.server import build_app_context, build_tool_registry, create_mcp_server, main


def test_generate_project_map_summarizes_objects(adapter: object) -> None:
    payload = adapter.generate_project_map("A")

    assert payload["summary"]
    assert len(payload["nodes"]) >= 5
    assert len(payload["edges"]) >= 4


def test_get_flow_graph_contains_folder_edge(adapter: object) -> None:
    graph = adapter.get_flow_graph("A")

    assert any(edge["source"] == "folder:RAW_DOCS" for edge in graph["edges"])
    assert any(node["id"] == "recipe:build_chunks" for node in graph["nodes"])


def test_analyze_flow_health_flags_missing_zones(adapter: object) -> None:
    health = adapter.analyze_flow_health("A")

    categories = {issue["category"] for issue in health["issues"]}
    assert "missing_flow_zones" in categories


def test_review_recipe_code_finds_managed_folder_and_vector_issues(adapter: object) -> None:
    review = adapter.review_recipe_code("A", "build_chunks")

    categories = {issue["category"] for issue in review["issues"]}
    assert "managed_folder_path" in categories
    assert "vector_normalization" in categories
    assert review["risk_level"] == "high"


def test_managed_folder_doctor_detects_non_local_get_path(adapter: object) -> None:
    diagnosis = adapter.managed_folder_doctor("A", folder_id="RAW_DOCS")

    issues = diagnosis["analyses"][0]["issues"]
    categories = {issue["category"] for issue in issues}
    assert "non_local_get_path" in categories


def test_code_env_doctor_reports_missing_package(adapter: object) -> None:
    diagnosis = adapter.code_env_doctor("rag-env")

    categories = {issue["category"] for issue in diagnosis["dependency_issues"]}
    assert "missing_embeddings_package" in categories
    assert "python_version" in categories


def test_detect_rag_pipeline_returns_key_components(adapter: object) -> None:
    detection = adapter.detect_rag_pipeline("A")

    assert detection["is_rag_pipeline"] is True
    assert "chunking" in detection["detected_components"]
    assert "vector_store" in detection["detected_components"]


def test_audit_rag_pipeline_flags_expected_risks(adapter: object) -> None:
    audit = adapter.audit_rag_pipeline("A", deep=True)

    categories = {risk["category"] for risk in audit["main_risks"]}
    assert "missing_overlap" in categories
    assert "missing_reranker" in categories
    assert "missing_evaluation" in categories


def test_create_mcp_server_smoke_test(adapter: object, settings: object) -> None:
    server = create_mcp_server(build_app_context(settings=settings, dataiku=adapter))

    assert server is not None


def test_flow_health_command_returns_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    adapter: object,
    settings: object,
) -> None:
    monkeypatch.setattr(
        "dataiku_codex_mcp.server.build_app_context",
        lambda settings: build_app_context(settings=settings, dataiku=adapter),
    )

    exit_code = main(
        [
            "--env-file",
            "examples/sample_env.example",
            "flow-health",
            "A",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["summary"]["issue_count"] >= 1


def test_audit_rag_pipeline_command_returns_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    adapter: object,
    settings: object,
) -> None:
    monkeypatch.setattr(
        "dataiku_codex_mcp.server.build_app_context",
        lambda settings: build_app_context(settings=settings, dataiku=adapter),
    )

    exit_code = main(
        [
            "--env-file",
            "examples/sample_env.example",
            "audit-rag-pipeline",
            "A",
            "--deep",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["deep"] is True
    assert payload["data"]["main_risks"]


def test_review_recipe_code_tool_redacts_secret(adapter: object, settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_review_recipe_code").handler("A", "build_chunks")

    dumped = json.dumps(payload)
    assert "super-secret" not in dumped
    assert payload["data"]["risk_level"] == "high"
