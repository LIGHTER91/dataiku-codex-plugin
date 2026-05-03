from __future__ import annotations

import pytest

from dataiku_codex_mcp.errors import RedactionError
from dataiku_codex_mcp.redaction import Redactor


def test_redact_text_hides_common_secret_patterns() -> None:
    redactor = Redactor()
    text = "api_key=super-secret Authorization: Bearer abc123"

    redacted = redactor.redact_text(text)

    assert "super-secret" not in redacted
    assert "abc123" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_nested_payload_hides_sensitive_keys() -> None:
    redactor = Redactor()
    payload = {
        "recipe": {
            "token": "secret-token",
            "nested": [{"password": "pw"}, {"safe": "value"}],
        }
    }

    redacted = redactor.redact(payload)

    assert redacted["recipe"]["token"] == "[REDACTED]"
    assert redacted["recipe"]["nested"][0]["password"] == "[REDACTED]"
    assert redacted["recipe"]["nested"][1]["safe"] == "value"


def test_assert_safe_raises_for_remaining_private_key() -> None:
    redactor = Redactor()

    with pytest.raises(RedactionError):
        redactor.assert_safe({"key_material": "-----BEGIN PRIVATE KEY-----still here"})
