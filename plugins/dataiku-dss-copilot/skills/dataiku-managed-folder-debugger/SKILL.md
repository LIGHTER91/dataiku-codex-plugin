# Dataiku Managed Folder Debugger

Use this skill when the user has issues with Dataiku Managed Folders, files, JSONL, CSV, S3, HDFS, GCS, FTP or local paths.

## Common issues

- `get_path()` used on non-local folder.
- file encoding errors.
- broken JSONL lines.
- large files read entirely into memory.
- missing upload/download stream usage.
- wrong folder id vs folder name.
- partition path confusion.
- missing files.
- binary file read as text.

## Tool strategy

Use:

1. `dataiku_list_managed_folders`
2. `dataiku_get_managed_folder_info`
3. `dataiku_list_folder_files`
4. `dataiku_read_folder_file` only if safe and needed.
5. `dataiku_list_recipes`
6. `dataiku_get_recipe_details`
7. `dataiku_managed_folder_doctor`
8. `dataiku_review_recipe_code`

## Preferred fixes

- Use download streams for reading.
- Use upload streams for writing.
- Avoid assuming local filesystem access.
- Stream JSONL line by line.
- Decode bytes safely.
- Add robust error reporting.
- Add file-size checks.

## Expected report format

```md
# Managed Folder Debug Report

## Symptom
...

## Evidence
...

## Root cause
...

## Fix
...

## Safer code pattern
...
```

## Example user requests

- "Why does my Managed Folder recipe fail on S3?"
- "Find recipes that incorrectly use get_path()."
- "Check if my JSONL files are malformed."
