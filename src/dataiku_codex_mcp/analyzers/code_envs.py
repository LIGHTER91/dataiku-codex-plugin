"""Code environment diagnostics."""

from __future__ import annotations

from typing import Any


def analyze_code_env(details: dict[str, Any]) -> dict[str, Any]:
    """Produce a structured diagnosis for a code environment."""

    issues: list[dict[str, Any]] = []
    python_version = str(details.get("python_version") or "")
    packages = [str(package) for package in details.get("packages", [])]
    package_names = {package.split("==", 1)[0].lower() for package in packages}

    if python_version and tuple(_safe_version_parts(python_version)) < (3, 10):
        issues.append(
            {
                "severity": "medium",
                "category": "python_version",
                "message": (
                    f"Python {python_version} may be too old for the expected plugin baseline."
                ),
                "suggested_fix": (
                    "Prefer Python 3.10+ for reproducibility and library compatibility."
                ),
            }
        )
    if "sentence-transformers" not in package_names:
        issues.append(
            {
                "severity": "high",
                "category": "missing_embeddings_package",
                "message": "sentence-transformers is not installed in the code environment.",
                "suggested_fix": (
                    "Install sentence-transformers in the Dataiku code env or pin an "
                    "alternative embedding runtime."
                ),
            }
        )
    if "faiss-cpu" in package_names and "numpy" not in package_names:
        issues.append(
            {
                "severity": "medium",
                "category": "incomplete_vector_stack",
                "message": "faiss-cpu is present without an explicit numpy dependency.",
                "suggested_fix": "Pin numpy alongside faiss-cpu to avoid runtime mismatches.",
            }
        )

    for explicit_issue in details.get("known_issues", []):
        issues.append(
            {
                "severity": "medium",
                "category": "known_issue",
                "message": str(explicit_issue),
                "suggested_fix": (
                    "Resolve the environment issue before rerunning dependent recipes."
                ),
            }
        )

    return {
        "environment": details.get("name"),
        "symptoms": [issue["message"] for issue in issues],
        "dependency_issues": issues,
        "recommended_installation_fix": [issue["suggested_fix"] for issue in issues],
        "reproducibility_recommendations": [
            "Pin package versions explicitly.",
            "Export the environment specification with the project.",
            "Keep model and wheel dependencies versioned with deployment artifacts.",
        ],
    }


def _safe_version_parts(version: str) -> list[int]:
    parts: list[int] = []
    for chunk in version.split(".")[:2]:
        try:
            parts.append(int(chunk))
        except ValueError:
            parts.append(0)
    while len(parts) < 2:
        parts.append(0)
    return parts
