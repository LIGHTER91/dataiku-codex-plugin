"""Code environment tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register code environment tools."""

    def dataiku_list_code_envs() -> dict[str, object]:
        ctx.permissions.require("dataiku_list_code_envs", level=PermissionLevel.READ)
        payload = ctx.redactor.redact({"code_envs": ctx.dataiku.list_code_envs()})
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_code_envs",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_list_code_envs", "mode": ctx.settings.mode.value},
        )

    def dataiku_get_code_env_details(env_name: str) -> dict[str, object]:
        ctx.permissions.require("dataiku_get_code_env_details", level=PermissionLevel.READ)
        payload = ctx.redactor.redact(ctx.dataiku.get_code_env_details(env_name))
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_code_env_details",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            object_name=env_name,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_get_code_env_details", "mode": ctx.settings.mode.value},
        )

    def dataiku_code_env_doctor(env_name: str) -> dict[str, object]:
        ctx.permissions.require("dataiku_code_env_doctor", level=PermissionLevel.READ)
        payload = ctx.redactor.redact(ctx.dataiku.code_env_doctor(env_name))
        ctx.audit.log_tool_call(
            tool_name="dataiku_code_env_doctor",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            object_name=env_name,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_code_env_doctor", "mode": ctx.settings.mode.value},
        )

    registry.register(
        "dataiku_list_code_envs",
        dataiku_list_code_envs,
        description="List Dataiku code environments when accessible.",
    )
    registry.register(
        "dataiku_get_code_env_details",
        dataiku_get_code_env_details,
        description="Retrieve code environment settings and packages.",
    )
    registry.register(
        "dataiku_code_env_doctor",
        dataiku_code_env_doctor,
        description="Analyze code environment issues.",
    )
