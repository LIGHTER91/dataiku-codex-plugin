# Permission Model

## Modes

## readonly

Can inspect:

- projects.
- Flow metadata.
- datasets metadata.
- dataset schemas.
- small dataset previews.
- recipes and recipe code.
- Managed Folder metadata.
- small files through safe read APIs.
- scenarios metadata.
- recent runs/logs.
- code env metadata if allowed.

Cannot:

- modify objects.
- run scenarios.
- upload files.
- delete anything.

## write

Includes readonly capabilities and can:

- create recipes.
- update recipe code.
- create Managed Folders.
- upload files.
- write generated documentation.

Requires:

- `DATAIKU_ENABLE_WRITE_TOOLS=true`
- explicit approval per operation.

## execute

Includes readonly capabilities and can:

- run scenarios.
- run jobs if implemented.

Requires:

- `DATAIKU_ENABLE_EXECUTE_TOOLS=true`
- explicit approval per operation.

## admin

Can inspect admin-level objects where the API key allows.

Possible capabilities:

- code environments.
- plugins.
- connections metadata without secrets.
- global settings summaries.

Requires:

- `DATAIKU_ENABLE_ADMIN_TOOLS=true`

## dangerous

Reserved for destructive operations.

Should remain disabled unless a future version implements strong safeguards.

## Project allowlist

Environment variable:

```env
DATAIKU_PROJECT_ALLOWLIST=PROJECT_A,PROJECT_B
```

If set, the server must reject all project operations outside this list.

## Project blocklist

Environment variable:

```env
DATAIKU_PROJECT_BLOCKLIST=SECRET_PROJECT,HR_PROJECT
```

If set, the server must reject operations on these projects.

## Tool allowlist/blocklist

Optional environment variables:

```env
DATAIKU_TOOL_ALLOWLIST=dataiku_ping,dataiku_list_projects
DATAIKU_TOOL_BLOCKLIST=dataiku_preview_dataset,dataiku_read_folder_file
```

## Approval input pattern

Write/execute tools should include:

```json
{
  "approved": true,
  "approval_reason": "User explicitly approved this action."
}
```

If `approved` is missing or false, the server must reject the operation and return a dry-run summary if possible.

## Permission test requirements

Every tool must have tests for:

- allowed mode.
- denied mode.
- blocked project.
- blocked tool.
- missing approval for write/execute.
