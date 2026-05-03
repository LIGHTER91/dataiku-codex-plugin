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


def test_create_scenario_requires_approval(adapter: object, write_settings: object) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    with pytest.raises(PermissionDeniedError) as exc_info:
        registry.get("dataiku_create_scenario").handler(
            "A",
            "nightly_orders",
            "custom_python",
            None,
            ["orders"],
            False,
        )

    assert exc_info.value.details["dry_run_summary"]["operation"] == "create_scenario"


def test_create_custom_python_scenario_creates_scenario(
    adapter: object,
    write_settings: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_create_scenario").handler(
        "A",
        "nightly_orders",
        "custom_python",
        None,
        ["orders"],
        False,
        True,
        "User explicitly approved this action.",
    )

    assert payload["data"]["created"] is True
    scenario = adapter.client.get_project("A").get_scenario("nightly_orders")
    assert scenario.scenario_type == "custom_python"
    assert 'scenario.build_dataset("orders"' in scenario.code


def test_create_step_based_scenario_creates_steps(
    adapter: object,
    write_settings: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_create_scenario").handler(
        "A",
        "step_build_orders",
        "step_based",
        None,
        ["orders"],
        True,
        True,
        "User explicitly approved this action.",
    )

    assert payload["data"]["created"] is True
    scenario = adapter.client.get_project("A").get_scenario("step_build_orders")
    assert scenario.scenario_type == "step_based"
    assert scenario.steps[0]["params"]["builds"][0]["itemId"] == "orders"


def test_create_scenario_command_returns_json(
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
            "create-scenario",
            "A",
            "cli_orders_scenario",
            "--build-datasets",
            "orders",
            "--approved",
            "--approval-reason",
            "User explicitly approved this action.",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["created"] is True
    assert payload["data"]["scenario_id"] == "cli_orders_scenario"
