"""Thin Dataiku API wrapper used by MCP tools."""

from __future__ import annotations

import base64
import binascii
import io
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, Protocol, cast

from dataiku_codex_mcp.analyzers.ai_engineering import (
    audit_prompt_injection,
    compare_chunking_strategies,
    generate_architecture_diagram,
    inspect_vector_store,
    monitor_embedding_drift,
    prioritize_technical_debt,
    run_rag_evaluation,
    score_project_quality,
)
from dataiku_codex_mcp.analyzers.code_envs import analyze_code_env
from dataiku_codex_mcp.analyzers.code_review import review_recipe_code
from dataiku_codex_mcp.analyzers.documentation import (
    generate_flow_documentation as render_flow_documentation,
)
from dataiku_codex_mcp.analyzers.documentation import (
    generate_project_readme as render_project_readme,
)
from dataiku_codex_mcp.analyzers.documentation import (
    generate_rag_audit_report as render_rag_audit_report,
)
from dataiku_codex_mcp.analyzers.documentation import (
    generate_troubleshooting_report as render_troubleshooting_report,
)
from dataiku_codex_mcp.analyzers.flow_graph import (
    analyze_flow_health,
    build_flow_graph,
    generate_project_map,
)
from dataiku_codex_mcp.analyzers.folder_doctor import analyze_managed_folder
from dataiku_codex_mcp.analyzers.intent_router import route_ml_intent as analyze_ml_intent
from dataiku_codex_mcp.analyzers.log_analysis import (
    explain_failure as analyze_failure_explanation,
)
from dataiku_codex_mcp.analyzers.log_analysis import summarize_logs
from dataiku_codex_mcp.analyzers.ml_bootstrap import (
    build_prediction_blueprint,
    build_target_suggestions,
    resolve_prediction_type,
)
from dataiku_codex_mcp.analyzers.ml_commands import (
    get_ml_command_definition,
    list_ml_command_definitions,
    resolve_command_algorithm,
)
from dataiku_codex_mcp.analyzers.ops import (
    build_code_env_update_plan,
    build_cost_performance_report,
    build_production_readiness_checklist,
    build_production_readiness_report,
    build_scenario_dependency_map,
    generate_governance_documentation,
)
from dataiku_codex_mcp.analyzers.rag_audit import audit_rag_pipeline, detect_rag_pipeline
from dataiku_codex_mcp.config import AppSettings
from dataiku_codex_mcp.errors import (
    ConfigurationError,
    DataikuCodexError,
    DataikuObjectNotFoundError,
    UnsupportedOperationError,
    map_exception,
)

_MISSING = object()


class DSSClientLike(Protocol):
    """Subset of methods the adapter needs from the Dataiku client."""

    def list_projects(self) -> Sequence[Any]:
        ...

    def get_project(self, project_key: str) -> Any:
        ...

    def list_code_envs(self) -> Sequence[Any]:
        ...

    def get_code_env(self, env_name: str) -> Any:
        ...


class DataikuClientFactory:
    """Create a Dataiku DSS client from validated settings."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def create(self) -> DSSClientLike:
        try:
            import dataikuapi  # type: ignore[import-untyped]
        except ModuleNotFoundError as exc:
            raise ConfigurationError(
                "The dataiku-api-client dependency is not installed.",
                suggested_fix='Install dependencies with `pip install -e ".[dev]"`.',
            ) from exc

        try:
            return cast(
                DSSClientLike,
                dataikuapi.DSSClient(self.settings.dss_url, self.settings.api_key_value),
            )
        except Exception as exc:  # pragma: no cover - depends on the real client
            raise map_exception(exc) from exc


class DataikuDSSAdapter:
    """Normalize Dataiku API responses into JSON-safe dictionaries."""

    def __init__(self, settings: AppSettings, client: DSSClientLike | None = None) -> None:
        self.settings = settings
        self._client = client

    @property
    def client(self) -> DSSClientLike:
        if self._client is None:
            self._client = DataikuClientFactory(self.settings).create()
        return self._client

    def ping(self) -> dict[str, Any]:
        info = self._get_instance_info_payload()
        return {
            "reachable": True,
            "dss_url": self.settings.dss_url,
            "version": info.get("version"),
            "user": info.get("user"),
        }

    def get_instance_info(self) -> dict[str, Any]:
        info = self._get_instance_info_payload()
        return {
            "version": info.get("version"),
            "node_type": info.get("node_type"),
            "user": info.get("user"),
            "features": info.get("features", []),
        }

    def list_projects(self, *, include_archived: bool = False) -> list[dict[str, Any]]:
        try:
            raw_projects = self.client.list_projects()
        except Exception as exc:
            raise map_exception(exc) from exc

        projects: list[dict[str, Any]] = []
        for raw_project in raw_projects:
            normalized = self._normalize_project(raw_project)
            is_archived = bool(normalized.get("archived"))
            if is_archived and not include_archived:
                continue
            projects.append(
                {
                    "project_key": normalized.get("project_key"),
                    "name": normalized.get("name"),
                    "owner": normalized.get("owner"),
                    "tags": normalized.get("tags", []),
                    "status": normalized.get("status"),
                }
            )
        return projects

    def get_project_summary(self, project_key: str) -> dict[str, Any]:
        project = self._get_project(project_key)
        metadata = self._normalize_mapping(
            self._call_method(
                project,
                ("get_summary", "get_metadata", "get_definition", "to_dict"),
                default={},
            )
        )
        scenarios = self._list_scenarios(project)
        warnings: list[str] = []
        if scenarios is None:
            scenarios_count = 0
            warnings.append("Scenario metadata is not available through the current API surface.")
        else:
            scenarios_count = len(scenarios)
        return {
            "project_key": project_key,
            "name": metadata.get("name") or metadata.get("projectName") or project_key,
            "datasets_count": len(self.list_datasets(project_key)),
            "recipes_count": len(self.list_recipes(project_key)),
            "managed_folders_count": len(self.list_managed_folders(project_key)),
            "scenarios_count": scenarios_count,
            "warnings": warnings,
        }

    def list_datasets(self, project_key: str) -> list[dict[str, Any]]:
        project = self._get_project(project_key)
        raw_datasets = self._call_method(project, ("list_datasets", "listDatasets"))
        datasets: list[dict[str, Any]] = []
        for raw_dataset in raw_datasets:
            normalized = self._normalize_mapping(raw_dataset)
            datasets.append(
                {
                    "name": (
                        normalized.get("name")
                        or normalized.get("datasetName")
                        or normalized.get("id")
                    ),
                    "type": normalized.get("type") or normalized.get("datasetType"),
                    "connection": self._extract_connection(normalized),
                    "schema_columns_count": self._extract_schema_columns_count(normalized),
                    "tags": self._normalize_tags(normalized.get("tags")),
                }
            )
        return datasets

    def get_dataset_schema(self, project_key: str, dataset_name: str) -> dict[str, Any]:
        dataset = self._get_dataset(project_key, dataset_name)
        raw_schema = self._call_method(
            dataset,
            ("get_schema", "get_schema_as_json", "get_schema_json"),
            default={},
        )
        columns = self._normalize_columns(raw_schema)
        if not columns:
            columns = self._normalize_columns(self._normalize_mapping(dataset))
        return {"columns": columns}

    def list_recipes(self, project_key: str) -> list[dict[str, Any]]:
        project = self._get_project(project_key)
        raw_recipes = self._call_method(project, ("list_recipes", "listRecipes"))
        recipes: list[dict[str, Any]] = []
        for raw_recipe in raw_recipes:
            normalized = self._normalize_mapping(raw_recipe)
            recipes.append(
                {
                    "name": (
                        normalized.get("name")
                        or normalized.get("recipeName")
                        or normalized.get("id")
                    ),
                    "type": normalized.get("type") or normalized.get("recipeType"),
                    "inputs": self._normalize_bindings(normalized.get("inputs")),
                    "outputs": self._normalize_bindings(normalized.get("outputs")),
                    "last_modified": (
                        normalized.get("lastModifiedOn")
                        or normalized.get("last_modified")
                        or normalized.get("updatedAt")
                    ),
                }
            )
        return recipes

    def get_recipe_details(self, project_key: str, recipe_name: str) -> dict[str, Any]:
        recipe = self._get_recipe(project_key, recipe_name)
        raw_recipe = self._normalize_mapping(recipe)
        definition = self._normalize_mapping(
            self._call_method(recipe, ("get_definition", "to_dict"), default={})
        )
        settings_obj = self._call_method(recipe, ("get_settings",), default=definition)
        settings = self._extract_recipe_settings(settings_obj)
        combined = {**settings, **definition, **raw_recipe}
        code = self._call_method(recipe, ("get_code", "get_recipe_code"), default=None)
        if code is None:
            code = self._call_method(settings_obj, ("get_code",), default=None)
        if isinstance(code, bytes):
            code = code.decode("utf-8", errors="replace")
        if code is None:
            code = combined.get("code") or self._extract_nested_value(combined, ("recipe", "code"))
        return {
            "name": combined.get("name") or combined.get("recipeName") or recipe_name,
            "type": combined.get("type") or combined.get("recipeType"),
            "inputs": self._normalize_bindings(combined.get("inputs")),
            "outputs": self._normalize_bindings(combined.get("outputs")),
            "settings": settings,
            "code": code,
        }

    def list_managed_folders(self, project_key: str) -> list[dict[str, Any]]:
        project = self._get_project(project_key)
        raw_folders = self._call_method(
            project,
            ("list_managed_folders", "list_managedfolders", "listManagedFolders"),
        )
        folders: list[dict[str, Any]] = []
        for raw_folder in raw_folders:
            normalized = self._normalize_mapping(raw_folder)
            folders.append(
                {
                    "folder_id": (
                        normalized.get("folderId")
                        or normalized.get("id")
                        or normalized.get("name")
                    ),
                    "name": normalized.get("name") or normalized.get("label"),
                    "type": normalized.get("type") or normalized.get("backendType"),
                    "connection": self._extract_connection(normalized),
                    "partitioning": (
                        normalized.get("partitioning")
                        or normalized.get("partitioningType")
                    ),
                }
            )
        return folders

    def get_managed_folder_info(self, project_key: str, folder_id: str) -> dict[str, Any]:
        folder = self._get_managed_folder(project_key, folder_id)
        raw_folder = self._normalize_mapping(folder)
        info = self._normalize_mapping(
            self._call_method(folder, ("get_info", "get_definition", "to_dict"), default={})
        )
        combined = {**raw_folder, **info}
        local_path_available = bool(
            combined.get("localPathAvailable") or combined.get("local_path_available")
        )
        warnings: list[str] = []
        if not local_path_available:
            warnings.append(
                "Use Dataiku stream APIs for this Managed Folder; "
                "local filesystem access may be unavailable."
            )
        return {
            "folder_id": folder_id,
            "name": combined.get("name") or combined.get("label") or folder_id,
            "backend_type": (
                combined.get("backendType")
                or combined.get("type")
                or combined.get("backend_type")
            ),
            "local_path_available": local_path_available,
            "warnings": warnings,
        }

    def list_folder_files(
        self,
        project_key: str,
        folder_id: str,
        *,
        path: str = "/",
        recursive: bool = False,
        limit: int = 100,
    ) -> dict[str, Any]:
        folder = self._get_managed_folder(project_key, folder_id)
        raw_files = self._list_folder_files(folder, path=path, recursive=recursive)
        normalized_files = [self._normalize_file_entry(entry) for entry in raw_files]
        return {
            "files": normalized_files[:limit],
            "truncated": len(normalized_files) > limit,
        }

    def generate_project_map(self, project_key: str) -> dict[str, Any]:
        flow_graph = self.get_flow_graph(project_key)
        return generate_project_map(
            graph=flow_graph,
            datasets=self.list_datasets(project_key),
            recipes=self.list_recipes(project_key),
            folders=self.list_managed_folders(project_key),
        )

    def get_flow_graph(
        self,
        project_key: str,
        *,
        include_recipes: bool = True,
        include_folders: bool = True,
        include_models: bool = True,
        include_zones: bool = True,
    ) -> dict[str, Any]:
        del include_models
        del include_zones
        datasets = self.list_datasets(project_key)
        recipes = self.list_recipes(project_key)
        folders = self.list_managed_folders(project_key)
        recipe_details_by_name = {
            recipe["name"]: self.get_recipe_details(project_key, recipe["name"])
            for recipe in recipes
            if recipe.get("name")
        }
        return build_flow_graph(
            project_key=project_key,
            datasets=datasets,
            recipes=recipes,
            folders=folders,
            recipe_details_by_name=recipe_details_by_name,
            include_recipes=include_recipes,
            include_folders=include_folders,
        )

    def analyze_flow_health(self, project_key: str) -> dict[str, Any]:
        graph = self.get_flow_graph(project_key)
        return analyze_flow_health(
            graph=graph,
            recipes=self.list_recipes(project_key),
            datasets=self.list_datasets(project_key),
            folders=self.list_managed_folders(project_key),
        )

    def review_recipe_code(self, project_key: str, recipe_name: str) -> dict[str, Any]:
        recipe = self.get_recipe_details(project_key, recipe_name)
        return review_recipe_code(recipe)

    def managed_folder_doctor(
        self,
        project_key: str,
        folder_id: str | None = None,
    ) -> dict[str, Any]:
        folders = self.list_managed_folders(project_key)
        if not folders:
            return {
                "issues": [],
                "summary": "No Managed Folders were found in the project.",
                "folders": [],
            }

        target_folders = [
            folder
            for folder in folders
            if folder_id is None or folder.get("folder_id") == folder_id
        ]
        recipes = self.list_recipes(project_key)
        recipe_details = [
            self.get_recipe_details(project_key, recipe["name"])
            for recipe in recipes
            if recipe.get("name")
        ]
        analyses: list[dict[str, Any]] = []
        for folder in target_folders:
            current_folder_id = folder.get("folder_id")
            if not isinstance(current_folder_id, str):
                continue
            folder_info = self.get_managed_folder_info(project_key, current_folder_id)
            folder_files = self.list_folder_files(project_key, current_folder_id)
            related_recipes = [
                recipe
                for recipe in recipe_details
                if current_folder_id in str(recipe.get("code") or "")
            ]
            analyses.append(
                analyze_managed_folder(
                    folder_info=folder_info,
                    folder_files=folder_files,
                    related_recipes=related_recipes,
                )
            )
        return {
            "analyses": analyses,
            "summary": f"Analyzed {len(analyses)} Managed Folder(s).",
        }

    def list_scenarios(self, project_key: str) -> list[dict[str, Any]]:
        project = self._get_project(project_key)
        raw_scenarios = self._list_scenarios(project)
        scenarios: list[dict[str, Any]] = []
        for raw_scenario in raw_scenarios or []:
            scenario = self._coerce_scenario(project_key, project, raw_scenario)
            settings = self._get_scenario_settings(scenario)
            status = self._get_scenario_status(scenario)
            scenario_id = (
                self._extract_scenario_id(raw_scenario)
                or self._extract_scenario_id(self._normalize_api_mapping(settings))
                or self._extract_scenario_id(self._normalize_api_mapping(status))
                or self._read_attribute(scenario, "id")
            )
            settings_mapping = self._normalize_api_mapping(settings)
            status_mapping = self._normalize_api_mapping(status)
            scenarios.append(
                {
                    "scenario_id": scenario_id,
                    "name": (
                        settings_mapping.get("name")
                        or self._extract_scenario_name(raw_scenario)
                        or str(scenario_id)
                    ),
                    "active": (
                        settings_mapping.get("active")
                        if "active" in settings_mapping
                        else self._read_attribute(settings, "active")
                    ),
                    "running": (
                        status_mapping.get("running")
                        if "running" in status_mapping
                        else self._read_attribute(status, "running")
                    ),
                    "trigger_type": self._extract_trigger_type(settings, settings_mapping),
                }
            )
        return scenarios

    def get_scenario_runs(
        self,
        project_key: str,
        scenario_id: str,
        *,
        limit: int = 10,
    ) -> dict[str, Any]:
        scenario = self._get_scenario(project_key, scenario_id)
        runs = self._call_scenario_last_runs(scenario, limit=limit)
        return {
            "scenario_id": scenario_id,
            "runs": [self._normalize_scenario_run(run) for run in runs],
        }

    def get_job_logs(
        self,
        project_key: str,
        *,
        job_id: str | None = None,
        run_id: str | None = None,
        scenario_id: str | None = None,
        max_lines: int | None = None,
    ) -> dict[str, Any]:
        failure_context = self._resolve_failure_context(
            project_key,
            job_id=job_id,
            run_id=run_id,
            scenario_id=scenario_id,
        )
        applied_max_lines = min(
            max_lines or self.settings.max_log_lines,
            self.settings.max_log_lines,
        )
        analysis = summarize_logs(
            log_text=failure_context["log_text"],
            failed_steps=failure_context.get("failed_steps"),
            error_details=failure_context.get("error_details"),
        )
        truncated_logs, truncated = self._truncate_logs(
            failure_context["log_text"],
            max_lines=applied_max_lines,
        )
        return {
            "logs": truncated_logs,
            "detected_errors": analysis["detected_errors"],
            "probable_root_cause": analysis["probable_root_cause"],
            "truncated": truncated,
            "line_count": failure_context["line_count"],
            "max_lines_applied": applied_max_lines,
            "source_type": failure_context["source_type"],
            "job_id": job_id,
            "run_id": run_id,
            "scenario_id": failure_context.get("scenario_id"),
        }

    def explain_failure(
        self,
        project_key: str,
        *,
        job_id: str | None = None,
        run_id: str | None = None,
        scenario_id: str | None = None,
    ) -> dict[str, Any]:
        failure_context = self._resolve_failure_context(
            project_key,
            job_id=job_id,
            run_id=run_id,
            scenario_id=scenario_id,
        )
        analysis = analyze_failure_explanation(
            log_text=failure_context["log_text"],
            failed_steps=failure_context.get("failed_steps"),
            error_details=failure_context.get("error_details"),
        )
        return {
            "symptoms": analysis["symptoms"],
            "root_causes": analysis["root_causes"],
            "evidence": analysis["evidence"],
            "recommended_fixes": analysis["recommended_fixes"],
            "source_type": failure_context["source_type"],
            "job_id": job_id,
            "run_id": run_id,
            "scenario_id": failure_context.get("scenario_id"),
        }

    def list_code_envs(self) -> list[dict[str, Any]]:
        raw_envs = self._call_method(
            self.client,
            ("list_code_envs", "listCodeEnvs"),
            default=[],
        )
        envs: list[dict[str, Any]] = []
        for raw_env in raw_envs:
            normalized = self._normalize_mapping(raw_env)
            packages = normalized.get("packages")
            envs.append(
                {
                    "name": normalized.get("name") or normalized.get("envName"),
                    "language": normalized.get("language") or "python",
                    "python_version": (
                        normalized.get("pythonVersion")
                        or normalized.get("python_version")
                    ),
                    "packages_count": (
                        len(packages)
                        if isinstance(packages, Sequence) and not isinstance(packages, str)
                        else normalized.get("packagesCount") or 0
                    ),
                }
            )
        return envs

    def get_code_env_details(self, env_name: str) -> dict[str, Any]:
        code_env = self._get_code_env_handle(env_name)
        raw_details = self._normalize_api_mapping(code_env)
        settings = self._normalize_api_mapping(
            self._call_method(code_env, ("get_settings",), default={})
        )
        definition = self._normalize_api_mapping(
            self._call_method(code_env, ("get_definition", "get_info", "to_dict"), default={})
        )
        combined = {**raw_details, **definition, **settings}
        packages = combined.get("packages")
        normalized_packages = (
            [str(package) for package in packages]
            if isinstance(packages, Sequence) and not isinstance(packages, str)
            else []
        )
        return {
            "name": combined.get("name") or combined.get("envName") or env_name,
            "language": combined.get("language") or "python",
            "python_version": (
                combined.get("pythonVersion")
                or combined.get("python_version")
            ),
            "packages": normalized_packages,
            "settings": (
                combined.get("settings") if isinstance(combined.get("settings"), Mapping) else {}
            ),
            "known_issues": (
                [str(issue) for issue in combined.get("known_issues", [])]
                if isinstance(combined.get("known_issues"), Sequence)
                and not isinstance(combined.get("known_issues"), str)
                else []
            ),
        }

    def code_env_doctor(self, env_name: str) -> dict[str, Any]:
        details = self.get_code_env_details(env_name)
        return analyze_code_env(details)

    def _collect_recipe_details(self, project_key: str) -> list[dict[str, Any]]:
        return [
            self.get_recipe_details(project_key, recipe["name"])
            for recipe in self.list_recipes(project_key)
            if recipe.get("name")
        ]

    def _collect_dataset_schemas(
        self,
        project_key: str,
        datasets: Sequence[Mapping[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        return {
            str(dataset["name"]): self.get_dataset_schema(project_key, str(dataset["name"]))
            for dataset in datasets
            if dataset.get("name")
        }

    def detect_rag_pipeline(self, project_key: str) -> dict[str, Any]:
        return detect_rag_pipeline(self._collect_recipe_details(project_key))

    def audit_rag_pipeline(self, project_key: str, *, deep: bool = False) -> dict[str, Any]:
        datasets = self.list_datasets(project_key)
        dataset_schemas = self._collect_dataset_schemas(project_key, datasets)
        recipe_details = self._collect_recipe_details(project_key)
        return audit_rag_pipeline(
            recipe_details=recipe_details,
            datasets=datasets,
            dataset_schemas=dataset_schemas,
            deep=deep,
        )

    def run_rag_eval(
        self,
        project_key: str,
        *,
        benchmark_dataset_name: str | None = None,
    ) -> dict[str, Any]:
        datasets = self.list_datasets(project_key)
        dataset_schemas = self._collect_dataset_schemas(project_key, datasets)
        recipe_details = self._collect_recipe_details(project_key)
        detection = detect_rag_pipeline(recipe_details)
        rag_audit = audit_rag_pipeline(
            recipe_details=recipe_details,
            datasets=datasets,
            dataset_schemas=dataset_schemas,
            deep=True,
        )
        return run_rag_evaluation(
            project_key=project_key,
            detection=detection,
            rag_audit=rag_audit,
            datasets=datasets,
            dataset_schemas=dataset_schemas,
            recipe_details=recipe_details,
            benchmark_dataset_name=benchmark_dataset_name,
        )

    def compare_chunking_strategies(
        self,
        project_key: str,
        *,
        dataset_name: str | None = None,
        strategies: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        return compare_chunking_strategies(
            project_key=project_key,
            recipe_details=self._collect_recipe_details(project_key),
            dataset_name=dataset_name,
            strategies=strategies,
        )

    def inspect_vector_store(self, project_key: str) -> dict[str, Any]:
        datasets = self.list_datasets(project_key)
        dataset_schemas = self._collect_dataset_schemas(project_key, datasets)
        recipe_details = self._collect_recipe_details(project_key)
        rag_audit = audit_rag_pipeline(
            recipe_details=recipe_details,
            datasets=datasets,
            dataset_schemas=dataset_schemas,
            deep=True,
        )
        return inspect_vector_store(
            project_key=project_key,
            rag_audit=rag_audit,
            dataset_schemas=dataset_schemas,
            recipe_details=recipe_details,
        )

    def monitor_embedding_drift(
        self,
        project_key: str,
        *,
        reference_dataset_name: str | None = None,
        current_dataset_name: str | None = None,
    ) -> dict[str, Any]:
        datasets = self.list_datasets(project_key)
        dataset_schemas = self._collect_dataset_schemas(project_key, datasets)
        return monitor_embedding_drift(
            project_key=project_key,
            dataset_schemas=dataset_schemas,
            recipe_details=self._collect_recipe_details(project_key),
            reference_dataset_name=reference_dataset_name,
            current_dataset_name=current_dataset_name,
        )

    def audit_prompt_injection(self, project_key: str) -> dict[str, Any]:
        datasets = self.list_datasets(project_key)
        dataset_schemas = self._collect_dataset_schemas(project_key, datasets)
        return audit_prompt_injection(
            project_key=project_key,
            dataset_schemas=dataset_schemas,
            recipe_details=self._collect_recipe_details(project_key),
        )

    def generate_architecture_diagram(self, project_key: str) -> dict[str, Any]:
        recipe_details = self._collect_recipe_details(project_key)
        detection = detect_rag_pipeline(recipe_details)
        return generate_architecture_diagram(
            project_key=project_key,
            flow_graph=self.get_flow_graph(project_key),
            detection=detection,
        )

    def score_project_quality(self, project_key: str) -> dict[str, Any]:
        project_summary = self.get_project_summary(project_key)
        flow_health = self.analyze_flow_health(project_key)
        rag_audit = self.audit_rag_pipeline(project_key, deep=True)
        readiness_report = self.generate_production_readiness_report(project_key)
        code_env_update_plan = self.plan_code_env_updates()
        return score_project_quality(
            project_key=project_key,
            project_summary=project_summary,
            flow_health=flow_health,
            rag_audit=rag_audit,
            readiness_report=readiness_report,
            code_env_update_plan=code_env_update_plan,
        )

    def prioritize_technical_debt(self, project_key: str) -> dict[str, Any]:
        return prioritize_technical_debt(
            project_key=project_key,
            flow_health=self.analyze_flow_health(project_key),
            rag_audit=self.audit_rag_pipeline(project_key, deep=True),
            readiness_report=self.generate_production_readiness_report(project_key),
            code_env_update_plan=self.plan_code_env_updates(),
        )

    def generate_project_readme(self, project_key: str) -> dict[str, Any]:
        summary = self.get_project_summary(project_key)
        datasets = self.list_datasets(project_key)
        recipes = self.list_recipes(project_key)
        folders = self.list_managed_folders(project_key)
        scenarios = self.list_scenarios(project_key)
        flow_health = self.analyze_flow_health(project_key)
        markdown = render_project_readme(
            summary=summary,
            datasets=datasets,
            recipes=recipes,
            folders=folders,
            scenarios=scenarios,
            flow_health=flow_health,
            warnings=summary.get("warnings", []),
        )
        return {"markdown": markdown}

    def generate_flow_documentation(self, project_key: str) -> dict[str, Any]:
        summary = self.get_project_summary(project_key)
        recipes = self.list_recipes(project_key)
        project_map = self.generate_project_map(project_key)
        flow_graph = self.get_flow_graph(project_key)
        flow_health = self.analyze_flow_health(project_key)
        markdown = render_flow_documentation(
            summary=summary,
            project_map=project_map,
            flow_graph=flow_graph,
            flow_health=flow_health,
            recipes=recipes,
        )
        return {"markdown": markdown}

    def generate_troubleshooting_report(
        self,
        project_key: str,
        *,
        focus: str | None = None,
    ) -> dict[str, Any]:
        summary = self.get_project_summary(project_key)
        flow_health = self.analyze_flow_health(project_key)
        warnings: list[str] = []

        folder_diagnosis, folder_warning = self._attempt_optional_collection(
            "managed folder diagnosis",
            lambda: self.managed_folder_doctor(project_key)
        )
        if folder_warning:
            warnings.append(folder_warning)

        code_env_diagnoses: list[dict[str, Any]] = []
        code_envs, code_env_warning = self._attempt_optional_collection(
            "code environment listing",
            self.list_code_envs,
        )
        if code_env_warning:
            warnings.append(code_env_warning)
        elif isinstance(code_envs, list):
            for code_env in code_envs:
                env_name = code_env.get("name")
                if not isinstance(env_name, str) or not env_name:
                    continue
                diagnosis, env_warning = self._attempt_optional_collection(
                    f"code environment diagnosis for {env_name}",
                    lambda env_name=env_name: self.code_env_doctor(env_name)
                )
                if env_warning:
                    warnings.append(env_warning)
                    continue
                if isinstance(diagnosis, Mapping):
                    code_env_diagnoses.append(dict(diagnosis))

        recipe_reviews: list[dict[str, Any]] = []
        for recipe in self.list_recipes(project_key):
            recipe_name = recipe.get("name")
            if not isinstance(recipe_name, str) or not recipe_name:
                continue
            review, review_warning = self._attempt_optional_collection(
                f"recipe review for {recipe_name}",
                lambda recipe_name=recipe_name: self.review_recipe_code(project_key, recipe_name)
            )
            if review_warning:
                warnings.append(review_warning)
                continue
            if isinstance(review, Mapping):
                recipe_reviews.append(dict(review))

        scenario_runs: list[dict[str, Any]] = []
        scenarios, scenario_warning = self._attempt_optional_collection(
            "scenario listing",
            lambda: self.list_scenarios(project_key)
        )
        if scenario_warning:
            warnings.append(scenario_warning)
        elif isinstance(scenarios, list):
            for scenario in scenarios:
                scenario_id = scenario.get("scenario_id")
                if not isinstance(scenario_id, str) or not scenario_id:
                    continue
                runs, run_warning = self._attempt_optional_collection(
                    f"scenario runs for {scenario_id}",
                    lambda scenario_id=scenario_id: self.get_scenario_runs(
                        project_key,
                        scenario_id,
                        limit=3,
                    )
                )
                if run_warning:
                    warnings.append(run_warning)
                    continue
                if isinstance(runs, Mapping):
                    scenario_runs.append(dict(runs))

        markdown = render_troubleshooting_report(
            summary=summary,
            focus=focus,
            flow_health=flow_health,
            folder_diagnosis=(
                dict(folder_diagnosis) if isinstance(folder_diagnosis, Mapping) else None
            ),
            code_env_diagnoses=code_env_diagnoses,
            recipe_reviews=recipe_reviews,
            scenario_runs=scenario_runs,
            warnings=warnings + summary.get("warnings", []),
        )
        return {"markdown": markdown}

    def generate_rag_audit_report(self, project_key: str) -> dict[str, Any]:
        summary = self.get_project_summary(project_key)
        detection = self.detect_rag_pipeline(project_key)
        audit = self.audit_rag_pipeline(project_key, deep=True)
        markdown = render_rag_audit_report(
            summary=summary,
            detection=detection,
            audit=audit,
        )
        return {"markdown": markdown}

    def preview_update_recipe_code(
        self,
        project_key: str,
        recipe_name: str,
        *,
        new_code: str,
        reason: str,
    ) -> dict[str, Any]:
        recipe = self.get_recipe_details(project_key, recipe_name)
        current_code = str(recipe.get("code") or "")
        return self._action_summary(
            operation="update_recipe_code",
            project_key=project_key,
            object_type="recipe",
            object_name=recipe_name,
            risk_level="medium",
            rollback_possible=True,
            exact_operation="Update the code payload of an existing recipe.",
            changes={
                "recipe_type": recipe.get("type"),
                "reason": reason,
                "current_code_lines": len(current_code.splitlines()),
                "new_code_lines": len(new_code.splitlines()),
                "code_changed": current_code != new_code,
            },
        )

    def update_recipe_code(
        self,
        project_key: str,
        recipe_name: str,
        *,
        new_code: str,
    ) -> dict[str, Any]:
        recipe = self._get_recipe(project_key, recipe_name)
        settings = self._call_method(recipe, ("get_settings",), default=None)
        if settings is None or not hasattr(settings, "set_code") or not hasattr(settings, "save"):
            raise UnsupportedOperationError(
                "The target recipe does not expose editable code settings.",
                suggested_fix=(
                    "Use this tool only on code-based recipes supported by the "
                    "Dataiku API."
                ),
            )
        current_code = self.get_recipe_details(project_key, recipe_name).get("code")
        try:
            settings.set_code(new_code)
            settings.save()
        except Exception as exc:
            raise map_exception(exc) from exc
        return {
            "recipe_name": recipe_name,
            "updated": True,
            "previous_code_lines": len(str(current_code or "").splitlines()),
            "new_code_lines": len(new_code.splitlines()),
            "rollback_guidance": (
                "Re-run dataiku_update_recipe_code with the previous code "
                "content if a rollback is needed."
            ),
        }

    def preview_create_python_recipe(
        self,
        project_key: str,
        recipe_name: str,
        *,
        inputs: list[str],
        outputs: list[str],
        code: str,
    ) -> dict[str, Any]:
        existing_recipe_names = {
            recipe.get("name")
            for recipe in self.list_recipes(project_key)
            if recipe.get("name")
        }
        known_inputs = self._known_project_bindings(project_key)
        missing_inputs = [item for item in inputs if item not in known_inputs]
        missing_outputs = [item for item in outputs if item not in known_inputs]
        return self._action_summary(
            operation="create_python_recipe",
            project_key=project_key,
            object_type="recipe",
            object_name=recipe_name,
            risk_level="medium",
            rollback_possible=True,
            exact_operation="Create a new Python recipe with the provided bindings and code.",
            changes={
                "recipe_exists": recipe_name in existing_recipe_names,
                "inputs": inputs,
                "outputs": outputs,
                "missing_inputs": missing_inputs,
                "missing_outputs": missing_outputs,
                "code_lines": len(code.splitlines()),
            },
        )

    def create_python_recipe(
        self,
        project_key: str,
        recipe_name: str,
        *,
        inputs: list[str],
        outputs: list[str],
        code: str,
    ) -> dict[str, Any]:
        self._validate_python_recipe_creation(
            project_key,
            recipe_name,
            inputs=inputs,
            outputs=outputs,
        )
        project = self._get_project(project_key)
        creator = self._call_method(project, ("new_recipe",), "python", recipe_name)
        for input_name in inputs:
            self._call_method(creator, ("with_input",), input_name)
        for output_name in outputs:
            self._call_method(creator, ("with_output",), output_name)
        recipe = self._call_method(creator, ("create", "build"))
        settings = self._call_method(recipe, ("get_settings",), default=None)
        if settings is not None and hasattr(settings, "set_code") and hasattr(settings, "save"):
            try:
                settings.set_code(code)
                settings.save()
            except Exception as exc:
                raise map_exception(exc) from exc
        return {
            "recipe_name": recipe_name,
            "created": True,
            "inputs": inputs,
            "outputs": outputs,
            "rollback_guidance": (
                "Delete the new recipe manually in DSS if you need to roll back this creation."
            ),
        }

    def suggest_prediction_targets(
        self,
        project_key: str,
        dataset_name: str,
        *,
        limit: int = 5,
    ) -> dict[str, Any]:
        schema = self.get_dataset_schema(project_key, dataset_name)
        return build_target_suggestions(
            dataset_name,
            cast(list[dict[str, Any]], schema.get("columns", [])),
            limit=limit,
        )

    def list_ml_commands(self) -> dict[str, Any]:
        commands = [command.to_dict() for command in list_ml_command_definitions()]
        return {
            "commands": commands,
            "summary": f"Loaded {len(commands)} reusable ML command(s).",
        }

    def plan_ml_command(
        self,
        project_key: str,
        dataset_name: str,
        command_name: str,
        *,
        target_variable: str | None = None,
        prepared_dataset_name: str | None = None,
        prepare_recipe_name: str | None = None,
        prediction_type: str | None = None,
        ml_backend_type: str | None = None,
        guess_policy: str | None = None,
    ) -> dict[str, Any]:
        return self._resolve_ml_command_plan(
            project_key,
            dataset_name,
            command_name,
            target_variable=target_variable,
            prepared_dataset_name=prepared_dataset_name,
            prepare_recipe_name=prepare_recipe_name,
            prediction_type=prediction_type,
            ml_backend_type=ml_backend_type,
            guess_policy=guess_policy,
        )

    def preview_run_ml_command(
        self,
        project_key: str,
        dataset_name: str,
        command_name: str,
        *,
        target_variable: str | None = None,
        prepared_dataset_name: str | None = None,
        prepare_recipe_name: str | None = None,
        prediction_type: str | None = None,
        ml_backend_type: str | None = None,
        guess_policy: str | None = None,
    ) -> dict[str, Any]:
        plan = self._resolve_ml_command_plan(
            project_key,
            dataset_name,
            command_name,
            target_variable=target_variable,
            prepared_dataset_name=prepared_dataset_name,
            prepare_recipe_name=prepare_recipe_name,
            prediction_type=prediction_type,
            ml_backend_type=ml_backend_type,
            guess_policy=guess_policy,
        )
        return self._action_summary(
            operation="run_ml_command",
            project_key=project_key,
            object_type="ml_command",
            object_name=str(plan["command"]["name"]),
            risk_level="medium",
            rollback_possible=True,
            exact_operation=(
                "Run a reusable ML command that creates a standard Prepare recipe "
                "and a Visual ML prediction task."
            ),
            changes={
                "source_dataset": dataset_name,
                "target_variable": plan["target_variable"],
                "auto_selected_target": plan["auto_selected_target"],
                "prediction_type": plan["prediction_type"],
                "recommended_algorithm": plan["recommended_algorithm"],
                "prepared_dataset_name": plan["prepared_dataset_name"],
                "prepare_recipe_name": plan["prepare_recipe_name"],
                "ml_backend_type": plan["ml_backend_type"],
                "guess_policy": plan["guess_policy"],
            },
        )

    def run_ml_command(
        self,
        project_key: str,
        dataset_name: str,
        command_name: str,
        *,
        target_variable: str | None = None,
        prepared_dataset_name: str | None = None,
        prepare_recipe_name: str | None = None,
        prediction_type: str | None = None,
        ml_backend_type: str | None = None,
        guess_policy: str | None = None,
    ) -> dict[str, Any]:
        plan = self._resolve_ml_command_plan(
            project_key,
            dataset_name,
            command_name,
            target_variable=target_variable,
            prepared_dataset_name=prepared_dataset_name,
            prepare_recipe_name=prepare_recipe_name,
            prediction_type=prediction_type,
            ml_backend_type=ml_backend_type,
            guess_policy=guess_policy,
        )
        self._validate_prediction_flow_creation(
            project_key,
            prepare_recipe_name=str(plan["prepare_recipe_name"]),
            prepared_dataset_name=str(plan["prepared_dataset_name"]),
        )

        prepare_recipe_payload = self._create_prepare_recipe(
            project_key,
            recipe_name=str(plan["prepare_recipe_name"]),
            input_dataset=dataset_name,
            output_dataset=str(plan["prepared_dataset_name"]),
        )
        ml_task_payload = self._create_prediction_ml_task(
            project_key,
            input_dataset=str(plan["prepared_dataset_name"]),
            target_variable=str(plan["target_variable"]),
            dss_prediction_type=str(plan["dss_prediction_type"]),
            algorithm_name=str(plan["recommended_algorithm"]),
            ml_backend_type=str(plan["ml_backend_type"]),
            guess_policy=str(plan["guess_policy"]),
        )
        return {
            "created": True,
            "command": plan["command"],
            "source_dataset": dataset_name,
            "target_variable": plan["target_variable"],
            "auto_selected_target": plan["auto_selected_target"],
            "prediction_type": plan["prediction_type"],
            "prepare_recipe": prepare_recipe_payload,
            "ml_task": ml_task_payload,
            "rollback_guidance": (
                "Delete the Prepare recipe and the ML analysis manually in DSS "
                "if you need to roll back this command."
            ),
        }

    def preview_bootstrap_xgboost_flow(
        self,
        project_key: str,
        dataset_name: str,
        target_variable: str,
        *,
        prepared_dataset_name: str | None = None,
        prepare_recipe_name: str | None = None,
        prediction_type: str | None = None,
        ml_backend_type: str = "PY_MEMORY",
        guess_policy: str = "DEFAULT",
    ) -> dict[str, Any]:
        plan = self._resolve_ml_command_plan(
            project_key,
            dataset_name,
            "xgboost_prediction_flow",
            target_variable=target_variable,
            prepared_dataset_name=prepared_dataset_name,
            prepare_recipe_name=prepare_recipe_name,
            prediction_type=prediction_type,
            ml_backend_type=ml_backend_type,
            guess_policy=guess_policy,
        )
        return self._action_summary(
            operation="bootstrap_xgboost_flow",
            project_key=project_key,
            object_type="ml_blueprint",
            object_name=str(plan["analysis_label"]),
            risk_level="medium",
            rollback_possible=True,
            exact_operation=(
                "Create a Prepare recipe and a Dataiku Visual ML prediction task "
                "configured for XGBoost."
            ),
            changes={
                "source_dataset": dataset_name,
                "target_variable": plan["target_variable"],
                "prediction_type": plan["prediction_type"],
                "recommended_algorithm": plan["recommended_algorithm"],
                "prepared_dataset_name": plan["prepared_dataset_name"],
                "prepared_dataset_exists": plan["prepared_dataset_exists"],
                "prepare_recipe_name": plan["prepare_recipe_name"],
                "prepare_recipe_exists": plan["prepare_recipe_exists"],
                "target_reasoning": plan["target_reasoning"],
                "target_warnings": plan["target_warnings"],
                "ml_backend_type": plan["ml_backend_type"],
                "guess_policy": plan["guess_policy"],
            },
        )

    def bootstrap_xgboost_flow(
        self,
        project_key: str,
        dataset_name: str,
        target_variable: str,
        *,
        prepared_dataset_name: str | None = None,
        prepare_recipe_name: str | None = None,
        prediction_type: str | None = None,
        ml_backend_type: str = "PY_MEMORY",
        guess_policy: str = "DEFAULT",
    ) -> dict[str, Any]:
        payload = self.run_ml_command(
            project_key,
            dataset_name,
            "xgboost_prediction_flow",
            target_variable=target_variable,
            prepared_dataset_name=prepared_dataset_name,
            prepare_recipe_name=prepare_recipe_name,
            prediction_type=prediction_type,
            ml_backend_type=ml_backend_type,
            guess_policy=guess_policy,
        )
        return {
            "created": payload["created"],
            "source_dataset": payload["source_dataset"],
            "target_variable": payload["target_variable"],
            "prediction_type": payload["prediction_type"],
            "prepare_recipe": payload["prepare_recipe"],
            "ml_task": payload["ml_task"],
            "rollback_guidance": payload["rollback_guidance"],
        }

    def list_ml_tasks(self, project_key: str) -> list[dict[str, Any]]:
        project = self._get_project(project_key)
        raw_tasks = self._call_method(project, ("list_ml_tasks",), default=[])
        task_entries: list[Any] = []
        if isinstance(raw_tasks, Mapping):
            nested_tasks = raw_tasks.get("mlTasks") or raw_tasks.get("tasks")
            if isinstance(nested_tasks, Sequence) and not isinstance(
                nested_tasks,
                (str, bytes),
            ):
                task_entries = list(nested_tasks)
        elif isinstance(raw_tasks, Sequence) and not isinstance(raw_tasks, (str, bytes)):
            task_entries = list(raw_tasks)

        normalized_tasks: list[dict[str, Any]] = []
        for raw_task in task_entries:
            normalized = self._normalize_ml_task_summary(raw_task)
            if normalized.get("analysis_id") and normalized.get("ml_task_id"):
                normalized_tasks.append(normalized)
        return normalized_tasks

    def get_ml_task_details(
        self,
        project_key: str,
        analysis_id: str,
        ml_task_id: str,
    ) -> dict[str, Any]:
        task = self._get_ml_task(project_key, analysis_id, ml_task_id)
        summary = self._find_ml_task_summary(project_key, analysis_id, ml_task_id)
        status = self._normalize_mapping(self._call_method(task, ("get_status",), default={}))
        settings = self._extract_ml_task_settings(
            self._call_method(task, ("get_settings",), default={})
        )
        trained_model_ids = self._extract_trained_model_ids(status)
        return {
            **summary,
            "status": status,
            "enabled_algorithms": self._extract_enabled_algorithms(settings),
            "trained_models_count": len(trained_model_ids),
            "trained_model_ids": trained_model_ids,
        }

    def list_trained_models(
        self,
        project_key: str,
        analysis_id: str,
        ml_task_id: str,
        *,
        model_ids: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        task = self._get_ml_task(project_key, analysis_id, ml_task_id)
        summary = self._find_ml_task_summary(project_key, analysis_id, ml_task_id)
        resolved_model_ids = (
            [str(model_id) for model_id in model_ids]
            if model_ids is not None
            else [
                str(model_id)
                for model_id in self._call_method(task, ("get_trained_models_ids",), default=[])
            ]
        )
        if not resolved_model_ids:
            return {
                **summary,
                "models": [],
                "summary": "No trained models are currently available for this Visual ML task.",
            }

        raw_snippets = self._call_method(
            task,
            ("get_trained_model_snippet",),
            ids=resolved_model_ids,
            default={},
        )
        snippet_map: dict[str, dict[str, Any]] = {}
        if isinstance(raw_snippets, Mapping):
            snippet_map = {
                str(model_id): self._normalize_mapping(snippet)
                for model_id, snippet in raw_snippets.items()
            }

        models: list[dict[str, Any]] = []
        for model_id in resolved_model_ids:
            snippet = snippet_map.get(model_id, {})
            metrics = self._normalize_metric_values(snippet.get("metrics", {}))
            models.append(
                {
                    "model_id": model_id,
                    "algorithm": snippet.get("algorithm"),
                    "session_id": snippet.get("sessionId") or snippet.get("session_id"),
                    "session_name": snippet.get("sessionName") or snippet.get("session_name"),
                    "metrics": metrics,
                    "primary_metric": self._select_primary_metric(metrics),
                    "snippet": snippet,
                }
            )
        return {
            **summary,
            "models": models,
            "summary": f"Found {len(models)} trained model(s) for this Visual ML task.",
        }

    def preview_train_ml_task(
        self,
        project_key: str,
        analysis_id: str,
        ml_task_id: str,
        *,
        session_name: str | None = None,
        session_description: str | None = None,
        run_queue: bool = False,
    ) -> dict[str, Any]:
        details = self.get_ml_task_details(project_key, analysis_id, ml_task_id)
        return self._action_summary(
            operation="train_ml_task",
            project_key=project_key,
            object_type="ml_task",
            object_name=ml_task_id,
            risk_level="medium",
            rollback_possible=False,
            exact_operation="Train an existing Dataiku Visual ML task.",
            changes={
                "analysis_id": analysis_id,
                "ml_task_id": ml_task_id,
                "input_dataset": details.get("input_dataset"),
                "target_variable": details.get("target_variable"),
                "enabled_algorithms": details.get("enabled_algorithms"),
                "existing_trained_models_count": details.get("trained_models_count"),
                "session_name": session_name,
                "session_description": session_description,
                "run_queue": run_queue,
            },
        )

    def train_ml_task(
        self,
        project_key: str,
        analysis_id: str,
        ml_task_id: str,
        *,
        session_name: str | None = None,
        session_description: str | None = None,
        run_queue: bool = False,
    ) -> dict[str, Any]:
        task = self._get_ml_task(project_key, analysis_id, ml_task_id)
        trained_model_ids = self._call_method(
            task,
            ("train",),
            session_name,
            session_description,
            run_queue,
            default=[],
        )
        if not isinstance(trained_model_ids, Sequence) or isinstance(
            trained_model_ids,
            (str, bytes),
        ):
            trained_model_ids = []
        trained_models_payload = self.list_trained_models(
            project_key,
            analysis_id,
            ml_task_id,
            model_ids=[str(model_id) for model_id in trained_model_ids],
        )
        return {
            "trained": True,
            "analysis_id": analysis_id,
            "ml_task_id": ml_task_id,
            "session_name": session_name,
            "session_description": session_description,
            "run_queue": run_queue,
            "trained_model_ids": [str(model_id) for model_id in trained_model_ids],
            "trained_models": trained_models_payload["models"],
        }

    def preview_deploy_trained_model_to_flow(
        self,
        project_key: str,
        analysis_id: str,
        ml_task_id: str,
        *,
        model_id: str | None = None,
        saved_model_name: str | None = None,
        train_dataset: str | None = None,
        test_dataset: str | None = None,
        redo_optimization: bool = True,
    ) -> dict[str, Any]:
        task_details = self.get_ml_task_details(project_key, analysis_id, ml_task_id)
        trained_models = self.list_trained_models(project_key, analysis_id, ml_task_id)
        available_models = cast(list[dict[str, Any]], trained_models["models"])
        selected_model_id = self._select_default_model_id(
            available_models,
            requested_model_id=model_id,
        )
        resolved_saved_model_name = (
            saved_model_name
            if saved_model_name
            else f"{analysis_id}_{ml_task_id}_saved_model"
        )
        resolved_train_dataset = (
            train_dataset if train_dataset else cast(str | None, task_details.get("input_dataset"))
        )
        if not resolved_train_dataset:
            raise ConfigurationError(
                "Could not infer the training dataset for this ML task.",
                suggested_fix="Provide train_dataset explicitly.",
            )
        return self._action_summary(
            operation="deploy_trained_model_to_flow",
            project_key=project_key,
            object_type="trained_model",
            object_name=selected_model_id,
            risk_level="medium",
            rollback_possible=True,
            exact_operation="Deploy a trained Visual ML model to the Flow as a saved model.",
            changes={
                "analysis_id": analysis_id,
                "ml_task_id": ml_task_id,
                "selected_model_id": selected_model_id,
                "saved_model_name": resolved_saved_model_name,
                "train_dataset": resolved_train_dataset,
                "test_dataset": test_dataset,
                "redo_optimization": redo_optimization,
            },
        )

    def deploy_trained_model_to_flow(
        self,
        project_key: str,
        analysis_id: str,
        ml_task_id: str,
        *,
        model_id: str | None = None,
        saved_model_name: str | None = None,
        train_dataset: str | None = None,
        test_dataset: str | None = None,
        redo_optimization: bool = True,
    ) -> dict[str, Any]:
        task = self._get_ml_task(project_key, analysis_id, ml_task_id)
        task_details = self.get_ml_task_details(project_key, analysis_id, ml_task_id)
        trained_models = self.list_trained_models(project_key, analysis_id, ml_task_id)
        available_models = cast(list[dict[str, Any]], trained_models["models"])
        selected_model_id = self._select_default_model_id(
            available_models,
            requested_model_id=model_id,
        )
        resolved_saved_model_name = (
            saved_model_name
            if saved_model_name
            else f"{analysis_id}_{ml_task_id}_saved_model"
        )
        resolved_train_dataset = (
            train_dataset if train_dataset else cast(str | None, task_details.get("input_dataset"))
        )
        if not resolved_train_dataset:
            raise ConfigurationError(
                "Could not infer the training dataset for this ML task.",
                suggested_fix="Provide train_dataset explicitly.",
            )
        deployment = self._normalize_mapping(
            self._call_method(
                task,
                ("deploy_to_flow",),
                selected_model_id,
                resolved_saved_model_name,
                resolved_train_dataset,
                test_dataset,
                redo_optimization,
            )
        )
        return {
            "deployed": True,
            "analysis_id": analysis_id,
            "ml_task_id": ml_task_id,
            "model_id": selected_model_id,
            "saved_model_name": resolved_saved_model_name,
            "train_dataset": resolved_train_dataset,
            "test_dataset": test_dataset,
            "redo_optimization": redo_optimization,
            "saved_model_id": deployment.get("savedModelId"),
            "train_recipe_name": deployment.get("trainRecipeName"),
            "deployment": deployment,
            "rollback_guidance": (
                "Delete the saved model and generated training recipe manually in DSS "
                "if you need to roll back this deployment."
            ),
        }

    def list_saved_models(self, project_key: str) -> list[dict[str, Any]]:
        project = self._get_project(project_key)
        raw_saved_models = self._call_method(project, ("list_saved_models",), default=[])
        if not isinstance(raw_saved_models, Sequence) or isinstance(raw_saved_models, (str, bytes)):
            return []
        return [
            self._normalize_saved_model_summary(saved_model)
            for saved_model in raw_saved_models
            if self._normalize_saved_model_summary(saved_model).get("saved_model_id")
        ]

    def get_saved_model_details(
        self,
        project_key: str,
        saved_model_id: str,
    ) -> dict[str, Any]:
        saved_model = self._get_saved_model(project_key, saved_model_id)
        summary = self._find_saved_model_summary(project_key, saved_model_id)
        versions = self._call_method(saved_model, ("list_versions",), default=[])
        normalized_versions = []
        if isinstance(versions, Sequence) and not isinstance(versions, (str, bytes)):
            normalized_versions = [
                self._normalize_saved_model_version(version)
                for version in versions
            ]
        active_version = self._call_method(saved_model, ("get_active_version",), default=None)
        active_version_id = self._extract_saved_model_version_id(active_version)
        active_version_details = {}
        active_version_metrics: dict[str, Any] = {}
        if active_version_id is not None:
            active_version_details = self._normalize_mapping(
                self._call_method(
                    saved_model,
                    ("get_version_details",),
                    active_version_id,
                    default={},
                )
            )
            active_version_metrics = self._normalize_metric_values(
                self._call_method(
                    saved_model,
                    ("get_metric_values",),
                    active_version_id,
                    default={},
                )
            )
        return {
            **summary,
            "active_version_id": active_version_id,
            "versions": normalized_versions,
            "versions_count": len(normalized_versions),
            "active_version_details": active_version_details,
            "active_version_metrics": active_version_metrics,
            "primary_metric": self._select_primary_metric(active_version_metrics),
        }

    def preview_create_prediction_scoring_recipe(
        self,
        project_key: str,
        saved_model_id: str,
        input_dataset: str,
        *,
        recipe_name: str,
        output_dataset_name: str,
        output_connection: str | None = None,
    ) -> dict[str, Any]:
        self.get_saved_model_details(project_key, saved_model_id)
        self._get_dataset(project_key, input_dataset)
        resolved_output_connection = (
            output_connection
            if output_connection
            else self._resolve_visual_output_connection(project_key, input_dataset)
        )
        existing_recipe_names = {
            str(recipe.get("name"))
            for recipe in self.list_recipes(project_key)
            if recipe.get("name")
        }
        existing_dataset_names = {
            str(dataset.get("name"))
            for dataset in self.list_datasets(project_key)
            if dataset.get("name")
        }
        return self._action_summary(
            operation="create_prediction_scoring_recipe",
            project_key=project_key,
            object_type="recipe",
            object_name=recipe_name,
            risk_level="medium",
            rollback_possible=True,
            exact_operation=(
                "Create a native Dataiku prediction scoring recipe from a "
                "deployed saved model."
            ),
            changes={
                "saved_model_id": saved_model_id,
                "input_dataset": input_dataset,
                "output_dataset_name": output_dataset_name,
                "output_connection": resolved_output_connection,
                "recipe_exists": recipe_name in existing_recipe_names,
                "output_dataset_exists": output_dataset_name in existing_dataset_names,
            },
        )

    def create_prediction_scoring_recipe(
        self,
        project_key: str,
        saved_model_id: str,
        input_dataset: str,
        *,
        recipe_name: str,
        output_dataset_name: str,
        output_connection: str | None = None,
    ) -> dict[str, Any]:
        self._validate_scoring_recipe_creation(
            project_key,
            recipe_name=recipe_name,
            output_dataset_name=output_dataset_name,
        )
        self.get_saved_model_details(project_key, saved_model_id)
        self._get_dataset(project_key, input_dataset)
        project = self._get_project(project_key)
        resolved_output_connection = (
            output_connection
            if output_connection
            else self._resolve_visual_output_connection(project_key, input_dataset)
        )
        creator = self._call_method(project, ("new_recipe",), "prediction_scoring", recipe_name)
        self._call_method(creator, ("with_input_model",), saved_model_id)
        self._call_method(creator, ("with_input",), input_dataset)
        self._call_method(
            creator,
            ("with_new_output",),
            output_dataset_name,
            resolved_output_connection,
        )
        recipe = self._call_method(creator, ("create", "build"))
        return {
            "created": True,
            "recipe_name": recipe_name,
            "recipe_type": "prediction_scoring",
            "saved_model_id": saved_model_id,
            "input_dataset": input_dataset,
            "output_dataset_name": output_dataset_name,
            "output_connection": resolved_output_connection,
            "recipe": self._normalize_mapping(
                self._call_method(recipe, ("get_definition", "to_dict"), default={})
            ),
        }

    def list_model_evaluation_stores(self, project_key: str) -> list[dict[str, Any]]:
        project = self._get_project(project_key)
        raw_stores = self._call_method(project, ("list_model_evaluation_stores",), default=[])
        if not isinstance(raw_stores, Sequence) or isinstance(raw_stores, (str, bytes)):
            return []
        return [
            self._normalize_model_evaluation_store_summary(store)
            for store in raw_stores
            if self._normalize_model_evaluation_store_summary(store).get("evaluation_store_id")
        ]

    def get_model_evaluation_store_details(
        self,
        project_key: str,
        evaluation_store_id: str,
    ) -> dict[str, Any]:
        store = self._get_model_evaluation_store(project_key, evaluation_store_id)
        summary = self._find_model_evaluation_store_summary(project_key, evaluation_store_id)
        settings = self._normalize_settings_payload(
            self._call_method(store, ("get_settings",), default={})
        )
        try:
            raw_evaluations = self._call_method(
                store,
                ("list_model_evaluations", "list_evaluations"),
                default=[],
            )
        except DataikuCodexError:
            raw_evaluations = []
        evaluations: list[dict[str, Any]] = []
        if isinstance(raw_evaluations, Sequence) and not isinstance(raw_evaluations, (str, bytes)):
            evaluations = [
                self._normalize_model_evaluation_summary(evaluation)
                for evaluation in raw_evaluations
            ]
        try:
            latest_evaluation = self._call_method(
                store,
                ("get_latest_model_evaluation", "get_latest_evaluation"),
                default=None,
            )
        except DataikuCodexError:
            latest_evaluation = None
        latest_metrics: dict[str, Any] = {}
        latest_full_info: dict[str, Any] = {}
        latest_evaluation_id: str | None = None
        if latest_evaluation is not None:
            latest_evaluation_id = self._extract_evaluation_id(latest_evaluation)
            try:
                latest_metrics = self._normalize_metric_values(
                    self._call_method(latest_evaluation, ("get_metrics",), default={})
                )
            except DataikuCodexError:
                latest_metrics = {}
            try:
                latest_full_info = self._normalize_evaluation_full_info(
                    self._call_method(latest_evaluation, ("get_full_info",), default={})
                )
            except DataikuCodexError:
                latest_full_info = {}
        try:
            last_metric_values = self._normalize_metric_values(
                self._call_method(store, ("get_last_metric_values",), default={})
            )
        except DataikuCodexError:
            last_metric_values = {}
        return {
            **summary,
            "settings": settings,
            "evaluations_count": len(evaluations),
            "evaluations": evaluations,
            "latest_evaluation_id": latest_evaluation_id,
            "latest_metrics": latest_metrics,
            "latest_full_info": latest_full_info,
            "last_metric_values": last_metric_values,
            "primary_metric": self._select_primary_metric(latest_metrics or last_metric_values),
        }

    def preview_create_model_evaluation(
        self,
        project_key: str,
        saved_model_id: str,
        evaluation_dataset: str,
        *,
        evaluation_store_id: str | None = None,
        evaluation_store_name: str | None = None,
        recipe_name: str | None = None,
        scored_output_dataset: str | None = None,
        metrics_output_dataset: str | None = None,
        metrics: Sequence[str] | None = None,
        run_immediately: bool = False,
    ) -> dict[str, Any]:
        plan = self._resolve_model_evaluation_plan(
            project_key,
            saved_model_id,
            evaluation_dataset,
            evaluation_store_id=evaluation_store_id,
            evaluation_store_name=evaluation_store_name,
            recipe_name=recipe_name,
            scored_output_dataset=scored_output_dataset,
            metrics_output_dataset=metrics_output_dataset,
            metrics=metrics,
            run_immediately=run_immediately,
        )
        return self._action_summary(
            operation="create_model_evaluation",
            project_key=project_key,
            object_type="evaluation_recipe",
            object_name=str(plan["recipe_name"]),
            risk_level="medium" if run_immediately else "low",
            rollback_possible=True,
            exact_operation=(
                "Create Dataiku-native evaluation assets for a deployed saved model and "
                "optionally run the evaluation recipe immediately."
            ),
            changes=plan,
        )

    def create_model_evaluation(
        self,
        project_key: str,
        saved_model_id: str,
        evaluation_dataset: str,
        *,
        evaluation_store_id: str | None = None,
        evaluation_store_name: str | None = None,
        recipe_name: str | None = None,
        scored_output_dataset: str | None = None,
        metrics_output_dataset: str | None = None,
        metrics: Sequence[str] | None = None,
        run_immediately: bool = False,
    ) -> dict[str, Any]:
        plan = self._resolve_model_evaluation_plan(
            project_key,
            saved_model_id,
            evaluation_dataset,
            evaluation_store_id=evaluation_store_id,
            evaluation_store_name=evaluation_store_name,
            recipe_name=recipe_name,
            scored_output_dataset=scored_output_dataset,
            metrics_output_dataset=metrics_output_dataset,
            metrics=metrics,
            run_immediately=run_immediately,
        )
        self._validate_model_evaluation_creation(
            project_key,
            recipe_name=str(plan["recipe_name"]),
            evaluation_store_id=cast(str | None, plan["evaluation_store_id"]),
            evaluation_store_name=cast(str | None, plan["evaluation_store_name"]),
            scored_output_dataset=str(plan["scored_output_dataset"]),
            metrics_output_dataset=str(plan["metrics_output_dataset"]),
        )

        project = self._get_project(project_key)
        evaluation_store_handle = None
        resolved_store_id = cast(str | None, plan["evaluation_store_id"])
        if resolved_store_id is None:
            evaluation_store_handle = self._call_method(
                project,
                ("create_model_evaluation_store",),
                str(plan["evaluation_store_name"]),
            )
            resolved_store_id = (
                cast(str | None, self._read_attribute(evaluation_store_handle, "mes_id"))
                or cast(str | None, self._read_attribute(evaluation_store_handle, "id"))
                or cast(str | None, self._normalize_mapping(evaluation_store_handle).get("id"))
            )
            if resolved_store_id is None:
                raise UnsupportedOperationError(
                    "Could not resolve the created model evaluation store identifier.",
                    suggested_fix=(
                        "Create the evaluation store manually in DSS and pass "
                        "evaluation_store_id explicitly."
                    ),
                )
        else:
            evaluation_store_handle = self._get_model_evaluation_store(
                project_key,
                resolved_store_id,
            )

        connection = self._resolve_visual_output_connection(project_key, evaluation_dataset)
        self._ensure_managed_dataset(project_key, str(plan["scored_output_dataset"]), connection)
        self._ensure_managed_dataset(project_key, str(plan["metrics_output_dataset"]), connection)

        creator = self._call_method(
            project,
            ("new_recipe",),
            "evaluation",
            str(plan["recipe_name"]),
        )
        self._call_method(creator, ("with_input_model",), saved_model_id)
        self._call_method(creator, ("with_input",), evaluation_dataset)
        self._call_method(creator, ("with_output",), str(plan["scored_output_dataset"]))
        self._call_method(creator, ("with_output_metrics",), str(plan["metrics_output_dataset"]))
        self._call_method(creator, ("with_output_evaluation_store",), resolved_store_id)
        recipe = self._call_method(creator, ("create", "build"))

        run_job_id = None
        if run_immediately:
            run_job = self._call_method(recipe, ("run",), default=None)
            run_job_id = self._read_attribute(run_job, "id") if run_job is not None else None

        try:
            details = self.get_model_evaluation_store_details(project_key, resolved_store_id)
        except DataikuCodexError as exc:
            details = {
                **self._find_model_evaluation_store_summary(project_key, resolved_store_id),
                "details_warning": exc.message,
            }
        return {
            "created": True,
            "recipe_name": str(plan["recipe_name"]),
            "saved_model_id": saved_model_id,
            "evaluation_dataset": evaluation_dataset,
            "evaluation_store_id": resolved_store_id,
            "evaluation_store_name": plan["evaluation_store_name"],
            "scored_output_dataset": plan["scored_output_dataset"],
            "metrics_output_dataset": plan["metrics_output_dataset"],
            "metrics": plan["metrics"],
            "run_immediately": run_immediately,
            "run_job_id": run_job_id,
            "evaluation_store": details,
            "recipe": self._normalize_mapping(
                self._call_method(recipe, ("get_definition", "to_dict"), default={})
            ),
        }

    def compare_saved_models(
        self,
        project_key: str,
        saved_model_ids: Sequence[str],
        *,
        metric_name: str | None = None,
    ) -> dict[str, Any]:
        models = [
            self.get_saved_model_details(project_key, saved_model_id)
            for saved_model_id in saved_model_ids
        ]
        comparison_metric = metric_name or self._select_comparison_metric(models)
        ranked_models = sorted(
            models,
            key=lambda model: self._metric_sort_value(
                cast(dict[str, Any], model.get("active_version_metrics", {})),
                comparison_metric,
            ),
            reverse=self._metric_prefers_higher(comparison_metric),
        )
        best_model = ranked_models[0] if ranked_models else None
        return {
            "metric_name": comparison_metric,
            "models": ranked_models,
            "best_model": best_model,
            "summary": (
                f"Compared {len(ranked_models)} saved model(s) using metric {comparison_metric}."
            ),
        }

    def generate_model_evaluation_report(
        self,
        project_key: str,
        *,
        evaluation_store_id: str | None = None,
        saved_model_ids: Sequence[str] | None = None,
        metric_name: str | None = None,
    ) -> dict[str, Any]:
        if evaluation_store_id is not None:
            details = self.get_model_evaluation_store_details(project_key, evaluation_store_id)
            primary_metric = cast(dict[str, Any], details.get("primary_metric") or {})
            report_lines = [
                f"# Model Evaluation Report for {evaluation_store_id}",
                "",
                f"- Project: {project_key}",
                f"- Evaluations count: {details.get('evaluations_count', 0)}",
                f"- Primary metric: {primary_metric.get('metric_name', 'n/a')}",
                f"- Primary value: {primary_metric.get('metric_value', 'n/a')}",
            ]
            return {
                "basis": "evaluation_store",
                "evaluation_store": details,
                "report_markdown": "\n".join(report_lines),
                "summary": f"Generated an evaluation report from store {evaluation_store_id}.",
            }

        if not saved_model_ids:
            raise ConfigurationError(
                "Provide evaluation_store_id or at least one saved_model_id.",
                suggested_fix="Pass --evaluation-store-id or --saved-model-ids.",
            )
        comparison = self.compare_saved_models(
            project_key,
            saved_model_ids,
            metric_name=metric_name,
        )
        best_model = cast(dict[str, Any] | None, comparison.get("best_model"))
        report_lines = [
            "# Saved Model Comparison Report",
            "",
            f"- Project: {project_key}",
            f"- Comparison metric: {comparison.get('metric_name')}",
        ]
        if best_model is not None:
            report_lines.append(
                f"- Best model: {best_model.get('name') or best_model.get('saved_model_id')}"
            )
        for model in cast(list[dict[str, Any]], comparison.get("models", [])):
            primary_metric = cast(dict[str, Any], model.get("primary_metric") or {})
            report_lines.append(
                
                    f"- {model.get('name') or model.get('saved_model_id')}: "
                    f"{primary_metric.get('metric_name', comparison.get('metric_name'))}="
                    f"{primary_metric.get('metric_value', 'n/a')}"
                
            )
        return {
            "basis": "saved_model_comparison",
            "comparison": comparison,
            "report_markdown": "\n".join(report_lines),
            "summary": "Generated a saved model comparison report.",
        }

    def route_ml_intent(
        self,
        intent_text: str,
        *,
        default_project_key: str | None = None,
        default_dataset_name: str | None = None,
    ) -> dict[str, Any]:
        routed = analyze_ml_intent(
            intent_text,
            default_project_key=default_project_key,
            default_dataset_name=default_dataset_name,
        )
        return self._resolve_routed_ml_intent(routed)

    def preview_run_routed_ml_intent(
        self,
        intent_text: str,
        *,
        default_project_key: str | None = None,
        default_dataset_name: str | None = None,
    ) -> dict[str, Any]:
        routed = self.route_ml_intent(
            intent_text,
            default_project_key=default_project_key,
            default_dataset_name=default_dataset_name,
        )
        intent_type = cast(str, routed["intent_type"])
        if intent_type == "bootstrap_ml_command":
            return self.preview_run_ml_command(
                cast(str, routed["project_key"]),
                cast(str, routed["dataset_name"]),
                cast(str, routed["command_name"]),
                target_variable=cast(str | None, routed.get("target_variable")),
            )
        if intent_type == "train_latest_ml_task":
            return self.preview_train_ml_task(
                cast(str, routed["project_key"]),
                cast(str, routed["analysis_id"]),
                cast(str, routed["ml_task_id"]),
            )
        if intent_type == "deploy_best_model":
            return self.preview_deploy_trained_model_to_flow(
                cast(str, routed["project_key"]),
                cast(str, routed["analysis_id"]),
                cast(str, routed["ml_task_id"]),
                model_id=cast(str | None, routed.get("model_id")),
                saved_model_name=cast(str | None, routed.get("saved_model_name")),
            )
        raise ConfigurationError(
            "This intent does not map to an executable ML action.",
            suggested_fix="Route the intent first and use one of the executable intent types.",
        )

    def run_routed_ml_intent(
        self,
        intent_text: str,
        *,
        default_project_key: str | None = None,
        default_dataset_name: str | None = None,
    ) -> dict[str, Any]:
        routed = self.route_ml_intent(
            intent_text,
            default_project_key=default_project_key,
            default_dataset_name=default_dataset_name,
        )
        intent_type = cast(str, routed["intent_type"])
        if intent_type == "bootstrap_ml_command":
            return self.run_ml_command(
                cast(str, routed["project_key"]),
                cast(str, routed["dataset_name"]),
                cast(str, routed["command_name"]),
                target_variable=cast(str | None, routed.get("target_variable")),
            )
        if intent_type == "train_latest_ml_task":
            return self.train_ml_task(
                cast(str, routed["project_key"]),
                cast(str, routed["analysis_id"]),
                cast(str, routed["ml_task_id"]),
            )
        if intent_type == "deploy_best_model":
            return self.deploy_trained_model_to_flow(
                cast(str, routed["project_key"]),
                cast(str, routed["analysis_id"]),
                cast(str, routed["ml_task_id"]),
                model_id=cast(str | None, routed.get("model_id")),
                saved_model_name=cast(str | None, routed.get("saved_model_name")),
            )
        raise ConfigurationError(
            "This intent does not map to an executable ML action.",
            suggested_fix="Use a setup, train latest task or deploy best model style request.",
        )

    def list_plugin_usages(self, project_key: str) -> list[dict[str, Any]]:
        project = self._get_project(project_key)
        raw_usages = self._call_method(project, ("list_plugins_usages",), default=[])
        if not isinstance(raw_usages, Sequence) or isinstance(raw_usages, (str, bytes)):
            return []
        usages: list[dict[str, Any]] = []
        for raw_usage in raw_usages:
            normalized = self._normalize_mapping(raw_usage)
            plugin_usage_bundle = getattr(raw_usage, "plugin_usages", None)
            usage_objects = (
                getattr(plugin_usage_bundle, "usages", [])
                if plugin_usage_bundle
                else []
            )
            normalized_usages: list[dict[str, Any]] = []
            for usage_object in usage_objects if isinstance(usage_objects, Sequence) else []:
                usage_mapping = self._normalize_mapping(usage_object)
                normalized_usages.append(
                    {
                        "object_type": usage_mapping.get("objectType")
                        or usage_mapping.get("object_type")
                        or self._read_attribute(usage_object, "object_type"),
                        "object_id": usage_mapping.get("objectId")
                        or usage_mapping.get("object_id")
                        or self._read_attribute(usage_object, "object_id"),
                        "element_kind": usage_mapping.get("elementKind")
                        or usage_mapping.get("element_kind")
                        or self._read_attribute(usage_object, "element_kind"),
                        "element_type": usage_mapping.get("elementType")
                        or usage_mapping.get("element_type")
                        or self._read_attribute(usage_object, "element_type"),
                        "project_key": usage_mapping.get("projectKey")
                        or usage_mapping.get("project_key")
                        or self._read_attribute(usage_object, "project_key"),
                    }
                )
            usages.append(
                {
                    "plugin_id": normalized.get("pluginId")
                    or normalized.get("plugin_id")
                    or self._read_attribute(raw_usage, "plugin_id")
                    or normalized.get("id"),
                    "plugin_name": normalized.get("pluginName")
                    or normalized.get("plugin_name")
                    or normalized.get("name")
                    or self._read_attribute(raw_usage, "plugin_id"),
                    "usage_type": normalized.get("usageType")
                    or normalized.get("type")
                    or (
                        sorted(
                            {
                                str(item.get("element_kind"))
                                for item in normalized_usages
                                if item.get("element_kind")
                            }
                        )
                    ),
                    "recipe_names": [
                        str(item["object_id"])
                        for item in normalized_usages
                        if item.get("object_type") == "RECIPE" and item.get("object_id")
                    ],
                    "object_usages": normalized_usages,
                }
            )
        return usages

    def generate_scenario_dependency_map(self, project_key: str) -> dict[str, Any]:
        scenarios = []
        for scenario in self.list_scenarios(project_key):
            scenario_id = scenario.get("scenario_id")
            if not isinstance(scenario_id, str) or not scenario_id:
                continue
            scenario_handle = self._get_scenario(project_key, scenario_id)
            settings = self._normalize_settings_payload(
                self._get_scenario_settings(scenario_handle)
            )
            scenarios.append(
                {
                    **scenario,
                    "steps": settings.get("params", {}).get("steps", [])
                    if isinstance(settings.get("params"), Mapping)
                    else [],
                }
            )
        return build_scenario_dependency_map(
            project_key=project_key,
            scenarios=scenarios,
            known_datasets=[
                str(dataset.get("name"))
                for dataset in self.list_datasets(project_key)
                if dataset.get("name")
            ],
            known_recipes=[
                str(recipe.get("name"))
                for recipe in self.list_recipes(project_key)
                if recipe.get("name")
            ],
        )

    def plan_code_env_updates(self, *, env_name: str | None = None) -> dict[str, Any]:
        target_env_names = [env_name] if env_name else [
            str(code_env.get("name"))
            for code_env in self.list_code_envs()
            if code_env.get("name")
        ]
        diagnoses = [self.code_env_doctor(target_env_name) for target_env_name in target_env_names]
        return build_code_env_update_plan(diagnoses)

    def generate_production_readiness_report(self, project_key: str) -> dict[str, Any]:
        return build_production_readiness_report(
            project_key=project_key,
            project_summary=self.get_project_summary(project_key),
            flow_health=self.analyze_flow_health(project_key),
            scenario_dependency_map=self.generate_scenario_dependency_map(project_key),
            code_env_update_plan=self.plan_code_env_updates(),
            plugin_usages=self.list_plugin_usages(project_key),
            ml_assets={
                "ml_tasks": len(self.list_ml_tasks(project_key)),
                "saved_models": len(self.list_saved_models(project_key)),
            },
        )

    def generate_cost_performance_report(self, project_key: str) -> dict[str, Any]:
        return build_cost_performance_report(
            project_key=project_key,
            project_summary=self.get_project_summary(project_key),
            flow_health=self.analyze_flow_health(project_key),
            scenario_dependency_map=self.generate_scenario_dependency_map(project_key),
            code_env_update_plan=self.plan_code_env_updates(),
            plugin_usages=self.list_plugin_usages(project_key),
            ml_assets={
                "ml_tasks": len(self.list_ml_tasks(project_key)),
                "saved_models": len(self.list_saved_models(project_key)),
            },
            model_evaluation_store_count=len(self.list_model_evaluation_stores(project_key)),
        )

    def generate_production_readiness_checklist(self, project_key: str) -> dict[str, Any]:
        return build_production_readiness_checklist(
            project_key=project_key,
            readiness_report=self.generate_production_readiness_report(project_key),
            cost_performance_report=self.generate_cost_performance_report(project_key),
            scenario_dependency_map=self.generate_scenario_dependency_map(project_key),
            code_env_update_plan=self.plan_code_env_updates(),
            plugin_usages=self.list_plugin_usages(project_key),
            ml_assets={
                "ml_tasks": len(self.list_ml_tasks(project_key)),
                "saved_models": len(self.list_saved_models(project_key)),
            },
        )

    def generate_governance_documentation(self, project_key: str) -> dict[str, Any]:
        project_summary = self.get_project_summary(project_key)
        readiness_report = self.generate_production_readiness_report(project_key)
        cost_report = self.generate_cost_performance_report(project_key)
        checklist = self.generate_production_readiness_checklist(project_key)
        governance = generate_governance_documentation(
            project_summary=project_summary,
            readiness_report=readiness_report,
            cost_performance_report=cost_report,
            production_checklist=checklist,
            plugin_usages=self.list_plugin_usages(project_key),
            code_env_update_plan=self.plan_code_env_updates(),
        )
        return {
            "markdown": governance["markdown"],
            "summary": governance["summary"],
            "readiness": readiness_report.get("readiness"),
            "checklist_gate": checklist.get("readiness_gate"),
        }

    def preview_create_managed_folder(
        self,
        project_key: str,
        folder_name: str,
        *,
        connection: str | None = None,
        folder_type: str | None = None,
    ) -> dict[str, Any]:
        existing_folder_names = {
            folder.get("name")
            for folder in self.list_managed_folders(project_key)
            if folder.get("name")
        }
        resolved_connection = self._resolve_managed_folder_connection(project_key, connection)
        return self._action_summary(
            operation="create_managed_folder",
            project_key=project_key,
            object_type="managed_folder",
            object_name=folder_name,
            risk_level="low",
            rollback_possible=True,
            exact_operation="Create a new Managed Folder in the target project.",
            changes={
                "folder_exists": folder_name in existing_folder_names,
                "connection": resolved_connection,
                "folder_type": folder_type or "default",
            },
        )

    def create_managed_folder(
        self,
        project_key: str,
        folder_name: str,
        *,
        connection: str | None = None,
        folder_type: str | None = None,
    ) -> dict[str, Any]:
        existing_folder_names = {
            folder.get("name")
            for folder in self.list_managed_folders(project_key)
            if folder.get("name")
        }
        if folder_name in existing_folder_names:
            raise ConfigurationError(
                f"Managed Folder {folder_name} already exists.",
                suggested_fix="Choose a new folder name or delete the existing folder first.",
            )
        project = self._get_project(project_key)
        resolved_connection = self._resolve_managed_folder_connection(project_key, connection)
        folder = self._call_method(
            project,
            ("create_managed_folder",),
            folder_name,
            folder_type,
            resolved_connection,
        )
        normalized_folder = self._normalize_mapping(folder)
        folder_id = (
            normalized_folder.get("folderId")
            or normalized_folder.get("id")
            or self._find_managed_folder_id_by_name(project_key, folder_name)
            or folder_name
        )
        return {
            "folder_id": folder_id,
            "created": True,
            "connection": resolved_connection,
            "rollback_guidance": (
                "Delete the Managed Folder manually in DSS if you need to roll back this creation."
            ),
        }

    def preview_upload_file_to_folder(
        self,
        project_key: str,
        folder_id: str,
        *,
        file_path: str,
        content_base64: str,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        payload = self._decode_base64_content(content_base64)
        existing_paths = {
            file_entry.get("path")
            for file_entry in self.list_folder_files(
                project_key,
                folder_id,
                recursive=True,
                limit=self.settings.max_listed_files,
            ).get("files", [])
            if file_entry.get("path")
        }
        normalized_path = file_path.lstrip("/")
        return self._action_summary(
            operation="upload_file_to_folder",
            project_key=project_key,
            object_type="managed_folder_file",
            object_name=f"{folder_id}:{normalized_path}",
            risk_level="medium",
            rollback_possible=True,
            exact_operation="Upload a file into an existing Managed Folder.",
            changes={
                "folder_id": folder_id,
                "file_path": normalized_path,
                "size_bytes": len(payload),
                "file_exists": normalized_path in existing_paths,
                "overwrite": overwrite,
            },
        )

    def upload_file_to_folder(
        self,
        project_key: str,
        folder_id: str,
        *,
        file_path: str,
        content_base64: str,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        payload = self._decode_base64_content(content_base64)
        normalized_path = file_path.lstrip("/")
        existing_paths = {
            file_entry.get("path")
            for file_entry in self.list_folder_files(
                project_key,
                folder_id,
                recursive=True,
                limit=self.settings.max_listed_files,
            ).get("files", [])
            if file_entry.get("path")
        }
        if normalized_path in existing_paths and not overwrite:
            raise ConfigurationError(
                f"File {normalized_path} already exists in folder {folder_id}.",
                suggested_fix=(
                    "Retry with overwrite=true if replacing the existing file "
                    "is intended."
                ),
            )
        folder = self._get_managed_folder(project_key, folder_id)
        try:
            upload_result = self._call_method(
                folder,
                ("put_file",),
                normalized_path,
                io.BytesIO(payload),
            )
        except Exception as exc:
            raise map_exception(exc) from exc
        normalized = self._normalize_mapping(upload_result)
        return {
            "folder_id": folder_id,
            "file_path": normalized.get("path") or normalized_path,
            "size": normalized.get("size") or len(payload),
            "uploaded": True,
            "rollback_guidance": (
                "Delete the uploaded file from the Managed Folder if you need to roll back."
            ),
        }

    def _find_managed_folder_id_by_name(
        self,
        project_key: str,
        folder_name: str,
    ) -> str | None:
        for folder in self.list_managed_folders(project_key):
            if folder.get("name") == folder_name:
                folder_id = folder.get("folder_id")
                if isinstance(folder_id, str) and folder_id:
                    return folder_id
        return None

    def _resolve_managed_folder_connection(
        self,
        project_key: str,
        requested_connection: str | None,
    ) -> str:
        if requested_connection:
            return requested_connection

        existing_connections: list[str] = []
        for folder in self.list_managed_folders(project_key):
            connection = folder.get("connection")
            if (
                isinstance(connection, str)
                and connection
                and connection not in existing_connections
            ):
                existing_connections.append(connection)
        if existing_connections:
            return existing_connections[0]

        raw_connections = self._call_method(self.client, ("list_connections",), default=[])
        available_names: list[str] = []
        if isinstance(raw_connections, Sequence) and not isinstance(raw_connections, (str, bytes)):
            for raw_connection in raw_connections:
                normalized = self._normalize_mapping(raw_connection)
                name = normalized.get("name")
                if isinstance(name, str) and name and name not in available_names:
                    available_names.append(name)

        for preferred_name in (
            "dataiku-managed-storage",
            "filesystem_folders",
            "filesystem_managed",
        ):
            if preferred_name in available_names:
                return preferred_name
        return available_names[0] if available_names else "filesystem_folders"

    def _extract_recipe_settings(self, raw_settings: Any) -> dict[str, Any]:
        if isinstance(raw_settings, Mapping):
            return dict(raw_settings)

        get_recipe_raw_definition = getattr(raw_settings, "get_recipe_raw_definition", None)
        if callable(get_recipe_raw_definition):
            try:
                definition = get_recipe_raw_definition()
            except Exception as exc:
                raise map_exception(exc) from exc
            if isinstance(definition, Mapping):
                return dict(definition)

        recipe_settings = getattr(raw_settings, "recipe_settings", None)
        if isinstance(recipe_settings, Mapping):
            return dict(recipe_settings)

        data = getattr(raw_settings, "data", None)
        if isinstance(data, Mapping):
            recipe_data = data.get("recipe")
            if isinstance(recipe_data, Mapping):
                return dict(recipe_data)

        return self._normalize_api_mapping(raw_settings)

    def preview_create_scenario(
        self,
        project_key: str,
        scenario_name: str,
        *,
        scenario_type: str = "custom_python",
        code: str | None = None,
        build_datasets: list[str] | None = None,
        active: bool = False,
    ) -> dict[str, Any]:
        normalized_type = self._normalize_scenario_type(scenario_type)
        datasets_to_build = build_datasets or []
        generated_code = self._resolve_scenario_code(
            scenario_type=normalized_type,
            code=code,
            build_datasets=datasets_to_build,
        )
        existing_ids, existing_names = self._existing_scenario_identifiers(project_key)
        missing_datasets = self._find_unknown_datasets(project_key, datasets_to_build)
        return self._action_summary(
            operation="create_scenario",
            project_key=project_key,
            object_type="scenario",
            object_name=scenario_name,
            risk_level="medium",
            rollback_possible=True,
            exact_operation="Create a new Dataiku scenario in the target project.",
            changes={
                "scenario_exists": (
                    scenario_name in existing_ids or scenario_name in existing_names
                ),
                "scenario_type": normalized_type,
                "active": active,
                "build_datasets": datasets_to_build,
                "missing_build_datasets": missing_datasets,
                "code_lines": len(generated_code.splitlines()) if generated_code else 0,
            },
        )

    def create_scenario(
        self,
        project_key: str,
        scenario_name: str,
        *,
        scenario_type: str = "custom_python",
        code: str | None = None,
        build_datasets: list[str] | None = None,
        active: bool = False,
    ) -> dict[str, Any]:
        normalized_type = self._normalize_scenario_type(scenario_type)
        datasets_to_build = build_datasets or []
        generated_code = self._resolve_scenario_code(
            scenario_type=normalized_type,
            code=code,
            build_datasets=datasets_to_build,
        )
        self._validate_scenario_creation(
            project_key,
            scenario_name,
            scenario_type=normalized_type,
            build_datasets=datasets_to_build,
        )

        definition: dict[str, Any] = {
            "params": {},
            "triggers": [],
            "reporters": [],
            "active": active,
            "customMeta": {"kv": {}},
            "tags": [],
        }
        if normalized_type == "step_based":
            definition["params"] = {
                "steps": self._build_step_based_scenario_steps(
                    project_key,
                    datasets_to_build,
                )
            }

        project = self._get_project(project_key)
        scenario = self._call_method(
            project,
            ("create_scenario",),
            scenario_name,
            normalized_type,
            definition,
        )

        if normalized_type == "custom_python":
            settings = self._call_method(scenario, ("get_settings",), default=None)
            if settings is not None and hasattr(settings, "code") and hasattr(settings, "save"):
                try:
                    settings.code = generated_code
                    if hasattr(settings, "active"):
                        settings.active = active
                    settings.save()
                except Exception as exc:
                    raise map_exception(exc) from exc
            else:
                self._call_method(scenario, ("set_payload",), generated_code)

        scenario_id = self._read_attribute(scenario, "id") or scenario_name
        return {
            "scenario_id": str(scenario_id),
            "scenario_name": scenario_name,
            "scenario_type": normalized_type,
            "active": active,
            "created": True,
            "build_datasets": datasets_to_build,
            "code_lines": len(generated_code.splitlines()) if generated_code else 0,
            "rollback_guidance": (
                "Delete the scenario manually in DSS if you need to roll back this creation."
            ),
        }

    def preview_run_scenario(
        self,
        project_key: str,
        scenario_id: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        scenarios = {
            scenario.get("scenario_id"): scenario
            for scenario in self.list_scenarios(project_key)
        }
        scenario = scenarios.get(scenario_id, {})
        return self._action_summary(
            operation="run_scenario",
            project_key=project_key,
            object_type="scenario",
            object_name=scenario_id,
            risk_level="high",
            rollback_possible=False,
            exact_operation="Trigger a scenario execution on DSS.",
            changes={
                "active": scenario.get("active"),
                "running": scenario.get("running"),
                "trigger_type": scenario.get("trigger_type"),
                "params": params or {},
            },
        )

    def run_scenario(
        self,
        project_key: str,
        scenario_id: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        scenario = self._get_scenario(project_key, scenario_id)
        trigger_fire = self._call_method(scenario, ("run",), params or {})
        raw = self._normalize_api_mapping(
            self._call_method(trigger_fire, ("get_raw",), default={})
        )
        scenario_run = self._call_method(
            trigger_fire,
            ("get_scenario_run",),
            default=None,
        )
        return {
            "scenario_id": scenario_id,
            "trigger_id": (
                raw.get("trigger", {}).get("id")
                if isinstance(raw.get("trigger"), Mapping)
                else self._read_attribute(trigger_fire, "trigger_id")
            ),
            "trigger_run_id": raw.get("runId") or self._read_attribute(trigger_fire, "run_id"),
            "scenario_run_id": (
                self._normalize_mapping(
                    self._call_method(scenario_run, ("get_info",), default={})
                ).get("runId")
                if scenario_run is not None
                else None
            ),
            "requested": True,
            "rollback_guidance": "Scenario runs cannot be rolled back automatically.",
        }

    def preview_create_project_documentation(
        self,
        project_key: str,
        *,
        target: str,
        markdown: str,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        resolved_target = self._resolve_documentation_target(project_key, target)
        return self._action_summary(
            operation="create_project_documentation",
            project_key=project_key,
            object_type=resolved_target["target_type"],
            object_name=str(resolved_target["target_name"]),
            risk_level="medium",
            rollback_possible=resolved_target["target_type"] == "project_library",
            exact_operation="Write generated markdown into a project library file or wiki article.",
            changes={
                "target": target,
                "target_type": resolved_target["target_type"],
                "exists": resolved_target["exists"],
                "overwrite": overwrite,
                "markdown_lines": len(markdown.splitlines()),
            },
        )

    def create_project_documentation(
        self,
        project_key: str,
        *,
        target: str,
        markdown: str,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        resolved_target = self._resolve_documentation_target(project_key, target)
        if resolved_target["exists"] and not overwrite:
            raise ConfigurationError(
                f"Target {target} already exists.",
                suggested_fix=(
                    "Retry with overwrite=true if replacing the existing "
                    "documentation is intended."
                ),
            )

        if resolved_target["target_type"] == "project_library":
            file_handle = resolved_target["handle"]
            if file_handle is None:
                library = resolved_target["container"]
                try:
                    file_handle = library.add_file(resolved_target["path"])
                except Exception as exc:
                    raise map_exception(exc) from exc
            try:
                self._call_method(file_handle, ("write",), markdown)
            except Exception as exc:
                raise map_exception(exc) from exc
            return {
                "target": target,
                "written": True,
                "target_type": "project_library",
                "rollback_guidance": (
                    "Overwrite or delete the library file manually to revert "
                    "this change."
                ),
            }

        article = resolved_target["handle"]
        if article is None:
            wiki = resolved_target["container"]
            try:
                article = self._call_method(
                    wiki,
                    ("create_article",),
                    resolved_target["article_name"],
                    None,
                    markdown,
                )
            except Exception as exc:
                raise map_exception(exc) from exc
            return {
                "target": target,
                "written": True,
                "target_type": "wiki_article",
                "rollback_guidance": (
                    "Delete or edit the wiki article manually to revert this "
                    "change."
                ),
            }

        article_data = self._call_method(article, ("get_data",), default=None)
        if (
            article_data is None
            or not hasattr(article_data, "set_body")
            or not hasattr(article_data, "save")
        ):
            raise UnsupportedOperationError(
                "The target wiki article does not expose editable content through the API.",
                suggested_fix="Write to the project library instead, or adapt the wiki wrapper.",
            )
        try:
            article_data.set_body(markdown)
            article_data.save()
        except Exception as exc:
            raise map_exception(exc) from exc
        return {
            "target": target,
            "written": True,
            "target_type": "wiki_article",
            "rollback_guidance": "Edit or delete the wiki article manually to revert this change.",
        }

    def _get_instance_info_payload(self) -> dict[str, Any]:
        client = self.client
        methods = (
            "get_info",
            "info",
            "get_general_info",
            "get_instance_info",
        )
        for method_name in methods:
            method = getattr(client, method_name, None)
            if method is None:
                continue
            try:
                raw = method()
            except Exception as exc:
                raise map_exception(exc) from exc
            normalized = self._normalize_mapping(raw)
            return {
                "version": normalized.get("version"),
                "node_type": normalized.get("nodeType") or normalized.get("node_type"),
                "user": normalized.get("user") or normalized.get("login"),
                "features": normalized.get("features", []),
            }
        return {"version": None, "node_type": None, "user": None, "features": []}

    def _get_project(self, project_key: str) -> Any:
        return self._call_method(self.client, ("get_project",), project_key)

    def _get_dataset(self, project_key: str, dataset_name: str) -> Any:
        project = self._get_project(project_key)
        return self._call_method(project, ("get_dataset", "getDataset"), dataset_name)

    def _get_recipe(self, project_key: str, recipe_name: str) -> Any:
        project = self._get_project(project_key)
        return self._call_method(project, ("get_recipe", "getRecipe"), recipe_name)

    def _get_managed_folder(self, project_key: str, folder_id: str) -> Any:
        project = self._get_project(project_key)
        return self._call_method(
            project,
            ("get_managed_folder", "get_managedfolder", "getManagedFolder"),
            folder_id,
        )

    def _get_scenario(self, project_key: str, scenario_id: str) -> Any:
        project = self._get_project(project_key)
        return self._call_method(project, ("get_scenario", "getScenario"), scenario_id)

    def _get_ml_task(self, project_key: str, analysis_id: str, ml_task_id: str) -> Any:
        project = self._get_project(project_key)
        return self._call_method(project, ("get_ml_task",), analysis_id, ml_task_id)

    def _get_saved_model(self, project_key: str, saved_model_id: str) -> Any:
        project = self._get_project(project_key)
        return self._call_method(project, ("get_saved_model",), saved_model_id)

    def _get_model_evaluation_store(self, project_key: str, evaluation_store_id: str) -> Any:
        project = self._get_project(project_key)
        return self._call_method(
            project,
            ("get_model_evaluation_store",),
            evaluation_store_id,
        )

    def _get_job(self, project_key: str, job_id: str) -> Any:
        project = self._get_project(project_key)
        return self._call_method(project, ("get_job", "getJob"), job_id)

    def _get_code_env_handle(self, env_name: str) -> Any:
        env_lang = self._resolve_code_env_language(env_name)
        for method_name in ("get_code_env", "getCodeEnv"):
            method = getattr(self.client, method_name, None)
            if not callable(method):
                continue
            try:
                return method(env_lang, env_name)
            except TypeError:
                try:
                    return method(env_name)
                except Exception as exc:
                    raise map_exception(exc) from exc
            except Exception as exc:
                raise map_exception(exc) from exc
        raise UnsupportedOperationError(
            "Code environment retrieval is not supported by the current API object.",
            suggested_fix="Adapt the wrapper to the installed dataiku-api-client methods.",
        )

    def _resolve_code_env_language(self, env_name: str) -> str:
        for code_env in self.list_code_envs():
            if code_env.get("name") != env_name:
                continue
            language = code_env.get("language")
            if isinstance(language, str) and language:
                return language.upper()
        return "PYTHON"

    def _list_scenarios(self, project: Any) -> list[Any] | None:
        raw_scenarios = self._call_method(
            project,
            ("list_scenarios", "listScenarios"),
            default=None,
        )
        if raw_scenarios is None:
            return None
        return list(raw_scenarios)

    def _coerce_scenario(self, project_key: str, project: Any, raw_scenario: Any) -> Any:
        if hasattr(raw_scenario, "get_settings") or hasattr(raw_scenario, "get_status"):
            return raw_scenario
        to_scenario = getattr(raw_scenario, "to_scenario", None)
        if callable(to_scenario):
            try:
                return to_scenario()
            except Exception as exc:
                raise map_exception(exc) from exc
        scenario_id = self._extract_scenario_id(raw_scenario)
        if not scenario_id:
            raise DataikuObjectNotFoundError(
                "Could not resolve the scenario identifier from the Dataiku API response.",
                suggested_fix="Adapt the scenario wrapper to the installed client payload shape.",
            )
        return self._call_method(project, ("get_scenario", "getScenario"), str(scenario_id))

    def _get_scenario_settings(self, scenario: Any) -> Any:
        return self._call_method(scenario, ("get_settings",), default={})

    def _get_scenario_status(self, scenario: Any) -> Any:
        return self._call_method(scenario, ("get_status",), default={})

    def _call_scenario_last_runs(self, scenario: Any, *, limit: int) -> list[Any]:
        method = getattr(scenario, "get_last_runs", None)
        if not callable(method):
            raise UnsupportedOperationError(
                "Scenario runs are not supported by the current API object.",
                suggested_fix="Adapt the wrapper to the installed dataiku-api-client methods.",
            )
        try:
            try:
                return list(method(limit=limit, only_finished_runs=False))
            except TypeError:
                return list(method(limit=limit))
        except Exception as exc:
            raise map_exception(exc) from exc

    def _find_scenario_run(
        self,
        project_key: str,
        run_id: str,
        *,
        scenario_id: str | None = None,
    ) -> tuple[str, Any]:
        if scenario_id is not None:
            scenario = self._get_scenario(project_key, scenario_id)
            return scenario_id, self._call_method(scenario, ("get_run",), run_id)

        for scenario_summary in self.list_scenarios(project_key):
            current_scenario_id = scenario_summary.get("scenario_id")
            if not isinstance(current_scenario_id, str) or not current_scenario_id:
                continue
            try:
                scenario = self._get_scenario(project_key, current_scenario_id)
                run = self._call_method(scenario, ("get_run",), run_id)
                return current_scenario_id, run
            except DataikuObjectNotFoundError:
                continue

        raise DataikuObjectNotFoundError(
            f"Scenario run {run_id} could not be found in project {project_key}.",
            details={"project_key": project_key, "run_id": run_id},
            suggested_fix="Pass a valid run_id or provide the matching scenario_id.",
        )

    def _resolve_failure_context(
        self,
        project_key: str,
        *,
        job_id: str | None,
        run_id: str | None,
        scenario_id: str | None,
    ) -> dict[str, Any]:
        if bool(job_id) == bool(run_id):
            raise ConfigurationError(
                "Provide exactly one of job_id or run_id.",
                suggested_fix="Use job_id for DSS jobs or run_id for scenario runs.",
            )

        if job_id is not None:
            job = self._get_job(project_key, job_id)
            log_text = self._call_method(job, ("get_log",), default="")
            status = self._normalize_mapping(
                self._call_method(job, ("get_status",), default={})
            )
            return {
                "source_type": "job",
                "log_text": str(log_text or ""),
                "line_count": self._count_lines(str(log_text or "")),
                "failed_steps": self._extract_failed_activities(status),
                "error_details": self._extract_job_error_details(status),
                "scenario_id": None,
            }

        assert run_id is not None
        resolved_scenario_id, run = self._find_scenario_run(
            project_key,
            run_id,
            scenario_id=scenario_id,
        )
        log_text = self._call_method(run, ("get_log",), default="")
        details = self._normalize_mapping(self._call_method(run, ("get_details",), default={}))
        return {
            "source_type": "scenario_run",
            "log_text": str(log_text or ""),
            "line_count": self._count_lines(str(log_text or "")),
            "failed_steps": self._extract_failed_steps(details),
            "error_details": self._extract_run_error_details(details),
            "scenario_id": resolved_scenario_id,
        }

    def _list_folder_files(self, folder: Any, *, path: str, recursive: bool) -> list[Any]:
        list_files = getattr(folder, "list_files", None)
        if callable(list_files):
            try:
                return list(list_files(path=path, recursive=recursive))
            except Exception as exc:
                raise map_exception(exc) from exc
        list_contents = getattr(folder, "list_contents", None)
        if callable(list_contents):
            try:
                contents = self._normalize_mapping(list_contents())
            except Exception as exc:
                raise map_exception(exc) from exc
            raw_items = contents.get("items")
            if isinstance(raw_items, Sequence) and not isinstance(raw_items, (str, bytes)):
                return list(raw_items)
            return []
        list_paths = getattr(folder, "list_paths_in_partition", None)
        if callable(list_paths):
            try:
                return list(list_paths())
            except Exception as exc:
                raise map_exception(exc) from exc
        raise UnsupportedOperationError(
            "Managed Folder file listing is not supported by the current API object.",
            suggested_fix="Adapt the wrapper to the installed dataiku-api-client methods.",
        )

    def _call_method(
        self,
        target: Any,
        method_names: Sequence[str],
        *args: Any,
        default: Any = _MISSING,
        **kwargs: Any,
    ) -> Any:
        for method_name in method_names:
            method = getattr(target, method_name, None)
            if callable(method):
                try:
                    return method(*args, **kwargs)
                except Exception as exc:
                    raise map_exception(exc) from exc
        if default is not _MISSING:
            return default
        raise UnsupportedOperationError(
            f"Dataiku API object does not support any of: {', '.join(method_names)}.",
            details={"methods": list(method_names)},
            suggested_fix=(
                "Verify the installed dataiku-api-client version and adapt the wrapper "
                "to its method names."
            ),
        )

    def _normalize_scenario_run(self, run: Any) -> dict[str, Any]:
        info = self._normalize_mapping(self._call_method(run, ("get_info",), default={}))
        details = self._normalize_mapping(self._call_method(run, ("get_details",), default={}))
        outcome = self._extract_run_outcome(run, info)
        return {
            "run_id": info.get("runId") or self._read_attribute(run, "id"),
            "outcome": outcome,
            "start_time": self._normalize_timestamp(
                self._read_attribute(run, "start_time") or info.get("start")
            ),
            "duration": self._extract_run_duration(run, info),
            "failed_steps": self._extract_failed_steps(details),
        }

    @staticmethod
    def _extract_scenario_id(raw_scenario: Any) -> str | None:
        normalized = DataikuDSSAdapter._normalize_mapping(raw_scenario)
        scenario_id = (
            normalized.get("scenarioId")
            or normalized.get("id")
            or normalized.get("name")
        )
        if scenario_id is not None:
            return str(scenario_id)
        candidate = DataikuDSSAdapter._read_attribute(raw_scenario, "id")
        return str(candidate) if candidate is not None else None

    @staticmethod
    def _extract_scenario_name(raw_scenario: Any) -> str | None:
        normalized = DataikuDSSAdapter._normalize_mapping(raw_scenario)
        scenario_name = normalized.get("name") or normalized.get("label")
        if scenario_name is not None:
            return str(scenario_name)
        candidate = DataikuDSSAdapter._read_attribute(raw_scenario, "name")
        return str(candidate) if candidate is not None else None

    @staticmethod
    def _extract_trigger_type(settings_obj: Any, settings: Mapping[str, Any]) -> str | None:
        raw_triggers = settings.get("triggers") or settings.get("raw_triggers")
        if raw_triggers is None:
            try:
                raw_triggers = settings_obj.raw_triggers
            except Exception:
                raw_triggers = None
        if isinstance(raw_triggers, Sequence) and not isinstance(raw_triggers, (str, bytes)):
            for trigger in raw_triggers:
                if isinstance(trigger, Mapping):
                    trigger_type = trigger.get("type") or trigger.get("triggerType")
                    if trigger_type is not None:
                        return str(trigger_type)
        return None

    @staticmethod
    def _normalize_timestamp(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if hasattr(value, "isoformat"):
            try:
                return str(value.isoformat())
            except Exception:
                return str(value)
        if isinstance(value, (int, float)) and value > 0:
            seconds = value / 1000 if value > 10_000_000_000 else value
            return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
        return str(value)

    @staticmethod
    def _extract_run_outcome(run: Any, info: Mapping[str, Any]) -> str | None:
        try:
            outcome = run.outcome
        except Exception:
            outcome = None
        if isinstance(outcome, str):
            return outcome
        result = info.get("result")
        if isinstance(result, Mapping):
            mapped_outcome = result.get("outcome")
            if mapped_outcome is not None:
                return str(mapped_outcome)
        running = DataikuDSSAdapter._read_attribute(run, "running", default=False)
        return "RUNNING" if running else None

    @staticmethod
    def _extract_run_duration(run: Any, info: Mapping[str, Any]) -> float | int | None:
        try:
            duration = run.duration
        except Exception:
            duration = None
        if isinstance(duration, (float, int)):
            return duration

        start = info.get("start")
        end = info.get("end")
        if isinstance(start, (int, float)) and isinstance(end, (int, float)) and end >= start:
            if start > 10_000_000_000:
                return (end - start) / 1000
            return end - start
        return None

    @staticmethod
    def _extract_failed_steps(details: Mapping[str, Any]) -> list[str]:
        step_runs = details.get("stepRuns")
        if not isinstance(step_runs, Sequence) or isinstance(step_runs, (str, bytes)):
            return []
        failed_steps: list[str] = []
        for step in step_runs:
            outcome = None
            if isinstance(step, Mapping):
                result = step.get("result")
                if isinstance(result, Mapping):
                    outcome = result.get("outcome")
                if outcome == "FAILED":
                    name = (
                        step.get("stepName")
                        or step.get("stepId")
                        or step.get("name")
                        or step.get("runId")
                    )
                    if name is not None:
                        failed_steps.append(str(name))
            else:
                try:
                    outcome = step.outcome
                except Exception:
                    outcome = None
                if outcome == "FAILED":
                    name = DataikuDSSAdapter._read_attribute(step, "step_name")
                    if name is None:
                        name = DataikuDSSAdapter._read_attribute(step, "id")
                    if name is not None:
                        failed_steps.append(str(name))
        return failed_steps

    @staticmethod
    def _extract_run_error_details(details: Mapping[str, Any]) -> dict[str, Any]:
        error_details = details.get("first_error_details")
        if isinstance(error_details, Mapping):
            return dict(error_details)
        step_runs = details.get("stepRuns")
        if not isinstance(step_runs, Sequence) or isinstance(step_runs, (str, bytes)):
            return {}
        for step in step_runs:
            if isinstance(step, Mapping):
                result = step.get("result")
                if isinstance(result, Mapping) and isinstance(result.get("thrown"), Mapping):
                    return dict(result["thrown"])
                for item in step.get("additionalReportItems", []):
                    if (
                        isinstance(item, Mapping)
                        and item.get("outcome") == "FAILED"
                        and isinstance(item.get("thrown"), Mapping)
                    ):
                        return dict(item["thrown"])
            else:
                try:
                    first_error = step.first_error_details
                except Exception:
                    first_error = None
                if isinstance(first_error, Mapping):
                    return dict(first_error)
        return {}

    @staticmethod
    def _extract_failed_activities(status: Mapping[str, Any]) -> list[str]:
        failed: list[str] = []
        activities = status.get("activities") or status.get("steps")
        if isinstance(activities, Sequence) and not isinstance(activities, (str, bytes)):
            for activity in activities:
                if not isinstance(activity, Mapping):
                    continue
                outcome = activity.get("state") or activity.get("outcome") or activity.get("status")
                if str(outcome).upper() in {"FAILED", "ERROR"}:
                    name = activity.get("name") or activity.get("activity") or activity.get("id")
                    if name is not None:
                        failed.append(str(name))
        return failed

    @staticmethod
    def _extract_job_error_details(status: Mapping[str, Any]) -> dict[str, Any]:
        for key in ("error", "errorDetails", "thrown"):
            candidate = status.get(key)
            if isinstance(candidate, Mapping):
                return dict(candidate)
        return {}

    def _known_project_bindings(self, project_key: str) -> set[str]:
        dataset_names = {
            str(dataset.get("name"))
            for dataset in self.list_datasets(project_key)
            if dataset.get("name")
        }
        folder_ids = {
            str(folder.get("folder_id"))
            for folder in self.list_managed_folders(project_key)
            if folder.get("folder_id")
        }
        return dataset_names | folder_ids

    def _resolve_prediction_target_selection(
        self,
        project_key: str,
        dataset_name: str,
        *,
        target_variable: str,
        prediction_type: str | None,
    ) -> dict[str, Any]:
        dataset_column = self._get_dataset_column(project_key, dataset_name, target_variable)
        try:
            return resolve_prediction_type(dataset_column, prediction_type)
        except ValueError as exc:
            raise ConfigurationError(
                str(exc),
                suggested_fix=(
                    "Choose a different target column, or pass an explicit prediction_type "
                    "if you know this target should be treated differently."
                ),
            ) from exc

    def _resolve_ml_command_plan(
        self,
        project_key: str,
        dataset_name: str,
        command_name: str,
        *,
        target_variable: str | None,
        prepared_dataset_name: str | None,
        prepare_recipe_name: str | None,
        prediction_type: str | None,
        ml_backend_type: str | None,
        guess_policy: str | None,
    ) -> dict[str, Any]:
        try:
            command = get_ml_command_definition(command_name)
        except ValueError as exc:
            raise ConfigurationError(
                str(exc),
                suggested_fix=(
                    "Call list_ml_commands first, then use one of the returned "
                    "catalog command names or aliases."
                ),
            ) from exc

        auto_selected_target = False
        resolved_target_variable = target_variable
        if resolved_target_variable is None:
            suggestions = self.suggest_prediction_targets(project_key, dataset_name, limit=1)
            candidates = suggestions.get("candidates", [])
            if not candidates:
                raise ConfigurationError(
                    "No prediction target could be auto-selected for this dataset.",
                    suggested_fix=(
                        "Pass target_variable explicitly, or inspect the dataset "
                        "schema and choose a business outcome column manually."
                    ),
                )
            first_candidate = candidates[0]
            resolved_target_variable = str(first_candidate["target_variable"])
            auto_selected_target = True

        selection = self._resolve_prediction_target_selection(
            project_key,
            dataset_name,
            target_variable=resolved_target_variable,
            prediction_type=prediction_type,
        )
        try:
            algorithm_name = resolve_command_algorithm(
                command,
                str(selection["prediction_type"]),
            )
        except ValueError as exc:
            raise ConfigurationError(
                str(exc),
                suggested_fix=(
                    "Choose another catalog command, or select a target whose "
                    "prediction type is supported by this command."
                ),
            ) from exc

        resolved_ml_backend_type = ml_backend_type or command.default_ml_backend_type
        resolved_guess_policy = guess_policy or command.default_guess_policy
        blueprint = build_prediction_blueprint(
            command.name,
            dataset_name,
            resolved_target_variable,
            algorithm_name=algorithm_name,
            prepared_dataset_name=prepared_dataset_name,
            prepare_recipe_name=prepare_recipe_name,
        )
        existing_recipe_names = {
            str(recipe.get("name"))
            for recipe in self.list_recipes(project_key)
            if recipe.get("name")
        }
        existing_dataset_names = {
            str(dataset.get("name"))
            for dataset in self.list_datasets(project_key)
            if dataset.get("name")
        }
        return {
            "command": command.to_dict(),
            "analysis_label": blueprint["analysis_label"],
            "saved_model_name": blueprint["saved_model_name"],
            "source_dataset": dataset_name,
            "target_variable": resolved_target_variable,
            "auto_selected_target": auto_selected_target,
            "prediction_type": selection["prediction_type"],
            "dss_prediction_type": selection["dss_prediction_type"],
            "recommended_algorithm": blueprint["algorithm_name"],
            "prepared_dataset_name": blueprint["prepared_dataset_name"],
            "prepared_dataset_exists": (
                blueprint["prepared_dataset_name"] in existing_dataset_names
            ),
            "prepare_recipe_name": blueprint["prepare_recipe_name"],
            "prepare_recipe_exists": (
                blueprint["prepare_recipe_name"] in existing_recipe_names
            ),
            "target_reasoning": selection["reasoning"],
            "target_warnings": selection["warnings"],
            "ml_backend_type": resolved_ml_backend_type,
            "guess_policy": resolved_guess_policy,
            "summary": (
                f"Catalog command {command.name} will prepare {dataset_name}, "
                f"predict {resolved_target_variable}, and enable "
                f"{blueprint['algorithm_name']}."
            ),
        }

    def _get_dataset_column(
        self,
        project_key: str,
        dataset_name: str,
        column_name: str,
    ) -> dict[str, Any]:
        schema = self.get_dataset_schema(project_key, dataset_name)
        for column in cast(list[dict[str, Any]], schema.get("columns", [])):
            if str(column.get("name")) == column_name:
                return column
        raise ConfigurationError(
            f"Target column {column_name} was not found in dataset {dataset_name}.",
            suggested_fix="Choose a target variable that exists in the dataset schema.",
        )

    def _find_ml_task_summary(
        self,
        project_key: str,
        analysis_id: str,
        ml_task_id: str,
    ) -> dict[str, Any]:
        for task_summary in self.list_ml_tasks(project_key):
            if (
                task_summary.get("analysis_id") == analysis_id
                and task_summary.get("ml_task_id") == ml_task_id
            ):
                return task_summary
        raise DataikuObjectNotFoundError(
            f"ML task {analysis_id}/{ml_task_id} could not be found in project {project_key}.",
            details={
                "project_key": project_key,
                "analysis_id": analysis_id,
                "ml_task_id": ml_task_id,
            },
            suggested_fix="List ML tasks first and use a valid analysis_id / ml_task_id pair.",
        )

    def _find_saved_model_summary(
        self,
        project_key: str,
        saved_model_id: str,
    ) -> dict[str, Any]:
        for saved_model in self.list_saved_models(project_key):
            if saved_model.get("saved_model_id") == saved_model_id:
                return saved_model
        return {
            "saved_model_id": saved_model_id,
            "name": saved_model_id,
        }

    def _find_model_evaluation_store_summary(
        self,
        project_key: str,
        evaluation_store_id: str,
    ) -> dict[str, Any]:
        for store in self.list_model_evaluation_stores(project_key):
            if store.get("evaluation_store_id") == evaluation_store_id:
                return store
        return {
            "evaluation_store_id": evaluation_store_id,
            "name": evaluation_store_id,
        }

    def _validate_scoring_recipe_creation(
        self,
        project_key: str,
        *,
        recipe_name: str,
        output_dataset_name: str,
    ) -> None:
        existing_recipe_names = {
            str(recipe.get("name"))
            for recipe in self.list_recipes(project_key)
            if recipe.get("name")
        }
        if recipe_name in existing_recipe_names:
            raise ConfigurationError(
                f"Recipe {recipe_name} already exists.",
                suggested_fix="Provide a different recipe_name.",
            )
        existing_dataset_names = {
            str(dataset.get("name"))
            for dataset in self.list_datasets(project_key)
            if dataset.get("name")
        }
        if output_dataset_name in existing_dataset_names:
            raise ConfigurationError(
                f"Dataset {output_dataset_name} already exists.",
                suggested_fix="Provide a different output_dataset_name.",
            )

    def _validate_model_evaluation_creation(
        self,
        project_key: str,
        *,
        recipe_name: str,
        evaluation_store_id: str | None,
        evaluation_store_name: str | None,
        scored_output_dataset: str,
        metrics_output_dataset: str,
    ) -> None:
        existing_recipe_names = {
            str(recipe.get("name"))
            for recipe in self.list_recipes(project_key)
            if recipe.get("name")
        }
        if recipe_name in existing_recipe_names:
            raise ConfigurationError(
                f"Recipe {recipe_name} already exists.",
                suggested_fix="Provide a different recipe_name.",
            )
        existing_dataset_names = {
            str(dataset.get("name"))
            for dataset in self.list_datasets(project_key)
            if dataset.get("name")
        }
        for dataset_name, field_name in (
            (scored_output_dataset, "scored_output_dataset"),
            (metrics_output_dataset, "metrics_output_dataset"),
        ):
            if dataset_name in existing_dataset_names:
                raise ConfigurationError(
                    f"Dataset {dataset_name} already exists.",
                    suggested_fix=f"Provide a different {field_name}.",
                )
        if evaluation_store_id is None:
            existing_store_names = {
                str(store.get("name"))
                for store in self.list_model_evaluation_stores(project_key)
                if store.get("name")
            }
            if evaluation_store_name in existing_store_names:
                raise ConfigurationError(
                    f"Model evaluation store {evaluation_store_name} already exists.",
                    suggested_fix=(
                        "Pass evaluation_store_id or use a different "
                        "evaluation_store_name."
                    ),
                )

    def _resolve_model_evaluation_plan(
        self,
        project_key: str,
        saved_model_id: str,
        evaluation_dataset: str,
        *,
        evaluation_store_id: str | None,
        evaluation_store_name: str | None,
        recipe_name: str | None,
        scored_output_dataset: str | None,
        metrics_output_dataset: str | None,
        metrics: Sequence[str] | None,
        run_immediately: bool,
    ) -> dict[str, Any]:
        self.get_saved_model_details(project_key, saved_model_id)
        self._get_dataset(project_key, evaluation_dataset)
        resolved_recipe_name = recipe_name or f"evaluate_{saved_model_id}_{evaluation_dataset}"
        resolved_store_name = (
            evaluation_store_name or f"mes_{saved_model_id}_{evaluation_dataset}"
        )
        resolved_scored_output = (
            scored_output_dataset or f"{evaluation_dataset}_scored_{saved_model_id}"
        )
        resolved_metrics_output = (
            metrics_output_dataset or f"{evaluation_dataset}_metrics_{saved_model_id}"
        )
        return {
            "saved_model_id": saved_model_id,
            "evaluation_dataset": evaluation_dataset,
            "evaluation_store_id": evaluation_store_id,
            "evaluation_store_name": resolved_store_name,
            "recipe_name": resolved_recipe_name,
            "scored_output_dataset": resolved_scored_output,
            "metrics_output_dataset": resolved_metrics_output,
            "metrics": list(metrics or []),
            "run_immediately": run_immediately,
        }

    def _ensure_managed_dataset(
        self,
        project_key: str,
        dataset_name: str,
        connection_name: str,
    ) -> None:
        existing_dataset_names = {
            str(dataset.get("name"))
            for dataset in self.list_datasets(project_key)
            if dataset.get("name")
        }
        if dataset_name in existing_dataset_names:
            return
        project = self._get_project(project_key)
        builder = self._call_method(project, ("new_managed_dataset",), dataset_name)
        self._call_method(builder, ("with_store_into",), connection_name)
        self._call_method(builder, ("create",), default=None)

    def _resolve_routed_ml_intent(self, routed: dict[str, Any]) -> dict[str, Any]:
        missing_fields = list(cast(list[str], routed.get("missing_fields", [])))
        intent_type = cast(str, routed.get("intent_type"))
        project_key = cast(str | None, routed.get("project_key"))
        if intent_type in {"train_latest_ml_task", "deploy_best_model"} and project_key is not None:
            latest_task = self._select_latest_ml_task(project_key)
            routed["analysis_id"] = latest_task["analysis_id"]
            routed["ml_task_id"] = latest_task["ml_task_id"]
            if intent_type == "deploy_best_model":
                trained_models = self.list_trained_models(
                    project_key,
                    cast(str, latest_task["analysis_id"]),
                    cast(str, latest_task["ml_task_id"]),
                )
                selected_model = self._select_best_model(
                    cast(list[dict[str, Any]], trained_models.get("models", [])),
                    metric_name=cast(str | None, routed.get("metric_name")),
                )
                routed["model_id"] = selected_model.get("model_id")
                routed["saved_model_name"] = (
                    f"{latest_task['analysis_id']}_{latest_task['ml_task_id']}_saved_model"
                )
        routed["can_execute"] = len(missing_fields) == 0 and intent_type != "unknown"
        return routed

    def _select_latest_ml_task(self, project_key: str) -> dict[str, Any]:
        tasks = self.list_ml_tasks(project_key)
        if not tasks:
            raise ConfigurationError(
                f"No Visual ML task is available in project {project_key}.",
                suggested_fix=(
                    "Run a bootstrap ML command first, then retrain or deploy "
                    "from that task."
                ),
            )
        return tasks[-1]

    def _select_best_model(
        self,
        models: Sequence[Mapping[str, Any]],
        *,
        metric_name: str | None,
    ) -> Mapping[str, Any]:
        if not models:
            raise ConfigurationError(
                "No trained models are available for this ML task.",
                suggested_fix="Train the ML task before requesting a deployment.",
            )
        comparison_metric = metric_name or self._select_comparison_metric(list(models))
        ranked_models = sorted(
            models,
            key=lambda model: self._metric_sort_value(
                cast(dict[str, Any], model.get("metrics", {})),
                comparison_metric,
            ),
            reverse=self._metric_prefers_higher(comparison_metric),
        )
        return ranked_models[0]

    def _validate_prediction_flow_creation(
        self,
        project_key: str,
        *,
        prepare_recipe_name: str,
        prepared_dataset_name: str,
    ) -> None:
        existing_recipe_names = {
            str(recipe.get("name"))
            for recipe in self.list_recipes(project_key)
            if recipe.get("name")
        }
        if prepare_recipe_name in existing_recipe_names:
            raise ConfigurationError(
                f"Recipe {prepare_recipe_name} already exists.",
                suggested_fix="Provide a different prepare_recipe_name.",
            )

        existing_dataset_names = {
            str(dataset.get("name"))
            for dataset in self.list_datasets(project_key)
            if dataset.get("name")
        }
        if prepared_dataset_name in existing_dataset_names:
            raise ConfigurationError(
                f"Dataset {prepared_dataset_name} already exists.",
                suggested_fix="Provide a different prepared_dataset_name.",
            )

    def _resolve_visual_output_connection(
        self,
        project_key: str,
        source_dataset: str,
    ) -> str:
        source_connection: str | None = None
        for dataset in self.list_datasets(project_key):
            if dataset.get("name") != source_dataset:
                continue
            connection = dataset.get("connection")
            if isinstance(connection, str) and connection:
                source_connection = connection
            break

        raw_connections = self._call_method(self.client, ("list_connections",), default=[])
        available_names: list[str] = []
        if isinstance(raw_connections, Sequence) and not isinstance(
            raw_connections,
            (str, bytes),
        ):
            for raw_connection in raw_connections:
                normalized = self._normalize_mapping(raw_connection)
                name = normalized.get("name")
                if isinstance(name, str) and name and name not in available_names:
                    available_names.append(name)

        for preferred_name in (
            "dataiku-managed-storage",
            "filesystem_managed",
            "filesystem_folders",
        ):
            if preferred_name in available_names:
                return preferred_name
        if source_connection:
            return source_connection
        return available_names[0] if available_names else "dataiku-managed-storage"

    def _create_prepare_recipe(
        self,
        project_key: str,
        *,
        recipe_name: str,
        input_dataset: str,
        output_dataset: str,
    ) -> dict[str, Any]:
        project = self._get_project(project_key)
        creator = self._call_method(project, ("new_recipe",), "prepare", recipe_name)
        self._call_method(creator, ("with_input",), input_dataset)
        output_connection = self._resolve_visual_output_connection(
            project_key,
            input_dataset,
        )
        if hasattr(creator, "with_new_output"):
            self._call_method(
                creator,
                ("with_new_output",),
                output_dataset,
                output_connection,
            )
        else:
            self._call_method(creator, ("with_output",), output_dataset)
        recipe = self._call_method(creator, ("create", "build"))
        steps_count = 0
        settings = self._call_method(recipe, ("get_settings",), default=None)
        if settings is not None and hasattr(settings, "save"):
            raw_steps = getattr(settings, "raw_steps", None)
            if isinstance(raw_steps, list):
                steps_count = len(raw_steps)
            try:
                settings.save()
            except Exception as exc:
                raise map_exception(exc) from exc
        build_job = self._call_method(
            recipe,
            ("run",),
            default=None,
            wait=True,
            no_fail=False,
        )
        build_job_id = self._read_attribute(build_job, "id") if build_job is not None else None
        return {
            "recipe_name": recipe_name,
            "recipe_type": "prepare",
            "input_dataset": input_dataset,
            "output_dataset": output_dataset,
            "output_connection": output_connection,
            "steps_count": steps_count,
            "materialized_output": build_job is not None,
            "build_job_id": build_job_id,
            "created": True,
        }

    def _create_prediction_ml_task(
        self,
        project_key: str,
        *,
        input_dataset: str,
        target_variable: str,
        dss_prediction_type: str,
        algorithm_name: str,
        ml_backend_type: str,
        guess_policy: str,
    ) -> dict[str, Any]:
        project = self._get_project(project_key)
        task = self._call_method(
            project,
            ("create_prediction_ml_task",),
            input_dataset,
            target_variable,
            ml_backend_type,
            guess_policy,
            dss_prediction_type,
            True,
        )
        settings = self._call_method(task, ("get_settings",), default=None)
        if settings is None:
            raise UnsupportedOperationError(
                "The created ML task does not expose settings through the current API.",
                suggested_fix=(
                    "Open the task in DSS manually, or upgrade the Dataiku client if "
                    "your version does not expose ML task settings."
                ),
            )
        if not hasattr(settings, "disable_all_algorithms") or not hasattr(
            settings, "set_algorithm_enabled"
        ):
            raise UnsupportedOperationError(
                "The ML task settings do not support algorithm selection.",
                suggested_fix="Use a Dataiku client version that exposes ML algorithm settings.",
            )

        all_algorithm_names: list[str] = []
        if hasattr(settings, "get_all_possible_algorithm_names"):
            try:
                raw_algorithm_names = settings.get_all_possible_algorithm_names()
            except Exception as exc:
                raise map_exception(exc) from exc
            if isinstance(raw_algorithm_names, Sequence) and not isinstance(
                raw_algorithm_names,
                (str, bytes),
            ):
                all_algorithm_names = [str(name) for name in raw_algorithm_names]
        if all_algorithm_names and algorithm_name not in all_algorithm_names:
            raise UnsupportedOperationError(
                f"The ML task does not expose the algorithm {algorithm_name}.",
                suggested_fix=(
                    "Check that XGBoost is available in the DSS instance and supported by "
                    "the selected ML backend."
                ),
            )

        try:
            settings.disable_all_algorithms()
            settings.set_algorithm_enabled(algorithm_name, True)
            settings.save()
        except Exception as exc:
            raise map_exception(exc) from exc

        analysis_id = self._read_attribute(task, "analysis_id")
        if analysis_id is None:
            analysis_id = self._read_attribute(task, "analysisId")
        ml_task_id = self._read_attribute(task, "mltask_id")
        if ml_task_id is None:
            ml_task_id = self._read_attribute(task, "mlTaskId")

        return {
            "created": True,
            "input_dataset": input_dataset,
            "target_variable": target_variable,
            "prediction_type": dss_prediction_type,
            "algorithm_enabled": algorithm_name,
            "ml_backend_type": ml_backend_type,
            "guess_policy": guess_policy,
            "analysis_id": analysis_id,
            "ml_task_id": ml_task_id,
        }

    def _extract_ml_task_settings(self, raw_settings: Any) -> dict[str, Any]:
        if isinstance(raw_settings, Mapping):
            return dict(raw_settings)
        get_raw = getattr(raw_settings, "get_raw", None)
        if callable(get_raw):
            try:
                settings = get_raw()
            except Exception as exc:
                raise map_exception(exc) from exc
            if isinstance(settings, Mapping):
                return dict(settings)
        mltask_settings = getattr(raw_settings, "mltask_settings", None)
        if isinstance(mltask_settings, Mapping):
            return dict(mltask_settings)
        return self._normalize_api_mapping(raw_settings)

    def _validate_python_recipe_creation(
        self,
        project_key: str,
        recipe_name: str,
        *,
        inputs: list[str],
        outputs: list[str],
    ) -> None:
        if not recipe_name.strip():
            raise ConfigurationError(
                "Recipe name cannot be empty.",
                suggested_fix="Provide a non-empty recipe_name.",
            )
        existing_recipe_names = {
            str(recipe.get("name"))
            for recipe in self.list_recipes(project_key)
            if recipe.get("name")
        }
        if recipe_name in existing_recipe_names:
            raise ConfigurationError(
                f"Recipe {recipe_name} already exists.",
                suggested_fix="Choose a new recipe name or delete the existing recipe first.",
            )
        known_bindings = self._known_project_bindings(project_key)
        missing_inputs = [item for item in inputs if item not in known_bindings]
        missing_outputs = [item for item in outputs if item not in known_bindings]
        if missing_inputs or missing_outputs:
            raise ConfigurationError(
                "Recipe inputs or outputs reference unknown project objects.",
                details={
                    "missing_inputs": missing_inputs,
                    "missing_outputs": missing_outputs,
                },
                suggested_fix=(
                    "Create the missing datasets or Managed Folders first, or "
                    "adjust the recipe bindings."
                ),
            )

    def _validate_scenario_creation(
        self,
        project_key: str,
        scenario_name: str,
        *,
        scenario_type: str,
        build_datasets: list[str],
    ) -> None:
        if not scenario_name.strip():
            raise ConfigurationError(
                "Scenario name cannot be empty.",
                suggested_fix="Provide a non-empty scenario_name.",
            )
        existing_ids, existing_names = self._existing_scenario_identifiers(project_key)
        if scenario_name in existing_ids or scenario_name in existing_names:
            raise ConfigurationError(
                f"Scenario {scenario_name} already exists.",
                suggested_fix="Choose a new scenario name or delete the existing scenario first.",
            )
        missing_datasets = self._find_unknown_datasets(project_key, build_datasets)
        if missing_datasets:
            raise ConfigurationError(
                "Scenario build targets reference unknown datasets.",
                details={"missing_build_datasets": missing_datasets},
                suggested_fix=(
                    "Create the missing datasets first, or adjust the scenario build targets."
                ),
            )
        if scenario_type == "step_based" and not build_datasets:
            raise ConfigurationError(
                "A step-based scenario requires at least one dataset to build.",
                suggested_fix="Provide one or more build_datasets for the step-based scenario.",
            )

    def _existing_scenario_identifiers(self, project_key: str) -> tuple[set[str], set[str]]:
        existing_ids: set[str] = set()
        existing_names: set[str] = set()
        for scenario in self.list_scenarios(project_key):
            scenario_id = scenario.get("scenario_id")
            if isinstance(scenario_id, str) and scenario_id:
                existing_ids.add(scenario_id)
            scenario_name = scenario.get("name")
            if isinstance(scenario_name, str) and scenario_name:
                existing_names.add(scenario_name)
        return existing_ids, existing_names

    def _find_unknown_datasets(
        self,
        project_key: str,
        dataset_names: list[str],
    ) -> list[str]:
        known_datasets = {
            dataset["name"]
            for dataset in self.list_datasets(project_key)
            if dataset.get("name")
        }
        return [
            dataset_name
            for dataset_name in dataset_names
            if dataset_name not in known_datasets
        ]

    @staticmethod
    def _normalize_scenario_type(scenario_type: str) -> str:
        normalized_type = scenario_type.strip().lower()
        if normalized_type not in {"custom_python", "step_based"}:
            raise ConfigurationError(
                f"Unsupported scenario_type: {scenario_type}.",
                suggested_fix="Use scenario_type=custom_python or scenario_type=step_based.",
            )
        return normalized_type

    def _resolve_scenario_code(
        self,
        *,
        scenario_type: str,
        code: str | None,
        build_datasets: list[str],
    ) -> str | None:
        if scenario_type == "step_based":
            if code is not None:
                raise ConfigurationError(
                    "Step-based scenario creation does not accept inline Python code.",
                    suggested_fix=(
                        "Remove the code payload or switch scenario_type to custom_python."
                    ),
                )
            return None
        if code is not None:
            return code
        if build_datasets:
            return self._generate_custom_python_scenario_code(build_datasets)
        raise ConfigurationError(
            "A custom Python scenario requires code or build_datasets.",
            suggested_fix=(
                "Provide a Python code payload, or pass build_datasets to generate "
                "the scenario body automatically."
            ),
        )

    @staticmethod
    def _generate_custom_python_scenario_code(build_datasets: list[str]) -> str:
        lines = [
            "from dataiku.scenario import Scenario",
            "",
            "scenario = Scenario()",
        ]
        for dataset_name in build_datasets:
            lines.append(
                f'scenario.build_dataset("{dataset_name}", build_mode="NON_RECURSIVE_FORCED_BUILD")'
            )
        return "\n".join(lines)

    @staticmethod
    def _build_step_based_scenario_steps(
        project_key: str,
        build_datasets: list[str],
    ) -> list[dict[str, Any]]:
        steps: list[dict[str, Any]] = []
        for index, dataset_name in enumerate(build_datasets, start=1):
            steps.append(
                {
                    "id": f"build_{index}_true_d_{project_key}.{dataset_name}",
                    "type": "build_flowitem",
                    "name": f"build dataset {dataset_name}",
                    "enabled": True,
                    "alwaysShowComment": False,
                    "runConditionType": "RUN_IF_STATUS_MATCH",
                    "runConditionStatuses": ["SUCCESS", "WARNING"],
                    "resetScenarioStatus": False,
                    "delayBetweenRetries": 10,
                    "maxRetriesOnFail": 0,
                    "params": {
                        "builds": [
                            {
                                "type": "DATASET",
                                "projectKey": project_key,
                                "itemId": dataset_name,
                            }
                        ],
                        "jobType": "NON_RECURSIVE_FORCED_BUILD",
                        "autoUpdateSchemaBeforeEachRecipeRun": False,
                        "stopAtFlowZoneBoundary": False,
                        "refreshHiveMetastore": True,
                        "handleWarningsAs": "WARNING",
                        "proceedOnFailure": False,
                    },
                }
            )
        return steps

    @staticmethod
    def _decode_base64_content(content_base64: str) -> bytes:
        try:
            return base64.b64decode(content_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ConfigurationError(
                "Invalid base64 content for file upload.",
                suggested_fix="Provide a valid base64-encoded payload.",
            ) from exc

    @staticmethod
    def _action_summary(
        *,
        operation: str,
        project_key: str,
        object_type: str,
        object_name: str,
        risk_level: str,
        rollback_possible: bool,
        exact_operation: str,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "operation": operation,
            "project_key": project_key,
            "target": {
                "object_type": object_type,
                "object_name": object_name,
            },
            "risk_level": risk_level,
            "rollback_possible": rollback_possible,
            "exact_operation": exact_operation,
            "changes": changes,
        }

    def _resolve_documentation_target(
        self,
        project_key: str,
        target: str,
    ) -> dict[str, Any]:
        project = self._get_project(project_key)
        if target.startswith("wiki:"):
            article_name = target.split(":", 1)[1].strip()
            if not article_name:
                raise ConfigurationError(
                    "Wiki documentation target cannot be empty.",
                    suggested_fix="Use a target like wiki:Architecture Overview.",
                )
            wiki = self._call_method(project, ("get_wiki",))
            article = None
            try:
                article = self._call_method(wiki, ("get_article",), article_name)
                exists = True
            except DataikuObjectNotFoundError:
                exists = False
            return {
                "target_type": "wiki_article",
                "target_name": article_name,
                "article_name": article_name,
                "exists": exists,
                "handle": article,
                "container": wiki,
            }

        path = target.split(":", 1)[1] if target.startswith("library:") else target
        normalized_path = path.strip().lstrip("/")
        if not normalized_path:
            raise ConfigurationError(
                "Project library target cannot be empty.",
                suggested_fix="Use a target like library:docs/README.md.",
            )
        library = self._call_method(project, ("get_library",))
        file_handle = self._call_method(library, ("get_file",), normalized_path, default=None)
        return {
            "target_type": "project_library",
            "target_name": normalized_path,
            "path": normalized_path,
            "exists": file_handle is not None,
            "handle": file_handle,
            "container": library,
        }

    @staticmethod
    def _truncate_logs(log_text: str, *, max_lines: int) -> tuple[str, bool]:
        lines = log_text.splitlines()
        if len(lines) <= max_lines:
            return log_text, False
        truncated_lines = lines[:max_lines]
        truncated_lines.append(
            f"... [truncated after {max_lines} line(s) out of {len(lines)} total]"
        )
        return "\n".join(truncated_lines), True

    @staticmethod
    def _count_lines(log_text: str) -> int:
        return len(log_text.splitlines())

    def _attempt_optional_collection(
        self,
        label: str,
        collector: Any,
    ) -> tuple[Any, str | None]:
        try:
            return collector(), None
        except Exception as exc:
            normalized = map_exception(exc)
            return None, f"{label}: {normalized.error_type}: {normalized.message}"

    @staticmethod
    def _read_attribute(target: Any, attribute: str, *, default: Any = None) -> Any:
        try:
            return object.__getattribute__(target, attribute)
        except Exception:
            return default

    @classmethod
    def _normalize_api_mapping(cls, raw_value: Any) -> dict[str, Any]:
        normalized = cls._normalize_mapping(raw_value)
        nested_data = normalized.get("data")
        if isinstance(nested_data, Mapping):
            flattened = dict(nested_data)
            for key, value in normalized.items():
                if key != "data":
                    flattened[key] = value
            return flattened
        return normalized

    @staticmethod
    def _normalize_project(raw_project: Any) -> dict[str, Any]:
        normalized = DataikuDSSAdapter._normalize_mapping(raw_project)
        project_key = (
            normalized.get("projectKey")
            or normalized.get("project_key")
            or normalized.get("id")
        )
        name = normalized.get("name") or project_key
        owner = normalized.get("owner") or normalized.get("ownerLogin")
        status = normalized.get("status") or normalized.get("projectStatus")
        archived = normalized.get("archived")
        if archived is None and isinstance(status, str):
            archived = status.lower() == "archived"
        tags = normalized.get("tags") or []
        return {
            "project_key": project_key,
            "name": name,
            "owner": owner,
            "status": status,
            "archived": bool(archived),
            "tags": list(tags) if isinstance(tags, Sequence) and not isinstance(tags, str) else [],
        }

    @staticmethod
    def _normalize_tags(raw_tags: Any) -> list[str]:
        if isinstance(raw_tags, Sequence) and not isinstance(raw_tags, str):
            return [str(tag) for tag in raw_tags]
        return []

    @staticmethod
    def _extract_connection(payload: Mapping[str, Any]) -> str | None:
        nested_params = payload.get("params")
        if isinstance(nested_params, Mapping):
            candidate = nested_params.get("connection") or nested_params.get("connectionName")
            if candidate is not None:
                return str(candidate)
        candidate = payload.get("connection") or payload.get("connectionName")
        return str(candidate) if candidate is not None else None

    @staticmethod
    def _normalize_ml_task_summary(raw_task: Any) -> dict[str, Any]:
        normalized = DataikuDSSAdapter._normalize_mapping(raw_task)
        return {
            "analysis_id": normalized.get("analysisId") or normalized.get("analysis_id"),
            "ml_task_id": (
                normalized.get("mlTaskId")
                or normalized.get("mltaskId")
                or normalized.get("ml_task_id")
            ),
            "analysis_name": normalized.get("analysisName") or normalized.get("analysisLabel"),
            "task_name": normalized.get("mlTaskName") or normalized.get("taskName"),
            "task_type": normalized.get("taskType"),
            "input_dataset": normalized.get("inputDataset") or normalized.get("input_dataset"),
            "prediction_type": (
                normalized.get("predictionType") or normalized.get("prediction_type")
            ),
        }

    @staticmethod
    def _extract_enabled_algorithms(settings: Mapping[str, Any]) -> list[str]:
        modeling = settings.get("modeling")
        if not isinstance(modeling, Mapping):
            return []
        enabled_algorithms: list[str] = []
        algorithm_name_map = {
            "xgboost": "XGBOOST",
            "lightgbm": "LIGHTGBM",
            "random_forest": "RANDOM_FOREST",
            "logistic_regression": "LOGISTIC_REGRESSION",
        }
        for algorithm_key, algorithm_settings in modeling.items():
            if not isinstance(algorithm_settings, Mapping):
                continue
            if algorithm_settings.get("enabled") is True:
                enabled_algorithms.append(
                    algorithm_name_map.get(str(algorithm_key), str(algorithm_key).upper())
                )
        return enabled_algorithms

    @staticmethod
    def _extract_trained_model_ids(status: Mapping[str, Any]) -> list[str]:
        raw_full_model_ids = status.get("fullModelIds")
        if not isinstance(raw_full_model_ids, Sequence) or isinstance(
            raw_full_model_ids,
            (str, bytes),
        ):
            return []
        model_ids: list[str] = []
        for raw_model in raw_full_model_ids:
            if not isinstance(raw_model, Mapping):
                continue
            model_id = raw_model.get("id")
            if model_id is not None:
                model_ids.append(str(model_id))
        return model_ids

    @staticmethod
    def _select_default_model_id(
        models: Sequence[Mapping[str, Any]],
        *,
        requested_model_id: str | None,
    ) -> str:
        if requested_model_id:
            return requested_model_id
        if not models:
            raise ConfigurationError(
                "No trained models are available for this ML task.",
                suggested_fix="Train the ML task first or provide a valid model_id.",
            )
        selected_model_id = models[-1].get("model_id")
        if not isinstance(selected_model_id, str) or not selected_model_id:
            raise ConfigurationError(
                "Could not resolve a deployable trained model identifier.",
                suggested_fix="Provide model_id explicitly.",
            )
        return selected_model_id

    @staticmethod
    def _normalize_saved_model_summary(raw_saved_model: Any) -> dict[str, Any]:
        normalized = DataikuDSSAdapter._normalize_mapping(raw_saved_model)
        return {
            "saved_model_id": (
                normalized.get("id")
                or normalized.get("savedModelId")
                or normalized.get("saved_model_id")
            ),
            "name": normalized.get("name") or normalized.get("label"),
            "prediction_type": (
                normalized.get("predictionType") or normalized.get("prediction_type")
            ),
            "active_version_id": (
                normalized.get("activeVersionId") or normalized.get("active_version_id")
            ),
        }

    @staticmethod
    def _normalize_saved_model_version(raw_version: Any) -> dict[str, Any]:
        normalized = DataikuDSSAdapter._normalize_mapping(raw_version)
        return {
            "version_id": (
                normalized.get("id")
                or normalized.get("versionId")
                or normalized.get("version_id")
            ),
            "label": normalized.get("label") or normalized.get("name"),
            "active": normalized.get("active"),
            "created_on": normalized.get("createdOn") or normalized.get("created_on"),
        }

    @staticmethod
    def _normalize_model_evaluation_store_summary(raw_store: Any) -> dict[str, Any]:
        normalized = DataikuDSSAdapter._normalize_mapping(raw_store)
        settings = {}
        get_settings = getattr(raw_store, "get_settings", None)
        if callable(get_settings):
            try:
                settings = DataikuDSSAdapter._normalize_settings_payload(get_settings())
            except DataikuCodexError:
                settings = {}
        return {
            "evaluation_store_id": (
                normalized.get("id")
                or normalized.get("mesId")
                or normalized.get("evaluationStoreId")
                or normalized.get("evaluation_store_id")
                or DataikuDSSAdapter._read_attribute(raw_store, "evaluation_store_id")
                or DataikuDSSAdapter._read_attribute(raw_store, "mes_id")
                or DataikuDSSAdapter._read_attribute(raw_store, "id")
            ),
            "name": (
                normalized.get("name")
                or normalized.get("label")
                or settings.get("name")
                or settings.get("label")
            ),
            "object_type": normalized.get("objectType") or "MODEL_EVALUATION_STORE",
        }

    @staticmethod
    def _normalize_model_evaluation_summary(raw_evaluation: Any) -> dict[str, Any]:
        normalized = DataikuDSSAdapter._normalize_mapping(raw_evaluation)
        return {
            "evaluation_id": DataikuDSSAdapter._extract_evaluation_id(raw_evaluation),
            "label": normalized.get("label") or normalized.get("name"),
            "created_on": normalized.get("createdOn") or normalized.get("created_on"),
        }

    @staticmethod
    def _normalize_settings_payload(raw_settings: Any) -> dict[str, Any]:
        if isinstance(raw_settings, Mapping):
            return dict(raw_settings)
        get_raw = getattr(raw_settings, "get_raw", None)
        if callable(get_raw):
            try:
                payload = get_raw()
            except Exception as exc:
                raise map_exception(exc) from exc
            if isinstance(payload, Mapping):
                return dict(payload)
        obj_payload = getattr(raw_settings, "obj_payload", None)
        if isinstance(obj_payload, Mapping):
            return dict(obj_payload)
        return DataikuDSSAdapter._normalize_mapping(raw_settings)

    @staticmethod
    def _normalize_evaluation_full_info(raw_full_info: Any) -> dict[str, Any]:
        if isinstance(raw_full_info, Mapping):
            return dict(raw_full_info)
        get_raw = getattr(raw_full_info, "get_raw", None)
        if callable(get_raw):
            try:
                payload = get_raw()
            except Exception as exc:
                raise map_exception(exc) from exc
            if isinstance(payload, Mapping):
                return dict(payload)
        return DataikuDSSAdapter._normalize_mapping(raw_full_info)

    @staticmethod
    def _extract_saved_model_version_id(raw_version: Any) -> str | None:
        if raw_version is None:
            return None
        if isinstance(raw_version, str):
            return raw_version
        normalized = DataikuDSSAdapter._normalize_mapping(raw_version)
        version_id = normalized.get("id") or normalized.get("versionId")
        if version_id is not None:
            return str(version_id)
        candidate = DataikuDSSAdapter._read_attribute(raw_version, "id")
        return str(candidate) if candidate is not None else None

    @staticmethod
    def _extract_evaluation_id(raw_evaluation: Any) -> str | None:
        get_full_id = getattr(raw_evaluation, "get_full_id", None)
        if callable(get_full_id):
            try:
                full_id = get_full_id()
            except Exception as exc:
                raise map_exception(exc) from exc
            if full_id is not None:
                return str(full_id)
        normalized = DataikuDSSAdapter._normalize_mapping(raw_evaluation)
        evaluation_id = (
            normalized.get("id")
            or normalized.get("evaluationId")
            or normalized.get("fullId")
            or normalized.get("evaluation_id")
        )
        if evaluation_id is not None:
            return str(evaluation_id)
        candidate = (
            DataikuDSSAdapter._read_attribute(raw_evaluation, "id")
            or DataikuDSSAdapter._read_attribute(raw_evaluation, "evaluation_id")
            or DataikuDSSAdapter._read_attribute(raw_evaluation, "full_id")
        )
        return str(candidate) if candidate is not None else None

    @staticmethod
    def _normalize_metric_values(raw_metrics: Any) -> dict[str, Any]:
        get_raw = getattr(raw_metrics, "get_raw", None)
        if callable(get_raw):
            try:
                raw_metrics = get_raw()
            except Exception as exc:
                raise map_exception(exc) from exc
        if isinstance(raw_metrics, Mapping):
            if "metrics" in raw_metrics and isinstance(raw_metrics.get("metrics"), Mapping):
                return {
                    str(metric_name): metric_value
                    for metric_name, metric_value in cast(
                        Mapping[Any, Any],
                        raw_metrics.get("metrics"),
                    ).items()
                }
            if "metrics" in raw_metrics and isinstance(raw_metrics.get("metrics"), Sequence):
                mapped_metrics: dict[str, Any] = {}
                for item in cast(Sequence[Any], raw_metrics.get("metrics")):
                    metric_entry = DataikuDSSAdapter._normalize_metric_entry(item)
                    if metric_entry is None:
                        continue
                    metric_name, metric_value = metric_entry
                    mapped_metrics[metric_name] = metric_value
                return mapped_metrics
            return {
                str(metric_name): metric_value
                for metric_name, metric_value in raw_metrics.items()
                if isinstance(metric_name, str)
            }
        if isinstance(raw_metrics, Sequence) and not isinstance(raw_metrics, (str, bytes)):
            normalized_metrics: dict[str, Any] = {}
            for item in raw_metrics:
                metric_entry = DataikuDSSAdapter._normalize_metric_entry(item)
                if metric_entry is None:
                    continue
                metric_name, metric_value = metric_entry
                normalized_metrics[metric_name] = metric_value
            return normalized_metrics
        return {}

    @staticmethod
    def _normalize_metric_entry(raw_metric: Any) -> tuple[str, Any] | None:
        if not isinstance(raw_metric, Mapping):
            return None
        metric_name: str | None = None
        metric_descriptor = raw_metric.get("metric")
        if isinstance(metric_descriptor, str) and metric_descriptor:
            metric_name = metric_descriptor
        elif isinstance(metric_descriptor, Mapping):
            for key in ("metricType", "name", "id"):
                candidate = metric_descriptor.get(key)
                if isinstance(candidate, str) and candidate:
                    metric_name = candidate
                    break
        if metric_name is None:
            meta = raw_metric.get("meta")
            if isinstance(meta, Mapping):
                candidate = meta.get("name")
                if isinstance(candidate, str) and candidate:
                    metric_name = candidate
        if metric_name is None:
            candidate = raw_metric.get("name")
            if isinstance(candidate, str) and candidate:
                metric_name = candidate
        if metric_name is None:
            return None

        metric_value = raw_metric.get("value")
        if metric_value is None:
            last_values = raw_metric.get("lastValues")
            if isinstance(last_values, Sequence) and not isinstance(last_values, (str, bytes)):
                metric_value = next(
                    (
                        item.get("value")
                        for item in last_values
                        if isinstance(item, Mapping) and item.get("value") is not None
                    ),
                    None,
                )
        return metric_name, DataikuDSSAdapter._coerce_metric_value(metric_value)

    @staticmethod
    def _coerce_metric_value(raw_value: Any) -> Any:
        if not isinstance(raw_value, str):
            return raw_value
        lowered = raw_value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        try:
            if "." not in raw_value and "e" not in lowered:
                return int(raw_value)
            return float(raw_value)
        except ValueError:
            return raw_value

    @staticmethod
    def _select_primary_metric(metrics: Mapping[str, Any]) -> dict[str, Any] | None:
        if not metrics:
            return None
        preferred_metrics = (
            "accuracy",
            "auc",
            "f1",
            "precision",
            "recall",
            "rmse",
            "mae",
        )
        for metric_name in preferred_metrics:
            if metric_name in metrics:
                return {"metric_name": metric_name, "metric_value": metrics[metric_name]}
        first_metric_name = next(iter(metrics))
        return {
            "metric_name": first_metric_name,
            "metric_value": metrics[first_metric_name],
        }

    @staticmethod
    def _select_comparison_metric(models: Sequence[Mapping[str, Any]]) -> str:
        for preferred_metric in ("accuracy", "auc", "f1", "precision", "recall", "rmse", "mae"):
            for model in models:
                metrics = model.get("active_version_metrics") or model.get("metrics") or {}
                if isinstance(metrics, Mapping) and preferred_metric in metrics:
                    return preferred_metric
        return "accuracy"

    @staticmethod
    def _metric_prefers_higher(metric_name: str) -> bool:
        lowered = metric_name.lower()
        return lowered not in {"rmse", "mae", "loss", "mse", "logloss"}

    @staticmethod
    def _metric_sort_value(metrics: Mapping[str, Any], metric_name: str) -> float:
        metric_value = metrics.get(metric_name)
        if isinstance(metric_value, bool):
            return float(metric_value)
        if isinstance(metric_value, (int, float)):
            return float(metric_value)
        if DataikuDSSAdapter._metric_prefers_higher(metric_name):
            return float("-inf")
        return float("inf")

    @staticmethod
    def _extract_schema_columns_count(payload: Mapping[str, Any]) -> int:
        direct_count = payload.get("schemaColumnsCount") or payload.get("schema_columns_count")
        if isinstance(direct_count, int):
            return direct_count
        return len(DataikuDSSAdapter._normalize_columns(payload))

    @staticmethod
    def _normalize_columns(raw_schema: Any) -> list[dict[str, Any]]:
        if isinstance(raw_schema, Mapping):
            raw_columns = raw_schema.get("columns")
        elif isinstance(raw_schema, Sequence) and not isinstance(raw_schema, (str, bytes)):
            raw_columns = raw_schema
        else:
            raw_columns = None

        if not isinstance(raw_columns, Sequence) or isinstance(raw_columns, (str, bytes)):
            return []

        columns: list[dict[str, Any]] = []
        for raw_column in raw_columns:
            if not isinstance(raw_column, Mapping):
                continue
            columns.append(
                {
                    "name": raw_column.get("name") or raw_column.get("column"),
                    "type": raw_column.get("type") or "string",
                    "meaning": raw_column.get("meaning"),
                    "nullable": raw_column.get("nullable"),
                }
            )
        return columns

    @classmethod
    def _normalize_bindings(cls, raw_bindings: Any) -> list[str]:
        items: list[str] = []

        def _walk(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, str):
                items.append(value)
                return
            if isinstance(value, Mapping):
                for key in ("ref", "name", "dataset", "id"):
                    candidate = value.get(key)
                    if isinstance(candidate, str):
                        items.append(candidate)
                        return
                nested_items = value.get("items")
                if nested_items is not None:
                    _walk(nested_items)
                    return
                for nested_value in value.values():
                    if isinstance(nested_value, (Mapping, list, tuple)):
                        _walk(nested_value)
                return
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                for nested_value in value:
                    _walk(nested_value)

        _walk(raw_bindings)
        deduplicated: list[str] = []
        for item in items:
            if item not in deduplicated:
                deduplicated.append(item)
        return deduplicated

    @staticmethod
    def _extract_nested_value(payload: Mapping[str, Any], path: Sequence[str]) -> Any:
        current: Any = payload
        for key in path:
            if not isinstance(current, Mapping) or key not in current:
                return None
            current = current[key]
        return current

    @staticmethod
    def _normalize_file_entry(raw_entry: Any) -> dict[str, Any]:
        if isinstance(raw_entry, str):
            return {"path": raw_entry, "size": None, "last_modified": None}
        normalized = DataikuDSSAdapter._normalize_mapping(raw_entry)
        return {
            "path": (
                normalized.get("path")
                or normalized.get("fullPath")
                or normalized.get("filePath")
                or normalized.get("name")
            ),
            "size": normalized.get("size") or normalized.get("fileSize"),
            "last_modified": (
                normalized.get("lastModified")
                or normalized.get("last_modified")
                or normalized.get("updatedAt")
            ),
        }

    @staticmethod
    def _normalize_mapping(raw_value: Any) -> dict[str, Any]:
        if isinstance(raw_value, Mapping):
            return dict(raw_value)
        get_raw = getattr(raw_value, "get_raw", None)
        if callable(get_raw):
            try:
                converted = get_raw()
            except Exception as exc:
                raise map_exception(exc) from exc
            if isinstance(converted, Mapping):
                return dict(converted)
        obj_payload = getattr(raw_value, "obj_payload", None)
        if isinstance(obj_payload, Mapping):
            return dict(obj_payload)
        if hasattr(raw_value, "to_dict"):
            converted = raw_value.to_dict()
            if isinstance(converted, Mapping):
                return dict(converted)
        if hasattr(raw_value, "__dict__"):
            return {
                key: value
                for key, value in vars(raw_value).items()
                if not key.startswith("_")
            }
        return {}
