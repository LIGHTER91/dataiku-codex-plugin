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

    def dataiku_list_saved_models(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_list_saved_models",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            {"saved_models": ctx.dataiku.list_saved_models(project_key)}
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_saved_models",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_list_saved_models", "mode": ctx.settings.mode.value},
        )

    def dataiku_get_saved_model_details(
        project_key: str,
        saved_model_id: str,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_get_saved_model_details",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.get_saved_model_details(project_key, saved_model_id)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_saved_model_details",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=saved_model_id,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_get_saved_model_details", "mode": ctx.settings.mode.value},
        )

    def dataiku_create_prediction_scoring_recipe(
        project_key: str,
        saved_model_id: str,
        input_dataset: str,
        recipe_name: str,
        output_dataset_name: str,
        output_connection: str | None = None,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_create_prediction_scoring_recipe(
                project_key,
                saved_model_id,
                input_dataset,
                recipe_name=recipe_name,
                output_dataset_name=output_dataset_name,
                output_connection=output_connection,
            )
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_create_prediction_scoring_recipe",
            level=PermissionLevel.WRITE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.create_prediction_scoring_recipe(
                project_key,
                saved_model_id,
                input_dataset,
                recipe_name=recipe_name,
                output_dataset_name=output_dataset_name,
                output_connection=output_connection,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_create_prediction_scoring_recipe",
            mode=ctx.settings.mode.value,
            operation_type="write",
            success=True,
            project_key=project_key,
            object_name=recipe_name,
        )
        return ok(
            {"dry_run_summary": dry_run_summary, **payload},
            metadata={
                "tool": "dataiku_create_prediction_scoring_recipe",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_list_model_evaluation_stores(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_list_model_evaluation_stores",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            {"evaluation_stores": ctx.dataiku.list_model_evaluation_stores(project_key)}
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_model_evaluation_stores",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_list_model_evaluation_stores",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_get_model_evaluation_store_details(
        project_key: str,
        evaluation_store_id: str,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_get_model_evaluation_store_details",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.get_model_evaluation_store_details(project_key, evaluation_store_id)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_model_evaluation_store_details",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=evaluation_store_id,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_get_model_evaluation_store_details",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_create_model_evaluation(
        project_key: str,
        saved_model_id: str,
        evaluation_dataset: str,
        evaluation_store_id: str | None = None,
        evaluation_store_name: str | None = None,
        recipe_name: str | None = None,
        scored_output_dataset: str | None = None,
        metrics_output_dataset: str | None = None,
        metrics: list[str] | None = None,
        run_immediately: bool = False,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_create_model_evaluation(
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
        )
        required_level = PermissionLevel.EXECUTE if run_immediately else PermissionLevel.WRITE
        require_approved_action(
            ctx,
            tool_name="dataiku_create_model_evaluation",
            level=required_level,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.create_model_evaluation(
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
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_create_model_evaluation",
            mode=ctx.settings.mode.value,
            operation_type="execute" if run_immediately else "write",
            success=True,
            project_key=project_key,
            object_name=recipe_name or saved_model_id,
        )
        return ok(
            {"dry_run_summary": dry_run_summary, **payload},
            metadata={"tool": "dataiku_create_model_evaluation", "mode": ctx.settings.mode.value},
        )

    def dataiku_compare_saved_models(
        project_key: str,
        saved_model_ids: list[str],
        metric_name: str | None = None,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_compare_saved_models",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.compare_saved_models(
                project_key,
                saved_model_ids,
                metric_name=metric_name,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_compare_saved_models",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=",".join(saved_model_ids),
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_compare_saved_models", "mode": ctx.settings.mode.value},
        )

    def dataiku_generate_model_evaluation_report(
        project_key: str,
        evaluation_store_id: str | None = None,
        saved_model_ids: list[str] | None = None,
        metric_name: str | None = None,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_generate_model_evaluation_report",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.generate_model_evaluation_report(
                project_key,
                evaluation_store_id=evaluation_store_id,
                saved_model_ids=saved_model_ids,
                metric_name=metric_name,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_generate_model_evaluation_report",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=evaluation_store_id or ",".join(saved_model_ids or []),
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_generate_model_evaluation_report",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_route_ml_intent(
        intent_text: str,
        default_project_key: str | None = None,
        default_dataset_name: str | None = None,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_route_ml_intent",
            level=PermissionLevel.READ,
            project_key=default_project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.route_ml_intent(
                intent_text,
                default_project_key=default_project_key,
                default_dataset_name=default_dataset_name,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_route_ml_intent",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=default_project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_route_ml_intent", "mode": ctx.settings.mode.value},
        )

    def dataiku_run_routed_ml_intent(
        intent_text: str,
        default_project_key: str | None = None,
        default_dataset_name: str | None = None,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        route_preview = ctx.redactor.redact(
            ctx.dataiku.route_ml_intent(
                intent_text,
                default_project_key=default_project_key,
                default_dataset_name=default_dataset_name,
            )
        )
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_run_routed_ml_intent(
                intent_text,
                default_project_key=default_project_key,
                default_dataset_name=default_dataset_name,
            )
        )
        route_intent_type = str(route_preview.get("intent_type"))
        required_level = (
            PermissionLevel.EXECUTE
            if route_intent_type == "train_latest_ml_task"
            else PermissionLevel.WRITE
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_run_routed_ml_intent",
            level=required_level,
            project_key=default_project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.run_routed_ml_intent(
                intent_text,
                default_project_key=default_project_key,
                default_dataset_name=default_dataset_name,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_run_routed_ml_intent",
            mode=ctx.settings.mode.value,
            operation_type="execute" if required_level == PermissionLevel.EXECUTE else "write",
            success=True,
            project_key=default_project_key,
        )
        return ok(
            {
                "route": route_preview,
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={"tool": "dataiku_run_routed_ml_intent", "mode": ctx.settings.mode.value},
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
    registry.register(
        "dataiku_list_saved_models",
        dataiku_list_saved_models,
        description="List saved models already deployed to the project Flow.",
    )
    registry.register(
        "dataiku_get_saved_model_details",
        dataiku_get_saved_model_details,
        description="Inspect one saved model and its active version metrics.",
    )
    registry.register(
        "dataiku_create_prediction_scoring_recipe",
        dataiku_create_prediction_scoring_recipe,
        description=(
            "Create a native prediction scoring recipe from a deployed saved "
            "model after explicit approval."
        ),
    )
    registry.register(
        "dataiku_list_model_evaluation_stores",
        dataiku_list_model_evaluation_stores,
        description="List model evaluation stores available in a project.",
    )
    registry.register(
        "dataiku_get_model_evaluation_store_details",
        dataiku_get_model_evaluation_store_details,
        description="Inspect one model evaluation store and its latest metrics.",
    )
    registry.register(
        "dataiku_create_model_evaluation",
        dataiku_create_model_evaluation,
        description=(
            "Create Dataiku-native evaluation assets for a saved model and "
            "optionally run the evaluation after explicit approval."
        ),
    )
    registry.register(
        "dataiku_compare_saved_models",
        dataiku_compare_saved_models,
        description="Compare multiple saved models using their active version metrics.",
    )
    registry.register(
        "dataiku_generate_model_evaluation_report",
        dataiku_generate_model_evaluation_report,
        description="Generate a saved model or evaluation store report without leaving Codex.",
    )
    registry.register(
        "dataiku_route_ml_intent",
        dataiku_route_ml_intent,
        description=(
            "Route a natural-language ML request to a reusable command instead "
            "of generating ad-hoc code."
        ),
    )
    registry.register(
        "dataiku_run_routed_ml_intent",
        dataiku_run_routed_ml_intent,
        description="Execute a routed ML intent after explicit approval.",
    )
