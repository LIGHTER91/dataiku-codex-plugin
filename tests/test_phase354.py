from __future__ import annotations

import pytest

from dataiku_codex_mcp.config import OperationMode
from dataiku_codex_mcp.errors import PermissionDeniedError
from dataiku_codex_mcp.server import build_app_context, build_tool_registry


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
            "enable_write_tools": True,
        }
    )


def _seed_ml_task(adapter: object) -> dict[str, object]:
    return adapter.run_ml_command("A", "orders", "xgb")["ml_task"]


def test_route_ml_intent_resolves_bootstrap_command(
    settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_route_ml_intent").handler(
        "setup xgboost on project A using dataset orders for is_repeat_customer"
    )

    assert payload["ok"] is True
    assert payload["data"]["intent_type"] == "bootstrap_ml_command"
    assert payload["data"]["command_name"] == "xgboost_prediction_flow"
    assert payload["data"]["can_execute"] is True


def test_run_routed_ml_intent_requires_approval(
    write_settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    with pytest.raises(PermissionDeniedError):
        registry.get("dataiku_run_routed_ml_intent").handler(
            "setup xgboost on project A using dataset orders for is_repeat_customer",
            None,
            None,
        )


def test_run_routed_ml_intent_bootstraps_ml_task(
    write_settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_run_routed_ml_intent").handler(
        "setup xgboost on project A using dataset orders for is_repeat_customer",
        None,
        None,
        True,
        "Approved routed bootstrap.",
    )

    assert payload["ok"] is True
    assert payload["data"]["ml_task"]["algorithm_enabled"] == "XGBOOST_CLASSIFICATION"
    assert payload["data"]["route"]["intent_type"] == "bootstrap_ml_command"


def test_route_and_run_train_latest_task(
    execute_settings: object,
    adapter: object,
) -> None:
    seeded_task = _seed_ml_task(adapter)
    registry = build_tool_registry(build_app_context(settings=execute_settings, dataiku=adapter))

    route_payload = registry.get("dataiku_route_ml_intent").handler(
        "train latest task on project A"
    )
    run_payload = registry.get("dataiku_run_routed_ml_intent").handler(
        "train latest task on project A",
        None,
        None,
        True,
        "Approved routed training.",
    )

    assert route_payload["data"]["analysis_id"] == seeded_task["analysis_id"]
    assert run_payload["data"]["trained"] is True
    assert run_payload["data"]["trained_model_ids"] == ["model_001"]


def test_route_and_run_deploy_best_model(
    write_settings: object,
    execute_settings: object,
    adapter: object,
) -> None:
    seeded_task = _seed_ml_task(adapter)
    execute_registry = build_tool_registry(
        build_app_context(settings=execute_settings, dataiku=adapter)
    )
    execute_registry.get("dataiku_train_ml_task").handler(
        "A",
        seeded_task["analysis_id"],
        seeded_task["ml_task_id"],
        None,
        None,
        False,
        True,
        "Approved training before deploy.",
    )

    write_registry = build_tool_registry(
        build_app_context(settings=write_settings, dataiku=adapter)
    )
    route_payload = write_registry.get("dataiku_route_ml_intent").handler(
        "deploy best model on project A"
    )
    run_payload = write_registry.get("dataiku_run_routed_ml_intent").handler(
        "deploy best model on project A",
        None,
        None,
        True,
        "Approved routed deployment.",
    )

    assert route_payload["data"]["intent_type"] == "deploy_best_model"
    assert route_payload["data"]["model_id"] == "model_001"
    assert run_payload["data"]["deployed"] is True
    assert run_payload["data"]["saved_model_name"].endswith("_saved_model")
