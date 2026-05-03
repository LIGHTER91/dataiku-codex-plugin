"""Identity resolution for local and remote tool calls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from dataiku_codex_mcp.config import AppSettings


def _coerce_claim_values(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        if "," in value:
            return tuple(part.strip() for part in value.split(",") if part.strip())
        if " " in value:
            return tuple(part.strip() for part in value.split(" ") if part.strip())
        return (value,) if value.strip() else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value),)


@dataclass(frozen=True)
class ActorContext:
    """Caller identity as seen by policy, permissions and audit."""

    subject: str
    source: str
    auth_mode: str
    authenticated: bool
    roles: tuple[str, ...]
    teams: tuple[str, ...]
    scopes: tuple[str, ...]
    client_id: str | None = None
    request_id: str | None = None
    session_id: str | None = None

    def public(self) -> dict[str, Any]:
        """Return a JSON-safe representation for logs or error details."""

        return asdict(self)


class IdentityResolver:
    """Resolve the current caller identity from FastMCP or local CLI context."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def current_actor(self) -> ActorContext:
        """Resolve the current actor, falling back to a trusted local operator."""

        access_token = self._try_get_access_token()
        request_context = self._try_get_request_context()
        if access_token is None:
            return ActorContext(
                subject=self.settings.local_actor_subject,
                source="local",
                auth_mode="local",
                authenticated=True,
                roles=self.settings.local_actor_roles,
                teams=(),
                scopes=(),
                client_id=getattr(request_context, "client_id", None),
                request_id=getattr(request_context, "request_id", None),
                session_id=getattr(request_context, "session_id", None),
            )

        claims = dict(access_token.claims)
        subject = str(
            claims.get(self.settings.auth_subject_claim)
            or claims.get("sub")
            or access_token.client_id
        )
        return ActorContext(
            subject=subject,
            source="remote",
            auth_mode=self.settings.remote_auth_mode.value,
            authenticated=True,
            roles=_coerce_claim_values(claims.get(self.settings.auth_role_claim)),
            teams=_coerce_claim_values(claims.get(self.settings.auth_team_claim)),
            scopes=tuple(access_token.scopes),
            client_id=access_token.client_id,
            request_id=getattr(request_context, "request_id", None),
            session_id=getattr(request_context, "session_id", None),
        )

    @staticmethod
    def _try_get_access_token() -> Any | None:
        try:
            from fastmcp.server.dependencies import get_access_token
        except ModuleNotFoundError:
            return None

        try:
            return get_access_token()
        except RuntimeError:
            return None

    @staticmethod
    def _try_get_request_context() -> Any | None:
        try:
            from fastmcp.server.dependencies import get_context
        except ModuleNotFoundError:
            return None

        try:
            context = get_context()
        except RuntimeError:
            return None

        try:
            request_context = context.request_context
        except RuntimeError:
            return None
        if request_context is None:
            return None

        client_id = getattr(request_context.meta, "client_id", None)
        session_id: str | None
        try:
            session_id = context.session_id
        except RuntimeError:
            session_id = None

        return type(
            "RequestContextInfo",
            (),
            {
                "client_id": client_id,
                "request_id": str(request_context.request_id),
                "session_id": session_id,
            },
        )()
