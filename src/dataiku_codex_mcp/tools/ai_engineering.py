"""Advanced AI engineering tool registrations for roadmap V3.0."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from dataiku_codex_mcp.models.common import ok
from dataiku_codex_mcp.permissions import PermissionLevel

if TYPE_CHECKING:
    from dataiku_codex_mcp.server import AppContext, ToolRegistry


def register_tools(registry: ToolRegistry, ctx: AppContext) -> None:
    """Register advanced AI engineering insight tools."""

    def _read_tool(
        tool_name: str,
        project_key: str,
        builder: Callable[[], dict[str, Any]],
        *,
        object_name: str | None = None,
    ) -> dict[str, Any]:
        ctx.permissions.require(tool_name, level=PermissionLevel.READ, project_key=project_key)
        payload = ctx.redactor.redact(builder())
        ctx.audit.log_tool_call(
            tool_name=tool_name,
            mode=ctx.settings.mode.value,
            operation_type="read",
            success=True,
            project_key=project_key,
            object_name=object_name,
        )
        return ok(payload, metadata={"tool": tool_name, "mode": ctx.settings.mode.value})

    def dataiku_run_rag_eval(
        project_key: str,
        benchmark_dataset_name: str | None = None,
    ) -> dict[str, object]:
        return _read_tool(
            "dataiku_run_rag_eval",
            project_key,
            lambda: ctx.dataiku.run_rag_eval(
                project_key,
                benchmark_dataset_name=benchmark_dataset_name,
            ),
            object_name=benchmark_dataset_name,
        )

    def dataiku_compare_chunking_strategies(
        project_key: str,
        dataset_name: str | None = None,
        strategies: list[str] | None = None,
    ) -> dict[str, object]:
        return _read_tool(
            "dataiku_compare_chunking_strategies",
            project_key,
            lambda: ctx.dataiku.compare_chunking_strategies(
                project_key,
                dataset_name=dataset_name,
                strategies=strategies,
            ),
            object_name=dataset_name,
        )

    def dataiku_inspect_vector_store(project_key: str) -> dict[str, object]:
        return _read_tool(
            "dataiku_inspect_vector_store",
            project_key,
            lambda: ctx.dataiku.inspect_vector_store(project_key),
        )

    def dataiku_monitor_embedding_drift(
        project_key: str,
        reference_dataset_name: str | None = None,
        current_dataset_name: str | None = None,
    ) -> dict[str, object]:
        object_name = ",".join(
            value for value in (reference_dataset_name, current_dataset_name) if value
        ) or None
        return _read_tool(
            "dataiku_monitor_embedding_drift",
            project_key,
            lambda: ctx.dataiku.monitor_embedding_drift(
                project_key,
                reference_dataset_name=reference_dataset_name,
                current_dataset_name=current_dataset_name,
            ),
            object_name=object_name,
        )

    def dataiku_audit_prompt_injection(project_key: str) -> dict[str, object]:
        return _read_tool(
            "dataiku_audit_prompt_injection",
            project_key,
            lambda: ctx.dataiku.audit_prompt_injection(project_key),
        )

    def dataiku_generate_architecture_diagram(project_key: str) -> dict[str, object]:
        return _read_tool(
            "dataiku_generate_architecture_diagram",
            project_key,
            lambda: ctx.dataiku.generate_architecture_diagram(project_key),
        )

    def dataiku_score_project_quality(project_key: str) -> dict[str, object]:
        return _read_tool(
            "dataiku_score_project_quality",
            project_key,
            lambda: ctx.dataiku.score_project_quality(project_key),
        )

    def dataiku_prioritize_technical_debt(project_key: str) -> dict[str, object]:
        return _read_tool(
            "dataiku_prioritize_technical_debt",
            project_key,
            lambda: ctx.dataiku.prioritize_technical_debt(project_key),
        )

    registry.register(
        "dataiku_run_rag_eval",
        dataiku_run_rag_eval,
        description="Build an analysis-first RAG evaluation report for a project.",
    )
    registry.register(
        "dataiku_compare_chunking_strategies",
        dataiku_compare_chunking_strategies,
        description="Compare reusable chunking strategies against the current project setup.",
    )
    registry.register(
        "dataiku_inspect_vector_store",
        dataiku_inspect_vector_store,
        description="Inspect vector store backend choices, index types and metadata coverage.",
    )
    registry.register(
        "dataiku_monitor_embedding_drift",
        dataiku_monitor_embedding_drift,
        description="Estimate embedding drift readiness from model and schema signals.",
    )
    registry.register(
        "dataiku_audit_prompt_injection",
        dataiku_audit_prompt_injection,
        description="Audit prompt-injection guardrails and source-safety controls.",
    )
    registry.register(
        "dataiku_generate_architecture_diagram",
        dataiku_generate_architecture_diagram,
        description="Generate a Mermaid architecture diagram for the project Flow and AI stack.",
    )
    registry.register(
        "dataiku_score_project_quality",
        dataiku_score_project_quality,
        description="Aggregate flow, RAG, ops and code-env signals into one quality score.",
    )
    registry.register(
        "dataiku_prioritize_technical_debt",
        dataiku_prioritize_technical_debt,
        description="Prioritize flow, RAG, ops and code-env debt into a ranked backlog.",
    )
