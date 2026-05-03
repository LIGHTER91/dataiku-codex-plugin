"""Application configuration loading and validation."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, SecretStr, ValidationError

from dataiku_codex_mcp.errors import ConfigurationError


class OperationMode(str, Enum):
    """Supported execution modes."""

    READONLY = "readonly"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


_ENV_FIELD_MAP = {
    "DATAIKU_DSS_URL": "dss_url",
    "DATAIKU_API_KEY": "api_key",
    "DATAIKU_DEFAULT_PROJECT": "default_project",
    "DATAIKU_PROJECT_ALLOWLIST": "project_allowlist",
    "DATAIKU_PROJECT_BLOCKLIST": "project_blocklist",
    "DATAIKU_TOOL_ALLOWLIST": "tool_allowlist",
    "DATAIKU_TOOL_BLOCKLIST": "tool_blocklist",
    "DATAIKU_MODE": "mode",
    "DATAIKU_MAX_PREVIEW_ROWS": "max_preview_rows",
    "DATAIKU_MAX_FILE_READ_BYTES": "max_file_read_bytes",
    "DATAIKU_MAX_LOG_LINES": "max_log_lines",
    "DATAIKU_MAX_LISTED_FILES": "max_listed_files",
    "DATAIKU_REDACT_SECRETS": "redact_secrets",
    "DATAIKU_ENABLE_WRITE_TOOLS": "enable_write_tools",
    "DATAIKU_ENABLE_EXECUTE_TOOLS": "enable_execute_tools",
    "DATAIKU_ENABLE_ADMIN_TOOLS": "enable_admin_tools",
    "DATAIKU_DEBUG": "debug",
}


def _parse_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    raise ConfigurationError(
        f"Invalid boolean value: {value!r}.",
        suggested_fix="Use one of true/false, yes/no, on/off or 1/0.",
    )


def _parse_csv_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return tuple(part.strip() for part in str(value).split(",") if part.strip())


def _parse_optional_int(value: Any, *, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"Invalid integer value: {value!r}.",
            suggested_fix="Use a positive integer for configured limits.",
        ) from exc
    if parsed <= 0:
        raise ConfigurationError(
            f"Configured limits must be positive, received {parsed}.",
            suggested_fix="Use a value greater than zero.",
        )
    return parsed


def _read_dotenv_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    parsed: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip().strip("\"'")
    return parsed


class AppSettings(BaseModel):
    """Validated application settings."""

    dss_url: str
    api_key: SecretStr
    default_project: str | None = None
    project_allowlist: tuple[str, ...] = Field(default_factory=tuple)
    project_blocklist: tuple[str, ...] = Field(default_factory=tuple)
    tool_allowlist: tuple[str, ...] = Field(default_factory=tuple)
    tool_blocklist: tuple[str, ...] = Field(default_factory=tuple)
    mode: OperationMode = OperationMode.READONLY
    max_preview_rows: int = 20
    max_file_read_bytes: int = 500_000
    max_log_lines: int = 1_000
    max_listed_files: int = 1_000
    redact_secrets: bool = True
    enable_write_tools: bool = False
    enable_execute_tools: bool = False
    enable_admin_tools: bool = False
    debug: bool = False

    @property
    def api_key_value(self) -> str:
        return self.api_key.get_secret_value()

    def public_settings(self) -> dict[str, Any]:
        """Return a redacted view safe for logs or CLI output."""

        data = self.model_dump(mode="json")
        data["api_key"] = "[REDACTED]"
        return data


def load_settings(
    *,
    env: dict[str, str] | None = None,
    dotenv_path: str | Path | None = None,
) -> AppSettings:
    """Load settings from the environment with safe defaults."""

    import os

    resolved_dotenv = Path(dotenv_path) if dotenv_path is not None else Path(".env")
    merged: dict[str, str] = _read_dotenv_file(resolved_dotenv)
    merged.update({key: value for key, value in os.environ.items() if key in _ENV_FIELD_MAP})
    if env:
        merged.update(env)

    payload: dict[str, Any] = {}
    missing_required: list[str] = []

    for env_key, field_name in _ENV_FIELD_MAP.items():
        value = merged.get(env_key)
        if env_key in {"DATAIKU_DSS_URL", "DATAIKU_API_KEY"} and not value:
            missing_required.append(env_key)
            continue
        if value is not None:
            payload[field_name] = value

    if missing_required:
        raise ConfigurationError(
            "Missing required configuration values.",
            details={"missing": missing_required},
            suggested_fix="Set DATAIKU_DSS_URL and DATAIKU_API_KEY before running the server.",
        )

    payload["project_allowlist"] = _parse_csv_list(payload.get("project_allowlist"))
    payload["project_blocklist"] = _parse_csv_list(payload.get("project_blocklist"))
    payload["tool_allowlist"] = _parse_csv_list(payload.get("tool_allowlist"))
    payload["tool_blocklist"] = _parse_csv_list(payload.get("tool_blocklist"))
    payload["mode"] = payload.get("mode", OperationMode.READONLY.value)
    payload["max_preview_rows"] = _parse_optional_int(payload.get("max_preview_rows"), default=20)
    payload["max_file_read_bytes"] = _parse_optional_int(
        payload.get("max_file_read_bytes"), default=500_000
    )
    payload["max_log_lines"] = _parse_optional_int(payload.get("max_log_lines"), default=1_000)
    payload["max_listed_files"] = _parse_optional_int(
        payload.get("max_listed_files"),
        default=1_000,
    )
    payload["redact_secrets"] = _parse_bool(payload.get("redact_secrets"), default=True)
    payload["enable_write_tools"] = _parse_bool(
        payload.get("enable_write_tools"), default=False
    )
    payload["enable_execute_tools"] = _parse_bool(
        payload.get("enable_execute_tools"), default=False
    )
    payload["enable_admin_tools"] = _parse_bool(
        payload.get("enable_admin_tools"), default=False
    )
    payload["debug"] = _parse_bool(payload.get("debug"), default=False)

    try:
        return AppSettings.model_validate(payload)
    except ValidationError as exc:
        raise ConfigurationError(
            "Invalid configuration values.",
            details={"errors": exc.errors(include_url=False)},
            suggested_fix="Fix the invalid environment values and rerun validate-config.",
        ) from exc
