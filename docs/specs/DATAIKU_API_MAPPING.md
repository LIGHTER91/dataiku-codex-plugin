# Dataiku API Mapping

This document maps the intended MCP tools to likely Dataiku Python API concepts.

Exact method names must be verified during implementation against the installed Dataiku API client version.

## Client

### Purpose

Connect to Dataiku DSS.

### Likely API object

- `dataikuapi.DSSClient`

### Plugin wrapper

- `DataikuClientFactory`
- `DataikuDSSAdapter`

## Projects

### MCP tools

- `dataiku_list_projects`
- `dataiku_get_project_summary`
- `dataiku_generate_project_map`

### Likely API objects

- `DSSClient`
- `DSSProject`

### Required data

- project key.
- project name.
- owner.
- metadata.
- variables if permitted.
- tags if available.

## Flow

### MCP tools

- `dataiku_get_flow_graph`
- `dataiku_analyze_flow_health`

### Likely API objects

- `DSSProject`
- project Flow accessors.
- recipes/datasets/folders/model handles.

### Implementation note

If a direct Flow graph API is not sufficient, reconstruct graph from recipe inputs and outputs.

## Datasets

### MCP tools

- `dataiku_list_datasets`
- `dataiku_get_dataset_schema`
- `dataiku_preview_dataset`
- `dataiku_analyze_dataset_quality`

### Likely API objects

- `DSSDataset`
- dataset schema methods.
- dataset settings methods.
- dataset data preview methods where supported.

### Safety

Default preview limit must be small.

## Recipes

### MCP tools

- `dataiku_list_recipes`
- `dataiku_get_recipe_details`
- `dataiku_review_recipe_code`
- `dataiku_update_recipe_code`
- `dataiku_create_python_recipe`

### Likely API objects

- `DSSRecipe`
- project recipe listings.
- recipe settings.
- recipe code accessors for code recipes.

### Safety

Updating code requires write mode and explicit approval.

## Managed Folders

### MCP tools

- `dataiku_list_managed_folders`
- `dataiku_get_managed_folder_info`
- `dataiku_list_folder_files`
- `dataiku_read_folder_file`
- `dataiku_managed_folder_doctor`
- `dataiku_upload_file_to_folder`
- `dataiku_create_managed_folder`

### Likely API objects

- `DSSManagedFolder`
- in-DSS `dataiku.Folder` concepts.
- file listing APIs.
- download/upload stream APIs.

### Critical implementation rule

Never assume a Managed Folder is a local filesystem directory. Use stream APIs for non-local backends.

## Scenarios / Jobs / Logs

### MCP tools

- `dataiku_list_scenarios`
- `dataiku_get_scenario_runs`
- `dataiku_run_scenario`
- `dataiku_get_job_logs`
- `dataiku_explain_failure`

### Likely API objects

- `DSSScenario`
- scenario runs.
- job handles/log access.

### Safety

Running scenarios requires execute mode and explicit approval.

## Code Environments

### MCP tools

- `dataiku_list_code_envs`
- `dataiku_get_code_env_details`
- `dataiku_code_env_doctor`

### Likely API objects

- client/admin-level code env APIs if permission allows.

### Safety

Code env modification is not part of v1 write tools.

## Plugins

### Possible future tools

- `dataiku_list_installed_plugins`
- `dataiku_get_plugin_info`

### Safety

Read-only only in early versions.

## Connections

### Possible future tools

- `dataiku_list_connections`
- `dataiku_get_connection_summary`

### Safety

Never request sensitive info by default. Never return credentials.

## Limitations

Some Dataiku objects may require admin permissions. The plugin must degrade gracefully when permissions are insufficient.
