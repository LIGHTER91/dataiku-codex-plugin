# Security Model

## Security principles

- Least privilege.
- Read-only by default.
- Explicit approval for write operations.
- Explicit approval for execute operations.
- No secret exfiltration.
- No credentials in logs.
- No full dataset dumps by default.
- No destructive actions by default.
- No arbitrary code execution unless explicitly enabled.
- No `sensitive_info=True` by default.
- User permissions in Dataiku must be respected.
- MCP server must enforce security independently from Codex.

## Data redaction

The plugin must redact:

- API keys.
- passwords.
- bearer tokens.
- private keys.
- OAuth tokens.
- connection strings.
- database credentials.
- secret environment variables.
- sensitive values in logs.
- PII-like fields if configured.

## Secret patterns

The redaction layer should detect patterns such as:

- `api_key=...`
- `password=...`
- `token=...`
- `Authorization: Bearer ...`
- `-----BEGIN PRIVATE KEY-----`
- AWS keys.
- GCP service account keys.
- Azure credentials.
- JDBC URLs with passwords.

## Dangerous operations

The following operations require explicit approval:

- update recipe code.
- create recipe.
- create dataset.
- create Managed Folder.
- upload files.
- run scenario.
- run job.
- update documentation.
- change project variables.
- change code env settings.
- inspect admin-level connections.

## Disabled by default

The following should be disabled unless explicitly implemented safely:

- delete project objects.
- delete datasets.
- delete recipes.
- delete Managed Folders.
- delete project.
- modify connections.
- retrieve connection credentials.
- run arbitrary code on DSS.
- export full datasets.

## Read limits

Default limits:

- max dataset preview rows: 20.
- max file read bytes: 500,000.
- max log lines: 1,000.
- max listed files: 1,000.

These must be configurable.

## Audit logging

Every tool call should log:

- timestamp.
- tool name.
- mode.
- project key if any.
- object name if any.
- success/failure.
- error type if any.

Never log:

- API keys.
- full data rows.
- file contents.
- credentials.
- secret values.

## Approval model

Before write/execute operations, Codex must show:

- what will be changed.
- target project.
- target object.
- risk level.
- rollback possibility.
- exact operation.

The MCP server must reject the operation unless the request includes an explicit approved flag or equivalent confirmed mechanism.

## Safe defaults

Default environment:

```env
DATAIKU_MODE=readonly
DATAIKU_ENABLE_WRITE_TOOLS=false
DATAIKU_ENABLE_EXECUTE_TOOLS=false
DATAIKU_ENABLE_ADMIN_TOOLS=false
DATAIKU_REDACT_SECRETS=true
```
