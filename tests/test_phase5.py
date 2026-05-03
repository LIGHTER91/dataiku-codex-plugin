from __future__ import annotations

import json

import pytest

from dataiku_codex_mcp.server import build_app_context, build_tool_registry, main


def test_generate_project_readme_contains_inventory(adapter: object) -> None:
    payload = adapter.generate_project_readme("A")

    markdown = payload["markdown"]
    assert "# Alpha" in markdown
    assert "## Datasets" in markdown
    assert "`orders`" in markdown
    assert "## Scenarios" in markdown


def test_generate_flow_documentation_contains_topology(adapter: object) -> None:
    payload = adapter.generate_flow_documentation("A")

    markdown = payload["markdown"]
    assert "## Topological Order" in markdown
    assert "recipe:build_chunks" in markdown
    assert "## Flow Health" in markdown


def test_generate_troubleshooting_report_contains_findings(adapter: object) -> None:
    payload = adapter.generate_troubleshooting_report("A", focus="rag")

    markdown = payload["markdown"]
    assert "# Troubleshooting Report: Alpha" in markdown
    assert "Focus: rag" in markdown
    assert "sentence-transformers" in markdown
    assert "embed_documents" in markdown


def test_generate_rag_audit_report_contains_risks(adapter: object) -> None:
    payload = adapter.generate_rag_audit_report("A")

    markdown = payload["markdown"]
    assert "# RAG Audit Report: Alpha" in markdown
    assert "RAG pipeline detected: True" in markdown
    assert "Chunk overlap is missing" in markdown


def test_generate_project_readme_tool_redacts_secret(adapter: object, settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_generate_project_readme").handler("A")

    dumped = json.dumps(payload)
    assert "super-secret" not in dumped


def test_generate_project_readme_command_returns_json(
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
            "generate-project-readme",
            "A",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["markdown"].startswith("# Alpha")


def test_generate_troubleshooting_report_command_returns_json(
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
            "generate-troubleshooting-report",
            "A",
            "--focus",
            "rag",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "Troubleshooting Report" in payload["data"]["markdown"]
