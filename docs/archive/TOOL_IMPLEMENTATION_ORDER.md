# Tool Implementation Order

## Phase 1 — Foundation

1. config loader.
2. Dataiku client wrapper.
3. permission guard.
4. redaction utility.
5. error normalizer.
6. audit logger.
7. MCP server bootstrap.
8. CLI entrypoint.
9. tests for all foundations.

## Phase 2 — Read-only core

1. `dataiku_ping`
2. `dataiku_get_instance_info`
3. `dataiku_list_projects`
4. `dataiku_get_project_summary`
5. `dataiku_list_datasets`
6. `dataiku_get_dataset_schema`
7. `dataiku_list_recipes`
8. `dataiku_get_recipe_details`
9. `dataiku_list_managed_folders`
10. `dataiku_get_managed_folder_info`
11. `dataiku_list_folder_files`

## Phase 3 — Analysis tools

1. `dataiku_generate_project_map`
2. `dataiku_get_flow_graph`
3. `dataiku_analyze_flow_health`
4. `dataiku_review_recipe_code`
5. `dataiku_managed_folder_doctor`
6. `dataiku_code_env_doctor`
7. `dataiku_detect_rag_pipeline`
8. `dataiku_audit_rag_pipeline`

## Phase 4 — Logs and scenarios

1. `dataiku_list_scenarios`
2. `dataiku_get_scenario_runs`
3. `dataiku_get_job_logs`
4. `dataiku_explain_failure`

## Phase 5 — Documentation

1. `dataiku_generate_project_readme`
2. `dataiku_generate_flow_documentation`
3. `dataiku_generate_troubleshooting_report`
4. `dataiku_generate_rag_audit_report`

## Phase 6 — Write tools

Only after permission system, approval flow and tests are complete:

1. `dataiku_update_recipe_code`
2. `dataiku_create_python_recipe`
3. `dataiku_create_managed_folder`
4. `dataiku_upload_file_to_folder`
5. `dataiku_run_scenario`
6. `dataiku_create_project_documentation`

## Phase 7 — Enterprise features

1. HTTP MCP transport.
2. centralized audit logging.
3. OAuth/Bearer auth.
4. per-tool policies.
5. deployment guide.
6. production monitoring.
