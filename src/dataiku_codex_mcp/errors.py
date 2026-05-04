"""Normalized exception types and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from dataiku_codex_mcp.models.common import err


@dataclass(eq=False)
class DataikuCodexError(Exception):
    """Base application error with a normalized payload."""

    message: str
    details: dict[str, Any] = field(default_factory=dict)
    suggested_fix: str | None = None
    error_type: ClassVar[str] = "DataikuCodexError"

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return err(
            self.error_type,
            self.message,
            details=self.details,
            suggested_fix=self.suggested_fix,
        )


class ConfigurationError(DataikuCodexError):
    error_type: ClassVar[str] = "ConfigurationError"


class DataikuConnectionError(DataikuCodexError):
    error_type: ClassVar[str] = "DataikuConnectionError"


class DataikuAuthenticationError(DataikuCodexError):
    error_type: ClassVar[str] = "DataikuAuthenticationError"


class PermissionDeniedError(DataikuCodexError):
    error_type: ClassVar[str] = "PermissionDeniedError"


class DataikuObjectNotFoundError(DataikuCodexError):
    error_type: ClassVar[str] = "DataikuObjectNotFoundError"


class DataikuAPIError(DataikuCodexError):
    error_type: ClassVar[str] = "DataikuAPIError"


class RedactionError(DataikuCodexError):
    error_type: ClassVar[str] = "RedactionError"


class UnsupportedOperationError(DataikuCodexError):
    error_type: ClassVar[str] = "UnsupportedOperationError"


def map_exception(exc: Exception) -> DataikuCodexError:
    """Map arbitrary exceptions to normalized application errors."""

    if isinstance(exc, DataikuCodexError):
        return exc

    message = str(exc) or exc.__class__.__name__
    lowered = message.lower()

    if isinstance(exc, PermissionError):
        return PermissionDeniedError(
            "The requested operation was denied.",
            suggested_fix="Check the configured mode, allowlists and approval flag.",
        )
    if isinstance(exc, TimeoutError):
        return DataikuConnectionError(
            "Timed out while contacting Dataiku DSS.",
            suggested_fix="Check DATAIKU_DSS_URL, network access and retry.",
        )
    if isinstance(exc, ModuleNotFoundError):
        return ConfigurationError(
            f"Missing dependency: {exc.name or 'unknown module'}.",
            suggested_fix="Install the project dependencies before running the server.",
        )
    if "401" in lowered or "unauthorized" in lowered or "forbidden" in lowered:
        return DataikuAuthenticationError(
            "Could not authenticate to Dataiku DSS.",
            suggested_fix="Check DATAIKU_API_KEY and the Dataiku user permissions.",
        )
    if "404" in lowered or "not found" in lowered:
        return DataikuObjectNotFoundError(
            "The requested Dataiku object could not be found.",
            suggested_fix="Verify the project key or object identifier.",
        )
    if isinstance(exc, OSError):
        return DataikuConnectionError(
            "Could not connect to Dataiku DSS.",
            suggested_fix="Check DATAIKU_DSS_URL, proxy/VPN settings and SSL connectivity.",
        )
    return DataikuAPIError(
        "Unexpected Dataiku API failure.",
        details={"original_error": exc.__class__.__name__},
        suggested_fix=(
            "Inspect the underlying Dataiku API response and add a dedicated "
            "mapper if needed."
        ),
    )


def normalize_exception(exc: Exception) -> dict[str, Any]:
    """Convert an exception into a normalized error envelope."""

    return map_exception(exc).to_dict()
