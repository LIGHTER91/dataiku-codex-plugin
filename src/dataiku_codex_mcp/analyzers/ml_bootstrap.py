"""Helpers for guided ML bootstrap workflows."""

from __future__ import annotations

import re
from typing import Any

NUMERIC_TYPES = {
    "bigint",
    "byte",
    "decimal",
    "double",
    "float",
    "int",
    "integer",
    "long",
    "number",
    "real",
    "short",
    "smallint",
    "tinyint",
}
BOOLEAN_TYPES = {"bool", "boolean"}
DATE_TYPES = {
    "date",
    "datetime",
    "timestamp",
    "timestamp with time zone",
    "timestamp without time zone",
}
STRING_TYPES = {"string", "str", "varchar", "char", "text"}

IDENTIFIER_TOKENS = (
    "id",
    "uuid",
    "guid",
    "email",
    "phone",
    "address",
    "url",
    "uri",
    "path",
    "token",
    "key",
    "hash",
)
TEXT_LIKE_TOKENS = (
    "body",
    "comment",
    "content",
    "description",
    "html",
    "markdown",
    "message",
    "note",
    "payload",
    "text",
)
TEMPORAL_TOKENS = (
    "created",
    "date",
    "time",
    "timestamp",
    "updated",
)
BINARY_HINT_TOKENS = (
    "active",
    "approved",
    "cancelled",
    "churn",
    "converted",
    "default",
    "flag",
    "fraud",
    "is_",
    "has_",
    "retained",
    "returned",
)
MULTICLASS_HINT_TOKENS = (
    "category",
    "channel",
    "class",
    "country",
    "label",
    "reason",
    "segment",
    "stage",
    "status",
    "tier",
    "type",
)
REGRESSION_HINT_TOKENS = (
    "amount",
    "count",
    "cost",
    "days",
    "duration",
    "margin",
    "minutes",
    "price",
    "quantity",
    "revenue",
    "score",
    "total",
    "value",
)

USER_PREDICTION_TYPES = {
    "binary": "binary_classification",
    "binary_classification": "binary_classification",
    "classification": "classification",
    "multiclass": "multiclass",
    "regression": "regression",
}
DSS_PREDICTION_TYPES = {
    "binary_classification": "BINARY_CLASSIFICATION",
    "multiclass": "MULTICLASS",
    "regression": "REGRESSION",
}


def build_target_suggestions(
    dataset_name: str,
    columns: list[dict[str, Any]],
    *,
    limit: int = 5,
) -> dict[str, Any]:
    """Rank likely prediction targets from a dataset schema."""

    candidates: list[dict[str, Any]] = []
    excluded_columns: list[dict[str, str]] = []
    for column in columns:
        suggestion = analyze_target_column(column)
        if suggestion["eligible"]:
            candidates.append(
                {
                    "target_variable": suggestion["target_variable"],
                    "prediction_type": suggestion["prediction_type"],
                    "recommended_algorithm": "xgboost",
                    "score": suggestion["score"],
                    "priority": suggestion["priority"],
                    "reasoning": suggestion["reasoning"],
                    "warnings": suggestion["warnings"],
                }
            )
        else:
            excluded_columns.append(
                {
                    "column_name": suggestion["target_variable"],
                    "reason": suggestion["reasoning"],
                }
            )

    candidates.sort(
        key=lambda item: (-int(item["score"]), str(item["target_variable"]).lower())
    )
    selected_candidates = candidates[: max(1, limit)] if candidates else []
    summary = (
        f"Found {len(selected_candidates)} likely prediction target(s) in {dataset_name}."
        if selected_candidates
        else (
            "No strong prediction targets were found from schema-only inspection. "
            "You may still choose a target manually if you know the dataset semantics."
        )
    )
    return {
        "dataset_name": dataset_name,
        "summary": summary,
        "candidates": selected_candidates,
        "excluded_columns": excluded_columns,
    }


def analyze_target_column(column: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized target suggestion profile for a column."""

    column_name = str(column.get("name") or "").strip()
    raw_type = str(column.get("type") or "string").strip().lower()
    normalized_name = normalize_identifier(column_name)
    canonical_type = canonicalize_column_type(raw_type)
    warnings: list[str] = []

    if not column_name:
        return {
            "target_variable": "",
            "eligible": False,
            "prediction_type": None,
            "score": 0,
            "priority": "low",
            "reasoning": "Unnamed columns cannot be used as reliable prediction targets.",
            "warnings": warnings,
        }

    if _contains_any(normalized_name, TEXT_LIKE_TOKENS):
        return {
            "target_variable": column_name,
            "eligible": False,
            "prediction_type": None,
            "score": 0,
            "priority": "low",
            "reasoning": (
                "Text-heavy columns are poor default XGBoost targets without "
                "task-specific preprocessing."
            ),
            "warnings": warnings,
        }

    if canonical_type == "date" or _contains_any(normalized_name, TEMPORAL_TOKENS):
        return {
            "target_variable": column_name,
            "eligible": False,
            "prediction_type": None,
            "score": 0,
            "priority": "low",
            "reasoning": (
                "Temporal columns are better suited to time-series workflows "
                "than generic XGBoost prediction setup."
            ),
            "warnings": warnings,
        }

    binary_hint = _contains_any(normalized_name, BINARY_HINT_TOKENS)
    multiclass_hint = _contains_any(normalized_name, MULTICLASS_HINT_TOKENS)
    regression_hint = _contains_any(normalized_name, REGRESSION_HINT_TOKENS)
    identifier_hint = _looks_like_identifier(normalized_name)

    if identifier_hint and not (binary_hint or multiclass_hint or regression_hint):
        return {
            "target_variable": column_name,
            "eligible": False,
            "prediction_type": None,
            "score": 0,
            "priority": "low",
            "reasoning": (
                "Identifier-like columns are usually lookup keys, not useful "
                "prediction targets."
            ),
            "warnings": warnings,
        }

    if canonical_type == "boolean":
        return _eligible_result(
            column_name,
            prediction_type="binary_classification",
            score=96,
            priority="high",
            reasoning="Boolean columns are strong default targets for binary classification.",
            warnings=warnings,
        )

    if binary_hint:
        score = 92 if canonical_type in {"boolean", "numeric"} else 86
        if canonical_type == "string":
            warnings.append(
                "This looks like a binary label from its name, but the string "
                "encoding may need cleanup."
            )
        return _eligible_result(
            column_name,
            prediction_type="binary_classification",
            score=score,
            priority="high",
            reasoning="The column name strongly suggests a yes/no business outcome.",
            warnings=warnings,
        )

    if regression_hint and canonical_type == "numeric":
        return _eligible_result(
            column_name,
            prediction_type="regression",
            score=88,
            priority="high",
            reasoning="The column name and numeric type fit a regression objective.",
            warnings=warnings,
        )

    if multiclass_hint and canonical_type in {"string", "numeric"}:
        if canonical_type == "numeric":
            warnings.append(
                "Numeric category codes may need remapping or casting for easier interpretation."
            )
        return _eligible_result(
            column_name,
            prediction_type="multiclass",
            score=84,
            priority="high",
            reasoning=(
                "The column name suggests a categorical business outcome with "
                "multiple classes."
            ),
            warnings=warnings,
        )

    if canonical_type == "numeric":
        return _eligible_result(
            column_name,
            prediction_type="regression",
            score=72,
            priority="medium",
            reasoning=(
                "Numeric columns are valid regression targets when no stronger "
                "label is available."
            ),
            warnings=warnings,
        )

    if canonical_type == "string":
        warnings.append(
            "Schema-only inspection cannot estimate class cardinality, so "
            "verify this is not a high-cardinality identifier."
        )
        return _eligible_result(
            column_name,
            prediction_type="multiclass",
            score=64,
            priority="medium",
            reasoning=(
                "Categorical string columns are workable default targets for "
                "multiclass classification."
            ),
            warnings=warnings,
        )

    return {
        "target_variable": column_name,
        "eligible": False,
        "prediction_type": None,
        "score": 0,
        "priority": "low",
        "reasoning": "The column type is not a strong default fit for guided XGBoost bootstrap.",
        "warnings": warnings,
    }


def resolve_prediction_type(
    column: dict[str, Any],
    requested_prediction_type: str | None = None,
) -> dict[str, Any]:
    """Resolve a user-facing and DSS-facing prediction type for a target column."""

    analysis = analyze_target_column(column)
    inferred_prediction_type = analysis["prediction_type"]
    if inferred_prediction_type is None:
        raise ValueError(analysis["reasoning"])

    if requested_prediction_type is None:
        resolved_prediction_type = inferred_prediction_type
    else:
        normalized_requested = USER_PREDICTION_TYPES.get(
            requested_prediction_type.strip().lower()
        )
        if normalized_requested is None:
            raise ValueError(
                "Unsupported prediction_type. Use binary_classification, "
                "multiclass, regression, or classification."
            )
        if normalized_requested == "classification":
            resolved_prediction_type = (
                "binary_classification"
                if inferred_prediction_type == "binary_classification"
                else "multiclass"
            )
        else:
            resolved_prediction_type = normalized_requested

    return {
        **analysis,
        "prediction_type": resolved_prediction_type,
        "dss_prediction_type": DSS_PREDICTION_TYPES[resolved_prediction_type],
    }


def build_prediction_blueprint(
    command_name: str,
    dataset_name: str,
    target_variable: str,
    *,
    algorithm_name: str,
    prepared_dataset_name: str | None = None,
    prepare_recipe_name: str | None = None,
) -> dict[str, str]:
    """Build deterministic names for generic prediction-flow assets."""

    dataset_slug = slugify(dataset_name)
    target_slug = slugify(target_variable)
    command_slug = slugify(command_name)
    return {
        "prepared_dataset_name": (
            prepared_dataset_name
            if prepared_dataset_name
            else f"{dataset_slug}_prepared_{target_slug}"
        ),
        "prepare_recipe_name": (
            prepare_recipe_name
            if prepare_recipe_name
            else f"prepare_{dataset_slug}_{target_slug}"
        ),
        "analysis_label": f"{command_slug}_{dataset_slug}_{target_slug}",
        "saved_model_name": f"{command_slug}_{target_slug}_model",
        "algorithm_name": algorithm_name,
    }


def canonicalize_column_type(raw_type: str) -> str:
    """Collapse Dataiku column types into a smaller heuristic space."""

    normalized = raw_type.strip().lower()
    if normalized in BOOLEAN_TYPES:
        return "boolean"
    if normalized in NUMERIC_TYPES:
        return "numeric"
    if normalized in DATE_TYPES:
        return "date"
    if normalized in STRING_TYPES:
        return "string"
    return "other"


def normalize_identifier(value: str) -> str:
    """Normalize a name for token matching."""

    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return normalized


def slugify(value: str) -> str:
    """Create a deterministic DSS-friendly identifier."""

    normalized = normalize_identifier(value)
    return normalized[:48] if normalized else "unnamed"


def _eligible_result(
    column_name: str,
    *,
    prediction_type: str,
    score: int,
    priority: str,
    reasoning: str,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "target_variable": column_name,
        "eligible": True,
        "prediction_type": prediction_type,
        "score": score,
        "priority": priority,
        "reasoning": reasoning,
        "warnings": warnings,
    }


def _contains_any(normalized_name: str, tokens: tuple[str, ...]) -> bool:
    return any(token in normalized_name for token in tokens)


def _looks_like_identifier(normalized_name: str) -> bool:
    parts = normalized_name.split("_")
    if parts == ["id"]:
        return True
    return any(part in IDENTIFIER_TOKENS for part in parts)
