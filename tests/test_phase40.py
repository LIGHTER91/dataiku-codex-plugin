from __future__ import annotations

from dataiku_codex_mcp.server import build_app_context, build_tool_registry


def _seed_ops_assets(adapter: object) -> None:
    adapter.create_scenario(
        "A",
        "nightly_ops",
        scenario_type="step_based",
        build_datasets=["orders"],
        active=True,
    )
    ml_task = adapter.run_ml_command("A", "orders", "xgb")["ml_task"]
    adapter.train_ml_task("A", ml_task["analysis_id"], ml_task["ml_task_id"])
    adapter.deploy_trained_model_to_flow(
        "A",
        ml_task["analysis_id"],
        ml_task["ml_task_id"],
        model_id="model_001",
        saved_model_name="orders_saved_model",
        train_dataset="orders",
    )


def test_list_plugin_usages_returns_inventory(
    settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_list_plugin_usages").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["plugin_usages"][0]["plugin_id"] == "custom-rag-tools"


def test_generate_scenario_dependency_map_finds_edges(
    settings: object,
    adapter: object,
) -> None:
    _seed_ops_assets(adapter)
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_generate_scenario_dependency_map").handler("A")

    assert payload["ok"] is True
    assert any(edge["target"] == "dataset:orders" for edge in payload["data"]["edges"])


def test_plan_code_env_updates_returns_prioritized_plan(
    settings: object,
    adapter: object,
) -> None:
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_plan_code_env_updates").handler()

    assert payload["ok"] is True
    assert payload["data"]["environments"][0]["environment"] == "rag-env"
    assert payload["data"]["environments"][0]["priority_score"] >= 3


def test_generate_production_readiness_report_aggregates_findings(
    settings: object,
    adapter: object,
) -> None:
    _seed_ops_assets(adapter)
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_generate_production_readiness_report").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["score"] <= 100
    assert payload["data"]["readiness"] in {"ready_for_trial", "needs_attention", "not_ready"}
    assert payload["data"]["findings"]


def test_generate_cost_performance_report_returns_hotspots(
    settings: object,
    adapter: object,
) -> None:
    _seed_ops_assets(adapter)
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_generate_cost_performance_report").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["overall_pressure_score"] <= 100
    assert payload["data"]["cost_pressure_level"] in {"low", "medium", "high"}
    assert payload["data"]["metrics"]["ml_compute_pressure"] >= 0


def test_generate_production_readiness_checklist_returns_gate(
    settings: object,
    adapter: object,
) -> None:
    _seed_ops_assets(adapter)
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_generate_production_readiness_checklist").handler("A")

    assert payload["ok"] is True
    assert payload["data"]["readiness_gate"] in {"ready", "almost_ready", "blocked"}
    assert payload["data"]["total_items"] == len(payload["data"]["checklist"])


def test_generate_governance_documentation_returns_markdown(
    settings: object,
    adapter: object,
) -> None:
    _seed_ops_assets(adapter)
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_generate_governance_documentation").handler("A")

    assert payload["ok"] is True
    assert "Governance Notes" in payload["data"]["markdown"]
    assert payload["data"]["checklist_gate"] in {"ready", "almost_ready", "blocked"}
