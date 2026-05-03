from __future__ import annotations

import json

import pytest

from dataiku_codex_mcp.server import build_app_context, build_tool_registry, main


def test_list_scenarios_returns_trigger_metadata(adapter: object) -> None:
    scenarios = adapter.list_scenarios("A")

    assert len(scenarios) == 2
    backfill = next(item for item in scenarios if item["scenario_id"] == "backfill_rag")
    assert backfill["active"] is False
    assert backfill["trigger_type"] == "manual"


def test_get_scenario_runs_includes_failed_steps(adapter: object) -> None:
    payload = adapter.get_scenario_runs("A", "backfill_rag", limit=5)

    assert payload["scenario_id"] == "backfill_rag"
    assert payload["runs"][0]["outcome"] == "FAILED"
    assert payload["runs"][0]["failed_steps"] == ["embed_documents"]


def test_get_job_logs_detects_errors_and_truncates(adapter: object) -> None:
    payload = adapter.get_job_logs("A", job_id="job_build_embeddings", max_lines=3)

    categories = {item["category"] for item in payload["detected_errors"]}
    assert payload["truncated"] is True
    assert "package_import_error" in categories
    assert "code_env_error" in categories
    assert payload["probable_root_cause"] is not None


def test_explain_failure_for_run_detects_code_env_issue(adapter: object) -> None:
    payload = adapter.explain_failure("A", run_id="run_backfill_001", scenario_id="backfill_rag")

    assert payload["source_type"] == "scenario_run"
    assert any("code environment" in symptom.lower() for symptom in payload["symptoms"])
    assert any("package is missing" in cause.lower() for cause in payload["root_causes"])
    assert any("embed_documents" in evidence for evidence in payload["evidence"])


def test_job_logs_tool_redacts_secrets(adapter: object, settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_get_job_logs").handler("A", job_id="job_build_embeddings")

    dumped = json.dumps(payload)
    assert "job-secret-token" not in dumped
    assert "[REDACTED]" in dumped


def test_scenario_runs_command_returns_json(
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
            "scenario-runs",
            "A",
            "backfill_rag",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["runs"][0]["run_id"] == "run_backfill_001"


def test_explain_failure_command_returns_json(
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
            "explain-failure",
            "A",
            "--job-id",
            "job_build_embeddings",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["recommended_fixes"]
