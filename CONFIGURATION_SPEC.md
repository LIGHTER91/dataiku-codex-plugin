# Configuration Specification

## Required environment variables

```env
DATAIKU_DSS_URL=https://dss.company.com
DATAIKU_API_KEY=changeme
```

## Optional environment variables

```env
DATAIKU_DEFAULT_PROJECT=
DATAIKU_PROJECT_ALLOWLIST=
DATAIKU_PROJECT_BLOCKLIST=
DATAIKU_TOOL_ALLOWLIST=
DATAIKU_TOOL_BLOCKLIST=
DATAIKU_MODE=readonly
DATAIKU_MAX_PREVIEW_ROWS=20
DATAIKU_MAX_FILE_READ_BYTES=500000
DATAIKU_MAX_LOG_LINES=1000
DATAIKU_MAX_LISTED_FILES=1000
DATAIKU_REDACT_SECRETS=true
DATAIKU_ENABLE_WRITE_TOOLS=false
DATAIKU_ENABLE_EXECUTE_TOOLS=false
DATAIKU_ENABLE_ADMIN_TOOLS=false
DATAIKU_DEBUG=false
```

## Modes

Allowed values:

```text
readonly
write
execute
admin
```

## Example `.env`

```env
DATAIKU_DSS_URL=https://dss.company.com
DATAIKU_API_KEY=replace-me
DATAIKU_MODE=readonly
DATAIKU_PROJECT_ALLOWLIST=PROJECT_A,PROJECT_B
DATAIKU_MAX_PREVIEW_ROWS=20
DATAIKU_MAX_FILE_READ_BYTES=500000
DATAIKU_MAX_LOG_LINES=1000
DATAIKU_REDACT_SECRETS=true
DATAIKU_ENABLE_WRITE_TOOLS=false
DATAIKU_ENABLE_EXECUTE_TOOLS=false
DATAIKU_ENABLE_ADMIN_TOOLS=false
```

## Config validation

The server must validate:

- DSS URL is set.
- API key is set.
- mode is valid.
- numeric limits are positive.
- write tools are disabled unless explicitly enabled.
- execute tools are disabled unless explicitly enabled.
- admin tools are disabled unless explicitly enabled.

## Safe defaults

If optional values are missing:

- use readonly mode.
- enable redaction.
- disable write tools.
- disable execute tools.
- disable admin tools.
- keep preview/file/log limits small.
