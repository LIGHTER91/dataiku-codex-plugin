"""RAG analysis tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register RAG-oriented audit tools."""

    def dataiku_detect_rag_pipeline(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_detect_rag_pipeline",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(ctx.dataiku.detect_rag_pipeline(project_key))
        ctx.audit.log_tool_call(
            tool_name="dataiku_detect_rag_pipeline",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_detect_rag_pipeline", "mode": ctx.settings.mode.value},
        )

    def dataiku_audit_rag_pipeline(project_key: str, deep: bool = False) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_audit_rag_pipeline",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.audit_rag_pipeline(project_key, deep=deep)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_audit_rag_pipeline",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_audit_rag_pipeline", "mode": ctx.settings.mode.value},
        )

    registry.register(
        "dataiku_detect_rag_pipeline",
        dataiku_detect_rag_pipeline,
        description="Detect whether a project contains a RAG pipeline.",
    )
    registry.register(
        "dataiku_audit_rag_pipeline",
        dataiku_audit_rag_pipeline,
        description="Audit RAG design and implementation risks.",
    )
