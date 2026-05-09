"""Natural-language routing for reusable ML commands."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from dataiku_codex_mcp.analyzers.ml_commands import get_ml_command_definition


@dataclass(frozen=True)
class RoutedMLIntent:
    """Structured routing result for one ML-oriented user intent."""

    intent_type: str
    resolved_tool: str | None
    requires_approval: bool
    project_key: str | None
    dataset_name: str | None
    command_name: str | None
    target_variable: str | None
    metric_name: str | None
    confidence: float
    missing_fields: tuple[str, ...]
    explanation: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_type": self.intent_type,
            "resolved_tool": self.resolved_tool,
            "requires_approval": self.requires_approval,
            "project_key": self.project_key,
            "dataset_name": self.dataset_name,
            "command_name": self.command_name,
            "target_variable": self.target_variable,
            "metric_name": self.metric_name,
            "confidence": self.confidence,
            "missing_fields": list(self.missing_fields),
            "explanation": self.explanation,
            "summary": self.summary,
        }


_PROJECT_PATTERNS = (
    re.compile(r"\b(?:project|projet)\s+([A-Za-z0-9_-]+)", re.IGNORECASE),
    re.compile(r"\b(?:sur|on)\s+([A-Z][A-Za-z0-9_-]{1,})\b"),
)
_DATASET_PATTERNS = (
    re.compile(r"\b(?:dataset|table|jeu(?:\s+de)?\s+donnees)\s+([A-Za-z0-9_-]+)", re.IGNORECASE),
)
_TARGET_PATTERNS = (
    re.compile(
        r"\b(?:predict|predicting|predire|for\s+predicting|pour\s+predire|target|cible)\s+([A-Za-z0-9_]+)",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:to|pour)\s+([A-Za-z0-9_]+)\s*$", re.IGNORECASE),
)
_METRIC_PATTERNS = (
    re.compile(r"\b(?:metric|metrique|by|sur)\s+([A-Za-z0-9_]+)", re.IGNORECASE),
)


def route_ml_intent(
    text: str,
    *,
    default_project_key: str | None = None,
    default_dataset_name: str | None = None,
) -> dict[str, Any]:
    """Route a free-form ML request to a reusable MCP command."""

    normalized = " ".join(text.strip().split())
    lowered = normalized.lower()

    project_key = _extract_identifier(normalized, _PROJECT_PATTERNS) or default_project_key
    dataset_name = _extract_identifier(normalized, _DATASET_PATTERNS) or default_dataset_name
    target_variable = _extract_identifier(normalized, _TARGET_PATTERNS)
    metric_name = _extract_identifier(normalized, _METRIC_PATTERNS)
    command_name = _detect_command_name(lowered)

    if _is_target_suggestion_request(lowered):
        missing_fields = _missing_fields(dataset_name, project_key)
        route = RoutedMLIntent(
            intent_type="suggest_prediction_targets",
            resolved_tool="dataiku_suggest_prediction_targets",
            requires_approval=False,
            project_key=project_key,
            dataset_name=dataset_name,
            command_name=None,
            target_variable=None,
            metric_name=None,
            confidence=_confidence_score(
                base=0.72,
                project_key=project_key,
                dataset_name=dataset_name,
            ),
            missing_fields=missing_fields,
            explanation=(
                "The request is asking what can be predicted from a dataset, so it routes "
                "to target discovery rather than a write action."
            ),
            summary=_build_summary(
                "Suggest prediction targets",
                project_key=project_key,
                dataset_name=dataset_name,
                command_name=None,
                target_variable=None,
            ),
        )
        return route.to_dict()

    if _is_deploy_request(lowered):
        missing_fields = tuple(field for field in ("project_key",) if project_key is None)
        route = RoutedMLIntent(
            intent_type="deploy_best_model",
            resolved_tool="dataiku_run_routed_ml_intent",
            requires_approval=True,
            project_key=project_key,
            dataset_name=None,
            command_name=None,
            target_variable=None,
            metric_name=metric_name,
            confidence=_confidence_score(base=0.76, project_key=project_key, dataset_name=None),
            missing_fields=missing_fields,
            explanation=(
                "The request is asking to deploy a trained model, so the router will select "
                "the latest task and then choose the best trained model."
            ),
            summary=_build_summary(
                "Deploy the best trained model from the latest ML task",
                project_key=project_key,
                dataset_name=None,
                command_name=None,
                target_variable=None,
            ),
        )
        return route.to_dict()

    if _is_training_request(lowered):
        missing_fields = tuple(field for field in ("project_key",) if project_key is None)
        route = RoutedMLIntent(
            intent_type="train_latest_ml_task",
            resolved_tool="dataiku_run_routed_ml_intent",
            requires_approval=True,
            project_key=project_key,
            dataset_name=None,
            command_name=None,
            target_variable=None,
            metric_name=None,
            confidence=_confidence_score(base=0.74, project_key=project_key, dataset_name=None),
            missing_fields=missing_fields,
            explanation=(
                "The request is asking to train an ML task, so the router will pick the "
                "latest available Visual ML task in the target project."
            ),
            summary=_build_summary(
                "Train the latest Visual ML task",
                project_key=project_key,
                dataset_name=None,
                command_name=None,
                target_variable=None,
            ),
        )
        return route.to_dict()

    if command_name is not None or _is_bootstrap_request(lowered):
        missing_fields_list: list[str] = []
        if project_key is None:
            missing_fields_list.append("project_key")
        if dataset_name is None:
            missing_fields_list.append("dataset_name")
        if command_name is None:
            missing_fields_list.append("command_name")
        route = RoutedMLIntent(
            intent_type="bootstrap_ml_command",
            resolved_tool="dataiku_run_routed_ml_intent",
            requires_approval=True,
            project_key=project_key,
            dataset_name=dataset_name,
            command_name=command_name,
            target_variable=target_variable,
            metric_name=None,
            confidence=_confidence_score(
                base=0.8,
                project_key=project_key,
                dataset_name=dataset_name,
            ),
            missing_fields=tuple(missing_fields_list),
            explanation=(
                "The request looks like an ML setup request, so it routes to the reusable "
                "ML command catalog instead of generating a new setup script."
            ),
            summary=_build_summary(
                "Run an ML bootstrap command",
                project_key=project_key,
                dataset_name=dataset_name,
                command_name=command_name,
                target_variable=target_variable,
            ),
        )
        return route.to_dict()

    route = RoutedMLIntent(
        intent_type="unknown",
        resolved_tool=None,
        requires_approval=False,
        project_key=project_key,
        dataset_name=dataset_name,
        command_name=command_name,
        target_variable=target_variable,
        metric_name=metric_name,
        confidence=0.2,
        missing_fields=(),
        explanation=(
            "The text does not match the supported ML routing patterns yet. "
            "Prefer explicit requests such as setup xgboost, train latest task, "
            "deploy best model or show me what I can predict."
        ),
        summary="Could not route the request to a supported ML command.",
    )
    return route.to_dict()


def _detect_command_name(text: str) -> str | None:
    alias_candidates = (
        "xgb",
        "xgboost",
        "lightgbm",
        "lgbm",
        "random forest",
        "random_forest",
        "rf",
        "logistic regression",
        "logistic_regression",
        "logit",
    )
    normalized_text = text.replace("-", " ").replace("/", " ")
    for alias in alias_candidates:
        if alias in normalized_text:
            canonical_alias = alias.replace(" ", "_")
            try:
                return get_ml_command_definition(canonical_alias).name
            except ValueError:
                continue
    return None


def _extract_identifier(text: str, patterns: tuple[re.Pattern[str], ...]) -> str | None:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def _is_bootstrap_request(text: str) -> bool:
    return any(
        token in text
        for token in (
            "set up",
            "setup",
            "bootstrap",
            "prepare flow",
            "baseline model",
            "modele",
            "model on",
        )
    )


def _is_training_request(text: str) -> bool:
    return "train" in text and any(token in text for token in ("task", "latest", "model"))


def _is_deploy_request(text: str) -> bool:
    return "deploy" in text and any(token in text for token in ("best", "model", "saved model"))


def _is_target_suggestion_request(text: str) -> bool:
    return any(
        token in text
        for token in (
            "what can i predict",
            "what could i predict",
            "show me what i can predict",
            "show possible predictions",
            "qu est ce que je peux predire",
            "que puis je predire",
            "prediction targets",
        )
    )


def _missing_fields(dataset_name: str | None, project_key: str | None) -> tuple[str, ...]:
    missing_fields: list[str] = []
    if project_key is None:
        missing_fields.append("project_key")
    if dataset_name is None:
        missing_fields.append("dataset_name")
    return tuple(missing_fields)


def _confidence_score(
    *,
    base: float,
    project_key: str | None,
    dataset_name: str | None,
) -> float:
    score = base
    if project_key is not None:
        score += 0.1
    if dataset_name is not None:
        score += 0.08
    return min(score, 0.98)


def _build_summary(
    action: str,
    *,
    project_key: str | None,
    dataset_name: str | None,
    command_name: str | None,
    target_variable: str | None,
) -> str:
    parts = [action]
    if command_name:
        parts.append(f"using {command_name}")
    if project_key:
        parts.append(f"on project {project_key}")
    if dataset_name:
        parts.append(f"with dataset {dataset_name}")
    if target_variable:
        parts.append(f"for target {target_variable}")
    return " ".join(parts) + "."
