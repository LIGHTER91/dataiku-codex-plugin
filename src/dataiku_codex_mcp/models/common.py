"""Common JSON-safe response models and helpers."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorDetails(BaseModel):
    """Normalized error payload returned by the CLI or MCP tools."""

    type: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    suggested_fix: str | None = None


class ErrorEnvelope(BaseModel):
    """Top-level error envelope."""

    ok: Literal[False] = False
    error: ErrorDetails


class SuccessEnvelope(BaseModel):
    """Top-level success envelope."""

    ok: Literal[True] = True
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def ok(
    data: dict[str, Any],
    *,
    warnings: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a normalized success response."""

    return SuccessEnvelope(
        data=data,
        warnings=warnings or [],
        metadata=metadata or {},
    ).model_dump(mode="json")


def err(
    error_type: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    suggested_fix: str | None = None,
) -> dict[str, Any]:
    """Build a normalized error response."""

    return ErrorEnvelope(
        error=ErrorDetails(
            type=error_type,
            message=message,
            details=details or {},
            suggested_fix=suggested_fix,
        )
    ).model_dump(mode="json")
