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
        }
    )


def test_list_ml_commands_returns_catalog(settings: object, adapter: object) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_list_ml_commands").handler()

    assert payload["ok"] is True
    command_names = [command["name"] for command in payload["data"]["commands"]]
    assert command_names == [
        "xgboost_prediction_flow",
        "lightgbm_prediction_flow",
        "random_forest_prediction_flow",
        "logistic_regression_prediction_flow",
    ]


def test_plan_ml_command_auto_selects_target(settings: object, adapter: object) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_plan_ml_command").handler(
        "A",
        "orders",
        "xgb",
    )

    assert payload["ok"] is True
    assert payload["data"]["command"]["name"] == "xgboost_prediction_flow"
    assert payload["data"]["target_variable"] == "is_repeat_customer"
    assert payload["data"]["auto_selected_target"] is True
    assert payload["data"]["recommended_algorithm"] == "XGBOOST_CLASSIFICATION"


def test_run_ml_command_requires_approval(
    write_settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    with pytest.raises(PermissionDeniedError) as exc_info:
        registry.get("dataiku_run_ml_command").handler(
            "A",
            "orders",
            "lightgbm_prediction_flow",
        )

    assert exc_info.value.details["dry_run_summary"]["operation"] == "run_ml_command"


def test_run_ml_command_executes_random_forest_baseline(
    write_settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_run_ml_command").handler(
        "A",
        "orders",
        "rf",
        None,
        None,
        None,
        None,
        None,
        None,
        True,
        "User explicitly approved this action.",
    )

    assert payload["data"]["created"] is True
    assert payload["data"]["command"]["name"] == "random_forest_prediction_flow"
    assert payload["data"]["prepare_recipe"]["output_connection"] == "dataiku-managed-storage"
    assert payload["data"]["prepare_recipe"]["materialized_output"] is True
    assert (
        payload["data"]["prepare_recipe"]["build_job_id"]
        == "Build_orders_prepared_is_repeat_customer"
    )
    assert payload["data"]["ml_task"]["input_dataset"] == "orders_prepared_is_repeat_customer"
    assert payload["data"]["ml_task"]["algorithm_enabled"] == "RANDOM_FOREST_CLASSIFICATION"


def test_run_ml_command_supports_lightgbm_regression(
    write_settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_run_ml_command").handler(
        "A",
        "orders",
        "lightgbm",
        "order_amount",
        None,
        None,
        "regression",
        None,
        None,
        True,
        "User explicitly approved this action.",
    )

    assert payload["data"]["prediction_type"] == "regression"
    assert payload["data"]["ml_task"]["algorithm_enabled"] == "LIGHTGBM_REGRESSION"


def test_plan_ml_command_cli_returns_json(
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
            "plan-ml-command",
            "A",
            "orders",
            "logit",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["command"]["name"] == "logistic_regression_prediction_flow"
    assert payload["data"]["recommended_algorithm"] == "LOGISTIC_REGRESSION"
