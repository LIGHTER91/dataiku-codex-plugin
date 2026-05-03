"""Permission enforcement for tool execution."""

from __future__ import annotations

from enum import Enum

from dataiku_codex_mcp.config import AppSettings, OperationMode
from dataiku_codex_mcp.errors import PermissionDeniedError


class PermissionLevel(str, Enum):
    """Permission levels supported by the tool layer."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    DANGEROUS = "dangerous"


class PermissionGuard:
    """Enforce mode, allowlist and approval rules."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def require(
        self,
        tool_name: str,
        *,
        level: PermissionLevel | str,
        project_key: str | None = None,
        approved: bool = False,
        approval_reason: str | None = None,
        enforce_approval: bool = True,
    ) -> None:
        normalized_level = PermissionLevel(level)

        if self.settings.tool_allowlist and tool_name not in self.settings.tool_allowlist:
            raise PermissionDeniedError(
                f"The tool {tool_name} is not in the configured tool allowlist.",
                details={"tool_name": tool_name},
                suggested_fix="Update DATAIKU_TOOL_ALLOWLIST or use an allowed tool.",
            )
        if tool_name in self.settings.tool_blocklist:
            raise PermissionDeniedError(
                f"The tool {tool_name} is blocked by configuration.",
                details={"tool_name": tool_name},
                suggested_fix="Remove the tool from DATAIKU_TOOL_BLOCKLIST if access is intended.",
            )
        if (
            project_key
            and self.settings.project_allowlist
            and project_key not in self.settings.project_allowlist
        ):
            raise PermissionDeniedError(
                f"Project {project_key} is outside the configured project allowlist.",
                details={"project_key": project_key},
                suggested_fix="Update DATAIKU_PROJECT_ALLOWLIST to include the project.",
            )
        if project_key and project_key in self.settings.project_blocklist:
            raise PermissionDeniedError(
                f"Project {project_key} is blocked by configuration.",
                details={"project_key": project_key},
                suggested_fix=(
                    "Remove the project from DATAIKU_PROJECT_BLOCKLIST if access "
                    "is intended."
                ),
            )

        if normalized_level is PermissionLevel.READ:
            return
        if normalized_level is PermissionLevel.DANGEROUS:
            raise PermissionDeniedError(
                f"The tool {tool_name} is marked as dangerous and is disabled by default.",
                details={"tool_name": tool_name, "required_level": normalized_level.value},
                suggested_fix=(
                    "Keep dangerous operations disabled unless a future hardened "
                    "flow enables them."
                ),
            )
        if normalized_level is PermissionLevel.WRITE:
            self._require_write(
                tool_name,
                approved=approved,
                approval_reason=approval_reason,
                enforce_approval=enforce_approval,
            )
            return
        if normalized_level is PermissionLevel.EXECUTE:
            self._require_execute(
                tool_name,
                approved=approved,
                approval_reason=approval_reason,
                enforce_approval=enforce_approval,
            )
            return
        if normalized_level is PermissionLevel.ADMIN:
            self._require_admin(tool_name)
            return

    def _require_write(
        self,
        tool_name: str,
        *,
        approved: bool,
        approval_reason: str | None,
        enforce_approval: bool,
    ) -> None:
        if self.settings.mode is not OperationMode.WRITE or not self.settings.enable_write_tools:
            raise PermissionDeniedError(
                f"The tool {tool_name} is not allowed in {self.settings.mode.value} mode.",
                details={
                    "mode": self.settings.mode.value,
                    "required_mode": OperationMode.WRITE.value,
                },
                suggested_fix="Set DATAIKU_MODE=write and DATAIKU_ENABLE_WRITE_TOOLS=true.",
            )
        if enforce_approval:
            self._require_approval(tool_name, approved=approved, approval_reason=approval_reason)

    def _require_execute(
        self,
        tool_name: str,
        *,
        approved: bool,
        approval_reason: str | None,
        enforce_approval: bool,
    ) -> None:
        if (
            self.settings.mode is not OperationMode.EXECUTE
            or not self.settings.enable_execute_tools
        ):
            raise PermissionDeniedError(
                f"The tool {tool_name} is not allowed in {self.settings.mode.value} mode.",
                details={
                    "mode": self.settings.mode.value,
                    "required_mode": OperationMode.EXECUTE.value,
                },
                suggested_fix="Set DATAIKU_MODE=execute and DATAIKU_ENABLE_EXECUTE_TOOLS=true.",
            )
        if enforce_approval:
            self._require_approval(tool_name, approved=approved, approval_reason=approval_reason)

    def _require_admin(self, tool_name: str) -> None:
        if self.settings.mode is not OperationMode.ADMIN or not self.settings.enable_admin_tools:
            raise PermissionDeniedError(
                f"The tool {tool_name} is not allowed in {self.settings.mode.value} mode.",
                details={
                    "mode": self.settings.mode.value,
                    "required_mode": OperationMode.ADMIN.value,
                },
                suggested_fix="Set DATAIKU_MODE=admin and DATAIKU_ENABLE_ADMIN_TOOLS=true.",
            )

    @staticmethod
    def _require_approval(
        tool_name: str,
        *,
        approved: bool,
        approval_reason: str | None,
    ) -> None:
        if approved and approval_reason:
            return
        raise PermissionDeniedError(
            f"The tool {tool_name} requires explicit approval.",
            details={"approved": approved},
            suggested_fix="Pass approved=true together with a non-empty approval_reason.",
        )
