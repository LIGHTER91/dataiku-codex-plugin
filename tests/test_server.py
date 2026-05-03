from __future__ import annotations

import json

import pytest

from dataiku_codex_mcp.server import build_app_context, build_tool_registry, main


def test_build_tool_registry_contains_phase_five_tools(
    adapter: object,
    settings: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    assert registry.names() == [
        "dataiku_analyze_flow_health",
        "dataiku_audit_rag_pipeline",
        "dataiku_code_env_doctor",
        "dataiku_create_managed_folder",
        "dataiku_create_project_documentation",
        "dataiku_create_python_recipe",
        "dataiku_create_scenario",
        "dataiku_detect_rag_pipeline",
        "dataiku_explain_failure",
        "dataiku_generate_flow_documentation",
        "dataiku_generate_project_map",
        "dataiku_generate_project_readme",
        "dataiku_generate_rag_audit_report",
        "dataiku_generate_troubleshooting_report",
        "dataiku_get_code_env_details",
        "dataiku_get_dataset_schema",
        "dataiku_get_flow_graph",
        "dataiku_get_instance_info",
        "dataiku_get_job_logs",
        "dataiku_get_managed_folder_info",
        "dataiku_get_project_summary",
        "dataiku_get_recipe_details",
        "dataiku_get_scenario_runs",
        "dataiku_list_code_envs",
        "dataiku_list_datasets",
        "dataiku_list_folder_files",
        "dataiku_list_managed_folders",
        "dataiku_list_projects",
        "dataiku_list_recipes",
        "dataiku_list_scenarios",
        "dataiku_managed_folder_doctor",
        "dataiku_ping",
        "dataiku_review_recipe_code",
        "dataiku_run_scenario",
        "dataiku_update_recipe_code",
        "dataiku_upload_file_to_folder",
    ]


def test_validate_config_command_returns_json(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--env-file",
            "examples/sample_env.example",
            "validate-config",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["settings"]["api_key"] == "[REDACTED]"


def test_ping_command_uses_cli_and_returns_json(
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
            "ping",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["data"]["reachable"] is True


def test_list_tools_command_returns_registered_tool_names(
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
            "list-tools",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert "dataiku_get_project_summary" in payload["data"]["tools"]


def test_project_summary_tool_returns_counts(adapter: object, settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_get_project_summary").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["datasets_count"] == 2
    assert payload["data"]["recipes_count"] == 2


def test_recipe_details_tool_redacts_secrets(adapter: object, settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_get_recipe_details").handler("A", "build_chunks")

    assert payload["ok"] is True
    assert "super-secret" not in payload["data"]["code"]
    assert "[REDACTED]" in payload["data"]["code"]


def test_folder_files_tool_can_limit_results(adapter: object, settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_list_folder_files").handler("A", "RAW_DOCS", limit=1)

    assert payload["ok"] is True
    assert payload["data"]["truncated"] is True
    assert len(payload["data"]["files"]) == 1


def test_project_summary_command_returns_json(
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
            "project-summary",
            "A",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["data"]["project_key"] == "A"
    assert payload["data"]["managed_folders_count"] == 1
