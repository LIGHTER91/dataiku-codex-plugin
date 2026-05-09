"""Operations-oriented summaries and readiness heuristics."""

from __future__ import annotations

from collections import Counter
from typing import Any


def build_scenario_dependency_map(
    *,
    project_key: str,
    scenarios: list[dict[str, Any]],
    known_datasets: list[str],
    known_recipes: list[str],
) -> dict[str, Any]:
    """Build a light dependency graph around scenarios and their referenced objects."""

    dataset_set = set(known_datasets)
    recipe_set = set(known_recipes)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for scenario in scenarios:
        scenario_id = str(scenario.get("scenario_id") or scenario.get("name") or "")
        if not scenario_id:
            continue
        nodes.append({"id": f"scenario:{scenario_id}", "type": "scenario", "name": scenario_id})
        references = _collect_named_references(scenario.get("steps", []), dataset_set | recipe_set)
        for ref_name in sorted(references):
            if ref_name in dataset_set:
                ref_type = "dataset"
            elif ref_name in recipe_set:
                ref_type = "recipe"
            else:
                continue
            nodes.append({"id": f"{ref_type}:{ref_name}", "type": ref_type, "name": ref_name})
            edges.append(
                {
                    "source": f"scenario:{scenario_id}",
                    "target": f"{ref_type}:{ref_name}",
                    "type": "depends_on",
                }
            )

    unique_nodes = _deduplicate_nodes(nodes)
    orphan_scenarios = [
        node["name"]
        for node in unique_nodes
        if node["type"] == "scenario"
        and not any(edge["source"] == node["id"] for edge in edges)
    ]
    return {
        "project_key": project_key,
        "nodes": unique_nodes,
        "edges": edges,
        "orphan_scenarios": orphan_scenarios,
        "summary": (
            f"Mapped {len([node for node in unique_nodes if node['type'] == 'scenario'])} "
            f"scenario(s) and {len(edges)} dependency edge(s)."
        ),
    }


def build_code_env_update_plan(
    diagnoses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Turn code environment diagnoses into an ordered update plan."""

    priorities: list[dict[str, Any]] = []
    for diagnosis in diagnoses:
        issues = diagnosis.get("dependency_issues", [])
        if not isinstance(issues, list):
            issues = []
        severity_counts = Counter(
            str(issue.get("severity", "low"))
            for issue in issues
            if isinstance(issue, dict)
        )
        priority_score = severity_counts.get("high", 0) * 3
        priority_score += severity_counts.get("medium", 0) * 2
        priority_score += severity_counts.get("low", 0)
        priorities.append(
            {
                "environment": diagnosis.get("environment"),
                "priority_score": priority_score,
                "issues_count": len(issues),
                "high_severity_issues": severity_counts.get("high", 0),
                "recommended_actions": diagnosis.get("recommended_installation_fix", []),
            }
        )

    ordered_priorities = sorted(
        priorities,
        key=lambda item: (
            -int(item["priority_score"]),
            -int(item["high_severity_issues"]),
            str(item["environment"]),
        ),
    )
    return {
        "environments": ordered_priorities,
        "summary": (
            f"Planned updates for {len(ordered_priorities)} code environment(s), "
            f"ordered by issue severity."
        ),
    }


def build_production_readiness_report(
    *,
    project_key: str,
    project_summary: dict[str, Any],
    flow_health: dict[str, Any],
    scenario_dependency_map: dict[str, Any],
    code_env_update_plan: dict[str, Any],
    plugin_usages: list[dict[str, Any]],
    ml_assets: dict[str, int],
) -> dict[str, Any]:
    """Aggregate project-level readiness signals into one report."""

    findings: list[dict[str, Any]] = []
    score = 100

    scenario_count = int(project_summary.get("scenarios_count", 0) or 0)
    if scenario_count == 0:
        findings.append(
            {
                "severity": "medium",
                "category": "missing_automation",
                "message": "No scenarios are configured for operational automation.",
            }
        )
        score -= 20

    flow_issues = flow_health.get("issues", [])
    if isinstance(flow_issues, list):
        for issue in flow_issues:
            if not isinstance(issue, dict):
                continue
            severity = str(issue.get("severity", "low"))
            findings.append(
                {
                    "severity": severity,
                    "category": f"flow_{issue.get('category', 'issue')}",
                    "message": str(issue.get("message", "Flow issue detected.")),
                }
            )
            if severity == "high":
                score -= 20
            elif severity == "medium":
                score -= 10
            else:
                score -= 3

    code_envs = code_env_update_plan.get("environments", [])
    if isinstance(code_envs, list) and code_envs:
        high_priority_envs = [
            env
            for env in code_envs
            if isinstance(env, dict) and int(env.get("priority_score", 0)) >= 3
        ]
        if high_priority_envs:
            findings.append(
                {
                    "severity": "medium",
                    "category": "code_env_debt",
                    "message": (
                        f"{len(high_priority_envs)} code environment(s) require dependency cleanup "
                        "before a confident production rollout."
                    ),
                }
            )
            score -= 12

    if not plugin_usages:
        findings.append(
            {
                "severity": "low",
                "category": "plugin_visibility",
                "message": "No plugin usages were reported by the project API surface.",
            }
        )
        score -= 3

    if int(ml_assets.get("saved_models", 0)) == 0 and int(ml_assets.get("ml_tasks", 0)) > 0:
        findings.append(
            {
                "severity": "medium",
                "category": "undeployed_ml_assets",
                "message": "Visual ML tasks exist but no saved model is deployed to the Flow yet.",
            }
        )
        score -= 10

    orphan_scenarios = scenario_dependency_map.get("orphan_scenarios", [])
    if isinstance(orphan_scenarios, list) and orphan_scenarios:
        findings.append(
            {
                "severity": "low",
                "category": "orphan_scenarios",
                "message": (
                    "Some scenarios do not reference any obvious dataset or recipe "
                    "dependency."
                ),
            }
        )
        score -= 5

    readiness = "ready_for_trial"
    if score < 55:
        readiness = "not_ready"
    elif score < 80:
        readiness = "needs_attention"

    return {
        "project_key": project_key,
        "readiness": readiness,
        "score": max(score, 0),
        "findings": findings,
        "summary": (
            f"Project {project_key} readiness is {readiness} with score {max(score, 0)}/100."
        ),
    }


def build_cost_performance_report(
    *,
    project_key: str,
    project_summary: dict[str, Any],
    flow_health: dict[str, Any],
    scenario_dependency_map: dict[str, Any],
    code_env_update_plan: dict[str, Any],
    plugin_usages: list[dict[str, Any]],
    ml_assets: dict[str, int],
    model_evaluation_store_count: int,
) -> dict[str, Any]:
    """Estimate operational cost and performance pressure from project signals."""

    datasets_count = int(project_summary.get("datasets_count", 0) or 0)
    recipes_count = int(project_summary.get("recipes_count", 0) or 0)
    folders_count = int(project_summary.get("managed_folders_count", 0) or 0)
    scenarios_count = int(project_summary.get("scenarios_count", 0) or 0)
    ml_tasks = int(ml_assets.get("ml_tasks", 0) or 0)
    saved_models = int(ml_assets.get("saved_models", 0) or 0)

    storage_pressure = min(
        100,
        datasets_count * 6
        + folders_count * 8
        + saved_models * 10
        + model_evaluation_store_count * 9,
    )
    orchestration_pressure = min(
        100,
        scenarios_count * 15
        + len(scenario_dependency_map.get("edges", [])) * 4,
    )
    ml_compute_pressure = min(
        100,
        ml_tasks * 20 + saved_models * 15 + model_evaluation_store_count * 12,
    )
    dependency_pressure = min(
        100,
        sum(
            int(environment.get("priority_score", 0) or 0) * 10
            for environment in code_env_update_plan.get("environments", [])
            if isinstance(environment, dict)
        ),
    )

    hotspots: list[dict[str, Any]] = []
    if storage_pressure >= 55:
        hotspots.append(
            {
                "severity": "medium",
                "category": "storage_pressure",
                "message": "Dataset, folder and model inventory suggest growing storage pressure.",
            }
        )
    if ml_compute_pressure >= 60:
        hotspots.append(
            {
                "severity": "medium",
                "category": "ml_compute_pressure",
                "message": (
                    "ML tasks and saved models may create meaningful compute "
                    "and retraining cost."
                ),
            }
        )
    if dependency_pressure >= 40:
        hotspots.append(
            {
                "severity": "medium",
                "category": "dependency_pressure",
                "message": (
                    "Code environment debt may translate into slower builds "
                    "and operational drag."
                ),
            }
        )
    if len(plugin_usages) >= 3:
        hotspots.append(
            {
                "severity": "low",
                "category": "plugin_surface_area",
                "message": (
                    "A wider plugin surface may increase maintenance and "
                    "upgrade coordination cost."
                ),
            }
        )

    flow_issues = flow_health.get("issues", [])
    if isinstance(flow_issues, list):
        for issue in flow_issues:
            if not isinstance(issue, dict):
                continue
            severity = str(issue.get("severity", "low"))
            if severity not in {"high", "medium"}:
                continue
            hotspots.append(
                {
                    "severity": severity,
                    "category": f"flow_{issue.get('category', 'issue')}",
                    "message": str(issue.get("message", "Flow issue detected.")),
                }
            )

    recommendations = _deduplicated_strings(
        [
            "Set retention expectations for scored datasets, evaluation stores and saved models.",
            "Schedule code env dependency cleanup before the next release window."
            if dependency_pressure >= 40
            else "",
            "Consolidate duplicate or orphaned Flow assets before scaling scenarios."
            if hotspots
            else "",
            "Track ML retraining cadence and evaluation-store growth as explicit cost indicators."
            if ml_compute_pressure >= 40
            else "",
        ]
    )

    overall_pressure = round(
        (storage_pressure * 0.25)
        + (orchestration_pressure * 0.2)
        + (ml_compute_pressure * 0.3)
        + (dependency_pressure * 0.25)
    )
    pressure_level = "low"
    if overall_pressure >= 65:
        pressure_level = "high"
    elif overall_pressure >= 40:
        pressure_level = "medium"

    return {
        "project_key": project_key,
        "cost_pressure_level": pressure_level,
        "overall_pressure_score": overall_pressure,
        "metrics": {
            "storage_pressure": storage_pressure,
            "orchestration_pressure": orchestration_pressure,
            "ml_compute_pressure": ml_compute_pressure,
            "dependency_pressure": dependency_pressure,
            "recipes_count": recipes_count,
        },
        "hotspots": hotspots,
        "recommendations": recommendations,
        "summary": (
            f"Cost and performance pressure for {project_key} is {pressure_level} "
            f"at {overall_pressure}/100."
        ),
    }


def build_production_readiness_checklist(
    *,
    project_key: str,
    readiness_report: dict[str, Any],
    cost_performance_report: dict[str, Any],
    scenario_dependency_map: dict[str, Any],
    code_env_update_plan: dict[str, Any],
    plugin_usages: list[dict[str, Any]],
    ml_assets: dict[str, int],
) -> dict[str, Any]:
    """Turn ops signals into a concrete production readiness checklist."""

    checklist_items = [
        _checklist_item(
            title="Automation scenarios configured",
            completed=not any(
                finding.get("category") == "missing_automation"
                for finding in readiness_report.get("findings", [])
                if isinstance(finding, dict)
            ),
            evidence=(
                f"{len(scenario_dependency_map.get('nodes', []))} scenario "
                "graph node(s) detected."
            ),
            owner="data_ops",
        ),
        _checklist_item(
            title="Code environments stabilized",
            completed=not any(
                isinstance(environment, dict)
                and int(environment.get("priority_score", 0) or 0) >= 3
                for environment in code_env_update_plan.get("environments", [])
            ),
            evidence=code_env_update_plan.get("summary", "No code env update plan available."),
            owner="platform_ops",
        ),
        _checklist_item(
            title="ML assets deployed intentionally",
            completed=int(ml_assets.get("saved_models", 0) or 0) > 0
            or int(ml_assets.get("ml_tasks", 0) or 0) == 0,
            evidence=(
                f"{int(ml_assets.get('ml_tasks', 0) or 0)} ML task(s), "
                f"{int(ml_assets.get('saved_models', 0) or 0)} saved model(s)."
            ),
            owner="ml_platform",
        ),
        _checklist_item(
            title="Cost and performance pressure understood",
            completed=str(cost_performance_report.get("cost_pressure_level")) != "high",
            evidence=cost_performance_report.get("summary", "No cost report available."),
            owner="project_owner",
        ),
        _checklist_item(
            title="Plugin surface inventoried",
            completed=bool(plugin_usages),
            evidence=f"{len(plugin_usages)} plugin usage record(s) reported.",
            owner="platform_ops",
        ),
    ]

    completed_items = sum(1 for item in checklist_items if item["completed"])
    readiness_gate = "blocked"
    if completed_items == len(checklist_items):
        readiness_gate = "ready"
    elif completed_items >= len(checklist_items) - 1:
        readiness_gate = "almost_ready"

    return {
        "project_key": project_key,
        "readiness_gate": readiness_gate,
        "completed_items": completed_items,
        "total_items": len(checklist_items),
        "checklist": checklist_items,
        "summary": (
            f"Production checklist for {project_key} is {readiness_gate} with "
            f"{completed_items}/{len(checklist_items)} items completed."
        ),
    }


def generate_governance_documentation(
    *,
    project_summary: dict[str, Any],
    readiness_report: dict[str, Any],
    cost_performance_report: dict[str, Any],
    production_checklist: dict[str, Any],
    plugin_usages: list[dict[str, Any]],
    code_env_update_plan: dict[str, Any],
) -> dict[str, Any]:
    """Generate governance-oriented markdown from ops reports."""

    project_name = project_summary.get("name") or project_summary.get("project_key") or "Unknown"
    lines = [
        f"# Governance Notes: {project_name}",
        "",
        "## Operational Posture",
        f"- Project key: {project_summary.get('project_key', 'unknown')}",
        f"- Readiness: {readiness_report.get('readiness', 'unknown')}",
        (
            "- Cost/performance pressure: "
            f"{cost_performance_report.get('cost_pressure_level', 'unknown')}"
        ),
        f"- Checklist gate: {production_checklist.get('readiness_gate', 'unknown')}",
        "",
        "## Key Findings",
    ]
    findings = readiness_report.get("findings", [])
    if isinstance(findings, list) and findings:
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            lines.append(
                f"- [{finding.get('severity', 'low')}] {finding.get('category', 'issue')}: "
                f"{finding.get('message', 'Issue detected.')}"
            )
    else:
        lines.append("- No readiness findings were reported.")

    lines.extend(
        [
            "",
            "## Platform Dependencies",
            f"- Plugin usage records: {len(plugin_usages)}",
        ]
    )
    if plugin_usages:
        for plugin_usage in plugin_usages:
            raw_usage_type = plugin_usage.get("usage_type", "unknown")
            usage_type = (
                ", ".join(str(item) for item in raw_usage_type)
                if isinstance(raw_usage_type, list)
                else str(raw_usage_type)
            )
            lines.append(
                f"- `{plugin_usage.get('plugin_id', 'unknown')}`: "
                f"{usage_type} usage."
            )
    else:
        lines.append("- No plugin usages were exposed by the API.")

    lines.extend(
        [
            "",
            "## Code Environment Follow-up",
        ]
    )
    environments = code_env_update_plan.get("environments", [])
    if isinstance(environments, list) and environments:
        for environment in environments:
            if not isinstance(environment, dict):
                continue
            lines.append(
                f"- `{environment.get('environment', 'unknown')}`: priority "
                f"{environment.get('priority_score', 0)}, "
                f"{environment.get('issues_count', 0)} issue(s)."
            )
    else:
        lines.append("- No code environment issues were detected.")

    lines.extend(
        [
            "",
            "## Release Checklist",
        ]
    )
    checklist = production_checklist.get("checklist", [])
    if isinstance(checklist, list) and checklist:
        for item in checklist:
            if not isinstance(item, dict):
                continue
            status = "done" if item.get("completed") else "pending"
            lines.append(
                f"- `{status}` {item.get('title', 'Unnamed item')} "
                f"({item.get('owner', 'owner')})"
            )
    else:
        lines.append("- No checklist items were generated.")

    return {
        "markdown": "\n".join(lines).strip() + "\n",
        "summary": "Generated governance documentation for "
        f"{project_summary.get('project_key', 'unknown')}.",
    }


def _collect_named_references(value: Any, known_names: set[str]) -> set[str]:
    references: set[str] = set()
    if isinstance(value, dict):
        for nested_value in value.values():
            references.update(_collect_named_references(nested_value, known_names))
        return references
    if isinstance(value, list):
        for nested_value in value:
            references.update(_collect_named_references(nested_value, known_names))
        return references
    if isinstance(value, str):
        if value in known_names:
            references.add(value)
        if ":" in value:
            suffix = value.rsplit(":", 1)[-1]
            if suffix in known_names:
                references.add(suffix)
    return references


def _deduplicate_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduplicated: dict[str, dict[str, Any]] = {}
    for node in nodes:
        node_id = str(node.get("id"))
        deduplicated[node_id] = node
    return list(deduplicated.values())


def _checklist_item(
    *,
    title: str,
    completed: bool,
    evidence: str,
    owner: str,
) -> dict[str, Any]:
    return {
        "title": title,
        "completed": completed,
        "evidence": evidence,
        "owner": owner,
    }


def _deduplicated_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered
