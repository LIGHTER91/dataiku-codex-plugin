"""CLI and MCP bootstrap for the Dataiku DSS Copilot server."""

from __future__ import annotations

import argparse
import base64
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dataiku_codex_mcp.audit import AuditLogger
from dataiku_codex_mcp.client import DataikuDSSAdapter
from dataiku_codex_mcp.config import AppSettings, load_settings
from dataiku_codex_mcp.errors import ConfigurationError, normalize_exception
from dataiku_codex_mcp.identity import IdentityResolver
from dataiku_codex_mcp.logging_utils import get_logger
from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionGuard
from dataiku_codex_mcp.policy import PolicyEngine
from dataiku_codex_mcp.redaction import Redactor
from dataiku_codex_mcp.remote_auth import build_auth_provider
from dataiku_codex_mcp.tools import (
    ai_engineering,
    code_envs,
    datasets,
    documentation,
    flow,
    instance,
    managed_folders,
    ml,
    ops,
    projects,
    rag,
    recipes,
    scenarios,
)

ToolHandler = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class RegisteredTool:
    """Simple internal tool record."""

    name: str
    handler: ToolHandler
    description: str


class ToolRegistry:
    """Local registry that can be adapted to CLI or MCP transports."""

    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, name: str, handler: ToolHandler, *, description: str) -> None:
        self._tools[name] = RegisteredTool(
            name=name,
            handler=handler,
            description=description,
        )

    def names(self) -> list[str]:
        return sorted(self._tools)

    def items(self) -> list[RegisteredTool]:
        return [self._tools[name] for name in self.names()]

    def get(self, name: str) -> RegisteredTool:
        return self._tools[name]


@dataclass(frozen=True)
class AppContext:
    """Shared application services passed to tools."""

    settings: AppSettings
    dataiku: DataikuDSSAdapter
    identity: IdentityResolver
    policy: PolicyEngine
    permissions: PermissionGuard
    redactor: Redactor
    audit: AuditLogger


def build_app_context(
    *,
    settings: AppSettings | None = None,
    dataiku: DataikuDSSAdapter | None = None,
) -> AppContext:
    """Construct the shared application context."""

    resolved_settings = settings or load_settings()
    logger = get_logger(debug=resolved_settings.debug)
    redactor = Redactor(enabled=resolved_settings.redact_secrets)
    adapter = dataiku or DataikuDSSAdapter(resolved_settings)
    identity = IdentityResolver(resolved_settings)
    policy = PolicyEngine(resolved_settings)
    permissions = PermissionGuard(
        resolved_settings,
        identity_resolver=identity,
        policy_engine=policy,
    )
    audit = AuditLogger(
        logger,
        identity_resolver=identity,
        policy_engine=policy,
        audit_log_path=resolved_settings.audit_log_path,
    )
    return AppContext(
        settings=resolved_settings,
        dataiku=adapter,
        identity=identity,
        policy=policy,
        permissions=permissions,
        redactor=redactor,
        audit=audit,
    )


def build_tool_registry(ctx: AppContext) -> ToolRegistry:
    """Build the local tool registry used by both CLI and MCP adapters."""

    registry = ToolRegistry()
    instance.register_tools(registry, ctx)
    projects.register_tools(registry, ctx)
    datasets.register_tools(registry, ctx)
    ml.register_tools(registry, ctx)
    recipes.register_tools(registry, ctx)
    managed_folders.register_tools(registry, ctx)
    flow.register_tools(registry, ctx)
    scenarios.register_tools(registry, ctx)
    code_envs.register_tools(registry, ctx)
    rag.register_tools(registry, ctx)
    ai_engineering.register_tools(registry, ctx)
    documentation.register_tools(registry, ctx)
    ops.register_tools(registry, ctx)
    return registry


def create_mcp_server(ctx: AppContext) -> Any:
    """Create the MCP server instance lazily to avoid hard import failures."""

    try:
        from fastmcp import FastMCP
    except ModuleNotFoundError as exc:
        raise ConfigurationError(
            "The fastmcp dependency is not installed.",
            suggested_fix='Install dependencies with `pip install -e ".[dev]"`.',
        ) from exc

    server = FastMCP("Dataiku DSS Copilot", auth=build_auth_provider(ctx.settings))
    registry = build_tool_registry(ctx)
    for tool in registry.items():
        tool.handler.__name__ = tool.name
        tool.handler.__doc__ = tool.description
        server.tool()(tool.handler)
    return server


def run_stdio_server(ctx: AppContext) -> None:
    """Run the MCP server using STDIO transport."""

    server = create_mcp_server(ctx)
    try:
        server.run(transport="stdio")
    except TypeError:
        server.run()


def run_http_server(
    ctx: AppContext,
    *,
    host: str | None = None,
    port: int | None = None,
    path: str | None = None,
) -> None:
    """Run the MCP server over Streamable HTTP transport."""

    server = create_mcp_server(ctx)
    server.run(
        transport="streamable-http",
        host=host or ctx.settings.http_host,
        port=port or ctx.settings.http_port,
        path=path or ctx.settings.http_path,
    )


def _dump_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _load_text_value(*, value: str | None, file_path: str | None, field_name: str) -> str:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8")
    if value is not None:
        return value
    raise ConfigurationError(
        f"Missing required text payload for {field_name}.",
        suggested_fix=(
            f"Provide --{field_name.replace('_', '-')} or "
            f"--{field_name.replace('_', '-')}-file."
        ),
    )


def _load_optional_text_value(*, value: str | None, file_path: str | None) -> str | None:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8")
    return value


def _load_base64_value(
    *,
    content_base64: str | None,
    source_file: str | None,
) -> str:
    if source_file:
        payload = Path(source_file).read_bytes()
        return base64.b64encode(payload).decode("ascii")
    if content_base64 is not None:
        return content_base64
    raise ConfigurationError(
        "Missing file content for upload.",
        suggested_fix="Provide --content-base64 or --source-file.",
    )


def _load_json_value(raw_json: str | None, *, field_name: str) -> dict[str, Any] | None:
    if raw_json is None:
        return None
    try:
        loaded = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Invalid JSON payload for {field_name}.",
            suggested_fix=f"Provide valid JSON for {field_name}.",
        ) from exc
    if loaded is None:
        return None
    if not isinstance(loaded, dict):
        raise ConfigurationError(
            f"{field_name} must be a JSON object.",
            suggested_fix=f"Provide a JSON object for {field_name}.",
        )
    return loaded


def _run_validate_config(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    return ok(
        {"settings": settings.public_settings()},
        metadata={"command": "validate-config", "mode": settings.mode.value},
    )


def _run_ping(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.ping()),
        metadata={"command": "ping", "mode": ctx.settings.mode.value},
    )


def _run_list_tools(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    return ok(
        {"tools": registry.names()},
        metadata={"command": "list-tools", "mode": ctx.settings.mode.value},
    )


def _run_serve_http(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    run_http_server(
        ctx,
        host=args.host,
        port=args.port,
        path=args.path,
    )
    return ok(
        {
            "transport": "http",
            "host": args.host or ctx.settings.http_host,
            "port": args.port or ctx.settings.http_port,
            "path": args.path or ctx.settings.http_path,
        },
        metadata={"command": "serve-http", "mode": ctx.settings.mode.value},
    )


def _run_list_projects(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    projects_payload = ctx.redactor.redact(
        {"projects": ctx.dataiku.list_projects(include_archived=args.include_archived)}
    )
    return ok(
        projects_payload,
        metadata={"command": "list-projects", "mode": ctx.settings.mode.value},
    )


def _run_project_summary(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.get_project_summary(args.project_key)),
        metadata={"command": "project-summary", "mode": ctx.settings.mode.value},
    )


def _run_list_datasets(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        {"datasets": ctx.redactor.redact(ctx.dataiku.list_datasets(args.project_key))},
        metadata={"command": "list-datasets", "mode": ctx.settings.mode.value},
    )


def _run_dataset_schema(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.get_dataset_schema(args.project_key, args.dataset_name)
        ),
        metadata={"command": "dataset-schema", "mode": ctx.settings.mode.value},
    )


def _run_suggest_prediction_targets(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.suggest_prediction_targets(
                args.project_key,
                args.dataset_name,
                limit=args.limit,
            )
        ),
        metadata={
            "command": "suggest-prediction-targets",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_list_ml_commands(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.list_ml_commands()),
        metadata={"command": "list-ml-commands", "mode": ctx.settings.mode.value},
    )


def _run_plan_ml_command(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.plan_ml_command(
                args.project_key,
                args.dataset_name,
                args.command_name,
                target_variable=args.target_variable,
                prepared_dataset_name=args.prepared_dataset_name,
                prepare_recipe_name=args.prepare_recipe_name,
                prediction_type=args.prediction_type,
                ml_backend_type=args.ml_backend_type,
                guess_policy=args.guess_policy,
            )
        ),
        metadata={"command": "plan-ml-command", "mode": ctx.settings.mode.value},
    )


def _run_list_recipes(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        {"recipes": ctx.redactor.redact(ctx.dataiku.list_recipes(args.project_key))},
        metadata={"command": "list-recipes", "mode": ctx.settings.mode.value},
    )


def _run_recipe_details(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.get_recipe_details(args.project_key, args.recipe_name)
        ),
        metadata={"command": "recipe-details", "mode": ctx.settings.mode.value},
    )


def _run_list_managed_folders(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        {"folders": ctx.redactor.redact(ctx.dataiku.list_managed_folders(args.project_key))},
        metadata={"command": "list-managed-folders", "mode": ctx.settings.mode.value},
    )


def _run_managed_folder_info(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.get_managed_folder_info(args.project_key, args.folder_id)
        ),
        metadata={"command": "managed-folder-info", "mode": ctx.settings.mode.value},
    )


def _run_list_folder_files(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.list_folder_files(
                args.project_key,
                args.folder_id,
                path=args.path,
                recursive=args.recursive,
                limit=args.limit,
            )
        ),
        metadata={"command": "list-folder-files", "mode": ctx.settings.mode.value},
    )


def _run_project_map(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.generate_project_map(args.project_key)),
        metadata={"command": "project-map", "mode": ctx.settings.mode.value},
    )


def _run_flow_graph(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.get_flow_graph(
                args.project_key,
                include_recipes=not args.no_recipes,
                include_folders=not args.no_folders,
                include_models=not args.no_models,
                include_zones=not args.no_zones,
            )
        ),
        metadata={"command": "flow-graph", "mode": ctx.settings.mode.value},
    )


def _run_flow_health(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.analyze_flow_health(args.project_key)),
        metadata={"command": "flow-health", "mode": ctx.settings.mode.value},
    )


def _run_review_recipe_code(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.review_recipe_code(args.project_key, args.recipe_name)
        ),
        metadata={"command": "review-recipe-code", "mode": ctx.settings.mode.value},
    )


def _run_managed_folder_doctor(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.managed_folder_doctor(args.project_key, folder_id=args.folder_id)
        ),
        metadata={"command": "managed-folder-doctor", "mode": ctx.settings.mode.value},
    )


def _run_list_scenarios(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        {"scenarios": ctx.redactor.redact(ctx.dataiku.list_scenarios(args.project_key))},
        metadata={"command": "list-scenarios", "mode": ctx.settings.mode.value},
    )


def _run_scenario_runs(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.get_scenario_runs(
                args.project_key,
                args.scenario_id,
                limit=args.limit,
            )
        ),
        metadata={"command": "scenario-runs", "mode": ctx.settings.mode.value},
    )


def _run_job_logs(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.get_job_logs(
                args.project_key,
                job_id=args.job_id,
                run_id=args.run_id,
                scenario_id=args.scenario_id,
                max_lines=args.max_lines,
            )
        ),
        metadata={"command": "job-logs", "mode": ctx.settings.mode.value},
    )


def _run_explain_failure(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.explain_failure(
                args.project_key,
                job_id=args.job_id,
                run_id=args.run_id,
                scenario_id=args.scenario_id,
            )
        ),
        metadata={"command": "explain-failure", "mode": ctx.settings.mode.value},
    )


def _run_generate_project_readme(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.generate_project_readme(args.project_key)),
        metadata={"command": "generate-project-readme", "mode": ctx.settings.mode.value},
    )


def _run_generate_flow_documentation(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.generate_flow_documentation(args.project_key)),
        metadata={
            "command": "generate-flow-documentation",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_generate_troubleshooting_report(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.generate_troubleshooting_report(args.project_key, focus=args.focus)
        ),
        metadata={
            "command": "generate-troubleshooting-report",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_generate_rag_audit_report(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.generate_rag_audit_report(args.project_key)),
        metadata={
            "command": "generate-rag-audit-report",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_update_recipe_code(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    new_code = _load_text_value(
        value=args.new_code,
        file_path=args.new_code_file,
        field_name="new_code",
    )
    return registry.get("dataiku_update_recipe_code").handler(
        args.project_key,
        args.recipe_name,
        new_code,
        args.reason,
        args.approved,
        args.approval_reason,
    )


def _run_create_python_recipe(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    code = _load_text_value(value=args.code, file_path=args.code_file, field_name="code")
    return registry.get("dataiku_create_python_recipe").handler(
        args.project_key,
        args.recipe_name,
        args.inputs,
        args.outputs,
        code,
        args.approved,
        args.approval_reason,
    )


def _run_bootstrap_xgboost_flow(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    return registry.get("dataiku_bootstrap_xgboost_flow").handler(
        args.project_key,
        args.dataset_name,
        args.target_variable,
        args.prepared_dataset_name,
        args.prepare_recipe_name,
        args.prediction_type,
        args.ml_backend_type,
        args.guess_policy,
        args.approved,
        args.approval_reason,
    )


def _run_run_ml_command(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    return registry.get("dataiku_run_ml_command").handler(
        args.project_key,
        args.dataset_name,
        args.command_name,
        args.target_variable,
        args.prepared_dataset_name,
        args.prepare_recipe_name,
        args.prediction_type,
        args.ml_backend_type,
        args.guess_policy,
        args.approved,
        args.approval_reason,
    )


def _run_list_ml_tasks(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact({"ml_tasks": ctx.dataiku.list_ml_tasks(args.project_key)}),
        metadata={"command": "list-ml-tasks", "mode": ctx.settings.mode.value},
    )


def _run_ml_task_details(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.get_ml_task_details(
                args.project_key,
                args.analysis_id,
                args.ml_task_id,
            )
        ),
        metadata={"command": "ml-task-details", "mode": ctx.settings.mode.value},
    )


def _run_list_trained_models(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.list_trained_models(
                args.project_key,
                args.analysis_id,
                args.ml_task_id,
            )
        ),
        metadata={"command": "list-trained-models", "mode": ctx.settings.mode.value},
    )


def _run_train_ml_task(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    return registry.get("dataiku_train_ml_task").handler(
        args.project_key,
        args.analysis_id,
        args.ml_task_id,
        args.session_name,
        args.session_description,
        args.run_queue,
        args.approved,
        args.approval_reason,
    )


def _run_deploy_trained_model_to_flow(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    return registry.get("dataiku_deploy_trained_model_to_flow").handler(
        args.project_key,
        args.analysis_id,
        args.ml_task_id,
        args.model_id,
        args.saved_model_name,
        args.train_dataset,
        args.test_dataset,
        args.redo_optimization,
        args.approved,
        args.approval_reason,
    )


def _run_list_saved_models(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact({"saved_models": ctx.dataiku.list_saved_models(args.project_key)}),
        metadata={"command": "list-saved-models", "mode": ctx.settings.mode.value},
    )


def _run_saved_model_details(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.get_saved_model_details(args.project_key, args.saved_model_id)
        ),
        metadata={"command": "saved-model-details", "mode": ctx.settings.mode.value},
    )


def _run_create_prediction_scoring_recipe(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    return registry.get("dataiku_create_prediction_scoring_recipe").handler(
        args.project_key,
        args.saved_model_id,
        args.input_dataset,
        args.recipe_name,
        args.output_dataset_name,
        args.output_connection,
        args.approved,
        args.approval_reason,
    )


def _run_list_model_evaluation_stores(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            {"evaluation_stores": ctx.dataiku.list_model_evaluation_stores(args.project_key)}
        ),
        metadata={
            "command": "list-model-evaluation-stores",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_model_evaluation_store_details(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.get_model_evaluation_store_details(
                args.project_key,
                args.evaluation_store_id,
            )
        ),
        metadata={
            "command": "model-evaluation-store-details",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_create_model_evaluation(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    return registry.get("dataiku_create_model_evaluation").handler(
        args.project_key,
        args.saved_model_id,
        args.evaluation_dataset,
        args.evaluation_store_id,
        args.evaluation_store_name,
        args.recipe_name,
        args.scored_output_dataset,
        args.metrics_output_dataset,
        args.metrics,
        args.run_immediately,
        args.approved,
        args.approval_reason,
    )


def _run_compare_saved_models(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.compare_saved_models(
                args.project_key,
                args.saved_model_ids,
                metric_name=args.metric_name,
            )
        ),
        metadata={"command": "compare-saved-models", "mode": ctx.settings.mode.value},
    )


def _run_generate_model_evaluation_report(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.generate_model_evaluation_report(
                args.project_key,
                evaluation_store_id=args.evaluation_store_id,
                saved_model_ids=args.saved_model_ids,
                metric_name=args.metric_name,
            )
        ),
        metadata={
            "command": "generate-model-evaluation-report",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_route_ml_intent(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.route_ml_intent(
                args.intent_text,
                default_project_key=args.default_project_key,
                default_dataset_name=args.default_dataset_name,
            )
        ),
        metadata={"command": "route-ml-intent", "mode": ctx.settings.mode.value},
    )


def _run_run_routed_ml_intent(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    return registry.get("dataiku_run_routed_ml_intent").handler(
        args.intent_text,
        args.default_project_key,
        args.default_dataset_name,
        args.approved,
        args.approval_reason,
    )


def _run_create_managed_folder(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    return registry.get("dataiku_create_managed_folder").handler(
        args.project_key,
        args.folder_name,
        args.connection,
        args.folder_type,
        args.approved,
        args.approval_reason,
    )


def _run_upload_file_to_folder(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    content_base64 = _load_base64_value(
        content_base64=args.content_base64,
        source_file=args.source_file,
    )
    return registry.get("dataiku_upload_file_to_folder").handler(
        args.project_key,
        args.folder_id,
        args.file_path,
        content_base64,
        args.overwrite,
        args.approved,
        args.approval_reason,
    )


def _run_run_scenario(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    params = _load_json_value(args.params_json, field_name="params_json")
    return registry.get("dataiku_run_scenario").handler(
        args.project_key,
        args.scenario_id,
        params,
        args.approved,
        args.approval_reason,
    )


def _run_create_scenario(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    code = _load_optional_text_value(value=args.code, file_path=args.code_file)
    return registry.get("dataiku_create_scenario").handler(
        args.project_key,
        args.scenario_name,
        args.scenario_type,
        code,
        args.build_datasets,
        args.active,
        args.approved,
        args.approval_reason,
    )


def _run_create_project_documentation(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    registry = build_tool_registry(ctx)
    markdown = _load_text_value(
        value=args.markdown,
        file_path=args.markdown_file,
        field_name="markdown",
    )
    return registry.get("dataiku_create_project_documentation").handler(
        args.project_key,
        args.target,
        markdown,
        args.overwrite,
        args.approved,
        args.approval_reason,
    )


def _run_list_code_envs(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        {"code_envs": ctx.redactor.redact(ctx.dataiku.list_code_envs())},
        metadata={"command": "list-code-envs", "mode": ctx.settings.mode.value},
    )


def _run_code_env_details(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.get_code_env_details(args.env_name)),
        metadata={"command": "code-env-details", "mode": ctx.settings.mode.value},
    )


def _run_code_env_doctor(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.code_env_doctor(args.env_name)),
        metadata={"command": "code-env-doctor", "mode": ctx.settings.mode.value},
    )


def _run_list_plugin_usages(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            {"plugin_usages": ctx.dataiku.list_plugin_usages(args.project_key)}
        ),
        metadata={"command": "list-plugin-usages", "mode": ctx.settings.mode.value},
    )


def _run_generate_scenario_dependency_map(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.generate_scenario_dependency_map(args.project_key)),
        metadata={
            "command": "generate-scenario-dependency-map",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_plan_code_env_updates(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.plan_code_env_updates(env_name=args.env_name)),
        metadata={"command": "plan-code-env-updates", "mode": ctx.settings.mode.value},
    )


def _run_generate_production_readiness_report(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.generate_production_readiness_report(args.project_key)
        ),
        metadata={
            "command": "generate-production-readiness-report",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_generate_cost_performance_report(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.generate_cost_performance_report(args.project_key)),
        metadata={
            "command": "generate-cost-performance-report",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_generate_production_readiness_checklist(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.generate_production_readiness_checklist(args.project_key)
        ),
        metadata={
            "command": "generate-production-readiness-checklist",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_generate_governance_documentation(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.generate_governance_documentation(args.project_key)),
        metadata={
            "command": "generate-governance-documentation",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_detect_rag_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.detect_rag_pipeline(args.project_key)),
        metadata={"command": "detect-rag-pipeline", "mode": ctx.settings.mode.value},
    )


def _run_audit_rag_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.audit_rag_pipeline(args.project_key, deep=args.deep)
        ),
        metadata={"command": "audit-rag-pipeline", "mode": ctx.settings.mode.value},
    )


def _run_run_rag_eval(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.run_rag_eval(
                args.project_key,
                benchmark_dataset_name=args.benchmark_dataset_name,
            )
        ),
        metadata={"command": "run-rag-eval", "mode": ctx.settings.mode.value},
    )


def _run_compare_chunking_strategies(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.compare_chunking_strategies(
                args.project_key,
                dataset_name=args.dataset_name,
                strategies=args.strategies,
            )
        ),
        metadata={
            "command": "compare-chunking-strategies",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_inspect_vector_store(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.inspect_vector_store(args.project_key)),
        metadata={"command": "inspect-vector-store", "mode": ctx.settings.mode.value},
    )


def _run_monitor_embedding_drift(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(
            ctx.dataiku.monitor_embedding_drift(
                args.project_key,
                reference_dataset_name=args.reference_dataset_name,
                current_dataset_name=args.current_dataset_name,
            )
        ),
        metadata={
            "command": "monitor-embedding-drift",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_audit_prompt_injection(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.audit_prompt_injection(args.project_key)),
        metadata={"command": "audit-prompt-injection", "mode": ctx.settings.mode.value},
    )


def _run_generate_architecture_diagram(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.generate_architecture_diagram(args.project_key)),
        metadata={
            "command": "generate-architecture-diagram",
            "mode": ctx.settings.mode.value,
        },
    )


def _run_score_project_quality(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.score_project_quality(args.project_key)),
        metadata={"command": "score-project-quality", "mode": ctx.settings.mode.value},
    )


def _run_prioritize_technical_debt(args: argparse.Namespace) -> dict[str, Any]:
    settings = load_settings(dotenv_path=args.env_file)
    ctx = build_app_context(settings=settings)
    return ok(
        ctx.redactor.redact(ctx.dataiku.prioritize_technical_debt(args.project_key)),
        metadata={
            "command": "prioritize-technical-debt",
            "mode": ctx.settings.mode.value,
        },
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dataiku-codex-mcp")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run the MCP server over STDIO transport.",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="Optional path to a .env file.",
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("validate-config")
    subparsers.add_parser("ping")
    subparsers.add_parser("list-tools")
    serve_http_parser = subparsers.add_parser("serve-http")
    serve_http_parser.add_argument("--host", default=None)
    serve_http_parser.add_argument("--port", type=int, default=None)
    serve_http_parser.add_argument("--path", default=None)
    list_projects_parser = subparsers.add_parser("list-projects")
    list_projects_parser.add_argument("--include-archived", action="store_true")
    project_summary_parser = subparsers.add_parser("project-summary")
    project_summary_parser.add_argument("project_key")
    list_datasets_parser = subparsers.add_parser("list-datasets")
    list_datasets_parser.add_argument("project_key")
    dataset_schema_parser = subparsers.add_parser("dataset-schema")
    dataset_schema_parser.add_argument("project_key")
    dataset_schema_parser.add_argument("dataset_name")
    subparsers.add_parser("list-ml-commands")
    suggest_prediction_targets_parser = subparsers.add_parser(
        "suggest-prediction-targets"
    )
    suggest_prediction_targets_parser.add_argument("project_key")
    suggest_prediction_targets_parser.add_argument("dataset_name")
    suggest_prediction_targets_parser.add_argument("--limit", type=int, default=5)
    plan_ml_command_parser = subparsers.add_parser("plan-ml-command")
    plan_ml_command_parser.add_argument("project_key")
    plan_ml_command_parser.add_argument("dataset_name")
    plan_ml_command_parser.add_argument("command_name")
    plan_ml_command_parser.add_argument("--target-variable", default=None)
    plan_ml_command_parser.add_argument("--prepared-dataset-name", default=None)
    plan_ml_command_parser.add_argument("--prepare-recipe-name", default=None)
    plan_ml_command_parser.add_argument("--prediction-type", default=None)
    plan_ml_command_parser.add_argument("--ml-backend-type", default=None)
    plan_ml_command_parser.add_argument("--guess-policy", default=None)
    list_recipes_parser = subparsers.add_parser("list-recipes")
    list_recipes_parser.add_argument("project_key")
    recipe_details_parser = subparsers.add_parser("recipe-details")
    recipe_details_parser.add_argument("project_key")
    recipe_details_parser.add_argument("recipe_name")
    list_managed_folders_parser = subparsers.add_parser("list-managed-folders")
    list_managed_folders_parser.add_argument("project_key")
    managed_folder_info_parser = subparsers.add_parser("managed-folder-info")
    managed_folder_info_parser.add_argument("project_key")
    managed_folder_info_parser.add_argument("folder_id")
    list_folder_files_parser = subparsers.add_parser("list-folder-files")
    list_folder_files_parser.add_argument("project_key")
    list_folder_files_parser.add_argument("folder_id")
    list_folder_files_parser.add_argument("--path", default="/")
    list_folder_files_parser.add_argument("--recursive", action="store_true")
    list_folder_files_parser.add_argument("--limit", type=int, default=100)
    project_map_parser = subparsers.add_parser("project-map")
    project_map_parser.add_argument("project_key")
    flow_graph_parser = subparsers.add_parser("flow-graph")
    flow_graph_parser.add_argument("project_key")
    flow_graph_parser.add_argument("--no-recipes", action="store_true")
    flow_graph_parser.add_argument("--no-folders", action="store_true")
    flow_graph_parser.add_argument("--no-models", action="store_true")
    flow_graph_parser.add_argument("--no-zones", action="store_true")
    flow_health_parser = subparsers.add_parser("flow-health")
    flow_health_parser.add_argument("project_key")
    review_recipe_parser = subparsers.add_parser("review-recipe-code")
    review_recipe_parser.add_argument("project_key")
    review_recipe_parser.add_argument("recipe_name")
    folder_doctor_parser = subparsers.add_parser("managed-folder-doctor")
    folder_doctor_parser.add_argument("project_key")
    folder_doctor_parser.add_argument("--folder-id", default=None)
    list_scenarios_parser = subparsers.add_parser("list-scenarios")
    list_scenarios_parser.add_argument("project_key")
    scenario_runs_parser = subparsers.add_parser("scenario-runs")
    scenario_runs_parser.add_argument("project_key")
    scenario_runs_parser.add_argument("scenario_id")
    scenario_runs_parser.add_argument("--limit", type=int, default=10)
    job_logs_parser = subparsers.add_parser("job-logs")
    job_logs_parser.add_argument("project_key")
    job_logs_parser.add_argument("--job-id", default=None)
    job_logs_parser.add_argument("--run-id", default=None)
    job_logs_parser.add_argument("--scenario-id", default=None)
    job_logs_parser.add_argument("--max-lines", type=int, default=None)
    explain_failure_parser = subparsers.add_parser("explain-failure")
    explain_failure_parser.add_argument("project_key")
    explain_failure_parser.add_argument("--job-id", default=None)
    explain_failure_parser.add_argument("--run-id", default=None)
    explain_failure_parser.add_argument("--scenario-id", default=None)
    generate_project_readme_parser = subparsers.add_parser("generate-project-readme")
    generate_project_readme_parser.add_argument("project_key")
    generate_flow_documentation_parser = subparsers.add_parser(
        "generate-flow-documentation"
    )
    generate_flow_documentation_parser.add_argument("project_key")
    generate_troubleshooting_parser = subparsers.add_parser(
        "generate-troubleshooting-report"
    )
    generate_troubleshooting_parser.add_argument("project_key")
    generate_troubleshooting_parser.add_argument("--focus", default=None)
    generate_rag_audit_parser = subparsers.add_parser("generate-rag-audit-report")
    generate_rag_audit_parser.add_argument("project_key")
    update_recipe_parser = subparsers.add_parser("update-recipe-code")
    update_recipe_parser.add_argument("project_key")
    update_recipe_parser.add_argument("recipe_name")
    update_recipe_parser.add_argument("--new-code", default=None)
    update_recipe_parser.add_argument("--new-code-file", default=None)
    update_recipe_parser.add_argument("--reason", required=True)
    update_recipe_parser.add_argument("--approved", action="store_true")
    update_recipe_parser.add_argument("--approval-reason", default=None)
    create_python_recipe_parser = subparsers.add_parser("create-python-recipe")
    create_python_recipe_parser.add_argument("project_key")
    create_python_recipe_parser.add_argument("recipe_name")
    create_python_recipe_parser.add_argument("--inputs", nargs="*", default=[])
    create_python_recipe_parser.add_argument("--outputs", nargs="*", default=[])
    create_python_recipe_parser.add_argument("--code", default=None)
    create_python_recipe_parser.add_argument("--code-file", default=None)
    create_python_recipe_parser.add_argument("--approved", action="store_true")
    create_python_recipe_parser.add_argument("--approval-reason", default=None)
    bootstrap_xgboost_parser = subparsers.add_parser("bootstrap-xgboost-flow")
    bootstrap_xgboost_parser.add_argument("project_key")
    bootstrap_xgboost_parser.add_argument("dataset_name")
    bootstrap_xgboost_parser.add_argument("target_variable")
    bootstrap_xgboost_parser.add_argument("--prepared-dataset-name", default=None)
    bootstrap_xgboost_parser.add_argument("--prepare-recipe-name", default=None)
    bootstrap_xgboost_parser.add_argument("--prediction-type", default=None)
    bootstrap_xgboost_parser.add_argument("--ml-backend-type", default="PY_MEMORY")
    bootstrap_xgboost_parser.add_argument("--guess-policy", default="DEFAULT")
    bootstrap_xgboost_parser.add_argument("--approved", action="store_true")
    bootstrap_xgboost_parser.add_argument("--approval-reason", default=None)
    run_ml_command_parser = subparsers.add_parser("run-ml-command")
    run_ml_command_parser.add_argument("project_key")
    run_ml_command_parser.add_argument("dataset_name")
    run_ml_command_parser.add_argument("command_name")
    run_ml_command_parser.add_argument("--target-variable", default=None)
    run_ml_command_parser.add_argument("--prepared-dataset-name", default=None)
    run_ml_command_parser.add_argument("--prepare-recipe-name", default=None)
    run_ml_command_parser.add_argument("--prediction-type", default=None)
    run_ml_command_parser.add_argument("--ml-backend-type", default=None)
    run_ml_command_parser.add_argument("--guess-policy", default=None)
    run_ml_command_parser.add_argument("--approved", action="store_true")
    run_ml_command_parser.add_argument("--approval-reason", default=None)
    list_ml_tasks_parser = subparsers.add_parser("list-ml-tasks")
    list_ml_tasks_parser.add_argument("project_key")
    ml_task_details_parser = subparsers.add_parser("ml-task-details")
    ml_task_details_parser.add_argument("project_key")
    ml_task_details_parser.add_argument("analysis_id")
    ml_task_details_parser.add_argument("ml_task_id")
    list_trained_models_parser = subparsers.add_parser("list-trained-models")
    list_trained_models_parser.add_argument("project_key")
    list_trained_models_parser.add_argument("analysis_id")
    list_trained_models_parser.add_argument("ml_task_id")
    train_ml_task_parser = subparsers.add_parser("train-ml-task")
    train_ml_task_parser.add_argument("project_key")
    train_ml_task_parser.add_argument("analysis_id")
    train_ml_task_parser.add_argument("ml_task_id")
    train_ml_task_parser.add_argument("--session-name", default=None)
    train_ml_task_parser.add_argument("--session-description", default=None)
    train_ml_task_parser.add_argument("--run-queue", action="store_true")
    train_ml_task_parser.add_argument("--approved", action="store_true")
    train_ml_task_parser.add_argument("--approval-reason", default=None)
    deploy_model_parser = subparsers.add_parser("deploy-trained-model-to-flow")
    deploy_model_parser.add_argument("project_key")
    deploy_model_parser.add_argument("analysis_id")
    deploy_model_parser.add_argument("ml_task_id")
    deploy_model_parser.add_argument("--model-id", default=None)
    deploy_model_parser.add_argument("--saved-model-name", default=None)
    deploy_model_parser.add_argument("--train-dataset", default=None)
    deploy_model_parser.add_argument("--test-dataset", default=None)
    deploy_model_parser.set_defaults(redo_optimization=True)
    deploy_model_parser.add_argument(
        "--no-redo-optimization",
        dest="redo_optimization",
        action="store_false",
    )
    deploy_model_parser.add_argument("--approved", action="store_true")
    deploy_model_parser.add_argument("--approval-reason", default=None)
    list_saved_models_parser = subparsers.add_parser("list-saved-models")
    list_saved_models_parser.add_argument("project_key")
    saved_model_details_parser = subparsers.add_parser("saved-model-details")
    saved_model_details_parser.add_argument("project_key")
    saved_model_details_parser.add_argument("saved_model_id")
    create_prediction_scoring_parser = subparsers.add_parser("create-prediction-scoring-recipe")
    create_prediction_scoring_parser.add_argument("project_key")
    create_prediction_scoring_parser.add_argument("saved_model_id")
    create_prediction_scoring_parser.add_argument("input_dataset")
    create_prediction_scoring_parser.add_argument("recipe_name")
    create_prediction_scoring_parser.add_argument("output_dataset_name")
    create_prediction_scoring_parser.add_argument("--output-connection", default=None)
    create_prediction_scoring_parser.add_argument("--approved", action="store_true")
    create_prediction_scoring_parser.add_argument("--approval-reason", default=None)
    list_model_evaluation_stores_parser = subparsers.add_parser("list-model-evaluation-stores")
    list_model_evaluation_stores_parser.add_argument("project_key")
    model_evaluation_store_details_parser = subparsers.add_parser("model-evaluation-store-details")
    model_evaluation_store_details_parser.add_argument("project_key")
    model_evaluation_store_details_parser.add_argument("evaluation_store_id")
    create_model_evaluation_parser = subparsers.add_parser("create-model-evaluation")
    create_model_evaluation_parser.add_argument("project_key")
    create_model_evaluation_parser.add_argument("saved_model_id")
    create_model_evaluation_parser.add_argument("evaluation_dataset")
    create_model_evaluation_parser.add_argument("--evaluation-store-id", default=None)
    create_model_evaluation_parser.add_argument("--evaluation-store-name", default=None)
    create_model_evaluation_parser.add_argument("--recipe-name", default=None)
    create_model_evaluation_parser.add_argument("--scored-output-dataset", default=None)
    create_model_evaluation_parser.add_argument("--metrics-output-dataset", default=None)
    create_model_evaluation_parser.add_argument("--metrics", nargs="*", default=None)
    create_model_evaluation_parser.add_argument("--run-immediately", action="store_true")
    create_model_evaluation_parser.add_argument("--approved", action="store_true")
    create_model_evaluation_parser.add_argument("--approval-reason", default=None)
    compare_saved_models_parser = subparsers.add_parser("compare-saved-models")
    compare_saved_models_parser.add_argument("project_key")
    compare_saved_models_parser.add_argument("saved_model_ids", nargs="+")
    compare_saved_models_parser.add_argument("--metric-name", default=None)
    generate_model_evaluation_report_parser = subparsers.add_parser(
        "generate-model-evaluation-report"
    )
    generate_model_evaluation_report_parser.add_argument("project_key")
    generate_model_evaluation_report_parser.add_argument("--evaluation-store-id", default=None)
    generate_model_evaluation_report_parser.add_argument(
        "--saved-model-ids",
        nargs="*",
        default=None,
    )
    generate_model_evaluation_report_parser.add_argument("--metric-name", default=None)
    route_ml_intent_parser = subparsers.add_parser("route-ml-intent")
    route_ml_intent_parser.add_argument("intent_text")
    route_ml_intent_parser.add_argument("--default-project-key", default=None)
    route_ml_intent_parser.add_argument("--default-dataset-name", default=None)
    run_routed_ml_intent_parser = subparsers.add_parser("run-routed-ml-intent")
    run_routed_ml_intent_parser.add_argument("intent_text")
    run_routed_ml_intent_parser.add_argument("--default-project-key", default=None)
    run_routed_ml_intent_parser.add_argument("--default-dataset-name", default=None)
    run_routed_ml_intent_parser.add_argument("--approved", action="store_true")
    run_routed_ml_intent_parser.add_argument("--approval-reason", default=None)
    create_managed_folder_parser = subparsers.add_parser("create-managed-folder")
    create_managed_folder_parser.add_argument("project_key")
    create_managed_folder_parser.add_argument("folder_name")
    create_managed_folder_parser.add_argument("--connection", default=None)
    create_managed_folder_parser.add_argument("--folder-type", default=None)
    create_managed_folder_parser.add_argument("--approved", action="store_true")
    create_managed_folder_parser.add_argument("--approval-reason", default=None)
    upload_file_parser = subparsers.add_parser("upload-file-to-folder")
    upload_file_parser.add_argument("project_key")
    upload_file_parser.add_argument("folder_id")
    upload_file_parser.add_argument("file_path")
    upload_file_parser.add_argument("--content-base64", default=None)
    upload_file_parser.add_argument("--source-file", default=None)
    upload_file_parser.add_argument("--overwrite", action="store_true")
    upload_file_parser.add_argument("--approved", action="store_true")
    upload_file_parser.add_argument("--approval-reason", default=None)
    create_scenario_parser = subparsers.add_parser("create-scenario")
    create_scenario_parser.add_argument("project_key")
    create_scenario_parser.add_argument("scenario_name")
    create_scenario_parser.add_argument("--scenario-type", default="custom_python")
    create_scenario_parser.add_argument("--code", default=None)
    create_scenario_parser.add_argument("--code-file", default=None)
    create_scenario_parser.add_argument("--build-datasets", nargs="*", default=[])
    create_scenario_parser.add_argument("--active", action="store_true")
    create_scenario_parser.add_argument("--approved", action="store_true")
    create_scenario_parser.add_argument("--approval-reason", default=None)
    run_scenario_parser = subparsers.add_parser("run-scenario")
    run_scenario_parser.add_argument("project_key")
    run_scenario_parser.add_argument("scenario_id")
    run_scenario_parser.add_argument("--params-json", default=None)
    run_scenario_parser.add_argument("--approved", action="store_true")
    run_scenario_parser.add_argument("--approval-reason", default=None)
    create_project_doc_parser = subparsers.add_parser("create-project-documentation")
    create_project_doc_parser.add_argument("project_key")
    create_project_doc_parser.add_argument("target")
    create_project_doc_parser.add_argument("--markdown", default=None)
    create_project_doc_parser.add_argument("--markdown-file", default=None)
    create_project_doc_parser.add_argument("--overwrite", action="store_true")
    create_project_doc_parser.add_argument("--approved", action="store_true")
    create_project_doc_parser.add_argument("--approval-reason", default=None)
    subparsers.add_parser("list-code-envs")
    code_env_details_parser = subparsers.add_parser("code-env-details")
    code_env_details_parser.add_argument("env_name")
    code_env_doctor_parser = subparsers.add_parser("code-env-doctor")
    code_env_doctor_parser.add_argument("env_name")
    list_plugin_usages_parser = subparsers.add_parser("list-plugin-usages")
    list_plugin_usages_parser.add_argument("project_key")
    scenario_dependency_map_parser = subparsers.add_parser("generate-scenario-dependency-map")
    scenario_dependency_map_parser.add_argument("project_key")
    plan_code_env_updates_parser = subparsers.add_parser("plan-code-env-updates")
    plan_code_env_updates_parser.add_argument("--env-name", default=None)
    production_readiness_parser = subparsers.add_parser("generate-production-readiness-report")
    production_readiness_parser.add_argument("project_key")
    cost_performance_parser = subparsers.add_parser("generate-cost-performance-report")
    cost_performance_parser.add_argument("project_key")
    production_checklist_parser = subparsers.add_parser(
        "generate-production-readiness-checklist"
    )
    production_checklist_parser.add_argument("project_key")
    governance_doc_parser = subparsers.add_parser("generate-governance-documentation")
    governance_doc_parser.add_argument("project_key")
    detect_rag_parser = subparsers.add_parser("detect-rag-pipeline")
    detect_rag_parser.add_argument("project_key")
    audit_rag_parser = subparsers.add_parser("audit-rag-pipeline")
    audit_rag_parser.add_argument("project_key")
    audit_rag_parser.add_argument("--deep", action="store_true")
    run_rag_eval_parser = subparsers.add_parser("run-rag-eval")
    run_rag_eval_parser.add_argument("project_key")
    run_rag_eval_parser.add_argument("--benchmark-dataset-name", default=None)
    compare_chunking_parser = subparsers.add_parser("compare-chunking-strategies")
    compare_chunking_parser.add_argument("project_key")
    compare_chunking_parser.add_argument("--dataset-name", default=None)
    compare_chunking_parser.add_argument("--strategies", nargs="*", default=None)
    inspect_vector_store_parser = subparsers.add_parser("inspect-vector-store")
    inspect_vector_store_parser.add_argument("project_key")
    monitor_embedding_drift_parser = subparsers.add_parser("monitor-embedding-drift")
    monitor_embedding_drift_parser.add_argument("project_key")
    monitor_embedding_drift_parser.add_argument("--reference-dataset-name", default=None)
    monitor_embedding_drift_parser.add_argument("--current-dataset-name", default=None)
    audit_prompt_injection_parser = subparsers.add_parser("audit-prompt-injection")
    audit_prompt_injection_parser.add_argument("project_key")
    architecture_diagram_parser = subparsers.add_parser("generate-architecture-diagram")
    architecture_diagram_parser.add_argument("project_key")
    score_quality_parser = subparsers.add_parser("score-project-quality")
    score_quality_parser.add_argument("project_key")
    prioritize_debt_parser = subparsers.add_parser("prioritize-technical-debt")
    prioritize_debt_parser.add_argument("project_key")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint used by the console script."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.stdio:
            settings = load_settings(dotenv_path=args.env_file)
            ctx = build_app_context(settings=settings)
            run_stdio_server(ctx)
            return 0

        command_map = {
            "validate-config": _run_validate_config,
            "ping": _run_ping,
            "list-tools": _run_list_tools,
            "serve-http": _run_serve_http,
            "list-projects": _run_list_projects,
            "project-summary": _run_project_summary,
            "list-datasets": _run_list_datasets,
            "dataset-schema": _run_dataset_schema,
            "list-ml-commands": _run_list_ml_commands,
            "suggest-prediction-targets": _run_suggest_prediction_targets,
            "plan-ml-command": _run_plan_ml_command,
            "list-recipes": _run_list_recipes,
            "recipe-details": _run_recipe_details,
            "list-managed-folders": _run_list_managed_folders,
            "managed-folder-info": _run_managed_folder_info,
            "list-folder-files": _run_list_folder_files,
            "project-map": _run_project_map,
            "flow-graph": _run_flow_graph,
            "flow-health": _run_flow_health,
            "review-recipe-code": _run_review_recipe_code,
            "managed-folder-doctor": _run_managed_folder_doctor,
            "list-scenarios": _run_list_scenarios,
            "scenario-runs": _run_scenario_runs,
            "job-logs": _run_job_logs,
            "explain-failure": _run_explain_failure,
            "generate-project-readme": _run_generate_project_readme,
            "generate-flow-documentation": _run_generate_flow_documentation,
            "generate-troubleshooting-report": _run_generate_troubleshooting_report,
            "generate-rag-audit-report": _run_generate_rag_audit_report,
            "update-recipe-code": _run_update_recipe_code,
            "create-python-recipe": _run_create_python_recipe,
            "bootstrap-xgboost-flow": _run_bootstrap_xgboost_flow,
            "run-ml-command": _run_run_ml_command,
            "list-ml-tasks": _run_list_ml_tasks,
            "ml-task-details": _run_ml_task_details,
            "list-trained-models": _run_list_trained_models,
            "train-ml-task": _run_train_ml_task,
            "deploy-trained-model-to-flow": _run_deploy_trained_model_to_flow,
            "list-saved-models": _run_list_saved_models,
            "saved-model-details": _run_saved_model_details,
            "create-prediction-scoring-recipe": _run_create_prediction_scoring_recipe,
            "list-model-evaluation-stores": _run_list_model_evaluation_stores,
            "model-evaluation-store-details": _run_model_evaluation_store_details,
            "create-model-evaluation": _run_create_model_evaluation,
            "compare-saved-models": _run_compare_saved_models,
            "generate-model-evaluation-report": _run_generate_model_evaluation_report,
            "route-ml-intent": _run_route_ml_intent,
            "run-routed-ml-intent": _run_run_routed_ml_intent,
            "create-managed-folder": _run_create_managed_folder,
            "upload-file-to-folder": _run_upload_file_to_folder,
            "create-scenario": _run_create_scenario,
            "run-scenario": _run_run_scenario,
            "create-project-documentation": _run_create_project_documentation,
            "list-code-envs": _run_list_code_envs,
            "code-env-details": _run_code_env_details,
            "code-env-doctor": _run_code_env_doctor,
            "list-plugin-usages": _run_list_plugin_usages,
            "generate-scenario-dependency-map": _run_generate_scenario_dependency_map,
            "plan-code-env-updates": _run_plan_code_env_updates,
            "generate-production-readiness-report": _run_generate_production_readiness_report,
            "generate-cost-performance-report": _run_generate_cost_performance_report,
            "generate-production-readiness-checklist": _run_generate_production_readiness_checklist,
            "generate-governance-documentation": _run_generate_governance_documentation,
            "detect-rag-pipeline": _run_detect_rag_pipeline,
            "audit-rag-pipeline": _run_audit_rag_pipeline,
            "run-rag-eval": _run_run_rag_eval,
            "compare-chunking-strategies": _run_compare_chunking_strategies,
            "inspect-vector-store": _run_inspect_vector_store,
            "monitor-embedding-drift": _run_monitor_embedding_drift,
            "audit-prompt-injection": _run_audit_prompt_injection,
            "generate-architecture-diagram": _run_generate_architecture_diagram,
            "score-project-quality": _run_score_project_quality,
            "prioritize-technical-debt": _run_prioritize_technical_debt,
        }
        command = command_map.get(args.command)
        if command is None:
            parser.print_help()
            return 0

        _dump_json(command(args))
        return 0
    except Exception as exc:
        payload = normalize_exception(exc)
        _dump_json(payload)
        return 1
