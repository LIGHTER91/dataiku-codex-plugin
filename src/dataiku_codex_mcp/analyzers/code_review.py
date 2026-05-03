"""Heuristic recipe review helpers."""

from __future__ import annotations

import re
from typing import Any


def review_recipe_code(recipe: dict[str, Any]) -> dict[str, Any]:
    """Review recipe code and settings for common issues."""

    recipe_name = recipe.get("name")
    recipe_type = str(recipe.get("type") or "").lower()
    raw_code = recipe.get("code")
    code = raw_code if isinstance(raw_code, str) else ""
    issues: list[dict[str, Any]] = []
    strengths: list[str] = []

    if recipe_type == "python":
        if "get_path(" in code:
            issues.append(
                _issue(
                    "high",
                    "managed_folder_path",
                    "Uses get_path() on a Managed Folder, which is unsafe on non-local backends.",
                    "Prefer Dataiku stream APIs for reading and writing folder content.",
                )
            )
        if re.search(r"open\(.+\)\.read\(|\.read\(\)", code):
            issues.append(
                _issue(
                    "medium",
                    "full_file_read",
                    "Reads file content eagerly into memory.",
                    "Stream large files line by line or chunk them incrementally.",
                )
            )
        if re.search(r"(^|\\n)\s*(/|[A-Z]:\\\\)", code):
            issues.append(
                _issue(
                    "medium",
                    "hardcoded_path",
                    "Contains a hardcoded absolute path.",
                    "Use Dataiku dataset/folder abstractions rather than fixed local paths.",
                )
            )
        if "logging." in code or "logger." in code:
            strengths.append("Structured logging appears to be present.")
        else:
            issues.append(
                _issue(
                    "low",
                    "missing_logging",
                    "No explicit logging was detected in the recipe code.",
                    "Add logging around I/O, batch progress and failure points.",
                )
            )
        if "try:" not in code or "except" not in code:
            issues.append(
                _issue(
                    "medium",
                    "missing_error_handling",
                    "No defensive exception handling was detected.",
                    "Wrap risky I/O and model loading paths with targeted exceptions.",
                )
            )
        if "set_schema" in code or "write_with_schema" in code:
            strengths.append("Output schema handling is explicitly addressed.")
        else:
            issues.append(
                _issue(
                    "medium",
                    "missing_schema_handling",
                    "No explicit output schema handling was detected.",
                    "Manage output schema deliberately before writing Dataiku outputs.",
                )
            )
        if "RecursiveCharacterTextSplitter" in code:
            strengths.append("Chunking logic is explicit and easy to inspect.")
        if "IndexFlatIP" in code and "normalize" not in code.lower():
            issues.append(
                _issue(
                    "high",
                    "vector_normalization",
                    "Inner-product vector search is used without obvious embedding normalization.",
                    "Normalize embeddings before indexing or switch to a metric aligned "
                    "with your model.",
                )
            )
    elif recipe_type == "sql":
        if "select *" in code.lower():
            issues.append(
                _issue(
                    "medium",
                    "select_star",
                    "Uses SELECT * which is fragile on wide or drifting schemas.",
                    "Enumerate only the required columns and add filtering where possible.",
                )
            )

    risk_level = _risk_level(issues)
    return {
        "recipe": recipe_name,
        "strengths": strengths,
        "issues": issues,
        "risk_level": risk_level,
        "suggested_patch": [issue["suggested_fix"] for issue in issues],
    }


def _issue(
    severity: str,
    category: str,
    message: str,
    suggested_fix: str,
) -> dict[str, str]:
    return {
        "severity": severity,
        "category": category,
        "message": message,
        "suggested_fix": suggested_fix,
    }


def _risk_level(issues: list[dict[str, Any]]) -> str:
    severities = {issue["severity"] for issue in issues}
    if "high" in severities:
        return "high"
    if "medium" in severities or len(issues) >= 3:
        return "medium"
    if issues:
        return "low"
    return "low"
