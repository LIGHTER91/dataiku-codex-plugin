# MCP Resources Specification

MCP resources may expose read-only references to Dataiku objects.

## Possible resources

```text
dataiku://projects
dataiku://projects/{project_key}
dataiku://projects/{project_key}/flow
dataiku://projects/{project_key}/datasets
dataiku://projects/{project_key}/recipes
dataiku://projects/{project_key}/folders
dataiku://projects/{project_key}/scenarios
```

## Resource rules

- resources are read-only.
- resources must respect project allowlist/blocklist.
- resources must not expose secrets.
- resources must not return full datasets.
- resources should return summaries, not heavy content.

## Example

```text
dataiku://projects/PROJECT_KEY/flow
```

returns:

```json
{
  "project_key": "PROJECT_KEY",
  "nodes": [],
  "edges": []
}
```
