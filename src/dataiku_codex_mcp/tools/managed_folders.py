"""Managed Folder tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel
from dataiku_codex_mcp.tools.write_safety import require_approved_action

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register Managed Folder tools."""

    def dataiku_list_managed_folders(project_key: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_list_managed_folders",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            {"folders": ctx.dataiku.list_managed_folders(project_key)}
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_managed_folders",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_list_managed_folders", "mode": ctx.settings.mode.value},
        )

    def dataiku_get_managed_folder_info(project_key: str, folder_id: str) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_get_managed_folder_info",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.get_managed_folder_info(project_key, folder_id)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_get_managed_folder_info",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=folder_id,
        )
        return ok(
            payload,
            metadata={
                "tool": "dataiku_get_managed_folder_info",
                "mode": ctx.settings.mode.value,
            },
        )

    def dataiku_list_folder_files(
        project_key: str,
        folder_id: str,
        path: str = "/",
        recursive: bool = False,
        limit: int = 100,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_list_folder_files",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.list_folder_files(
                project_key,
                folder_id,
                path=path,
                recursive=recursive,
                limit=limit,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_list_folder_files",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=folder_id,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_list_folder_files", "mode": ctx.settings.mode.value},
        )

    def dataiku_managed_folder_doctor(
        project_key: str,
        folder_id: str | None = None,
    ) -> dict[str, object]:
        ctx.permissions.require(
            "dataiku_managed_folder_doctor",
            level=PermissionLevel.READ,
            project_key=project_key,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.managed_folder_doctor(project_key, folder_id=folder_id)
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_managed_folder_doctor",
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=folder_id,
        )
        return ok(
            payload,
            metadata={"tool": "dataiku_managed_folder_doctor", "mode": ctx.settings.mode.value},
        )

    def dataiku_create_managed_folder(
        project_key: str,
        folder_name: str,
        connection: str | None = None,
        folder_type: str | None = None,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_create_managed_folder(
                project_key,
                folder_name,
                connection=connection,
                folder_type=folder_type,
            )
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_create_managed_folder",
            level=PermissionLevel.WRITE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.create_managed_folder(
                project_key,
                folder_name,
                connection=connection,
                folder_type=folder_type,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_create_managed_folder",
            mode=ctx.settings.mode.value,
            operation_type="write",
            success=True,
            project_key=project_key,
            object_name=folder_name,
        )
        return ok(
            {
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={"tool": "dataiku_create_managed_folder", "mode": ctx.settings.mode.value},
        )

    def dataiku_upload_file_to_folder(
        project_key: str,
        folder_id: str,
        file_path: str,
        content_base64: str,
        overwrite: bool = False,
        approved: bool = False,
        approval_reason: str | None = None,
    ) -> dict[str, object]:
        dry_run_summary = ctx.redactor.redact(
            ctx.dataiku.preview_upload_file_to_folder(
                project_key,
                folder_id,
                file_path=file_path,
                content_base64=content_base64,
                overwrite=overwrite,
            )
        )
        require_approved_action(
            ctx,
            tool_name="dataiku_upload_file_to_folder",
            level=PermissionLevel.WRITE,
            project_key=project_key,
            approved=approved,
            approval_reason=approval_reason,
            dry_run_summary=dry_run_summary,
        )
        payload = ctx.redactor.redact(
            ctx.dataiku.upload_file_to_folder(
                project_key,
                folder_id,
                file_path=file_path,
                content_base64=content_base64,
                overwrite=overwrite,
            )
        )
        ctx.audit.log_tool_call(
            tool_name="dataiku_upload_file_to_folder",
            mode=ctx.settings.mode.value,
            operation_type="write",
            success=True,
            project_key=project_key,
            object_name=f"{folder_id}:{file_path}",
        )
        return ok(
            {
                "dry_run_summary": dry_run_summary,
                **payload,
            },
            metadata={"tool": "dataiku_upload_file_to_folder", "mode": ctx.settings.mode.value},
        )

    registry.register(
        "dataiku_list_managed_folders",
        dataiku_list_managed_folders,
        description="List Managed Folders in a project.",
    )
    registry.register(
        "dataiku_get_managed_folder_info",
        dataiku_get_managed_folder_info,
        description="Retrieve Managed Folder metadata.",
    )
    registry.register(
        "dataiku_list_folder_files",
        dataiku_list_folder_files,
        description="List files in a Managed Folder.",
    )
    registry.register(
        "dataiku_managed_folder_doctor",
        dataiku_managed_folder_doctor,
        description="Detect common Managed Folder issues.",
    )
    registry.register(
        "dataiku_create_managed_folder",
        dataiku_create_managed_folder,
        description="Create a Managed Folder after approval.",
    )
    registry.register(
        "dataiku_upload_file_to_folder",
        dataiku_upload_file_to_folder,
        description="Upload a file into a Managed Folder after approval.",
    )
