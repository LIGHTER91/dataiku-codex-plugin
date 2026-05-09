# Error Handling Specification

## Goals

Errors must be:

- safe.
- readable.
- actionable.
- normalized.
- testable.
- free of secrets.

## Standard error response

```json
{
  "ok": false,
  "error": {
    "type": "ErrorType",
    "message": "Human-readable explanation.",
    "details": {},
    "suggested_fix": "Recommended next step."
  }
}
```

## Error categories

### ConfigurationError

Examples:

- missing `DATAIKU_DSS_URL`.
- missing `DATAIKU_API_KEY`.
- invalid mode.
- invalid allowlist.

### DataikuConnectionError

Examples:

- DSS unreachable.
- DNS failure.
- SSL error.
- timeout.

### DataikuAuthenticationError

Examples:

- invalid API key.
- expired token.
- insufficient auth.

### PermissionDeniedError

Examples:

- tool not allowed in mode.
- project not allowed.
- write operation in readonly mode.
- missing approval.

### DataikuObjectNotFoundError

Examples:

- project not found.
- dataset not found.
- recipe not found.
- Managed Folder not found.
- scenario not found.

### DataikuAPIError

Examples:

- unexpected Dataiku API response.
- unsupported operation.
- client version mismatch.

### FileTooLargeError

Examples:

- requested Managed Folder file exceeds max bytes.
- logs exceed line limit.

### BinaryFileError

Examples:

- attempted to read binary file as text.

### RedactionError

Examples:

- output contains unredacted secret-looking value.
- redaction failed.

### UnsupportedOperationError

Examples:

- requested API not supported by current Dataiku version.
- operation not implemented yet.

## Implementation requirements

- Catch Dataiku-specific exceptions.
- Map exceptions to normalized errors.
- Remove credentials from exception messages.
- Do not include raw stack traces in normal output.
- Keep stack traces only in debug logs, with redaction.
- Include suggested fixes.

## Example

```json
{
  "ok": false,
  "error": {
    "type": "PermissionDeniedError",
    "message": "The tool dataiku_update_recipe_code is not allowed in readonly mode.",
    "details": {
      "mode": "readonly",
      "required_mode": "write"
    },
    "suggested_fix": "Set DATAIKU_MODE=write and DATAIKU_ENABLE_WRITE_TOOLS=true, then explicitly approve the operation."
  }
}
```
