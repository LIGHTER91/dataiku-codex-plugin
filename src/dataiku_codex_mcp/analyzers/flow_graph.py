"""Flow graph reconstruction and health heuristics."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from collections.abc import Iterable
from typing import Any


def build_flow_graph(
    *,
    project_key: str,
    datasets: list[dict[str, Any]],
    recipes: list[dict[str, Any]],
    folders: list[dict[str, Any]],
    recipe_details_by_name: dict[str, dict[str, Any]],
    include_recipes: bool = True,
    include_folders: bool = True,
) -> dict[str, Any]:
    """Build a JSON-safe dependency graph from project objects."""

    dataset_names = {dataset["name"] for dataset in datasets if dataset.get("name")}
    folder_ids = {
        folder["folder_id"]
        for folder in folders
        if folder.get("folder_id")
    }

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for dataset in datasets:
        name = dataset.get("name")
        if name:
            nodes.append({"id": f"dataset:{name}", "type": "dataset", "name": name})

    if include_folders:
        for folder in folders:
            folder_id = folder.get("folder_id")
            if folder_id:
                nodes.append(
                    {"id": f"folder:{folder_id}", "type": "managed_folder", "name": folder_id}
                )

    if include_recipes:
        for recipe in recipes:
            recipe_name = recipe.get("name")
            if recipe_name:
                nodes.append({"id": f"recipe:{recipe_name}", "type": "recipe", "name": recipe_name})

    for recipe in recipes:
        recipe_name = recipe.get("name")
        if not recipe_name:
            continue
        recipe_node = f"recipe:{recipe_name}"
        for binding in recipe.get("inputs", []):
            edge = _binding_to_edge(
                binding=binding,
                dataset_names=dataset_names,
                folder_ids=folder_ids,
                default_prefix="dataset",
                target=recipe_node,
                direction="input",
            )
            if edge is not None:
                edges.append(edge)
        for binding in recipe.get("outputs", []):
            edge = _binding_to_edge(
                binding=binding,
                dataset_names=dataset_names,
                folder_ids=folder_ids,
                default_prefix="dataset",
                source=recipe_node,
                direction="output",
            )
            if edge is not None:
                edges.append(edge)

        folder_refs = detect_folder_references(
            recipe_details_by_name.get(recipe_name, {}).get("code"),
            folder_ids,
        )
        for folder_ref in folder_refs:
            edges.append(
                {
                    "source": f"folder:{folder_ref}",
                    "target": recipe_node,
                    "type": "folder_input",
                }
            )

    topological_order = _topological_order(nodes, edges)
    orphan_nodes = _find_orphans(nodes, edges)
    warnings: list[str] = []
    if orphan_nodes:
        warnings.append(f"Detected {len(orphan_nodes)} orphan node(s) in the Flow graph.")

    summary = (
        f"Project {project_key} graph contains {len(nodes)} node(s) and "
        f"{len(edges)} edge(s)."
    )
    return {
        "nodes": nodes,
        "edges": edges,
        "topological_order": topological_order,
        "orphan_nodes": orphan_nodes,
        "warnings": warnings,
        "summary": summary,
    }


def analyze_flow_health(
    *,
    graph: dict[str, Any],
    recipes: list[dict[str, Any]],
    datasets: list[dict[str, Any]],
    folders: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze high-level structural issues in the reconstructed Flow."""

    issues: list[dict[str, Any]] = []
    orphan_datasets = [
        node["name"]
        for node in graph["orphan_nodes"]
        if node.get("type") == "dataset"
    ]
    if orphan_datasets:
        issues.append(
            {
                "severity": "medium",
                "category": "orphan_datasets",
                "message": "Some datasets are disconnected from the active Flow.",
                "objects": orphan_datasets,
            }
        )

    recipes_without_outputs = [
        recipe["name"]
        for recipe in recipes
        if recipe.get("name") and not recipe.get("outputs")
    ]
    if recipes_without_outputs:
        issues.append(
            {
                "severity": "high",
                "category": "recipes_without_outputs",
                "message": "Some recipes have no declared outputs.",
                "objects": recipes_without_outputs,
            }
        )

    signatures = Counter(
        (
            tuple(sorted(recipe.get("inputs", []))),
            tuple(sorted(recipe.get("outputs", []))),
        )
        for recipe in recipes
    )
    duplicate_signature_names = {
        signature
        for signature, count in signatures.items()
        if count > 1
    }
    duplicated_logic = [
        recipe["name"]
        for recipe in recipes
        if (
            tuple(sorted(recipe.get("inputs", []))),
            tuple(sorted(recipe.get("outputs", []))),
        )
        in duplicate_signature_names
    ]
    if duplicated_logic:
        issues.append(
            {
                "severity": "medium",
                "category": "duplicated_logic",
                "message": "Several recipes appear to duplicate the same bindings.",
                "objects": duplicated_logic,
            }
        )

    object_names = [
        obj_name
        for obj_name in (
            [dataset.get("name") for dataset in datasets]
            + [recipe.get("name") for recipe in recipes]
            + [folder.get("folder_id") for folder in folders]
        )
        if obj_name
    ]
    if _mixed_naming_styles(object_names):
        issues.append(
            {
                "severity": "low",
                "category": "naming_inconsistencies",
                "message": "Object names mix different naming styles.",
                "objects": object_names,
            }
        )

    issues.append(
        {
            "severity": "low",
            "category": "missing_flow_zones",
            "message": "No Flow zone information is exposed by the current wrapper.",
            "objects": [],
        }
    )

    return {
        "issues": issues,
        "summary": {
            "issue_count": len(issues),
            "orphan_nodes": len(graph["orphan_nodes"]),
            "recipe_count": len(recipes),
        },
        "warnings": graph.get("warnings", []),
    }


def generate_project_map(
    *,
    graph: dict[str, Any],
    datasets: list[dict[str, Any]],
    recipes: list[dict[str, Any]],
    folders: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate a compact map suited for high-level project orientation."""

    return {
        "nodes": graph["nodes"],
        "edges": graph["edges"],
        "summary": (
            f"The project contains {len(datasets)} dataset(s), {len(recipes)} recipe(s) "
            f"and {len(folders)} managed folder(s)."
        ),
        "warnings": graph.get("warnings", []),
    }


def detect_folder_references(code: Any, folder_ids: Iterable[str]) -> list[str]:
    """Find folder identifiers referenced directly in recipe code."""

    if not isinstance(code, str):
        return []
    matches: list[str] = []
    for folder_id in folder_ids:
        if folder_id and folder_id in code and folder_id not in matches:
            matches.append(folder_id)
    return matches


def _binding_to_edge(
    *,
    binding: str,
    dataset_names: set[str],
    folder_ids: set[str],
    default_prefix: str,
    direction: str,
    source: str | None = None,
    target: str | None = None,
) -> dict[str, Any] | None:
    if not binding:
        return None
    if binding in folder_ids:
        node_id = f"folder:{binding}"
        edge_type = "folder_input" if direction == "input" else "folder_output"
    elif binding in dataset_names:
        node_id = f"dataset:{binding}"
        edge_type = "dataset_input" if direction == "input" else "dataset_output"
    else:
        node_id = f"{default_prefix}:{binding}"
        edge_type = "unknown_binding"

    if direction == "input":
        return {"source": node_id, "target": target, "type": edge_type}
    return {"source": source, "target": node_id, "type": edge_type}


def _topological_order(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[str]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    indegree: dict[str, int] = {node["id"]: 0 for node in nodes}
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        if target not in adjacency[source]:
            adjacency[source].add(target)
            indegree[target] = indegree.get(target, 0) + 1
            indegree.setdefault(source, 0)

    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    ordered: list[str] = []
    while queue:
        current = queue.popleft()
        ordered.append(current)
        for target in sorted(adjacency.get(current, set())):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if len(ordered) != len(indegree):
        remaining = sorted(node_id for node_id in indegree if node_id not in ordered)
        ordered.extend(remaining)
    return ordered


def _find_orphans(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    connected: set[str] = set()
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if isinstance(source, str):
            connected.add(source)
        if isinstance(target, str):
            connected.add(target)
    return [node for node in nodes if node["id"] not in connected]


def _mixed_naming_styles(names: list[str]) -> bool:
    styles = set()
    for name in names:
        if name.isupper():
            styles.add("upper")
        elif "_" in name and name.lower() == name:
            styles.add("snake")
        else:
            styles.add("other")
    return len(styles) > 1
