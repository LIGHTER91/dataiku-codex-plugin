from __future__ import annotations

import json

import pytest

from dataiku_codex_mcp.config import OperationMode
from dataiku_codex_mcp.errors import PermissionDeniedError
from dataiku_codex_mcp.server import build_app_context, build_tool_registry, main


@pytest.fixture
def write_settings(settings: object) -> object:
    return settings.model_copy(
        update={
            "mode": OperationMode.WRITE,
            "enable_write_tools": True,
            "enable_execute_tools": True,
        }
    )


@pytest.fixture
def execute_settings(settings: object) -> object:
    return settings.model_copy(
        update={
            "mode": OperationMode.EXECUTE,
            "enable_execute_tools": True,
        }
    )


def _seed_ml_task(adapter: object) -> dict[str, object]:
    return adapter.run_ml_command("A", "orders", "xgb")["ml_task"]


def test_list_ml_tasks_returns_created_task(
    write_settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))
    seeded_task = _seed_ml_task(adapter)

    payload = registry.get("dataiku_list_ml_tasks").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["ml_tasks"][0]["ml_task_id"] == seeded_task["ml_task_id"]
    assert payload["data"]["ml_tasks"][0]["input_dataset"] == "orders_prepared_is_repeat_customer"


def test_get_ml_task_details_reports_enabled_algorithms(
    write_settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))
    seeded_task = _seed_ml_task(adapter)

    payload = registry.get("dataiku_get_ml_task_details").handler(
        "A",
        seeded_task["analysis_id"],
        seeded_task["ml_task_id"],
    )

    assert payload["ok"] is True
    assert payload["data"]["enabled_algorithms"] == ["XGBOOST"]
    assert payload["data"]["trained_models_count"] == 0


def test_train_ml_task_requires_approval(
    execute_settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=execute_settings, dataiku=adapter))
    seeded_task = _seed_ml_task(adapter)

    with pytest.raises(PermissionDeniedError) as exc_info:
        registry.get("dataiku_train_ml_task").handler(
            "A",
            seeded_task["analysis_id"],
            seeded_task["ml_task_id"],
        )

    assert exc_info.value.details["dry_run_summary"]["operation"] == "train_ml_task"


def test_train_and_deploy_trained_model_to_flow(
    write_settings: object,
    execute_settings: object,
    adapter: object,
) -> None:
    seeded_task = _seed_ml_task(adapter)
    execute_registry = build_tool_registry(
        build_app_context(settings=execute_settings, dataiku=adapter)
    )
    train_payload = execute_registry.get("dataiku_train_ml_task").handler(
        "A",
        seeded_task["analysis_id"],
        seeded_task["ml_task_id"],
        "Baseline session",
        "Train the first reusable ML task",
        False,
        True,
        "User explicitly approved this action.",
    )

    assert train_payload["data"]["trained"] is True
    assert train_payload["data"]["trained_model_ids"] == ["model_001"]

    write_registry = build_tool_registry(
        build_app_context(settings=write_settings, dataiku=adapter)
    )
    list_payload = write_registry.get("dataiku_list_trained_models").handler(
        "A",
        seeded_task["analysis_id"],
        seeded_task["ml_task_id"],
    )
    assert list_payload["data"]["models"][0]["algorithm"] == "XGBOOST_CLASSIFICATION"

    deploy_payload = write_registry.get("dataiku_deploy_trained_model_to_flow").handler(
        "A",
        seeded_task["analysis_id"],
        seeded_task["ml_task_id"],
        None,
        "orders_saved_model",
        None,
        None,
        True,
        True,
        "User explicitly approved this action.",
    )

    assert deploy_payload["data"]["deployed"] is True
    assert deploy_payload["data"]["saved_model_name"] == "orders_saved_model"
    assert deploy_payload["data"]["saved_model_id"] == "saved_model_001"


def test_list_ml_tasks_cli_returns_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    write_settings: object,
    adapter: object,
) -> None:
    seeded_adapter = adapter
    _seed_ml_task(seeded_adapter)
    monkeypatch.setattr(
        "dataiku_codex_mcp.server.build_app_context",
        lambda settings: build_app_context(settings=write_settings, dataiku=seeded_adapter),
    )

    exit_code = main(
        [
            "--env-file",
            "examples/sample_env.example",
            "list-ml-tasks",
            "A",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["ml_tasks"][0]["task_type"] == "PREDICTION"
