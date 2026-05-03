"""Managed Folder issue detection heuristics."""

from __future__ import annotations

from typing import Any


def analyze_managed_folder(
    *,
    folder_info: dict[str, Any],
    folder_files: dict[str, Any],
    related_recipes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze common Managed Folder anti-patterns."""

    issues: list[dict[str, Any]] = []
    folder_id = folder_info.get("folder_id")
    file_paths = [entry.get("path") for entry in folder_files.get("files", []) if entry.get("path")]

    if not folder_info.get("local_path_available"):
        for recipe in related_recipes:
            raw_code = recipe.get("code")
            code = raw_code if isinstance(raw_code, str) else ""
            if "get_path(" in code:
                issues.append(
                    {
                        "severity": "high",
                        "category": "non_local_get_path",
                        "message": (
                            f"Recipe {recipe.get('name')} uses get_path() against non-local "
                            f"folder {folder_id}."
                        ),
                        "suggested_fix": "Switch to Dataiku download/upload stream APIs.",
                    }
                )
            if ".read()" in code:
                issues.append(
                    {
                        "severity": "medium",
                        "category": "eager_file_read",
                        "message": (
                            f"Recipe {recipe.get('name')} reads folder content eagerly into memory."
                        ),
                        "suggested_fix": "Stream JSONL or text files incrementally.",
                    }
                )

    if not file_paths:
        issues.append(
            {
                "severity": "medium",
                "category": "empty_folder",
                "message": f"Managed Folder {folder_id} contains no visible files.",
                "suggested_fix": (
                    "Verify upstream writers, partitioning and environment permissions."
                ),
            }
        )

    oversized = [
        entry["path"]
        for entry in folder_files.get("files", [])
        if isinstance(entry.get("size"), int) and entry["size"] > 500_000
    ]
    if oversized:
        issues.append(
            {
                "severity": "medium",
                "category": "large_files",
                "message": "Some files exceed the default safe read threshold.",
                "objects": oversized,
                "suggested_fix": "Read these files in streaming mode and avoid full previews.",
            }
        )

    return {
        "folder": folder_info,
        "files": folder_files,
        "issues": issues,
        "related_recipes": [recipe.get("name") for recipe in related_recipes],
        "summary": f"Detected {len(issues)} Managed Folder issue(s).",
    }
