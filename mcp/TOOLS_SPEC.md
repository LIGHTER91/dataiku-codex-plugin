# MCP Tools Specification

The canonical source for all tools is `../TOOL_CATALOG.md`.

## Implementation requirements

For each tool, implement:

1. Pydantic input model.
2. tool handler function.
3. permission check.
4. Dataiku adapter call.
5. output normalization.
6. redaction.
7. tests.

## Tool module split

```text
tools/
├── instance.py
├── projects.py
├── flow.py
├── datasets.py
├── recipes.py
├── managed_folders.py
├── scenarios.py
├── code_envs.py
├── rag.py
├── documentation.py
└── write_actions.py
```

## Tool handler pattern

```python
async def dataiku_list_projects(input: ListProjectsInput, ctx: AppContext) -> ToolResult:
    ctx.permissions.require("dataiku_list_projects", level="read")
    projects = ctx.dataiku.list_projects(include_archived=input.include_archived)
    return ok({"projects": projects})
```

## Tests

Every tool must have:

- success test.
- Dataiku API error test.
- permission denied test.
- redaction test if relevant.
