"""Helpers for guarded write and execute tools."""

from __future__ import annotations

from typing import Any

from dataiku_codex_mcp.errors import PermissionDeniedError
from dataiku_codex_mcp.permissions import PermissionLevel


def require_approved_action(
    ctx: Any,
    *,
    tool_name: str,
    level: PermissionLevel,
    project_key: str | None,
    approved: bool,
    approval_reason: str | None,
    dry_run_summary: dict[str, Any],
) -> None:
    """Enforce mode/access first, then explicit approval with a dry-run summary."""

    ctx.permissions.require(
        tool_name,
        level=level,
        project_key=project_key,
        approved=approved,
        approval_reason=approval_reason,
        enforce_approval=False,
    )
    if approved and approval_reason:
        return
    raise PermissionDeniedError(
        f"The tool {tool_name} requires explicit approval.",
        details={
            "approved": approved,
            "dry_run_summary": dry_run_summary,
        },
        suggested_fix=(
            "Review the dry-run summary, then retry with approved=true and a non-empty "
            "approval_reason."
        ),
    )
