"""Dataset-level tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register dataset-oriented tools."""

    def dataiku_list_datasets(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_list_datasets",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact({"datasets": ctx.dataiku.list_datasets(project_key)})
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_datasets",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_list_datasets", "mode": ctx.settings.mode.value},
        )

    def dataiku_get_dataset_schema(project_key: str, dataset_name: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_get_dataset_schema",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.get_dataset_schema(project_key, dataset_name)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_dataset_schema",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=dataset_name,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_get_dataset_schema", "mode": ctx.settings.mode.value},
        )

    registry.register(
        "dataiku_list_datasets",
        dataiku_list_datasets,
        description="List datasets in a project.",
    )
    registry.register(
        "dataiku_get_dataset_schema",
        dataiku_get_dataset_schema,
        description="Retrieve the schema of a dataset.",
    )
