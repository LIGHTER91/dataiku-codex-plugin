"""Audit logging for tool execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from logging import Logger


@dataclass(frozen=True)
class AuditEvent:
    """Minimal metadata-only audit event."""

    timestamp: str
    tool_name: str
    mode: str
    operation_type: str
    success: bool
    project_key: str | None = None
    object_name: str | None = None
    error_type: str | None = None


class AuditLogger:
    """Emit metadata-only audit events."""

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.events: list[AuditEvent] = []

    def log_tool_call(
        self,
        *,
        tool_name: str,
        mode: str,
        operation_type: str,
        success: bool,
        project_key: str | None = None,
        object_name: str | None = None,
        error_type: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool_name=tool_name,
            mode=mode,
            operation_type=operation_type,
            success=success,
            project_key=project_key,
            object_name=object_name,
            error_type=error_type,
        )
        self.events.append(event)
        self.logger.info("audit_event %s", asdict(event))
        return event
