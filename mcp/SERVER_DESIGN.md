# MCP Server Design

## Server purpose

The MCP server exposes Dataiku DSS capabilities as structured tools for Codex.

## Responsibilities

- connect to DSS.
- register tools.
- validate tool inputs.
- enforce permissions.
- call Dataiku APIs.
- normalize results.
- redact sensitive data.
- normalize errors.
- log audit events.

## Transports

### STDIO

Default.

```bash
dataiku-codex-mcp --stdio
```

### Streamable HTTP

Future enterprise mode.

```bash
dataiku-codex-mcp --http --host 0.0.0.0 --port 8080
```

## Tool registration pattern

Each tool module should expose a function:

```python
def register_tools(server: MCPServer, context: AppContext) -> None:
    ...
```

## App context

The server should create an `AppContext` containing:

- settings.
- Dataiku client.
- permission guard.
- redactor.
- audit logger.

## Output wrapper

Every tool should return:

```json
{
  "ok": true,
  "data": {},
  "warnings": [],
  "metadata": {}
}
```

or:

```json
{
  "ok": false,
  "error": {}
}
```
