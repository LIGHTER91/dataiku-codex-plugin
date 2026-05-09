# MCP Server Specification

## Purpose

Expose Dataiku DSS functionality as MCP tools usable by Codex.

## Supported transports

The server should support:

- STDIO transport for local usage.
- Streamable HTTP transport for enterprise deployment.

## Server layers

1. Transport layer.
2. Tool registry.
3. Input validation.
4. Permission guard.
5. Dataiku API adapter.
6. Result serializer.
7. Redaction layer.
8. Error normalization.
9. Audit logging.

## Python dependencies

Recommended:

```text
mcp
dataiku-api-client
pydantic
python-dotenv
pytest
pytest-mock
networkx
ruff
mypy
```

Optional:

```text
fastmcp
orjson
rich
pandas
pyarrow
python-magic
```

## Tool design rules

Every tool must:

- have typed input models.
- have typed output models where useful.
- return JSON-serializable output.
- have clear permission level.
- call the permission guard.
- apply redaction.
- handle Dataiku exceptions.
- include tests.

## Permission levels

- `read`: metadata, schemas, small previews, recipe code, logs.
- `write`: create/update non-destructive objects.
- `execute`: run scenarios/jobs.
- `admin`: inspect admin-level settings where API key allows.
- `dangerous`: delete or destructive operations. Disabled by default.

## Tool registration categories

- instance
- projects
- flow
- datasets
- recipes
- Managed Folders
- scenarios/jobs/logs
- code environments
- RAG audit
- documentation
- write actions

## Server CLI

Required:

```bash
dataiku-codex-mcp --stdio
```

Recommended:

```bash
dataiku-codex-mcp ping
dataiku-codex-mcp validate-config
dataiku-codex-mcp list-tools
dataiku-codex-mcp list-projects
```

## Error response format

```json
{
  "ok": false,
  "error": {
    "type": "DataikuConnectionError",
    "message": "Could not connect to Dataiku DSS.",
    "details": {
      "url": "redacted"
    },
    "suggested_fix": "Check DATAIKU_DSS_URL, network access and API key."
  }
}
```

## Success response format

```json
{
  "ok": true,
  "data": {},
  "warnings": [],
  "metadata": {
    "tool": "dataiku_list_projects",
    "mode": "readonly"
  }
}
```
