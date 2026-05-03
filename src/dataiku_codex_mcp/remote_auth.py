"""Remote authentication providers for HTTP MCP transport."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from dataiku_codex_mcp.config import AppSettings, RemoteAuthMode
from dataiku_codex_mcp.errors import ConfigurationError


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value),)


class StaticBearerToken(BaseModel):
    """Single static bearer token definition."""

    token: str
    subject: str
    client_id: str | None = None
    roles: tuple[str, ...] = Field(default_factory=tuple)
    teams: tuple[str, ...] = Field(default_factory=tuple)
    scopes: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("roles", "teams", "scopes", mode="before")
    @classmethod
    def _coerce_collections(cls, value: Any) -> tuple[str, ...]:
        return _as_tuple(value)


def build_auth_provider(settings: AppSettings) -> Any | None:
    """Build a FastMCP auth provider for remote HTTP transport."""

    if settings.remote_auth_mode is RemoteAuthMode.NONE:
        return None

    if settings.remote_auth_mode is RemoteAuthMode.BEARER:
        return _StaticBearerTokenVerifier.from_settings(settings)

    try:
        from fastmcp.server.auth.providers.jwt import JWTVerifier
    except ModuleNotFoundError as exc:
        raise ConfigurationError(
            "JWT authentication requires FastMCP auth dependencies.",
            suggested_fix='Install project dependencies with `pip install -e ".[dev]"`.',
        ) from exc

    issuer = (
        list(settings.jwt_issuer)
        if isinstance(settings.jwt_issuer, tuple)
        else settings.jwt_issuer
    )
    audience = (
        list(settings.jwt_audience)
        if isinstance(settings.jwt_audience, tuple)
        else settings.jwt_audience
    )

    return JWTVerifier(
        public_key=settings.jwt_public_key,
        jwks_uri=settings.jwt_jwks_uri,
        issuer=issuer,
        audience=audience,
        algorithm=settings.jwt_algorithm,
        required_scopes=list(settings.auth_required_scopes),
        base_url=settings.public_base_url,
    )


class _StaticBearerTokenVerifier:
    """Simple static bearer verifier backed by JSON configuration."""

    def __init__(
        self,
        *,
        tokens: tuple[StaticBearerToken, ...],
        required_scopes: tuple[str, ...],
        base_url: str | None,
    ) -> None:
        try:
            from fastmcp.server.auth import TokenVerifier
        except ModuleNotFoundError as exc:
            raise ConfigurationError(
                "Bearer authentication requires FastMCP to be installed.",
                suggested_fix='Install project dependencies with `pip install -e ".[dev]"`.',
            ) from exc

        class StaticTokenVerifier(TokenVerifier):
            async def verify_token(self, token: str) -> Any | None:
                try:
                    from fastmcp.server.auth import AccessToken
                except ModuleNotFoundError:
                    return None

                for entry in tokens:
                    if not secrets.compare_digest(entry.token, token):
                        continue
                    if required_scopes and not set(required_scopes).issubset(entry.scopes):
                        return None
                    return AccessToken(
                        token=token,
                        client_id=entry.client_id or entry.subject,
                        scopes=list(entry.scopes),
                        claims={
                            "sub": entry.subject,
                            "roles": list(entry.roles),
                            "teams": list(entry.teams),
                            "scope": " ".join(entry.scopes),
                        },
                    )
                return None

        self.provider = StaticTokenVerifier(
            base_url=base_url,
            required_scopes=list(required_scopes),
        )

    @classmethod
    def from_settings(cls, settings: AppSettings) -> Any:
        return cls(
            tokens=_load_static_tokens(settings),
            required_scopes=settings.auth_required_scopes,
            base_url=settings.public_base_url,
        ).provider


def _load_static_tokens(settings: AppSettings) -> tuple[StaticBearerToken, ...]:
    payload: Any
    if settings.bearer_tokens_json is not None:
        payload = settings.bearer_tokens_json
    elif settings.bearer_tokens_file:
        path = Path(settings.bearer_tokens_file)
        if not path.exists():
            raise ConfigurationError(
                "The configured bearer token file does not exist.",
                details={"bearer_tokens_file": str(path)},
                suggested_fix="Create the token file or update DATAIKU_BEARER_TOKENS_FILE.",
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigurationError(
                "The configured bearer token file is not valid JSON.",
                details={"bearer_tokens_file": str(path)},
                suggested_fix="Fix the token JSON and rerun validate-config.",
            ) from exc
    else:
        payload = []

    if not isinstance(payload, list):
        raise ConfigurationError(
            "Bearer token configuration must be a JSON array.",
            suggested_fix="Use a JSON array of token entries for bearer authentication.",
        )

    try:
        return tuple(StaticBearerToken.model_validate(item) for item in payload)
    except ValidationError as exc:
        raise ConfigurationError(
            "Invalid bearer token configuration.",
            details={"errors": exc.errors(include_url=False)},
            suggested_fix="Fix the bearer token entries and rerun validate-config.",
        ) from exc
