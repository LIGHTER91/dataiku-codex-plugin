"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from dataiku_codex_mcp.client import DataikuDSSAdapter
from dataiku_codex_mcp.config import AppSettings, OperationMode


class FakeDataset:
    """Fake dataset handle."""

    def __init__(
        self,
        name: str,
        dataset_type: str,
        connection: str,
        columns: list[dict[str, object]],
    ) -> None:
        self.name = name
        self.dataset_type = dataset_type
        self.connection = connection
        self.columns = columns

    def get_schema(self) -> dict[str, object]:
        return {"columns": self.columns}


class FakeRecipe:
    """Fake recipe handle."""

    def __init__(
        self,
        name: str,
        recipe_type: str,
        inputs: list[str],
        outputs: list[str],
        code: str,
        code_env_name: str | None = None,
        steps: list[dict[str, object]] | None = None,
        project: FakeProject | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.name = name
        self.recipe_type = recipe_type
        self.inputs = inputs
        self.outputs = outputs
        self.code = code
        self.code_env_name = code_env_name
        self.steps = list(steps or [])
        self.project = project
        self.metadata = dict(metadata or {})
        self.built = False

    def get_definition(self) -> dict[str, object]:
        return {
            "name": self.name,
            "type": self.recipe_type,
            "inputs": [{"ref": value} for value in self.inputs],
            "outputs": [{"ref": value} for value in self.outputs],
        }

    def get_settings(self) -> object:
        if self.recipe_type in {"prepare", "shaker"}:
            return FakePrepareRecipeSettings(self)
        return FakeRecipeSettings(self)

    def get_code(self) -> str:
        return self.code

    def run(self, wait: bool = True, no_fail: bool = False) -> FakeJob:
        del wait
        del no_fail
        self.built = True
        if self.recipe_type == "evaluation" and self.project is not None:
            saved_model_id = self.metadata.get("saved_model_id")
            evaluation_store_id = self.metadata.get("evaluation_store_id")
            evaluation_dataset = self.metadata.get("evaluation_dataset")
            if isinstance(saved_model_id, str) and isinstance(evaluation_store_id, str):
                saved_model = self.project.saved_models[saved_model_id]
                active_version_id = saved_model.get_active_version()
                metrics = saved_model.get_metric_values(active_version_id).get("metrics", {})
                if not isinstance(metrics, dict):
                    metrics = {}
                self.project.model_evaluation_stores[evaluation_store_id].add_evaluation(
                    saved_model_id=saved_model_id,
                    version_id=active_version_id,
                    evaluation_dataset=str(evaluation_dataset or "unknown"),
                    metrics=metrics,
                    recipe_name=self.name,
                )
        return FakeJob(
            job_id=f"Build_{self.outputs[0]}",
            log_text=f"INFO {self.recipe_type} recipe completed\n",
            status={"baseStatus": {"state": "DONE", "result": "SUCCESS"}},
        )


class FakeRecipeSettings:
    """Fake mutable recipe settings."""

    def __init__(self, recipe: FakeRecipe) -> None:
        self._recipe = recipe
        self.engine = recipe.recipe_type
        self.tags = ["critical"]
        self.code_env_name = recipe.code_env_name
        self.obj_payload = dict(recipe.metadata.get("settings_payload", {}))

    def get_code(self) -> str:
        return self._recipe.code

    def set_code(self, new_code: str) -> None:
        self._recipe.code = new_code

    def save(self) -> None:
        self._recipe.metadata["settings_payload"] = dict(self.obj_payload)
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "engine": self.engine,
            "tags": list(self.tags),
            "code_env_name": self.code_env_name,
        }


class FakePrepareRecipeSettings:
    """Fake mutable prepare recipe settings."""

    def __init__(self, recipe: FakeRecipe) -> None:
        self._recipe = recipe
        self.obj_payload = {"steps": recipe.steps}

    @property
    def raw_steps(self) -> list[dict[str, object]]:
        return self.obj_payload["steps"]

    def add_processor_step(self, step_type: str, params: dict[str, object]) -> None:
        self.raw_steps.append(
            {
                "metaType": "PROCESSOR",
                "type": step_type,
                "params": dict(params),
            }
        )

    def save(self) -> None:
        self._recipe.steps = list(self.raw_steps)


class FakeManagedFolder:
    """Fake Managed Folder handle."""

    def __init__(
        self,
        folder_id: str,
        name: str,
        backend_type: str,
        connection: str,
        partitioning: str,
        local_path_available: bool,
        files: list[dict[str, object]],
    ) -> None:
        self.folder_id = folder_id
        self.name = name
        self.backend_type = backend_type
        self.connection = connection
        self.partitioning = partitioning
        self.local_path_available = local_path_available
        self.files = files

    def get_info(self) -> dict[str, object]:
        return {
            "folderId": self.folder_id,
            "name": self.name,
            "backendType": self.backend_type,
            "connection": self.connection,
            "partitioning": self.partitioning,
            "localPathAvailable": self.local_path_available,
        }

    def list_files(
        self,
        *,
        path: str = "/",
        recursive: bool = False,
    ) -> list[dict[str, object]]:
        del path
        del recursive
        return list(self.files)

    def put_file(self, path: str, file_like: object) -> dict[str, object]:
        if hasattr(file_like, "read"):
            content = file_like.read()
        else:
            content = file_like
        if isinstance(content, str):
            payload = content.encode("utf-8")
        else:
            payload = bytes(content)
        normalized_path = path.lstrip("/")
        for file_entry in self.files:
            if file_entry.get("path") == normalized_path:
                file_entry["size"] = len(payload)
                file_entry["lastModified"] = "2026-05-02T12:00:00Z"
                return dict(file_entry)
        new_entry = {
            "path": normalized_path,
            "size": len(payload),
            "lastModified": "2026-05-02T12:00:00Z",
        }
        self.files.append(new_entry)
        return dict(new_entry)


class FakeCodeEnv:
    """Fake Dataiku code environment handle."""

    def __init__(
        self,
        name: str,
        python_version: str,
        packages: list[str],
        known_issues: list[str],
    ) -> None:
        self.name = name
        self.python_version = python_version
        self.packages = packages
        self.known_issues = known_issues

    def get_definition(self) -> dict[str, object]:
        return {
            "name": self.name,
            "language": "python",
            "pythonVersion": self.python_version,
            "packages": self.packages,
            "known_issues": self.known_issues,
        }


class FakeSavedModel:
    """Fake deployed saved model."""

    def __init__(
        self,
        *,
        saved_model_id: str,
        name: str,
        prediction_type: str,
        versions: list[dict[str, object]],
        active_version_id: str,
    ) -> None:
        self.id = saved_model_id
        self.name = name
        self.prediction_type = prediction_type
        self._versions = {str(version["id"]): dict(version) for version in versions}
        self._active_version_id = active_version_id

    def list_versions(self) -> list[dict[str, object]]:
        return [
            {
                "id": version_id,
                "label": version.get("label"),
                "active": version_id == self._active_version_id,
                "createdOn": version.get("createdOn"),
            }
            for version_id, version in self._versions.items()
        ]

    def get_active_version(self) -> str:
        return self._active_version_id

    def get_version_details(self, version_id: str) -> dict[str, object]:
        return dict(self._versions[version_id])

    def get_metric_values(self, version_id: str) -> dict[str, object]:
        version = self._versions[version_id]
        metrics = version.get("metrics", {})
        return {"metrics": dict(metrics) if isinstance(metrics, dict) else {}}


class FakeEvaluationFullInfo:
    """Fake evaluation full info payload."""

    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = dict(payload)

    def get_raw(self) -> dict[str, object]:
        return dict(self._payload)


class FakeModelEvaluation:
    """Fake model evaluation entry."""

    def __init__(
        self,
        *,
        evaluation_id: str,
        label: str,
        metrics: dict[str, object],
        full_info: dict[str, object],
    ) -> None:
        self.id = evaluation_id
        self.label = label
        self._metrics = dict(metrics)
        self._full_info = dict(full_info)

    def get_metrics(self) -> dict[str, object]:
        return dict(self._metrics)

    def get_full_info(self) -> FakeEvaluationFullInfo:
        return FakeEvaluationFullInfo(self._full_info)

    def get_full_id(self) -> str:
        return self.id


class FakeModelEvaluationStoreSettings:
    """Fake model evaluation store settings."""

    def __init__(self, store: FakeModelEvaluationStore) -> None:
        self._store = store

    def get_raw(self) -> dict[str, object]:
        return {
            "id": self._store.id,
            "name": self._store.name,
        }


class FakeModelEvaluationStore:
    """Fake model evaluation store."""

    def __init__(self, *, evaluation_store_id: str, name: str) -> None:
        self.id = evaluation_store_id
        self.mes_id = evaluation_store_id
        self.name = name
        self._evaluations: list[FakeModelEvaluation] = []

    def add_evaluation(
        self,
        *,
        saved_model_id: str,
        version_id: str,
        evaluation_dataset: str,
        metrics: dict[str, object],
        recipe_name: str,
    ) -> FakeModelEvaluation:
        evaluation = FakeModelEvaluation(
            evaluation_id=f"evaluation_{len(self._evaluations) + 1:03d}",
            label=f"Evaluation {len(self._evaluations) + 1}",
            metrics=metrics,
            full_info={
                "savedModelId": saved_model_id,
                "versionId": version_id,
                "evaluationDataset": evaluation_dataset,
                "recipeName": recipe_name,
            },
        )
        self._evaluations.append(evaluation)
        return evaluation

    def get_settings(self) -> FakeModelEvaluationStoreSettings:
        return FakeModelEvaluationStoreSettings(self)

    def list_model_evaluations(self) -> list[FakeModelEvaluation]:
        return list(self._evaluations)

    def get_latest_model_evaluation(self) -> FakeModelEvaluation | None:
        return self._evaluations[-1] if self._evaluations else None

    def get_last_metric_values(self) -> dict[str, object]:
        latest = self.get_latest_model_evaluation()
        if latest is None:
            return {"metrics": {}}
        return {"metrics": latest.get_metrics()}


class FakeMLTaskSettings:
    """Fake mutable ML task settings."""

    def __init__(self, task: FakeMLTask) -> None:
        self._task = task
        self.mltask_settings = {
            "predictionType": task.prediction_type,
            "targetVariable": task.target_variable,
            "modeling": {
                "xgboost": {"enabled": False},
                "lightgbm": {"enabled": False},
                "random_forest": {"enabled": False},
                "logistic_regression": {"enabled": False},
                "custom_mllib": [],
                "custom_python": [],
                "plugin_python": {},
            },
        }
        if task.enabled_algorithm is not None:
            modeling_key = {
                "XGBOOST_CLASSIFICATION": "xgboost",
                "XGBOOST_REGRESSION": "xgboost",
                "LIGHTGBM_CLASSIFICATION": "lightgbm",
                "LIGHTGBM_REGRESSION": "lightgbm",
                "RANDOM_FOREST_CLASSIFICATION": "random_forest",
                "RANDOM_FOREST_REGRESSION": "random_forest",
                "LOGISTIC_REGRESSION": "logistic_regression",
            }[task.enabled_algorithm]
            self.mltask_settings["modeling"][modeling_key]["enabled"] = True

    def disable_all_algorithms(self) -> None:
        for algorithm_settings in self.mltask_settings["modeling"].values():
            if isinstance(algorithm_settings, dict) and "enabled" in algorithm_settings:
                algorithm_settings["enabled"] = False

    def set_algorithm_enabled(self, algorithm_name: str, enabled: bool) -> None:
        if algorithm_name not in self.get_all_possible_algorithm_names():
            raise ValueError(f"Unsupported algorithm: {algorithm_name}")
        modeling_key = {
            "XGBOOST_CLASSIFICATION": "xgboost",
            "XGBOOST_REGRESSION": "xgboost",
            "LIGHTGBM_CLASSIFICATION": "lightgbm",
            "LIGHTGBM_REGRESSION": "lightgbm",
            "RANDOM_FOREST_CLASSIFICATION": "random_forest",
            "RANDOM_FOREST_REGRESSION": "random_forest",
            "LOGISTIC_REGRESSION": "logistic_regression",
        }[algorithm_name]
        self.mltask_settings["modeling"][modeling_key]["enabled"] = enabled
        self._task.enabled_algorithm = algorithm_name if enabled else None

    def get_all_possible_algorithm_names(self) -> list[str]:
        return [
            "XGBOOST_CLASSIFICATION",
            "XGBOOST_REGRESSION",
            "LIGHTGBM_CLASSIFICATION",
            "LIGHTGBM_REGRESSION",
            "RANDOM_FOREST_CLASSIFICATION",
            "RANDOM_FOREST_REGRESSION",
            "LOGISTIC_REGRESSION",
        ]

    def save(self) -> None:
        return None

    def get_raw(self) -> dict[str, object]:
        return dict(self.mltask_settings)


class FakeMLTask:
    """Fake DSS Visual ML task."""

    def __init__(
        self,
        *,
        analysis_id: str,
        ml_task_id: str,
        input_dataset: str,
        target_variable: str,
        prediction_type: str,
        ml_backend_type: str,
        guess_policy: str,
        project: FakeProject | None = None,
    ) -> None:
        self.analysis_id = analysis_id
        self.mltask_id = ml_task_id
        self.input_dataset = input_dataset
        self.target_variable = target_variable
        self.prediction_type = prediction_type
        self.ml_backend_type = ml_backend_type
        self.guess_policy = guess_policy
        self.project = project
        self.enabled_algorithm: str | None = None
        self.training = False
        self.analysis_name = f"Analysis {analysis_id}"
        self.task_name = f"Task {ml_task_id}"
        self.trained_models: list[dict[str, object]] = []
        self.deployments: list[dict[str, object]] = []

    def wait_guess_complete(self) -> None:
        return None

    def get_settings(self) -> FakeMLTaskSettings:
        return FakeMLTaskSettings(self)

    def get_status(self) -> dict[str, object]:
        return {
            "guessing": False,
            "training": self.training,
            "fullModelIds": [
                {
                    "id": str(model["model_id"]),
                    "fullModelId": {"sessionId": model["session_id"]},
                }
                for model in self.trained_models
            ],
        }

    def train(
        self,
        session_name: str | None = None,
        session_description: str | None = None,
        run_queue: bool = False,
    ) -> list[str]:
        del session_description
        del run_queue
        self.training = False
        model_id = f"model_{len(self.trained_models) + 1:03d}"
        session_id = f"session_{len(self.trained_models) + 1:03d}"
        self.trained_models.append(
            {
                "model_id": model_id,
                "algorithm": self.enabled_algorithm or "XGBOOST_CLASSIFICATION",
                "session_id": session_id,
                "session_name": session_name or f"Training session {len(self.trained_models) + 1}",
                "snippet": {
                    "algorithm": self.enabled_algorithm or "XGBOOST_CLASSIFICATION",
                    "sessionId": session_id,
                    "sessionName": (
                        session_name or f"Training session {len(self.trained_models) + 1}"
                    ),
                    "metrics": {"accuracy": 0.84},
                },
            }
        )
        return [model_id]

    def get_trained_models_ids(
        self,
        session_id: str | None = None,
        algorithm: str | None = None,
    ) -> list[str]:
        selected_models = list(self.trained_models)
        if session_id is not None:
            selected_models = [
                model for model in selected_models if model["session_id"] == session_id
            ]
        if algorithm is not None:
            selected_models = [
                model for model in selected_models if model["algorithm"] == algorithm
            ]
        return [str(model["model_id"]) for model in selected_models]

    def get_trained_model_snippet(
        self,
        id: str | None = None,
        ids: list[str] | None = None,
    ) -> dict[str, object]:
        snippets = {
            str(model["model_id"]): dict(model["snippet"])
            for model in self.trained_models
        }
        if id is not None:
            return dict(snippets[id])
        if ids is not None:
            return {model_id: dict(snippets[model_id]) for model_id in ids if model_id in snippets}
        return snippets

    def deploy_to_flow(
        self,
        model_id: str,
        model_name: str,
        train_dataset: str,
        test_dataset: str | None = None,
        redo_optimization: bool = True,
    ) -> dict[str, object]:
        deployment = {
            "savedModelId": f"saved_model_{len(self.deployments) + 1:03d}",
            "trainRecipeName": f"train_{model_name}",
            "modelId": model_id,
            "modelName": model_name,
            "trainDatasetRef": train_dataset,
            "testDatasetRef": test_dataset,
            "redoOptimization": redo_optimization,
        }
        self.deployments.append(deployment)
        if self.project is not None:
            matching_models = [
                model for model in self.trained_models if model["model_id"] == model_id
            ]
            trained_model = matching_models[0] if matching_models else None
            metrics = {}
            session_name = None
            if trained_model is not None:
                snippet = trained_model.get("snippet", {})
                if isinstance(snippet, dict):
                    metrics = snippet.get("metrics", {})
                session_name = trained_model.get("session_name")
            version_id = f"version_{len(self.project.saved_models) + 1:03d}"
            self.project.saved_models[deployment["savedModelId"]] = FakeSavedModel(
                saved_model_id=str(deployment["savedModelId"]),
                name=model_name,
                prediction_type=self.prediction_type,
                versions=[
                    {
                        "id": version_id,
                        "label": session_name or model_name,
                        "createdOn": "2026-05-04T12:00:00Z",
                        "algorithm": self.enabled_algorithm or "XGBOOST_CLASSIFICATION",
                        "trainDataset": train_dataset,
                        "metrics": dict(metrics) if isinstance(metrics, dict) else {},
                    }
                ],
                active_version_id=version_id,
            )
        return deployment


class FakeScenarioSettings:
    """Fake scenario settings object."""

    def __init__(self, scenario: FakeScenario) -> None:
        self._scenario = scenario
        self.name = scenario.name
        self.active = scenario._active
        self.code = scenario.code
        self.raw_triggers = [{"type": scenario._trigger_type}] if scenario._trigger_type else []
        self.data = {
            "name": self.name,
            "active": self.active,
            "type": scenario.scenario_type,
            "triggers": self.raw_triggers,
            "params": {"steps": list(scenario.steps)},
        }

    def get_raw(self) -> dict[str, object]:
        return dict(self.data)

    def save(self) -> None:
        self._scenario.name = self.name
        self._scenario._active = self.active
        self._scenario.code = self.code
        raw_params = self.data.get("params", {})
        raw_steps = raw_params.get("steps", []) if isinstance(raw_params, dict) else []
        self._scenario.steps = list(raw_steps) if isinstance(raw_steps, list) else []


class FakeScenarioStatus:
    """Fake scenario status object."""

    def __init__(self, *, running: bool, active: bool) -> None:
        self.running = running
        self.data = {"running": running, "active": active}

    def get_raw(self) -> dict[str, object]:
        return dict(self.data)


class FakeScenarioRun:
    """Fake scenario run handle."""

    def __init__(
        self,
        *,
        project_key: str,
        scenario_id: str,
        run_id: str,
        outcome: str,
        log_text: str,
        start_time: datetime,
        duration_seconds: int,
        step_runs: list[dict[str, object]],
    ) -> None:
        self.project_key = project_key
        self.scenario_id = scenario_id
        self.id = run_id
        self._outcome = outcome
        self._log_text = log_text
        self.start_time = start_time
        self.duration = duration_seconds
        self._step_runs = step_runs
        self.run = {
            "runId": run_id,
            "scenario": {"projectKey": project_key, "id": scenario_id},
            "start": int(start_time.timestamp() * 1000),
            "end": int((start_time + timedelta(seconds=duration_seconds)).timestamp() * 1000),
            "result": {"outcome": outcome},
        }

    @property
    def outcome(self) -> str:
        return self._outcome

    @property
    def running(self) -> bool:
        return False

    def get_info(self) -> dict[str, object]:
        return dict(self.run)

    def get_details(self) -> dict[str, object]:
        first_error: dict[str, object] | None = None
        for step in self._step_runs:
            result = step.get("result")
            if isinstance(result, dict) and isinstance(result.get("thrown"), dict):
                first_error = result["thrown"]
                break
        payload: dict[str, object] = {
            "scenarioRun": self.get_info(),
            "stepRuns": list(self._step_runs),
        }
        if first_error is not None:
            payload["first_error_details"] = first_error
        return payload

    def get_log(self, step_id: str | None = None) -> str:
        del step_id
        return self._log_text


class FakeTriggerFire:
    """Fake trigger fire returned by scenario.run()."""

    def __init__(self, scenario: FakeScenario, scenario_run: FakeScenarioRun) -> None:
        self.scenario = scenario
        self.trigger_id = f"manual-{scenario.id}"
        self.run_id = f"trigger-{scenario_run.id}"
        self._scenario_run = scenario_run
        self.trigger_fire = {
            "trigger": {"id": self.trigger_id},
            "runId": self.run_id,
            "cancelled": False,
        }

    def get_raw(self) -> dict[str, object]:
        return dict(self.trigger_fire)

    def get_scenario_run(self) -> FakeScenarioRun:
        return self._scenario_run


class FakeScenario:
    """Fake scenario handle."""

    def __init__(
        self,
        *,
        project_key: str,
        scenario_id: str,
        name: str,
        active: bool,
        running: bool,
        trigger_type: str,
        runs: list[FakeScenarioRun],
        scenario_type: str = "step_based",
        code: str = "",
        steps: list[dict[str, object]] | None = None,
    ) -> None:
        self.project_key = project_key
        self.id = scenario_id
        self.name = name
        self._active = active
        self._running = running
        self._trigger_type = trigger_type
        self.scenario_type = scenario_type
        self.code = code
        self.steps = list(steps or [])
        self._runs = {run.id: run for run in runs}
        self._ordered_run_ids = [run.id for run in runs]

    def get_settings(self) -> FakeScenarioSettings:
        return FakeScenarioSettings(self)

    def get_status(self) -> FakeScenarioStatus:
        return FakeScenarioStatus(running=self._running, active=self._active)

    def get_last_runs(
        self,
        limit: int = 10,
        only_finished_runs: bool = False,
    ) -> list[FakeScenarioRun]:
        del only_finished_runs
        return [self._runs[run_id] for run_id in self._ordered_run_ids[:limit]]

    def get_run(self, run_id: str) -> FakeScenarioRun:
        if run_id not in self._runs:
            raise ValueError(f"Run not found: {run_id}")
        return self._runs[run_id]

    def run(self, params: dict[str, object] | None = None) -> FakeTriggerFire:
        del params
        if not self._ordered_run_ids:
            created_run = FakeScenarioRun(
                project_key=self.project_key,
                scenario_id=self.id,
                run_id=f"run_{self.id}_001",
                outcome="SUCCESS",
                log_text="INFO scenario completed\n",
                start_time=datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc),
                duration_seconds=5,
                step_runs=[],
            )
            self._runs[created_run.id] = created_run
            self._ordered_run_ids.insert(0, created_run.id)
        latest_run = self._runs[self._ordered_run_ids[0]]
        return FakeTriggerFire(self, latest_run)


class FakeJob:
    """Fake DSS job handle."""

    def __init__(
        self,
        *,
        job_id: str,
        log_text: str,
        status: dict[str, object],
    ) -> None:
        self.id = job_id
        self._log_text = log_text
        self._status = status

    def get_log(self, activity: str | None = None) -> str:
        del activity
        return self._log_text

    def get_status(self) -> dict[str, object]:
        return dict(self._status)


class FakeLibraryFile:
    """Fake project library file."""

    def __init__(self, path: str, initial_content: str = "") -> None:
        self.path = path
        self.content = initial_content

    def write(self, data: str) -> None:
        self.content = data


class FakeLibrary:
    """Fake project library."""

    def __init__(self) -> None:
        self.files: dict[str, FakeLibraryFile] = {}

    def get_file(self, path: str) -> FakeLibraryFile | None:
        return self.files.get(path.lstrip("/"))

    def add_file(self, file_name: str) -> FakeLibraryFile:
        normalized = file_name.lstrip("/")
        file_handle = FakeLibraryFile(normalized)
        self.files[normalized] = file_handle
        return file_handle


class FakeWikiArticleData:
    """Fake wiki article data."""

    def __init__(self, article: FakeWikiArticle) -> None:
        self.article = article

    def set_body(self, content: str) -> None:
        self.article.body = content

    def save(self) -> None:
        return None


class FakeWikiArticle:
    """Fake wiki article."""

    def __init__(self, name: str, body: str = "") -> None:
        self.article_id = name
        self.name = name
        self.body = body

    def get_data(self) -> FakeWikiArticleData:
        return FakeWikiArticleData(self)


class FakeWiki:
    """Fake project wiki."""

    def __init__(self) -> None:
        self.articles: dict[str, FakeWikiArticle] = {}

    def get_article(self, article_id_or_name: str) -> FakeWikiArticle:
        if article_id_or_name not in self.articles:
            raise ValueError(f"Article not found: {article_id_or_name}")
        return self.articles[article_id_or_name]

    def create_article(
        self,
        article_name: str,
        parent_id: str | None = None,
        content: str | None = None,
    ) -> FakeWikiArticle:
        del parent_id
        article = FakeWikiArticle(article_name, content or "")
        self.articles[article_name] = article
        return article


class FakeManagedDatasetCreationHelper:
    """Fake managed dataset creation helper."""

    def __init__(self, project: FakeProject, dataset_name: str) -> None:
        self.project = project
        self.dataset_name = dataset_name
        self.connection = "filesystem_default"

    def with_store_into(
        self,
        connection: str,
        type_option_id: str | None = None,
        format_option_id: str | None = None,
    ) -> FakeManagedDatasetCreationHelper:
        del type_option_id
        del format_option_id
        self.connection = connection
        return self

    def create(self, overwrite: bool = False) -> FakeDataset:
        del overwrite
        dataset = FakeDataset(
            self.dataset_name,
            "Filesystem",
            self.connection,
            [],
        )
        self.project.datasets[self.dataset_name] = dataset
        return dataset


class FakeRecipeCreator:
    """Fake recipe creator for project.new_recipe()."""

    def __init__(self, project: FakeProject, recipe_type: str, name: str) -> None:
        self.project = project
        self.recipe_type = recipe_type
        self.name = name
        self.inputs: list[str] = []
        self.outputs: list[str] = []
        self.output_connection = "filesystem_default"
        self.input_model_id: str | None = None
        self.output_roles: dict[str, str] = {}

    def with_input(
        self,
        input_id: str,
        project_key: str | None = None,
        role: str = "main",
    ) -> FakeRecipeCreator:
        del project_key
        del role
        self.inputs.append(input_id)
        return self

    def with_output(
        self,
        output_id: str,
        append: bool = False,
        role: str = "main",
    ) -> FakeRecipeCreator:
        del append
        self.outputs.append(output_id)
        self.output_roles[role] = output_id
        return self

    def with_input_model(self, model_id: str) -> FakeRecipeCreator:
        self.input_model_id = model_id
        return self

    def with_output_metrics(self, output_id: str) -> FakeRecipeCreator:
        return self.with_output(output_id, role="metrics")

    def with_output_evaluation_store(self, evaluation_store_id: str) -> FakeRecipeCreator:
        return self.with_output(evaluation_store_id, role="evaluationStore")

    def with_existing_output(self, output_id: str, append: bool = False) -> FakeRecipeCreator:
        return self.with_output(output_id, append)

    def with_new_output(
        self,
        output_id: str,
        connection: str,
        type: str | None = None,
        format: str | None = None,
        override_sql_schema: object | None = None,
        partitioning_option_id: str | None = None,
        append: bool = False,
        object_type: str = "DATASET",
        overwrite: bool = False,
        **kwargs: object,
    ) -> FakeRecipeCreator:
        del type
        del format
        del override_sql_schema
        del partitioning_option_id
        del object_type
        del overwrite
        del kwargs
        self.output_connection = connection
        return self.with_output(output_id, append)

    def create(self) -> FakeRecipe:
        role_outputs = dict(self.output_roles)
        recipe = FakeRecipe(
            self.name,
            self.recipe_type,
            list(self.inputs),
            list(self.outputs),
            "",
            project=self.project,
            metadata={
                "saved_model_id": self.input_model_id,
                "evaluation_store_id": role_outputs.get("evaluationStore"),
                "metrics_output_dataset": role_outputs.get("metrics"),
                "scored_output_dataset": role_outputs.get("main"),
                "evaluation_dataset": self.inputs[0] if self.inputs else None,
                "settings_payload": {},
            },
        )
        self.project.recipes[self.name] = recipe
        template_columns: list[dict[str, object]] = []
        if self.inputs:
            first_input = self.project.datasets.get(self.inputs[0])
            if first_input is not None:
                template_columns = [dict(column) for column in first_input.columns]
        for output_name in self.outputs:
            if self.output_roles.get("evaluationStore") == output_name:
                continue
            if output_name not in self.project.datasets:
                self.project.datasets[output_name] = FakeDataset(
                    output_name,
                    "Filesystem",
                    self.output_connection,
                    template_columns,
                )
        return recipe


class FakeProject:
    """Fake project handle."""

    def __init__(self, project_key: str, name: str) -> None:
        self.project_key = project_key
        self.name = name
        self.datasets = {
            "orders": FakeDataset(
                "orders",
                "SQL",
                "warehouse",
                [
                    {"name": "order_id", "type": "bigint"},
                    {"name": "customer_email", "type": "string"},
                    {"name": "order_amount", "type": "double"},
                    {"name": "order_status", "type": "string"},
                    {"name": "is_repeat_customer", "type": "boolean"},
                    {"name": "days_since_last_order", "type": "int"},
                ],
            ),
            "chunks": FakeDataset(
                "chunks",
                "Filesystem",
                "filesystem_default",
                [
                    {"name": "chunk_id", "type": "string"},
                    {"name": "content", "type": "string"},
                    {"name": "source_path", "type": "string"},
                ],
            ),
        }
        self.recipes = {
            "build_chunks": FakeRecipe(
                "build_chunks",
                "python",
                ["orders"],
                ["chunks"],
                (
                    "import dataiku\n"
                    "from langchain.text_splitter import RecursiveCharacterTextSplitter\n"
                    "from sentence_transformers import SentenceTransformer\n"
                    "import faiss\n\n"
                    "folder = dataiku.Folder('RAW_DOCS')\n"
                    "path = folder.get_path()\n"
                    "with open(path + '/doc1.jsonl', 'r', encoding='utf-8') as stream:\n"
                    "    payload = stream.read()\n\n"
                    "api_key=super-secret\n"
                    "splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=0)\n"
                    "model = SentenceTransformer('all-MiniLM-L6-v2')\n"
                    "index = faiss.IndexFlatIP(1536)\n"
                    "top_k = 50\n"
                    "chunks = splitter.split_text(payload)\n"
                    "embeddings = model.encode(chunks)\n"
                ),
                code_env_name="rag-env",
            ),
            "join_orders": FakeRecipe(
                "join_orders",
                "sql",
                ["orders", "chunks"],
                ["enriched_orders"],
                "SELECT * FROM orders",
            ),
        }
        self.managed_folders = {
            "RAW_DOCS": FakeManagedFolder(
                "RAW_DOCS",
                "Raw Documents",
                "S3",
                "s3_docs",
                "NONE",
                False,
                [
                    {
                        "path": "doc1.jsonl",
                        "size": 123,
                        "lastModified": "2026-05-01T09:00:00Z",
                    },
                    {
                        "path": "doc2.jsonl",
                        "size": 456,
                        "lastModified": "2026-05-01T10:00:00Z",
                    },
                ],
            )
        }
        scenario_start = datetime(2026, 5, 1, 8, 30, tzinfo=timezone.utc)
        self.scenario_handles = {
            "daily_refresh": FakeScenario(
                project_key=project_key,
                scenario_id="daily_refresh",
                name="Daily Refresh",
                active=True,
                running=False,
                trigger_type="daily",
                runs=[
                    FakeScenarioRun(
                        project_key=project_key,
                        scenario_id="daily_refresh",
                        run_id="run_daily_001",
                        outcome="SUCCESS",
                        log_text=(
                            "INFO scenario started\n"
                            "INFO build_orders completed successfully\n"
                            "INFO scenario completed\n"
                        ),
                        start_time=scenario_start,
                        duration_seconds=120,
                        step_runs=[
                            {
                                "stepName": "build_orders",
                                "result": {"outcome": "SUCCESS"},
                                "additionalReportItems": [],
                            }
                        ],
                    )
                ],
            ),
            "backfill_rag": FakeScenario(
                project_key=project_key,
                scenario_id="backfill_rag",
                name="Backfill RAG",
                active=False,
                running=False,
                trigger_type="manual",
                runs=[
                    FakeScenarioRun(
                        project_key=project_key,
                        scenario_id="backfill_rag",
                        run_id="run_backfill_001",
                        outcome="FAILED",
                        log_text=(
                            "INFO start backfill\n"
                            "ERROR ImportError: No module named sentence_transformers\n"
                            "ERROR code env rag-env is missing package sentence-transformers\n"
                            "api_key=run-secret-token\n"
                        ),
                        start_time=scenario_start + timedelta(hours=2),
                        duration_seconds=45,
                        step_runs=[
                            {
                                "stepName": "embed_documents",
                                "result": {
                                    "outcome": "FAILED",
                                    "thrown": {
                                        "title": "ImportError",
                                        "message": "No module named sentence_transformers",
                                        "clazz": "ImportError",
                                        "code": "ERR_PYTHON_IMPORT",
                                    },
                                },
                                "additionalReportItems": [],
                            }
                        ],
                    )
                ],
            ),
        }
        self.jobs = {
            "job_build_embeddings": FakeJob(
                job_id="job_build_embeddings",
                log_text=(
                    "INFO building embeddings\n"
                    "ERROR ImportError: No module named sentence_transformers\n"
                    "ERROR Authorization: Bearer job-secret-token\n"
                    "ERROR code env rag-env failed to resolve dependencies\n"
                    "ERROR stack trace line\n"
                ),
                status={
                    "baseStatus": "FAILED",
                    "activities": [
                        {"name": "embed_documents", "state": "FAILED"},
                    ],
                    "errorDetails": {
                        "title": "ImportError",
                        "message": "No module named sentence_transformers",
                        "clazz": "ImportError",
                    },
                },
            )
        }
        self.ml_tasks: dict[str, FakeMLTask] = {}
        self.saved_models: dict[str, FakeSavedModel] = {}
        self.model_evaluation_stores: dict[str, FakeModelEvaluationStore] = {}
        self.plugin_usages = [
            {
                "pluginId": "custom-rag-tools",
                "pluginName": "Custom RAG Tools",
                "usageType": "recipe",
                "recipeNames": ["build_chunks"],
            }
        ]
        self.library = FakeLibrary()
        self.wiki = FakeWiki()

    def get_summary(self) -> dict[str, object]:
        return {"projectKey": self.project_key, "name": self.name}

    def list_datasets(self) -> list[dict[str, object]]:
        return [
            {
                "name": dataset.name,
                "type": dataset.dataset_type,
                "connection": dataset.connection,
                "schemaColumnsCount": len(dataset.columns),
                "tags": ["gold"] if dataset.name == "orders" else ["rag"],
            }
            for dataset in self.datasets.values()
        ]

    def get_dataset(self, dataset_name: str) -> FakeDataset:
        return self.datasets[dataset_name]

    def list_recipes(self) -> list[dict[str, object]]:
        return [
            {
                "name": recipe.name,
                "type": recipe.recipe_type,
                "inputs": [{"ref": value} for value in recipe.inputs],
                "outputs": [{"ref": value} for value in recipe.outputs],
                "lastModifiedOn": "2026-05-01T12:00:00Z",
            }
            for recipe in self.recipes.values()
        ]

    def get_recipe(self, recipe_name: str) -> FakeRecipe:
        return self.recipes[recipe_name]

    def new_recipe(self, recipe_type: str, name: str | None = None) -> FakeRecipeCreator:
        return FakeRecipeCreator(self, recipe_type, name or f"{recipe_type}_recipe")

    def new_managed_dataset(self, dataset_name: str) -> FakeManagedDatasetCreationHelper:
        return FakeManagedDatasetCreationHelper(self, dataset_name)

    def create_prediction_ml_task(
        self,
        input_dataset: str,
        target_variable: str,
        ml_backend_type: str = "PY_MEMORY",
        guess_policy: str = "DEFAULT",
        prediction_type: str | None = None,
        wait_guess_complete: bool = True,
    ) -> FakeMLTask:
        del wait_guess_complete
        analysis_id = f"analysis_{len(self.ml_tasks) + 1:03d}"
        ml_task_id = f"prediction_{len(self.ml_tasks) + 1:03d}"
        task = FakeMLTask(
            analysis_id=analysis_id,
            ml_task_id=ml_task_id,
            input_dataset=input_dataset,
            target_variable=target_variable,
            prediction_type=prediction_type or "REGRESSION",
            ml_backend_type=ml_backend_type,
            guess_policy=guess_policy,
            project=self,
        )
        task.analysis_name = f"{target_variable} analysis"
        task.task_name = f"Predict {target_variable}"
        self.ml_tasks[ml_task_id] = task
        return task

    def list_ml_tasks(self) -> dict[str, object]:
        return {
            "mlTasks": [
                {
                    "analysisId": task.analysis_id,
                    "mlTaskId": task.mltask_id,
                    "analysisName": task.analysis_name,
                    "mlTaskName": task.task_name,
                    "taskType": "PREDICTION",
                    "inputDataset": task.input_dataset,
                    "predictionType": task.prediction_type,
                }
                for task in self.ml_tasks.values()
            ]
        }

    def get_ml_task(self, analysis_id: str, mltask_id: str) -> FakeMLTask:
        task = self.ml_tasks[mltask_id]
        if task.analysis_id != analysis_id:
            raise ValueError(f"ML task not found: {analysis_id}/{mltask_id}")
        return task

    def list_saved_models(self) -> list[dict[str, object]]:
        return [
            {
                "id": saved_model.id,
                "name": saved_model.name,
                "predictionType": saved_model.prediction_type,
                "activeVersionId": saved_model.get_active_version(),
            }
            for saved_model in self.saved_models.values()
        ]

    def get_saved_model(self, saved_model_id: str) -> FakeSavedModel:
        return self.saved_models[saved_model_id]

    def create_model_evaluation_store(self, name: str) -> FakeModelEvaluationStore:
        evaluation_store_id = f"mes_{len(self.model_evaluation_stores) + 1:03d}"
        store = FakeModelEvaluationStore(
            evaluation_store_id=evaluation_store_id,
            name=name,
        )
        self.model_evaluation_stores[evaluation_store_id] = store
        return store

    def list_model_evaluation_stores(self) -> list[dict[str, object]]:
        return [
            {
                "id": store.id,
                "name": store.name,
            }
            for store in self.model_evaluation_stores.values()
        ]

    def get_model_evaluation_store(self, mes_id: str) -> FakeModelEvaluationStore:
        return self.model_evaluation_stores[mes_id]

    def list_plugins_usages(self) -> list[dict[str, object]]:
        return list(self.plugin_usages)

    def list_managed_folders(self) -> list[dict[str, object]]:
        return [
            {
                "folderId": folder.folder_id,
                "name": folder.name,
                "type": folder.backend_type,
                "connection": folder.connection,
                "partitioning": folder.partitioning,
            }
            for folder in self.managed_folders.values()
        ]

    def get_managed_folder(self, folder_id: str) -> FakeManagedFolder:
        return self.managed_folders[folder_id]

    def create_managed_folder(
        self,
        name: str,
        folder_type: str | None = None,
        connection_name: str = "filesystem_folders",
    ) -> FakeManagedFolder:
        folder = FakeManagedFolder(
            name,
            name,
            folder_type or "Filesystem",
            connection_name,
            "NONE",
            True,
            [],
        )
        self.managed_folders[name] = folder
        return folder

    def create_scenario(
        self,
        scenario_name: str,
        scenario_type: str,
        definition: dict[str, object] | None = None,
    ) -> FakeScenario:
        resolved_definition = definition or {"params": {}}
        raw_triggers = resolved_definition.get("triggers", [])
        trigger_type = "manual"
        if isinstance(raw_triggers, list) and raw_triggers:
            first_trigger = raw_triggers[0]
            if isinstance(first_trigger, dict):
                trigger_type = str(first_trigger.get("type") or trigger_type)
        raw_params = resolved_definition.get("params", {})
        raw_steps = raw_params.get("steps", []) if isinstance(raw_params, dict) else []
        scenario = FakeScenario(
            project_key=self.project_key,
            scenario_id=scenario_name,
            name=scenario_name,
            active=bool(resolved_definition.get("active", False)),
            running=False,
            trigger_type=trigger_type,
            runs=[],
            scenario_type=scenario_type,
            code="",
            steps=list(raw_steps) if isinstance(raw_steps, list) else [],
        )
        self.scenario_handles[scenario_name] = scenario
        return scenario

    def list_scenarios(self, as_type: str = "listitems") -> list[object]:
        if as_type == "objects":
            return list(self.scenario_handles.values())
        return [
            {
                "scenarioId": scenario.id,
                "name": scenario.name,
                "active": scenario.get_settings().active,
                "running": scenario.get_status().running,
            }
            for scenario in self.scenario_handles.values()
        ]

    def get_scenario(self, scenario_id: str) -> FakeScenario:
        return self.scenario_handles[scenario_id]

    def get_job(self, job_id: str) -> FakeJob:
        return self.jobs[job_id]

    def get_library(self) -> FakeLibrary:
        return self.library

    def get_wiki(self) -> FakeWiki:
        return self.wiki


class FakeDataikuClient:
    """Small fake client used across tests."""

    def __init__(self) -> None:
        self.projects = [
            {"projectKey": "A", "name": "Alpha", "owner": "alice", "tags": ["prod"]},
            {
                "projectKey": "ARCHIVE",
                "name": "Archive",
                "owner": "bob",
                "status": "archived",
            },
        ]
        self.project_handles = {"A": FakeProject("A", "Alpha")}
        self.code_envs = {
            "rag-env": FakeCodeEnv(
                "rag-env",
                "3.9",
                ["langchain==0.2.1", "faiss-cpu==1.7.4", "pandas==2.2.2"],
                ["Offline wheel for sentence-transformers is missing."],
            )
        }

    def get_info(self) -> dict[str, object]:
        return {"version": "14.0.2", "user": "tester", "features": ["projects"]}

    def list_projects(self) -> list[dict[str, object]]:
        return list(self.projects)

    def get_project(self, project_key: str) -> FakeProject:
        return self.project_handles[project_key]

    def list_connections(self) -> list[dict[str, object]]:
        return [
            {"name": "dataiku-managed-storage"},
            {"name": "warehouse"},
            {"name": "filesystem_default"},
        ]

    def list_code_envs(self) -> list[dict[str, object]]:
        return [
            {
                "name": code_env.name,
                "language": "python",
                "pythonVersion": code_env.python_version,
                "packagesCount": len(code_env.packages),
            }
            for code_env in self.code_envs.values()
        ]

    def get_code_env(self, env_lang: str | None, env_name: str | None = None) -> FakeCodeEnv:
        resolved_name = env_name if env_name is not None else env_lang
        assert resolved_name is not None
        return self.code_envs[resolved_name]


@pytest.fixture
def settings() -> AppSettings:
    return AppSettings(
        dss_url="https://dss.example.com",
        api_key="secret-key",  # type: ignore[arg-type]
        mode=OperationMode.READONLY,
    )


@pytest.fixture
def fake_client() -> FakeDataikuClient:
    return FakeDataikuClient()


@pytest.fixture
def adapter(settings: AppSettings, fake_client: FakeDataikuClient) -> DataikuDSSAdapter:
    return DataikuDSSAdapter(settings, client=fake_client)
