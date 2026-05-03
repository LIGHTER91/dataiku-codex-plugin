"""Audit logging for tool execution."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from logging import Logger
from pathlib import Path
from typing import TYPE_CHECKING

from dataiku_codex_mcp.identity import IdentityResolver

if TYPE_CHECKING:
    from dataiku_codex_mcp.policy import PolicyEngine


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
    actor_subject: str | None = None
    actor_source: str | None = None
    actor_auth_mode: str | None = None
    actor_roles: tuple[str, ...] = ()
    actor_teams: tuple[str, ...] = ()
    request_id: str | None = None
    session_id: str | None = None
    client_id: str | None = None


class AuditLogger:
    """Emit metadata-only audit events."""

    def __init__(
        self,
        logger: Logger,
        *,
        identity_resolver: IdentityResolver,
        policy_engine: PolicyEngine | None = None,
        audit_log_path: str | None = None,
    ) -> None:
        self.logger = logger
        self.identity_resolver = identity_resolver
        self.policy_engine = policy_engine
        self.audit_log_path = Path(audit_log_path) if audit_log_path else None
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
        actor = self.identity_resolver.current_actor()
        effective_roles = (
            self.policy_engine.resolve_effective_roles(actor)
            if self.policy_engine is not None
            else actor.roles
        )
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool_name=tool_name,
            mode=mode,
            operation_type=operation_type,
            success=success,
            project_key=project_key,
            object_name=object_name,
            error_type=error_type,
            actor_subject=actor.subject,
            actor_source=actor.source,
            actor_auth_mode=actor.auth_mode,
            actor_roles=effective_roles,
            actor_teams=actor.teams,
            request_id=actor.request_id,
            session_id=actor.session_id,
            client_id=actor.client_id,
        )
        self.events.append(event)
        self.logger.info("audit_event %s", asdict(event))
        if self.audit_log_path is not None:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(asdict(event), sort_keys=True))
                handle.write("\n")
        return event
