from __future__ import annotations

import json

import pytest

from dataiku_codex_mcp.config import OperationMode
from dataiku_codex_mcp.errors import DataikuAPIError, PermissionDeniedError
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
            "enable_write_tools": True,
        }
    )


def _seed_deployed_saved_model(
    adapter: object,
    *,
    command_name: str,
    prepared_dataset_name: str | None = None,
    prepare_recipe_name: str | None = None,
    saved_model_name: str,
    accuracy: float,
) -> dict[str, object]:
    ml_task = adapter.run_ml_command(
        "A",
        "orders",
        command_name,
        prepared_dataset_name=prepared_dataset_name,
        prepare_recipe_name=prepare_recipe_name,
    )["ml_task"]
    train_payload = adapter.train_ml_task(
        "A",
        ml_task["analysis_id"],
        ml_task["ml_task_id"],
        session_name=f"Train {saved_model_name}",
    )
    project = adapter.client.project_handles["A"]
    task = project.ml_tasks[ml_task["ml_task_id"]]
    task.trained_models[-1]["snippet"]["metrics"]["accuracy"] = accuracy
    task.trained_models[-1]["snippet"]["metrics"]["auc"] = accuracy + 0.01
    deployment = adapter.deploy_trained_model_to_flow(
        "A",
        ml_task["analysis_id"],
        ml_task["ml_task_id"],
        model_id=train_payload["trained_model_ids"][0],
        saved_model_name=saved_model_name,
        train_dataset="orders",
    )
    return {
        "ml_task": ml_task,
        "train": train_payload,
        "deployment": deployment,
    }


def test_saved_model_listing_and_details(
    settings: object,
    adapter: object,
) -> None:
    seeded = _seed_deployed_saved_model(
        adapter,
        command_name="xgb",
        saved_model_name="orders_saved_model",
        accuracy=0.84,
    )
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    list_payload = registry.get("dataiku_list_saved_models").handler("A")
    details_payload = registry.get("dataiku_get_saved_model_details").handler(
        "A",
        seeded["deployment"]["saved_model_id"],
    )

    assert list_payload["ok"] is True
    assert list_payload["data"]["saved_models"][0]["name"] == "orders_saved_model"
    assert details_payload["data"]["active_version_metrics"]["accuracy"] == 0.84
    assert details_payload["data"]["primary_metric"]["metric_name"] == "accuracy"


def test_create_prediction_scoring_recipe_requires_approval(
    write_settings: object,
    adapter: object,
) -> None:
    seeded = _seed_deployed_saved_model(
        adapter,
        command_name="xgb",
        saved_model_name="orders_saved_model",
        accuracy=0.84,
    )
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    with pytest.raises(PermissionDeniedError) as exc_info:
        registry.get("dataiku_create_prediction_scoring_recipe").handler(
            "A",
            seeded["deployment"]["saved_model_id"],
            "orders",
            "score_orders",
            "orders_scored",
        )

    assert (
        exc_info.value.details["dry_run_summary"]["operation"]
        == "create_prediction_scoring_recipe"
    )


def test_create_scoring_recipe_evaluation_and_report(
    write_settings: object,
    execute_settings: object,
    adapter: object,
) -> None:
    seeded = _seed_deployed_saved_model(
        adapter,
        command_name="xgb",
        saved_model_name="orders_saved_model",
        accuracy=0.84,
    )
    write_registry = build_tool_registry(
        build_app_context(settings=write_settings, dataiku=adapter)
    )
    execute_registry = build_tool_registry(
        build_app_context(settings=execute_settings, dataiku=adapter)
    )

    scoring_payload = write_registry.get("dataiku_create_prediction_scoring_recipe").handler(
        "A",
        seeded["deployment"]["saved_model_id"],
        "orders",
        "score_orders",
        "orders_scored",
        None,
        True,
        "Approved scoring recipe creation.",
    )
    evaluation_payload = execute_registry.get("dataiku_create_model_evaluation").handler(
        "A",
        seeded["deployment"]["saved_model_id"],
        "orders",
        None,
        None,
        "evaluate_orders_model",
        "orders_eval_scored",
        "orders_eval_metrics",
        ["accuracy", "auc"],
        True,
        True,
        "Approved evaluation recipe creation and run.",
    )
    report_payload = write_registry.get("dataiku_generate_model_evaluation_report").handler(
        "A",
        evaluation_payload["data"]["evaluation_store_id"],
        None,
        None,
    )

    assert scoring_payload["data"]["created"] is True
    assert scoring_payload["data"]["recipe_type"] == "prediction_scoring"
    assert evaluation_payload["data"]["created"] is True
    assert evaluation_payload["data"]["evaluation_store"]["latest_metrics"]["accuracy"] == 0.84
    assert "Model Evaluation Report" in report_payload["data"]["report_markdown"]


def test_compare_saved_models_picks_best_metric(
    write_settings: object,
    adapter: object,
) -> None:
    first = _seed_deployed_saved_model(
        adapter,
        command_name="xgb",
        saved_model_name="orders_saved_model_xgb",
        accuracy=0.84,
    )
    second = _seed_deployed_saved_model(
        adapter,
        command_name="rf",
        prepared_dataset_name="orders_prepared_rf",
        prepare_recipe_name="prepare_orders_rf",
        saved_model_name="orders_saved_model_rf",
        accuracy=0.91,
    )
    registry = build_tool_registry(build_app_context(settings=write_settings, dataiku=adapter))

    payload = registry.get("dataiku_compare_saved_models").handler(
        "A",
        [
            first["deployment"]["saved_model_id"],
            second["deployment"]["saved_model_id"],
        ],
        "accuracy",
    )

    assert payload["ok"] is True
    assert payload["data"]["best_model"]["name"] == "orders_saved_model_rf"
    assert payload["data"]["metric_name"] == "accuracy"


def test_list_saved_models_cli_returns_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    write_settings: object,
    adapter: object,
) -> None:
    _seed_deployed_saved_model(
        adapter,
        command_name="xgb",
        saved_model_name="orders_saved_model",
        accuracy=0.84,
    )
    monkeypatch.setattr(
        "dataiku_codex_mcp.server.build_app_context",
        lambda settings: build_app_context(settings=write_settings, dataiku=adapter),
    )

    exit_code = main(
        [
            "--env-file",
            "examples/sample_env.example",
            "list-saved-models",
            "A",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["data"]["saved_models"][0]["name"] == "orders_saved_model"


def test_saved_model_details_support_get_raw_like_objects(
    settings: object,
    adapter: object,
) -> None:
    project = adapter.client.project_handles["A"]

    class RawDetails:
        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = dict(payload)

        def get_raw(self) -> dict[str, object]:
            return dict(self._payload)

    class RawMetrics:
        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = dict(payload)

        def get_raw(self) -> dict[str, object]:
            return dict(self._payload)

    class RawSavedModel:
        def __init__(self) -> None:
            self.id = "RAW1"
            self.name = "orders_saved_model_raw"
            self.prediction_type = "BINARY_CLASSIFICATION"

        def list_versions(self) -> list[dict[str, object]]:
            return [{"id": "v1", "label": "Version 1", "active": True}]

        def get_active_version(self) -> dict[str, object]:
            return {"id": "v1", "active": True}

        def get_version_details(self, version_id: str) -> RawDetails:
            assert version_id == "v1"
            return RawDetails({"versionId": version_id, "foo": "bar"})

        def get_metric_values(self, version_id: str) -> RawMetrics:
            assert version_id == "v1"
            return RawMetrics(
                {
                    "metrics": [
                        {
                            "metric": {"metricType": "accuracy"},
                            "meta": {"name": "accuracy"},
                            "lastValues": [{"value": "0.91"}],
                        },
                        {
                            "metric": {"metricType": "auc"},
                            "meta": {"name": "auc"},
                            "lastValues": [{"value": "0.93"}],
                        },
                    ]
                }
            )

    project.saved_models["RAW1"] = RawSavedModel()
    registry = build_tool_registry(build_app_context(settings=settings, dataiku=adapter))

    payload = registry.get("dataiku_get_saved_model_details").handler("A", "RAW1")

    assert payload["ok"] is True
    assert payload["data"]["active_version_details"]["foo"] == "bar"
    assert payload["data"]["active_version_metrics"]["accuracy"] == 0.91
    assert payload["data"]["primary_metric"]["metric_name"] == "accuracy"


def test_create_model_evaluation_survives_pending_store_details(
    execute_settings: object,
    adapter: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = _seed_deployed_saved_model(
        adapter,
        command_name="xgb",
        saved_model_name="orders_saved_model_pending_eval",
        accuracy=0.84,
    )

    def raise_pending_details(project_key: str, evaluation_store_id: str) -> dict[str, object]:
        raise DataikuAPIError("Evaluation details are not ready yet.")

    monkeypatch.setattr(adapter, "get_model_evaluation_store_details", raise_pending_details)
    registry = build_tool_registry(
        build_app_context(settings=execute_settings, dataiku=adapter)
    )

    payload = registry.get("dataiku_create_model_evaluation").handler(
        "A",
        seeded["deployment"]["saved_model_id"],
        "orders",
        None,
        None,
        "evaluate_orders_model_pending",
        "orders_eval_scored_pending",
        "orders_eval_metrics_pending",
        ["accuracy", "auc"],
        True,
        True,
        "Approved evaluation recipe creation and run.",
    )

    assert payload["ok"] is True
    assert payload["data"]["created"] is True
    assert payload["data"]["evaluation_store"]["details_warning"] == (
        "Evaluation details are not ready yet."
    )
