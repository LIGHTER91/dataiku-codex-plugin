"""Guided ML bootstrap tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel
from dataiku_codex_mcp.tools.write_safety import require_approved_action

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register V3.5 guided ML bootstrap tools."""

    def dataiku_list_ml_commands() -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_list_ml_commands",
            level=PermissionLevel.READ,
            project_key=None,
        )
        payload = ctx.redactor.redact(ctx.dataiku.list_ml_commands())
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_ml_commands",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=None,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_list_ml_commands",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_suggest_prediction_targets(
        project_key: str,
        dataset_name: str,
        limit: int = 5,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_suggest_prediction_targets",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.suggest_prediction_targets(
                project_key,
                dataset_name,
                limit=limit,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_suggest_prediction_targets",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=dataset_name,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_suggest_prediction_targets",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_plan_ml_command(
        project_key: str,
        dataset_name: str,
        command_name: str,
        target_variable: str | None = None,
        prepared_dataset_name: str | None = None,
        prepare_recipe_name: str | None = None,
        prediction_type: str | None = None,
        ml_backend_type: str | None = None,
        guess_policy: str | None = None,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_plan_ml_command",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.plan_ml_command(
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
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_plan_ml_command",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=command_name,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_plan_ml_command",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_run_ml_command(
        project_key: str,
        dataset_name: str,
        command_name: str,
        target_variable: str | None = None,
        prepared_dataset_name: str | None = None,
        prepare_recipe_name: str | None = None,
        prediction_type: str | None = None,
        ml_backend_type: str | None = None,
        guess_policy: str | None = None,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_run_ml_command(
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
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_run_ml_command",
            level=PermissionLevel.WRITE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.run_ml_command(
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
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_run_ml_command",
            mode=ctx.settings.mode.value,
            operation_type="write",
            success=True,
            project_key=project_key,
            object_name=command_name,
        )
        return ok(
            {
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={
                "tool": "dataiku_run_ml_command",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_bootstrap_xgboost_flow(
        project_key: str,
        dataset_name: str,
        target_variable: str,
        prepared_dataset_name: str | None = None,
        prepare_recipe_name: str | None = None,
        prediction_type: str | None = None,
        ml_backend_type: str = "PY_MEMORY",
        guess_policy: str = "DEFAULT",
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_bootstrap_xgboost_flow(
                project_key,
                dataset_name,
                target_variable,
                prepared_dataset_name=prepared_dataset_name,
                prepare_recipe_name=prepare_recipe_name,
                prediction_type=prediction_type,
                ml_backend_type=ml_backend_type,
                guess_policy=guess_policy,
            )
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_bootstrap_xgboost_flow",
            level=PermissionLevel.WRITE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.bootstrap_xgboost_flow(
                project_key,
                dataset_name,
                target_variable,
                prepared_dataset_name=prepared_dataset_name,
                prepare_recipe_name=prepare_recipe_name,
                prediction_type=prediction_type,
                ml_backend_type=ml_backend_type,
                guess_policy=guess_policy,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_bootstrap_xgboost_flow",
            mode=ctx.settings.mode.value,
            operation_type="write",
            success=True,
            project_key=project_key,
            object_name=target_variable,
        )
        return ok(
            {
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={
                "tool": "dataiku_bootstrap_xgboost_flow",
                "mode": ctx.settings.mode.value,
            },
        )

    registry.register(
        "dataiku_list_ml_commands",
        dataiku_list_ml_commands,
        description="List reusable ML catalog commands.",
    )
    registry.register(
        "dataiku_suggest_prediction_targets",
        dataiku_suggest_prediction_targets,
        description="Suggest likely prediction targets for a dataset schema.",
    )
    registry.register(
        "dataiku_plan_ml_command",
        dataiku_plan_ml_command,
        description="Plan how a reusable ML catalog command would run on a dataset.",
    )
    registry.register(
        "dataiku_run_ml_command",
        dataiku_run_ml_command,
        description=(
            "Execute a reusable ML catalog command after explicit approval."
        ),
    )
    registry.register(
        "dataiku_bootstrap_xgboost_flow",
        dataiku_bootstrap_xgboost_flow,
        description=(
            "Create a Prepare recipe and a Visual ML prediction task configured "
            "for XGBoost after explicit approval."
        ),
    )
