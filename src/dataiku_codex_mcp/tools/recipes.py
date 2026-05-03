"""Recipe-level tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel
from dataiku_codex_mcp.tools.write_safety import require_approved_action

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register recipe-oriented tools."""

    def dataiku_list_recipes(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_list_recipes",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact({"recipes": ctx.dataiku.list_recipes(project_key)})
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_recipes",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_list_recipes", "mode": ctx.settings.mode.value},
        )

    def dataiku_get_recipe_details(project_key: str, recipe_name: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_get_recipe_details",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.get_recipe_details(project_key, recipe_name)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_recipe_details",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=recipe_name,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_get_recipe_details", "mode": ctx.settings.mode.value},
        )

    def dataiku_review_recipe_code(project_key: str, recipe_name: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_review_recipe_code",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.review_recipe_code(project_key, recipe_name)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_review_recipe_code",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=recipe_name,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_review_recipe_code", "mode": ctx.settings.mode.value},
        )

    def dataiku_update_recipe_code(
        project_key: str,
        recipe_name: str,
        new_code: str,
        reason: str,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_update_recipe_code(
                project_key,
                recipe_name,
                new_code=new_code,
                reason=reason,
            )
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_update_recipe_code",
            level=PermissionLevel.WRITE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.update_recipe_code(
                project_key,
                recipe_name,
                new_code=new_code,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_update_recipe_code",
            mode=ctx.settings.mode.value,
            operation_type="write",
            success=True,
            project_key=project_key,
            object_name=recipe_name,
        )
        return ok(
            {
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={"tool": "dataiku_update_recipe_code", "mode": ctx.settings.mode.value},
        )

    def dataiku_create_python_recipe(
        project_key: str,
        recipe_name: str,
        inputs: list[str],
        outputs: list[str],
        code: str,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_create_python_recipe(
                project_key,
                recipe_name,
                inputs=inputs,
                outputs=outputs,
                code=code,
            )
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_create_python_recipe",
            level=PermissionLevel.WRITE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.create_python_recipe(
                project_key,
                recipe_name,
                inputs=inputs,
                outputs=outputs,
                code=code,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_create_python_recipe",
            mode=ctx.settings.mode.value,
            operation_type="write",
            success=True,
            project_key=project_key,
            object_name=recipe_name,
        )
        return ok(
            {
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={"tool": "dataiku_create_python_recipe", "mode": ctx.settings.mode.value},
        )

    registry.register(
        "dataiku_list_recipes",
        dataiku_list_recipes,
        description="List recipes in a project.",
    )
    registry.register(
        "dataiku_get_recipe_details",
        dataiku_get_recipe_details,
        description="Retrieve recipe settings and code.",
    )
    registry.register(
        "dataiku_review_recipe_code",
        dataiku_review_recipe_code,
        description="Review recipe code for Dataiku-specific issues.",
    )
    registry.register(
        "dataiku_update_recipe_code",
        dataiku_update_recipe_code,
        description="Update the code of an existing recipe after approval.",
    )
    registry.register(
        "dataiku_create_python_recipe",
        dataiku_create_python_recipe,
        description="Create a new Python recipe after approval.",
    )
