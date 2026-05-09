"""Operations and production-readiness tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register V4.0 ops tools."""

    def dataiku_list_plugin_usages(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_list_plugin_usages",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            {"plugin_usages": ctx.dataiku.list_plugin_usages(project_key)}
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_plugin_usages",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_list_plugin_usages", "mode": ctx.settings.mode.value},
        )

    def dataiku_generate_scenario_dependency_map(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_generate_scenario_dependency_map",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.generate_scenario_dependency_map(project_key)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_generate_scenario_dependency_map",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_generate_scenario_dependency_map",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_plan_code_env_updates(env_name: str | None = None) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_plan_code_env_updates",
            level=PermissionLevel.READ,
            project_key=None,
        )
        payload = ctx.redactor.redact(ctx.dataiku.plan_code_env_updates(env_name=env_name))
        ctx.audit.log_tool_call(
            tool_name="dataiku_plan_code_env_updates",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=None,
            object_name=env_name,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_plan_code_env_updates", "mode": ctx.settings.mode.value},
        )

    def dataiku_generate_production_readiness_report(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_generate_production_readiness_report",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.generate_production_readiness_report(project_key)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_generate_production_readiness_report",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_generate_production_readiness_report",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_generate_cost_performance_report(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_generate_cost_performance_report",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.generate_cost_performance_report(project_key)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_generate_cost_performance_report",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_generate_cost_performance_report",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_generate_production_readiness_checklist(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_generate_production_readiness_checklist",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.generate_production_readiness_checklist(project_key)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_generate_production_readiness_checklist",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_generate_production_readiness_checklist",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_generate_governance_documentation(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_generate_governance_documentation",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.generate_governance_documentation(project_key)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_generate_governance_documentation",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_generate_governance_documentation",
                "mode": ctx.settings.mode.value,
            },
        )

    registry.register(
        "dataiku_list_plugin_usages",
        dataiku_list_plugin_usages,
        description="List plugin usages reported by the Dataiku project.",
    )
    registry.register(
        "dataiku_generate_scenario_dependency_map",
        dataiku_generate_scenario_dependency_map,
        description="Generate a lightweight dependency map around project scenarios.",
    )
    registry.register(
        "dataiku_plan_code_env_updates",
        dataiku_plan_code_env_updates,
        description=(
            "Plan code environment dependency updates and prioritize the "
            "riskiest environments first."
        ),
    )
    registry.register(
        "dataiku_generate_production_readiness_report",
        dataiku_generate_production_readiness_report,
        description=(
            "Aggregate Flow, scenario, plugin and code env signals into a "
            "production-readiness report."
        ),
    )
    registry.register(
        "dataiku_generate_cost_performance_report",
        dataiku_generate_cost_performance_report,
        description="Estimate project cost and performance pressure from operational signals.",
    )
    registry.register(
        "dataiku_generate_production_readiness_checklist",
        dataiku_generate_production_readiness_checklist,
        description="Turn operational signals into a concrete production checklist.",
    )
    registry.register(
        "dataiku_generate_governance_documentation",
        dataiku_generate_governance_documentation,
        description="Generate governance-oriented markdown for project operations.",
    )
