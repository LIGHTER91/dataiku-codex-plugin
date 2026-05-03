from __future__ import annotations

import pytest

from dataiku_codex_mcp.config import AppSettings, OperationMode
from dataiku_codex_mcp.errors import PermissionDeniedError
from dataiku_codex_mcp.permissions import PermissionGuard, PermissionLevel


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


def test_read_is_allowed_in_readonly_mode() -> None:
    guard = PermissionGuard(_settings())
    guard.require("dataiku_ping", level=PermissionLevel.READ)


def test_write_is_blocked_in_readonly_mode() -> None:
    guard = PermissionGuard(_settings())

    with pytest.raises(PermissionDeniedError):
        guard.require(
            "dataiku_update_recipe_code",
            level=PermissionLevel.WRITE,
            approved=True,
            approval_reason="approved",
        )


def test_write_requires_approval() -> None:
    guard = PermissionGuard(
        _settings(mode=OperationMode.WRITE, enable_write_tools=True)
    )

    with pytest.raises(PermissionDeniedError):
        guard.require("dataiku_update_recipe_code", level=PermissionLevel.WRITE)


def test_blocked_project_is_rejected() -> None:
    guard = PermissionGuard(_settings(project_blocklist=("SECRET_PROJECT",)))

    with pytest.raises(PermissionDeniedError):
        guard.require(
            "dataiku_get_project_summary",
            level=PermissionLevel.READ,
            project_key="SECRET_PROJECT",
        )


def test_blocked_tool_is_rejected() -> None:
    guard = PermissionGuard(_settings(tool_blocklist=("dataiku_ping",)))

    with pytest.raises(PermissionDeniedError):
        guard.require("dataiku_ping", level=PermissionLevel.READ)


def test_write_allowed_with_mode_flag_and_approval() -> None:
    guard = PermissionGuard(
        _settings(mode=OperationMode.WRITE, enable_write_tools=True)
    )

    guard.require(
        "dataiku_update_recipe_code",
        level=PermissionLevel.WRITE,
        approved=True,
        approval_reason="user explicitly approved this change",
    )
