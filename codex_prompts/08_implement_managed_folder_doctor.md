# Codex Prompt 08 — Implement Managed Folder Doctor

Implement Managed Folder analysis tools.

Read:

- `docs/specs/TOOL_CATALOG.md`
- `skills/dataiku-managed-folder-debugger/SKILL.md`
- `docs/decisions/ADR-003-managed-folders-stream-first.md`

Implement:

- `dataiku_list_managed_folders`
- `dataiku_get_managed_folder_info`
- `dataiku_list_folder_files`
- `dataiku_read_folder_file`
- `dataiku_managed_folder_doctor`

Critical rule:

Do not assume Managed Folders are local filesystem paths.

Detect:

- `get_path()` usage.
- hardcoded paths.
- missing stream APIs.
- malformed JSONL.
- encoding errors.
- file size risks.
- binary files.

Add unit tests and mocked integration tests.
