# MCP Safety Rules

## Global rules

- Read-only by default.
- Reject write tools unless write mode is enabled.
- Reject execute tools unless execute mode is enabled.
- Reject admin tools unless admin mode is enabled.
- Enforce project allowlist/blocklist.
- Enforce tool allowlist/blocklist.
- Redact secrets before returning outputs.
- Limit dataset previews.
- Limit file reads.
- Limit logs.

## Managed Folder rules

- Do not assume local filesystem access.
- Prefer stream APIs.
- Refuse huge reads by default.
- Detect binary files.
- Redact file contents.

## Recipe rules

- Redact hardcoded secrets.
- Do not run recipe code.
- Do not update recipe code without explicit approval.
- Create backup/dry-run if possible.

## Scenario rules

- Do not run scenarios in readonly mode.
- Running scenarios requires explicit approval.
- Explain potential impact before execution.

## Dataset rules

- No full export by default.
- Preview only small sample.
- Redact sensitive columns.
- Warn about PII risk.

## Admin rules

- Do not return credentials.
- Do not call sensitive info APIs unless explicitly allowed.
- Never expose connection passwords.
