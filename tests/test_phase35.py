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


def test_suggest_prediction_targets_finds_schema_candidates(
    adapter: object,
    settings: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_suggest_prediction_targets").handler("A", "orders")

    assert payload["ok"] is True
    candidates = payload["data"]["candidates"]
    assert candidates[0]["target_variable"] == "is_repeat_customer"
    assert candidates[0]["prediction_type"] == "binary_classification"
    assert any(candidate["target_variable"] == "order_amount" for candidate in candidates)


def test_bootstrap_xgboost_flow_requires_approval(
    adapter: object,
    write_settings: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    with pytest.raises(PermissionDeniedError) as exc_info:
        registry.get("dataiku_bootstrap_xgboost_flow").handler(
            "A",
            "orders",
            "is_repeat_customer",
        )

    assert exc_info.value.details["dry_run_summary"]["operation"] == "bootstrap_xgboost_flow"


def test_bootstrap_xgboost_flow_creates_prepare_recipe_and_ml_task(
    adapter: object,
    write_settings: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_bootstrap_xgboost_flow").handler(
        "A",
        "orders",
        "is_repeat_customer",
        None,
        None,
        None,
        "PY_MEMORY",
        "DEFAULT",
        True,
        "User explicitly approved this action.",
    )

    assert payload["data"]["created"] is True
    assert payload["data"]["prepare_recipe"]["recipe_name"] == "prepare_orders_is_repeat_customer"
    assert payload["data"]["ml_task"]["algorithm_enabled"] == "XGBOOST_CLASSIFICATION"
    fake_project = adapter.client.get_project("A")
    assert "prepare_orders_is_repeat_customer" in fake_project.recipes
    assert "orders_prepared_is_repeat_customer" in fake_project.datasets
    assert len(fake_project.ml_tasks) == 1


def test_bootstrap_xgboost_flow_supports_regression_target(
    adapter: object,
    write_settings: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_bootstrap_xgboost_flow").handler(
        "A",
        "orders",
        "order_amount",
        None,
        None,
        "regression",
        "PY_MEMORY",
        "DEFAULT",
        True,
        "User explicitly approved this action.",
    )

    assert payload["data"]["prediction_type"] == "regression"
    assert payload["data"]["ml_task"]["algorithm_enabled"] == "XGBOOST_REGRESSION"


def test_bootstrap_xgboost_flow_command_returns_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    adapter: object,
    write_settings: object,
) -> None:
    monkeypatch.setattr(
        "dataiku_codex_mcp.server.build_app_context",
        lambda settings: build_app_context(settings=write_settings, dataiku=adapter),
    )

    exit_code = main(
        [
            "--env-file",
            "examples/sample_env.example",
            "bootstrap-xgboost-flow",
            "A",
            "orders",
            "is_repeat_customer",
            "--approved",
            "--approval-reason",
            "User explicitly approved this action.",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["created"] is True
    assert payload["data"]["ml_task"]["algorithm_enabled"] == "XGBOOST_CLASSIFICATION"
