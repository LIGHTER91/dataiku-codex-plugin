from __future__ import annotations

import pytest

from dataiku_codex_mcp.config import OperationMode, load_settings
from dataiku_codex_mcp.errors import ConfigurationError


def test_load_settings_uses_safe_defaults() -> None:
    settings = load_settings(
        env={
            "DATAIKU_DSS_URL": "https://dss.example.com",
            "DATAIKU_API_KEY": "top-secret",
        }
    )

    assert settings.mode is OperationMode.READONLY
    assert settings.redact_secrets is True
    assert settings.enable_write_tools is False
    assert settings.max_preview_rows == 20


def test_load_settings_parses_lists_and_booleans() -> None:
    settings = load_settings(
        env={
            "DATAIKU_DSS_URL": "https://dss.example.com",
            "DATAIKU_API_KEY": "top-secret",
            "DATAIKU_MODE": "write",
            "DATAIKU_PROJECT_ALLOWLIST": "A,B",
            "DATAIKU_TOOL_BLOCKLIST": "dataiku_preview_dataset",
            "DATAIKU_ENABLE_WRITE_TOOLS": "true",
        }
    )

    assert settings.mode is OperationMode.WRITE
    assert settings.project_allowlist == ("A", "B")
    assert settings.tool_blocklist == ("dataiku_preview_dataset",)
    assert settings.enable_write_tools is True


def test_load_settings_requires_core_env_values() -> None:
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(env={}, dotenv_path="tests/fixtures/does-not-exist.env")

    assert exc_info.value.details["missing"] == ["DATAIKU_DSS_URL", "DATAIKU_API_KEY"]


def test_load_settings_rejects_invalid_mode() -> None:
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(
            env={
                "DATAIKU_DSS_URL": "https://dss.example.com",
                "DATAIKU_API_KEY": "top-secret",
                "DATAIKU_MODE": "banana",
            }
        )

    assert exc_info.value.error_type == "ConfigurationError"


def test_public_settings_redacts_api_key() -> None:
    settings = load_settings(
        env={
            "DATAIKU_DSS_URL": "https://dss.example.com",
            "DATAIKU_API_KEY": "top-secret",
        }
    )

    assert settings.public_settings()["api_key"] == "[REDACTED]"
