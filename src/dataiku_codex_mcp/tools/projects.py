"""Project-level tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register project-oriented tools."""

    def dataiku_list_projects(include_archived: bool = False) -> dict[str, object]:
        ctx.permissions.require("dataiku_list_projects", level=PermissionLevel.READ)
        projects = ctx.redactor.redact(
            {"projects": ctx.dataiku.list_projects(include_archived=include_archived)}
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_projects",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
        )
        return ok(
            projects,
            metadata={"tool": "dataiku_list_projects", "mode": ctx.settings.mode.value},
        )

    def dataiku_get_project_summary(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_get_project_summary",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(ctx.dataiku.get_project_summary(project_key))
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_project_summary",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_get_project_summary", "mode": ctx.settings.mode.value},
        )

    registry.register(
        "dataiku_list_projects",
        dataiku_list_projects,
        description="List accessible Dataiku projects.",
    )
    registry.register(
        "dataiku_get_project_summary",
        dataiku_get_project_summary,
        description="Get detailed project metadata and object counts.",
    )
