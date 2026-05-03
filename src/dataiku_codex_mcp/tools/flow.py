"""Flow analysis tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register Flow-oriented analysis tools."""

    def dataiku_generate_project_map(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_generate_project_map",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(ctx.dataiku.generate_project_map(project_key))
        ctx.audit.log_tool_call(
            tool_name="dataiku_generate_project_map",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_generate_project_map", "mode": ctx.settings.mode.value},
        )

    def dataiku_get_flow_graph(
        project_key: str,
        include_recipes: bool = True,
        include_folders: bool = True,
        include_models: bool = True,
        include_zones: bool = True,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_get_flow_graph",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.get_flow_graph(
                project_key,
                include_recipes=include_recipes,
                include_folders=include_folders,
                include_models=include_models,
                include_zones=include_zones,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_flow_graph",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_get_flow_graph", "mode": ctx.settings.mode.value},
        )

    def dataiku_analyze_flow_health(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_analyze_flow_health",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(ctx.dataiku.analyze_flow_health(project_key))
        ctx.audit.log_tool_call(
            tool_name="dataiku_analyze_flow_health",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_analyze_flow_health", "mode": ctx.settings.mode.value},
        )

    registry.register(
        "dataiku_generate_project_map",
        dataiku_generate_project_map,
        description="Generate a high-level project map.",
    )
    registry.register(
        "dataiku_get_flow_graph",
        dataiku_get_flow_graph,
        description="Return the dependency graph of the project Flow.",
    )
    registry.register(
        "dataiku_analyze_flow_health",
        dataiku_analyze_flow_health,
        description="Analyze the Flow for structural issues.",
    )
