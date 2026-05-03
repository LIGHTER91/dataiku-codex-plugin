"""Instance-level tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register instance-oriented tools."""

    def dataiku_ping() -> dict[str, object]:
        ctx.permissions.require("dataiku_ping", level=PermissionLevel.READ)
        payload = ctx.redactor.redact(ctx.dataiku.ping())
        ctx.audit.log_tool_call(
            tool_name="dataiku_ping",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_ping", "mode": ctx.settings.mode.value},
        )

    def dataiku_get_instance_info() -> dict[str, object]:
        ctx.permissions.require("dataiku_get_instance_info", level=PermissionLevel.READ)
        payload = ctx.redactor.redact(ctx.dataiku.get_instance_info())
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_instance_info",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_get_instance_info", "mode": ctx.settings.mode.value},
        )

    registry.register(
        "dataiku_ping",
        dataiku_ping,
        description="Check if the DSS instance is reachable.",
    )
    registry.register(
        "dataiku_get_instance_info",
        dataiku_get_instance_info,
        description="Retrieve high-level instance metadata.",
    )
