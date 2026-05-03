"""Policy engine and RBAC helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from dataiku_codex_mcp.config import AppSettings, PolicyDefaultDecision
from dataiku_codex_mcp.errors import ConfigurationError
from dataiku_codex_mcp.identity import ActorContext
from dataiku_codex_mcp.permissions import PermissionLevel


def _tuple_from_values(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value),)


class PolicyRule(BaseModel):
    """Single allow or deny rule."""

    effect: Literal["allow", "deny"]
    tools: tuple[str, ...] = ("*",)
    levels: tuple[str, ...] = Field(default_factory=tuple)
    modes: tuple[str, ...] = Field(default_factory=tuple)
    projects: tuple[str, ...] = Field(default_factory=tuple)
    principals: tuple[str, ...] = Field(default_factory=tuple)
    roles: tuple[str, ...] = Field(default_factory=tuple)
    teams: tuple[str, ...] = Field(default_factory=tuple)
    scopes: tuple[str, ...] = Field(default_factory=tuple)
    auth_modes: tuple[str, ...] = Field(default_factory=tuple)
    require_authenticated: bool | None = None
    reason: str | None = None

    @field_validator(
        "tools",
        "levels",
        "modes",
        "projects",
        "principals",
        "roles",
        "teams",
        "scopes",
        "auth_modes",
        mode="before",
    )
    @classmethod
    def _coerce_tuple_fields(cls, value: Any) -> tuple[str, ...]:
        return _tuple_from_values(value)


class PolicyConfig(BaseModel):
    """Structured policy configuration."""

    default_decision: PolicyDefaultDecision = PolicyDefaultDecision.ALLOW
    principal_roles: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    team_roles: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    tool_role_bindings: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    rules: tuple[PolicyRule, ...] = Field(default_factory=tuple)

    @field_validator("principal_roles", "team_roles", "tool_role_bindings", mode="before")
    @classmethod
    def _coerce_role_maps(cls, value: Any) -> dict[str, tuple[str, ...]]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("Role maps must be objects keyed by principal/team/tool pattern.")
        return {str(key): _tuple_from_values(raw_value) for key, raw_value in value.items()}


@dataclass(frozen=True)
class PolicyDecision:
    """Final policy decision for a tool invocation."""

    allowed: bool
    reason: str
    source: str
    matched_rule_index: int | None = None
    effective_roles: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""

        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "source": self.source,
            "matched_rule_index": self.matched_rule_index,
            "effective_roles": list(self.effective_roles),
        }


class PolicyEngine:
    """Evaluate allow/deny rules and per-tool RBAC bindings."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.config = self._load_config(settings)

    def resolve_effective_roles(self, actor: ActorContext) -> tuple[str, ...]:
        """Merge direct actor roles with principal/team policy bindings."""

        resolved = set(actor.roles)
        resolved.update(self.config.principal_roles.get(actor.subject, ()))
        for team in actor.teams:
            resolved.update(self.config.team_roles.get(team, ()))
        return tuple(sorted(resolved))

    def authorize(
        self,
        *,
        actor: ActorContext,
        tool_name: str,
        level: PermissionLevel,
        project_key: str | None,
        mode: str,
    ) -> PolicyDecision:
        """Authorize a tool call for the given actor and context."""

        effective_roles = self.resolve_effective_roles(actor)
        if self.settings.team_allowlist and actor.source == "remote":
            allowed_teams = set(self.settings.team_allowlist)
            if not allowed_teams.intersection(actor.teams):
                return PolicyDecision(
                    allowed=False,
                    reason="The caller team is outside the configured team allowlist.",
                    source="team_allowlist",
                    effective_roles=effective_roles,
                )

        required_roles = self._required_roles_for_tool(tool_name)
        if required_roles and not set(required_roles).intersection(effective_roles):
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"The tool {tool_name} requires one of the roles: "
                    f"{', '.join(required_roles)}."
                ),
                source="tool_role_binding",
                effective_roles=effective_roles,
            )

        for index, rule in enumerate(self.config.rules):
            if not self._rule_matches(
                rule=rule,
                actor=actor,
                tool_name=tool_name,
                level=level,
                project_key=project_key,
                mode=mode,
                effective_roles=effective_roles,
            ):
                continue
            return PolicyDecision(
                allowed=rule.effect == "allow",
                reason=rule.reason or f"Matched policy rule #{index}.",
                source="policy_rule",
                matched_rule_index=index,
                effective_roles=effective_roles,
            )

        if self.config.default_decision is PolicyDefaultDecision.ALLOW:
            return PolicyDecision(
                allowed=True,
                reason="No policy rule denied the request.",
                source="default",
                effective_roles=effective_roles,
            )
        return PolicyDecision(
            allowed=False,
            reason="No allow policy matched and the default policy is deny.",
            source="default",
            effective_roles=effective_roles,
        )

    def _required_roles_for_tool(self, tool_name: str) -> tuple[str, ...]:
        matched_roles: set[str] = set()
        for pattern, roles in self.config.tool_role_bindings.items():
            if fnmatch(tool_name, pattern):
                matched_roles.update(roles)
        return tuple(sorted(matched_roles))

    @staticmethod
    def _rule_matches(
        *,
        rule: PolicyRule,
        actor: ActorContext,
        tool_name: str,
        level: PermissionLevel,
        project_key: str | None,
        mode: str,
        effective_roles: tuple[str, ...],
    ) -> bool:
        if not any(fnmatch(tool_name, pattern) for pattern in rule.tools):
            return False
        if rule.levels and level.value not in rule.levels:
            return False
        if rule.modes and mode not in rule.modes:
            return False
        if rule.projects and (
            project_key is None
            or not any(fnmatch(project_key, pattern) for pattern in rule.projects)
        ):
            return False
        if rule.principals and actor.subject not in rule.principals:
            return False
        if rule.roles and not set(rule.roles).intersection(effective_roles):
            return False
        if rule.teams and not set(rule.teams).intersection(actor.teams):
            return False
        if rule.scopes and not set(rule.scopes).intersection(actor.scopes):
            return False
        if rule.auth_modes and actor.auth_mode not in rule.auth_modes:
            return False
        if (
            rule.require_authenticated is not None
            and actor.authenticated is not rule.require_authenticated
        ):
            return False
        return True

    @staticmethod
    def _load_config(settings: AppSettings) -> PolicyConfig:
        payload: dict[str, Any] = {
            "default_decision": settings.policy_default_decision.value,
        }
        if settings.policy_file:
            path = Path(settings.policy_file)
            if not path.exists():
                raise ConfigurationError(
                    "The configured policy file does not exist.",
                    details={"policy_file": str(path)},
                    suggested_fix="Create the policy JSON file or remove DATAIKU_POLICY_FILE.",
                )
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ConfigurationError(
                    "The configured policy file is not valid JSON.",
                    details={"policy_file": str(path)},
                    suggested_fix="Fix the policy JSON syntax and rerun validate-config.",
                ) from exc
            if not isinstance(loaded, dict):
                raise ConfigurationError(
                    "The configured policy file must contain a JSON object.",
                    details={"policy_file": str(path)},
                    suggested_fix="Wrap the policy configuration in a JSON object.",
                )
            payload.update(loaded)
        if settings.policy_json:
            payload.update(settings.policy_json)

        try:
            return PolicyConfig.model_validate(payload)
        except ValidationError as exc:
            raise ConfigurationError(
                "Invalid policy configuration.",
                details={"errors": exc.errors(include_url=False)},
                suggested_fix="Fix the policy JSON and rerun validate-config.",
            ) from exc
