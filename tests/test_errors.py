from __future__ import annotations

from dataiku_codex_mcp.errors import ConfigurationError, normalize_exception


def test_normalize_exception_preserves_custom_error_payload() -> None:
    payload = normalize_exception(
        ConfigurationError("Missing config", details={"missing": ["DATAIKU_DSS_URL"]})
    )

    assert payload["ok"] is False
    assert payload["error"]["type"] == "ConfigurationError"
    assert payload["error"]["details"]["missing"] == ["DATAIKU_DSS_URL"]


def test_normalize_exception_maps_permission_error() -> None:
    payload = normalize_exception(PermissionError("nope"))

    assert payload["error"]["type"] == "PermissionDeniedError"
