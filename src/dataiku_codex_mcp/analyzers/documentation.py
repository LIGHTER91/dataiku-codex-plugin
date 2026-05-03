"""Markdown report generators for project documentation."""

from __future__ import annotations

from typing import Any


def generate_project_readme(
    *,
    summary: dict[str, Any],
    datasets: list[dict[str, Any]],
    recipes: list[dict[str, Any]],
    folders: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    flow_health: dict[str, Any],
    warnings: list[str] | None = None,
) -> str:
    """Render a project README from collected metadata."""

    project_name = summary.get("name") or summary.get("project_key") or "Unknown project"
    lines = [
        f"# {project_name}",
        "",
        "## Overview",
        f"- Project key: {summary.get('project_key', 'unknown')}",
        f"- Datasets: {summary.get('datasets_count', len(datasets))}",
        f"- Recipes: {summary.get('recipes_count', len(recipes))}",
        f"- Managed Folders: {summary.get('managed_folders_count', len(folders))}",
        f"- Scenarios: {summary.get('scenarios_count', len(scenarios))}",
        "",
        "## What This Project Contains",
        _sentence_for_inventory(datasets, recipes, folders, scenarios),
        "",
        "## Datasets",
    ]
    lines.extend(_dataset_bullets(datasets))
    lines.extend(
        [
            "",
            "## Recipes",
        ]
    )
    lines.extend(_recipe_bullets(recipes))
    lines.extend(
        [
            "",
            "## Managed Folders",
        ]
    )
    lines.extend(_folder_bullets(folders))
    lines.extend(
        [
            "",
            "## Scenarios",
        ]
    )
    lines.extend(_scenario_bullets(scenarios))
    lines.extend(
        [
            "",
            "## Known Risks",
        ]
    )
    lines.extend(_issue_bullets(flow_health.get("issues", [])))
    lines.extend(_warnings_section(warnings or []))
    return "\n".join(lines).strip() + "\n"


def generate_flow_documentation(
    *,
    summary: dict[str, Any],
    project_map: dict[str, Any],
    flow_graph: dict[str, Any],
    flow_health: dict[str, Any],
    recipes: list[dict[str, Any]],
) -> str:
    """Render a Flow-oriented architecture document."""

    project_name = summary.get("name") or summary.get("project_key") or "Unknown project"
    lines = [
        f"# Flow Documentation: {project_name}",
        "",
        "## Summary",
        project_map.get("summary", "No Flow summary is available."),
        "",
        flow_graph.get("summary", "No graph summary is available."),
        "",
        "## Topological Order",
    ]
    topo = flow_graph.get("topological_order", [])
    if topo:
        for index, node_id in enumerate(topo, start=1):
            lines.append(f"{index}. `{node_id}`")
    else:
        lines.append("- No topological order could be derived.")

    lines.extend(
        [
            "",
            "## Dependencies",
        ]
    )
    lines.extend(_edge_bullets(flow_graph.get("edges", [])))
    lines.extend(
        [
            "",
            "## Recipe Bindings",
        ]
    )
    lines.extend(_recipe_binding_bullets(recipes))
    lines.extend(
        [
            "",
            "## Flow Health",
        ]
    )
    lines.extend(_issue_bullets(flow_health.get("issues", [])))
    lines.extend(_warnings_section(flow_health.get("warnings", [])))
    return "\n".join(lines).strip() + "\n"


def generate_troubleshooting_report(
    *,
    summary: dict[str, Any],
    focus: str | None,
    flow_health: dict[str, Any],
    folder_diagnosis: dict[str, Any] | None,
    code_env_diagnoses: list[dict[str, Any]],
    recipe_reviews: list[dict[str, Any]],
    scenario_runs: list[dict[str, Any]],
    warnings: list[str] | None = None,
) -> str:
    """Render a consolidated debugging report."""

    project_name = summary.get("name") or summary.get("project_key") or "Unknown project"
    lines = [
        f"# Troubleshooting Report: {project_name}",
        "",
        "## Scope",
        f"- Project key: {summary.get('project_key', 'unknown')}",
        f"- Focus: {focus or 'general health review'}",
        "",
        "## Structural Findings",
    ]
    lines.extend(_issue_bullets(flow_health.get("issues", [])))
    lines.extend(
        [
            "",
            "## Recipe Risks",
        ]
    )
    lines.extend(_recipe_review_bullets(recipe_reviews))
    lines.extend(
        [
            "",
            "## Managed Folder Findings",
        ]
    )
    lines.extend(_folder_diagnosis_bullets(folder_diagnosis))
    lines.extend(
        [
            "",
            "## Code Environment Findings",
        ]
    )
    lines.extend(_code_env_bullets(code_env_diagnoses))
    lines.extend(
        [
            "",
            "## Scenario Run Signals",
        ]
    )
    lines.extend(_scenario_run_bullets(scenario_runs))
    lines.extend(_warnings_section((warnings or []) + flow_health.get("warnings", [])))
    return "\n".join(lines).strip() + "\n"


def generate_rag_audit_report(
    *,
    summary: dict[str, Any],
    detection: dict[str, Any],
    audit: dict[str, Any],
) -> str:
    """Render a dedicated RAG audit report."""

    project_name = summary.get("name") or summary.get("project_key") or "Unknown project"
    lines = [
        f"# RAG Audit Report: {project_name}",
        "",
        "## Detection",
        f"- RAG pipeline detected: {bool(detection.get('is_rag_pipeline'))}",
        f"- Detected components: {', '.join(detection.get('detected_components', [])) or 'none'}",
        f"- Dataset count reviewed: {audit.get('dataset_count', 0)}",
        "",
        "## Evidence",
    ]
    evidence = detection.get("evidence", [])
    if evidence:
        for item in evidence:
            recipe = item.get("recipe", "unknown")
            component = item.get("component", "unknown")
            signal = item.get("signal", "unknown")
            lines.append(f"- `{recipe}` suggests `{component}` via `{signal}`.")
    else:
        lines.append("- No strong RAG signals were detected.")

    lines.extend(
        [
            "",
            "## Main Risks",
        ]
    )
    lines.extend(_issue_bullets(audit.get("main_risks", [])))
    lines.extend(
        [
            "",
            "## Recommendations",
        ]
    )
    recommendations = audit.get("recommendations", [])
    if recommendations:
        for recommendation in recommendations:
            lines.append(f"- {recommendation}")
    else:
        lines.append("- No additional recommendations were generated.")
    return "\n".join(lines).strip() + "\n"


def _sentence_for_inventory(
    datasets: list[dict[str, Any]],
    recipes: list[dict[str, Any]],
    folders: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
) -> str:
    return (
        f"This project currently exposes {len(datasets)} dataset(s), "
        f"{len(recipes)} recipe(s), {len(folders)} managed folder(s) and "
        f"{len(scenarios)} scenario(s)."
    )


def _dataset_bullets(datasets: list[dict[str, Any]]) -> list[str]:
    if not datasets:
        return ["- No datasets were found."]
    lines: list[str] = []
    for dataset in datasets:
        name = dataset.get("name") or "unknown"
        dataset_type = dataset.get("type") or "unknown"
        connection = dataset.get("connection") or "unspecified"
        columns = dataset.get("schema_columns_count") or 0
        tags = ", ".join(dataset.get("tags", [])) or "none"
        lines.append(
            f"- `{name}`: type `{dataset_type}`, connection `{connection}`, "
            f"{columns} column(s), tags `{tags}`."
        )
    return lines


def _recipe_bullets(recipes: list[dict[str, Any]]) -> list[str]:
    if not recipes:
        return ["- No recipes were found."]
    lines: list[str] = []
    for recipe in recipes:
        name = recipe.get("name") or "unknown"
        recipe_type = recipe.get("type") or "unknown"
        inputs = ", ".join(recipe.get("inputs", [])) or "none"
        outputs = ", ".join(recipe.get("outputs", [])) or "none"
        lines.append(
            f"- `{name}`: type `{recipe_type}`, inputs `{inputs}`, outputs `{outputs}`."
        )
    return lines


def _folder_bullets(folders: list[dict[str, Any]]) -> list[str]:
    if not folders:
        return ["- No Managed Folders were found."]
    lines: list[str] = []
    for folder in folders:
        folder_id = folder.get("folder_id") or "unknown"
        folder_type = folder.get("type") or "unknown"
        connection = folder.get("connection") or "unspecified"
        lines.append(
            f"- `{folder_id}`: backend `{folder_type}`, connection `{connection}`."
        )
    return lines


def _scenario_bullets(scenarios: list[dict[str, Any]]) -> list[str]:
    if not scenarios:
        return ["- No scenarios were found."]
    lines: list[str] = []
    for scenario in scenarios:
        scenario_id = scenario.get("scenario_id") or "unknown"
        active = scenario.get("active")
        running = scenario.get("running")
        trigger_type = scenario.get("trigger_type") or "unknown"
        lines.append(
            f"- `{scenario_id}`: active `{active}`, running `{running}`, trigger `{trigger_type}`."
        )
    return lines


def _edge_bullets(edges: list[dict[str, Any]]) -> list[str]:
    if not edges:
        return ["- No Flow edges were found."]
    lines: list[str] = []
    for edge in edges:
        source = edge.get("source") or "unknown"
        target = edge.get("target") or "unknown"
        edge_type = edge.get("type") or "unknown"
        lines.append(f"- `{source}` -> `{target}` (`{edge_type}`).")
    return lines


def _recipe_binding_bullets(recipes: list[dict[str, Any]]) -> list[str]:
    if not recipes:
        return ["- No recipe bindings are available."]
    lines: list[str] = []
    for recipe in recipes:
        name = recipe.get("name") or "unknown"
        inputs = ", ".join(recipe.get("inputs", [])) or "none"
        outputs = ", ".join(recipe.get("outputs", [])) or "none"
        lines.append(f"- `{name}` consumes `{inputs}` and produces `{outputs}`.")
    return lines


def _issue_bullets(issues: list[dict[str, Any]]) -> list[str]:
    if not issues:
        return ["- No issues were detected."]
    lines: list[str] = []
    for issue in issues:
        severity = issue.get("severity") or "unknown"
        message = issue.get("message") or "No message provided."
        objects = issue.get("objects", [])
        object_suffix = ""
        if isinstance(objects, list) and objects:
            object_suffix = f" Affected objects: {', '.join(str(obj) for obj in objects)}."
        lines.append(f"- [{severity}] {message}{object_suffix}")
    return lines


def _folder_diagnosis_bullets(folder_diagnosis: dict[str, Any] | None) -> list[str]:
    if not folder_diagnosis:
        return ["- No Managed Folder diagnosis was collected."]
    analyses = folder_diagnosis.get("analyses", [])
    if not analyses:
        return [f"- {folder_diagnosis.get('summary', 'No Managed Folder issues were found.')}"]
    lines: list[str] = []
    for analysis in analyses:
        folder = analysis.get("folder", {})
        folder_id = folder.get("folder_id") or folder.get("name") or "unknown"
        issues = analysis.get("issues", [])
        if not issues:
            lines.append(f"- `{folder_id}`: no issues detected.")
            continue
        for issue in issues:
            severity = issue.get("severity") or "unknown"
            message = issue.get("message") or "No message provided."
            lines.append(f"- `{folder_id}` [{severity}]: {message}")
    return lines


def _code_env_bullets(code_env_diagnoses: list[dict[str, Any]]) -> list[str]:
    if not code_env_diagnoses:
        return ["- No code environment diagnosis was collected."]
    lines: list[str] = []
    for diagnosis in code_env_diagnoses:
        env_name = diagnosis.get("environment") or "unknown"
        issues = diagnosis.get("dependency_issues", [])
        if not issues:
            lines.append(f"- `{env_name}`: no issues detected.")
            continue
        for issue in issues:
            severity = issue.get("severity") or "unknown"
            message = issue.get("message") or "No message provided."
            lines.append(f"- `{env_name}` [{severity}]: {message}")
    return lines


def _recipe_review_bullets(recipe_reviews: list[dict[str, Any]]) -> list[str]:
    if not recipe_reviews:
        return ["- No recipe review findings were collected."]
    lines: list[str] = []
    for review in recipe_reviews:
        recipe = review.get("recipe") or "unknown"
        issues = review.get("issues", [])
        if not issues:
            lines.append(f"- `{recipe}`: no issues detected.")
            continue
        for issue in issues:
            severity = issue.get("severity") or "unknown"
            message = issue.get("message") or "No message provided."
            lines.append(f"- `{recipe}` [{severity}]: {message}")
    return lines


def _scenario_run_bullets(scenario_runs: list[dict[str, Any]]) -> list[str]:
    if not scenario_runs:
        return ["- No scenario runs were collected."]
    lines: list[str] = []
    for entry in scenario_runs:
        scenario_id = entry.get("scenario_id") or "unknown"
        runs = entry.get("runs", [])
        if not runs:
            lines.append(f"- `{scenario_id}`: no recent runs.")
            continue
        for run in runs:
            run_id = run.get("run_id") or "unknown"
            outcome = run.get("outcome") or "unknown"
            failed_steps = ", ".join(run.get("failed_steps", [])) or "none"
            lines.append(
                f"- `{scenario_id}` / `{run_id}`: outcome `{outcome}`, "
                f"failed steps `{failed_steps}`."
            )
    return lines


def _warnings_section(warnings: list[str]) -> list[str]:
    warnings = [warning for warning in warnings if warning]
    if not warnings:
        return []
    lines = [
        "",
        "## Collection Warnings",
    ]
    for warning in warnings:
        lines.append(f"- {warning}")
    return lines
