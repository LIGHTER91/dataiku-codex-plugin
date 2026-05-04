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

    def dataiku_list_ml_tasks(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_list_ml_tasks",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact({"ml_tasks": ctx.dataiku.list_ml_tasks(project_key)})
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_ml_tasks",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_list_ml_tasks",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_get_ml_task_details(
        project_key: str,
        analysis_id: str,
        ml_task_id: str,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_get_ml_task_details",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.get_ml_task_details(project_key, analysis_id, ml_task_id)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_ml_task_details",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=ml_task_id,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_get_ml_task_details",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_list_trained_models(
        project_key: str,
        analysis_id: str,
        ml_task_id: str,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_list_trained_models",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.list_trained_models(project_key, analysis_id, ml_task_id)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_trained_models",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=ml_task_id,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_list_trained_models",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_train_ml_task(
        project_key: str,
        analysis_id: str,
        ml_task_id: str,
        session_name: str | None = None,
        session_description: str | None = None,
        run_queue: bool = False,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_train_ml_task(
                project_key,
                analysis_id,
                ml_task_id,
                session_name=session_name,
                session_description=session_description,
                run_queue=run_queue,
            )
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_train_ml_task",
            level=PermissionLevel.EXECUTE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.train_ml_task(
                project_key,
                analysis_id,
                ml_task_id,
                session_name=session_name,
                session_description=session_description,
                run_queue=run_queue,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_train_ml_task",
            mode=ctx.settings.mode.value,
            operation_type="execute",
            success=True,
            project_key=project_key,
            object_name=ml_task_id,
        )
        return ok(
            {
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={
                "tool": "dataiku_train_ml_task",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_deploy_trained_model_to_flow(
        project_key: str,
        analysis_id: str,
        ml_task_id: str,
        model_id: str | None = None,
        saved_model_name: str | None = None,
        train_dataset: str | None = None,
        test_dataset: str | None = None,
        redo_optimization: bool = True,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_deploy_trained_model_to_flow(
                project_key,
                analysis_id,
                ml_task_id,
                model_id=model_id,
                saved_model_name=saved_model_name,
                train_dataset=train_dataset,
                test_dataset=test_dataset,
                redo_optimization=redo_optimization,
            )
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_deploy_trained_model_to_flow",
            level=PermissionLevel.WRITE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.deploy_trained_model_to_flow(
                project_key,
                analysis_id,
                ml_task_id,
                model_id=model_id,
                saved_model_name=saved_model_name,
                train_dataset=train_dataset,
                test_dataset=test_dataset,
                redo_optimization=redo_optimization,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_deploy_trained_model_to_flow",
            mode=ctx.settings.mode.value,
            operation_type="write",
            success=True,
            project_key=project_key,
            object_name=ml_task_id,
        )
        return ok(
            {
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={
                "tool": "dataiku_deploy_trained_model_to_flow",
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
    registry.register(
        "dataiku_list_ml_tasks",
        dataiku_list_ml_tasks,
        description="List Visual ML tasks available in a project.",
    )
    registry.register(
        "dataiku_get_ml_task_details",
        dataiku_get_ml_task_details,
        description="Get details and status for one Visual ML task.",
    )
    registry.register(
        "dataiku_list_trained_models",
        dataiku_list_trained_models,
        description="List trained models available for one Visual ML task.",
    )
    registry.register(
        "dataiku_train_ml_task",
        dataiku_train_ml_task,
        description="Train an existing Visual ML task after explicit approval.",
    )
    registry.register(
        "dataiku_deploy_trained_model_to_flow",
        dataiku_deploy_trained_model_to_flow,
        description="Deploy a trained Visual ML model to the Flow after explicit approval.",
    )
