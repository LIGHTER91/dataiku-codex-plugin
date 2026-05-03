# Codex Prompt 02 — Generate MCP Server

Implement the MCP server.

Requirements:

- Support STDIO transport.
- Register tools from `TOOL_CATALOG.md`.
- Start with read-only tools.
- Add permission checks before each tool.
- Add redaction before returning output.
- Add structured logging.
- Add tests for all tools.

Do not implement destructive operations yet.

Initial tools:

1. `dataiku_ping`
2. `dataiku_get_instance_info`
3. `dataiku_list_projects`
4. `dataiku_get_project_summary`
5. `dataiku_list_datasets`
6. `dataiku_get_dataset_schema`
7. `dataiku_list_recipes`
8. `dataiku_get_recipe_details`
9. `dataiku_list_managed_folders`
10. `dataiku_list_folder_files`
