"""Scenario and log tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel
from dataiku_codex_mcp.tools.write_safety import require_approved_action

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register scenario, run and log tools."""

    def dataiku_list_scenarios(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_list_scenarios",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            {"scenarios": ctx.dataiku.list_scenarios(project_key)}
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_scenarios",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_list_scenarios", "mode": ctx.settings.mode.value},
        )

    def dataiku_get_scenario_runs(
        project_key: str,
        scenario_id: str,
        limit: int = 10,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_get_scenario_runs",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.get_scenario_runs(project_key, scenario_id, limit=limit)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_scenario_runs",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=scenario_id,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_get_scenario_runs", "mode": ctx.settings.mode.value},
        )

    def dataiku_get_job_logs(
        project_key: str,
        job_id: str | None = None,
        run_id: str | None = None,
        scenario_id: str | None = None,
        max_lines: int | None = None,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_get_job_logs",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.get_job_logs(
                project_key,
                job_id=job_id,
                run_id=run_id,
                scenario_id=scenario_id,
                max_lines=max_lines,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_job_logs",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=job_id or run_id,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_get_job_logs", "mode": ctx.settings.mode.value},
        )

    def dataiku_explain_failure(
        project_key: str,
        job_id: str | None = None,
        run_id: str | None = None,
        scenario_id: str | None = None,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_explain_failure",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.explain_failure(
                project_key,
                job_id=job_id,
                run_id=run_id,
                scenario_id=scenario_id,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_explain_failure",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=job_id or run_id,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_explain_failure", "mode": ctx.settings.mode.value},
        )

    def dataiku_create_scenario(
        project_key: str,
        scenario_name: str,
        scenario_type: str = "custom_python",
        code: str | None = None,
        build_datasets: list[str] | None = None,
        active: bool = False,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_create_scenario(
                project_key,
                scenario_name,
                scenario_type=scenario_type,
                code=code,
                build_datasets=build_datasets,
                active=active,
            )
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_create_scenario",
            level=PermissionLevel.WRITE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.create_scenario(
                project_key,
                scenario_name,
                scenario_type=scenario_type,
                code=code,
                build_datasets=build_datasets,
                active=active,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_create_scenario",
            mode=ctx.settings.mode.value,
            operation_type="write",
            success=True,
            project_key=project_key,
            object_name=scenario_name,
        )
        return ok(
            {
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={"tool": "dataiku_create_scenario", "mode": ctx.settings.mode.value},
        )

    def dataiku_run_scenario(
        project_key: str,
        scenario_id: str,
        params: dict[str, object] | None = None,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_run_scenario(
                project_key,
                scenario_id,
                params=params,
            )
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_run_scenario",
            level=PermissionLevel.EXECUTE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.run_scenario(
                project_key,
                scenario_id,
                params=params,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_run_scenario",
            mode=ctx.settings.mode.value,
            operation_type="execute",
            success=True,
            project_key=project_key,
            object_name=scenario_id,
        )
        return ok(
            {
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={"tool": "dataiku_run_scenario", "mode": ctx.settings.mode.value},
        )

    registry.register(
        "dataiku_list_scenarios",
        dataiku_list_scenarios,
        description="List scenarios in a project.",
    )
    registry.register(
        "dataiku_get_scenario_runs",
        dataiku_get_scenario_runs,
        description="Get recent runs for a Dataiku scenario.",
    )
    registry.register(
        "dataiku_get_job_logs",
        dataiku_get_job_logs,
        description="Retrieve logs for a DSS job or scenario run.",
    )
    registry.register(
        "dataiku_explain_failure",
        dataiku_explain_failure,
        description="Explain the likely cause of a scenario run or job failure.",
    )
    registry.register(
        "dataiku_create_scenario",
        dataiku_create_scenario,
        description="Create a Dataiku scenario after explicit approval.",
    )
    registry.register(
        "dataiku_run_scenario",
        dataiku_run_scenario,
        description="Trigger a scenario run after explicit approval.",
    )
