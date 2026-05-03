"""Documentation generation tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel
from dataiku_codex_mcp.tools.write_safety import require_approved_action

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register markdown documentation tools."""

    def dataiku_generate_project_readme(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_generate_project_readme",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(ctx.dataiku.generate_project_readme(project_key))
        ctx.audit.log_tool_call(
            tool_name="dataiku_generate_project_readme",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_generate_project_readme",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_generate_flow_documentation(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_generate_flow_documentation",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.generate_flow_documentation(project_key)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_generate_flow_documentation",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_generate_flow_documentation",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_generate_troubleshooting_report(
        project_key: str,
        focus: str | None = None,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_generate_troubleshooting_report",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.generate_troubleshooting_report(project_key, focus=focus)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_generate_troubleshooting_report",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=focus,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_generate_troubleshooting_report",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_generate_rag_audit_report(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_generate_rag_audit_report",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(ctx.dataiku.generate_rag_audit_report(project_key))
        ctx.audit.log_tool_call(
            tool_name="dataiku_generate_rag_audit_report",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_generate_rag_audit_report",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_create_project_documentation(
        project_key: str,
        target: str,
        markdown: str,
        overwrite: bool = False,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_create_project_documentation(
                project_key,
                target=target,
                markdown=markdown,
                overwrite=overwrite,
            )
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_create_project_documentation",
            level=PermissionLevel.WRITE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.create_project_documentation(
                project_key,
                target=target,
                markdown=markdown,
                overwrite=overwrite,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_create_project_documentation",
            mode=ctx.settings.mode.value,
            operation_type="write",
            success=True,
            project_key=project_key,
            object_name=target,
        )
        return ok(
            {
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={
                "tool": "dataiku_create_project_documentation",
                "mode": ctx.settings.mode.value,
            },
        )

    registry.register(
        "dataiku_generate_project_readme",
        dataiku_generate_project_readme,
        description="Generate a README-style markdown summary for a project.",
    )
    registry.register(
        "dataiku_generate_flow_documentation",
        dataiku_generate_flow_documentation,
        description="Generate markdown documentation for the project Flow.",
    )
    registry.register(
        "dataiku_generate_troubleshooting_report",
        dataiku_generate_troubleshooting_report,
        description="Generate a markdown troubleshooting report for the project.",
    )
    registry.register(
        "dataiku_generate_rag_audit_report",
        dataiku_generate_rag_audit_report,
        description="Generate a markdown RAG audit report for the project.",
    )
    registry.register(
        "dataiku_create_project_documentation",
        dataiku_create_project_documentation,
        description="Write generated markdown into the project after approval.",
    )
