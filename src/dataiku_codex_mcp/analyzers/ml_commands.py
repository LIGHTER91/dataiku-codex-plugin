"""Catalog of reusable ML commands for V3.5.1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MLCommandDefinition:
    """One reusable ML command exposed by the catalog."""

    name: str
    display_name: str
    description: str
    algorithm_family: str
    algorithm_by_prediction_type: dict[str, str]
    examples: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    default_ml_backend_type: str = "PY_MEMORY"
    default_guess_policy: str = "DEFAULT"
    family: str = "prediction_flow"

    @property
    def supported_prediction_types(self) -> list[str]:
        return sorted(self.algorithm_by_prediction_type)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "family": self.family,
            "algorithm_family": self.algorithm_family,
            "supported_prediction_types": self.supported_prediction_types,
            "default_ml_backend_type": self.default_ml_backend_type,
            "default_guess_policy": self.default_guess_policy,
            "examples": list(self.examples),
            "aliases": list(self.aliases),
        }


ML_COMMANDS: tuple[MLCommandDefinition, ...] = (
    MLCommandDefinition(
        name="xgboost_prediction_flow",
        display_name="XGBoost Prediction Flow",
        description=(
            "Create a standard Prepare recipe and a Visual ML prediction task "
            "restricted to XGBoost."
        ),
        algorithm_family="xgboost",
        algorithm_by_prediction_type={
            "binary_classification": "XGBOOST_CLASSIFICATION",
            "multiclass": "XGBOOST_CLASSIFICATION",
            "regression": "XGBOOST_REGRESSION",
        },
        examples=(
            "set up xgboost on project X using dataset Y",
            "prepare an xgboost flow for predicting churn",
        ),
        aliases=("xgboost", "xgb"),
    ),
    MLCommandDefinition(
        name="lightgbm_prediction_flow",
        display_name="LightGBM Prediction Flow",
        description=(
            "Create a standard Prepare recipe and a Visual ML prediction task "
            "restricted to LightGBM."
        ),
        algorithm_family="lightgbm",
        algorithm_by_prediction_type={
            "binary_classification": "LIGHTGBM_CLASSIFICATION",
            "multiclass": "LIGHTGBM_CLASSIFICATION",
            "regression": "LIGHTGBM_REGRESSION",
        },
        examples=(
            "launch a lightgbm setup on this dataset",
            "bootstrap a lightgbm model for target Z",
        ),
        aliases=("lightgbm", "lgbm"),
    ),
    MLCommandDefinition(
        name="random_forest_prediction_flow",
        display_name="Random Forest Prediction Flow",
        description=(
            "Create a standard Prepare recipe and a Visual ML prediction task "
            "restricted to Random Forest."
        ),
        algorithm_family="random_forest",
        algorithm_by_prediction_type={
            "binary_classification": "RANDOM_FOREST_CLASSIFICATION",
            "multiclass": "RANDOM_FOREST_CLASSIFICATION",
            "regression": "RANDOM_FOREST_REGRESSION",
        },
        examples=(
            "set up a random forest baseline",
            "bootstrap a random forest prediction flow",
        ),
        aliases=("random_forest", "rf"),
    ),
    MLCommandDefinition(
        name="logistic_regression_prediction_flow",
        display_name="Logistic Regression Prediction Flow",
        description=(
            "Create a standard Prepare recipe and a Visual ML classification task "
            "restricted to logistic regression."
        ),
        algorithm_family="logistic_regression",
        algorithm_by_prediction_type={
            "binary_classification": "LOGISTIC_REGRESSION",
            "multiclass": "LOGISTIC_REGRESSION",
        },
        examples=(
            "set up a logistic regression baseline",
            "create a fast interpretable classifier",
        ),
        aliases=("logistic_regression", "logit"),
    ),
)


def list_ml_command_definitions() -> list[MLCommandDefinition]:
    """Return the ordered ML command catalog."""

    return list(ML_COMMANDS)


def get_ml_command_definition(name: str) -> MLCommandDefinition:
    """Resolve a command from its canonical name or alias."""

    normalized = name.strip().lower()
    for command in ML_COMMANDS:
        if normalized == command.name:
            return command
        if normalized in command.aliases:
            return command
    raise ValueError(f"Unknown ML command: {name}")


def resolve_command_algorithm(
    command: MLCommandDefinition,
    prediction_type: str,
) -> str:
    """Resolve the DSS algorithm identifier for a command and prediction type."""

    algorithm_name = command.algorithm_by_prediction_type.get(prediction_type)
    if algorithm_name is None:
        raise ValueError(
            f"The ML command {command.name} does not support prediction_type={prediction_type}."
        )
    return algorithm_name
