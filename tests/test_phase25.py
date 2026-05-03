from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from dataiku_codex_mcp.audit import AuditLogger
from dataiku_codex_mcp.config import (
    AppSettings,
    OperationMode,
    RemoteAuthMode,
    ServerTransport,
    load_settings,
)
from dataiku_codex_mcp.identity import ActorContext
from dataiku_codex_mcp.logging_utils import get_logger
from dataiku_codex_mcp.permissions import PermissionDeniedError, PermissionGuard, PermissionLevel
from dataiku_codex_mcp.policy import PolicyEngine
from dataiku_codex_mcp.remote_auth import build_auth_provider
from dataiku_codex_mcp.server import main


class _StaticIdentityResolver:
    def __init__(self, actor: ActorContext) -> None:
        self.actor = actor

    def current_actor(self) -> ActorContext:
        return self.actor


def _settings(**overrides: object) -> AppSettings:
    payload: dict[str, object] = {
        "dss_url": "https://dss.example.com",
        "api_key": "top-secret",
        "mode": OperationMode.READONLY,
        "enable_write_tools": False,
        "enable_execute_tools": False,
        "enable_admin_tools": False,
    }
    payload.update(overrides)
    return AppSettings(**payload)  # type: ignore[arg-type]


def test_load_settings_parses_http_auth_and_policy_json() -> None:
    settings = load_settings(
        env={
            "DATAIKU_DSS_URL": "https://dss.example.com",
            "DATAIKU_API_KEY": "top-secret",
            "DATAIKU_TRANSPORT": "http",
            "DATAIKU_HTTP_PORT": "9100",
            "DATAIKU_HTTP_PATH": "secure-mcp",
            "DATAIKU_REMOTE_AUTH_MODE": "bearer",
            "DATAIKU_BEARER_TOKENS_JSON": json.dumps(
                [
                    {
                        "token": "abc123",
                        "subject": "alice",
                        "roles": ["reader"],
                        "teams": ["data-platform"],
                        "scopes": ["mcp:read"],
                    }
                ]
            ),
            "DATAIKU_POLICY_JSON": json.dumps(
                {
                    "tool_role_bindings": {"dataiku_run_scenario": ["operator"]},
                    "default_decision": "allow",
                }
            ),
        }
    )

    assert settings.transport is ServerTransport.HTTP
    assert settings.http_port == 9100
    assert settings.http_path == "/secure-mcp"
    assert settings.remote_auth_mode is RemoteAuthMode.BEARER
    assert settings.bearer_tokens_json is not None
    assert settings.policy_json is not None


def test_static_bearer_auth_provider_verifies_token() -> None:
    settings = _settings(
        remote_auth_mode=RemoteAuthMode.BEARER,
        bearer_tokens_json=[
            {
                "token": "secret-token",
                "subject": "alice@example.com",
                "client_id": "alice-cli",
                "roles": ["reader", "writer"],
                "teams": ["data-platform"],
                "scopes": ["mcp:read", "mcp:write"],
            }
        ],
    )

    provider = build_auth_provider(settings)
    token = asyncio.run(provider.verify_token("secret-token"))

    assert token is not None
    assert token.client_id == "alice-cli"
    assert token.claims["sub"] == "alice@example.com"
    assert token.claims["roles"] == ["reader", "writer"]


def test_permission_guard_applies_tool_role_bindings() -> None:
    settings = _settings(
        mode=OperationMode.EXECUTE,
        enable_execute_tools=True,
        policy_json={"tool_role_bindings": {"dataiku_run_scenario": ["operator"]}},
    )
    actor = ActorContext(
        subject="alice",
        source="remote",
        auth_mode="bearer",
        authenticated=True,
        roles=("reader",),
        teams=("data-platform",),
        scopes=("mcp:execute",),
    )
    guard = PermissionGuard(
        settings,
        identity_resolver=_StaticIdentityResolver(actor),
        policy_engine=PolicyEngine(settings),
    )

    with pytest.raises(PermissionDeniedError) as exc_info:
        guard.require(
            "dataiku_run_scenario",
            level=PermissionLevel.EXECUTE,
            approved=True,
            approval_reason="approved",
        )

    assert exc_info.value.details["policy"]["source"] == "tool_role_binding"


def test_permission_guard_applies_team_allowlist_to_remote_callers() -> None:
    settings = _settings(team_allowlist=("trusted-team",))
    actor = ActorContext(
        subject="alice",
        source="remote",
        auth_mode="bearer",
        authenticated=True,
        roles=("reader",),
        teams=("other-team",),
        scopes=("mcp:read",),
    )
    guard = PermissionGuard(
        settings,
        identity_resolver=_StaticIdentityResolver(actor),
        policy_engine=PolicyEngine(settings),
    )

    with pytest.raises(PermissionDeniedError) as exc_info:
        guard.require("dataiku_ping", level=PermissionLevel.READ)

    assert exc_info.value.details["policy"]["source"] == "team_allowlist"


def test_audit_logger_writes_jsonl() -> None:
    actor = ActorContext(
        subject="alice",
        source="remote",
        auth_mode="bearer",
        authenticated=True,
        roles=("reader",),
        teams=("data-platform",),
        scopes=("mcp:read",),
        client_id="alice-cli",
    )
    path = Path("tests/.audit-test.jsonl")
    if path.exists():
        path.unlink()
    settings = _settings(audit_log_path=str(path))
    logger = AuditLogger(
        get_logger("audit-test", debug=True),
        identity_resolver=_StaticIdentityResolver(actor),
        policy_engine=PolicyEngine(settings),
        audit_log_path=str(path),
    )

    logger.log_tool_call(
        tool_name="dataiku_ping",
        mode="readonly",
        operation_type="read",
        success=True,
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["actor_subject"] == "alice"
    assert payload["client_id"] == "alice-cli"
    path.unlink()


def test_serve_http_command_uses_runner(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}

    def fake_run_http_server(
        ctx: object,
        *,
        host: str | None = None,
        port: int | None = None,
        path: str | None = None,
    ) -> None:
        observed["ctx"] = ctx
        observed["host"] = host
        observed["port"] = port
        observed["path"] = path

    monkeypatch.setattr("dataiku_codex_mcp.server.run_http_server", fake_run_http_server)

    exit_code = main(
        [
            "--env-file",
            "examples/sample_env.example",
            "serve-http",
            "--host",
            "127.0.0.1",
            "--port",
            "9100",
            "--path",
            "/secure-mcp",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert observed["host"] == "127.0.0.1"
    assert observed["port"] == 9100
    assert observed["path"] == "/secure-mcp"
    assert payload["data"]["transport"] == "http"
