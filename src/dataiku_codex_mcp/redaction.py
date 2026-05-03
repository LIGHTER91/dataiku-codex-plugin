"""Secret redaction helpers."""

from __future__ import annotations

import re
from typing import Any

from dataiku_codex_mcp.errors import RedactionError

_SENSITIVE_KEYS = {
    "password",
    "passwd",
    "token",
    "api_key",
    "secret",
    "access_key",
    "private_key",
    "email",
    "phone",
    "address",
    "ssn",
    "iban",
    "credit_card",
    "card_number",
}


class Redactor:
    """Redact secret-looking values from nested payloads."""

    def __init__(self, *, enabled: bool = True, sensitive_keys: set[str] | None = None) -> None:
        self.enabled = enabled
        self.sensitive_keys = {key.lower() for key in (sensitive_keys or _SENSITIVE_KEYS)}
        self._patterns = [
            (
                re.compile(r"(?i)\b(api[_-]?key|token|password|secret)\s*[:=]\s*([^\s,;]+)"),
                lambda match: f"{match.group(1)}=[REDACTED]",
            ),
            (
                re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s]+)"),
                lambda match: f"{match.group(1)}[REDACTED]",
            ),
            (
                re.compile(
                    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
                    re.DOTALL,
                ),
                lambda _match: "[REDACTED_PRIVATE_KEY]",
            ),
            (
                re.compile(r"AKIA[0-9A-Z]{16}"),
                lambda _match: "[REDACTED_AWS_KEY]",
            ),
        ]

    def redact(self, value: Any, *, key: str | None = None) -> Any:
        """Recursively redact nested data structures."""

        if not self.enabled:
            return value
        if key and key.lower() in self.sensitive_keys:
            return "[REDACTED]"
        if isinstance(value, dict):
            return {
                inner_key: self.redact(inner_value, key=str(inner_key))
                for inner_key, inner_value in value.items()
            }
        if isinstance(value, list):
            return [self.redact(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.redact(item) for item in value)
        if isinstance(value, set):
            return {self.redact(item) for item in value}
        if isinstance(value, bytes):
            return self.redact(value.decode("utf-8", errors="replace"))
        if isinstance(value, str):
            return self.redact_text(value)
        return value

    def redact_text(self, text: str) -> str:
        """Redact common secret patterns from text."""

        result = text
        for pattern, replacement in self._patterns:
            result = pattern.sub(replacement, result)
        return result

    def assert_safe(self, value: Any) -> None:
        """Raise if a value still contains obvious secrets after redaction."""

        candidate = self.redact(value)
        serialized = str(candidate)
        if "-----BEGIN PRIVATE KEY-----" in serialized:
            raise RedactionError(
                "Redaction failed to remove a private key payload.",
                suggested_fix="Extend the redaction patterns before returning this output.",
            )
