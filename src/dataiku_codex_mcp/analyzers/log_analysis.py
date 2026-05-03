"""Scenario and job log analysis heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FailureSignal:
    """Static pattern used to classify a failure."""

    category: str
    symptom: str
    root_cause: str
    recommended_fix: str
    patterns: tuple[re.Pattern[str], ...]


_SIGNALS: tuple[FailureSignal, ...] = (
    FailureSignal(
        category="permission_error",
        symptom="A permission or access control error was detected.",
        root_cause="The Dataiku user or underlying connection lacks the required permissions.",
        recommended_fix=(
            "Check DSS user rights, connection credentials and object-level permissions."
        ),
        patterns=(
            re.compile(r"\b(permission denied|forbidden|access denied)\b", re.IGNORECASE),
            re.compile(r"\bunauthorized\b", re.IGNORECASE),
        ),
    ),
    FailureSignal(
        category="missing_dataset",
        symptom="A dataset lookup failed during execution.",
        root_cause="The recipe or scenario references a dataset that is missing or misnamed.",
        recommended_fix=(
            "Verify dataset existence, project key, recipe bindings and upstream Flow changes."
        ),
        patterns=(
            re.compile(r"\bdataset\b.*\bnot found\b", re.IGNORECASE),
            re.compile(r"\bunknown dataset\b", re.IGNORECASE),
        ),
    ),
    FailureSignal(
        category="missing_folder_file",
        symptom="A Managed Folder file could not be found.",
        root_cause=(
            "The expected folder file is missing, incorrectly named or stored "
            "in another partition."
        ),
        recommended_fix=(
            "Check folder contents, partitioning, upstream writers and file naming conventions."
        ),
        patterns=(
            re.compile(r"\bno such file or directory\b", re.IGNORECASE),
            re.compile(r"\bfile not found\b", re.IGNORECASE),
            re.compile(r"\bmanaged folder\b.*\bmissing\b", re.IGNORECASE),
        ),
    ),
    FailureSignal(
        category="code_env_error",
        symptom="A code environment setup issue was detected.",
        root_cause=(
            "The configured code environment is missing dependencies or is "
            "otherwise broken."
        ),
        recommended_fix=(
            "Inspect the code env packages, rebuild the env and validate wheel availability."
        ),
        patterns=(
            re.compile(r"\bcode env(ironment)?\b", re.IGNORECASE),
            re.compile(r"\bvirtualenv\b.*\bfailed\b", re.IGNORECASE),
        ),
    ),
    FailureSignal(
        category="package_import_error",
        symptom="A Python import failure occurred.",
        root_cause="A required Python package is missing from the selected code environment.",
        recommended_fix=(
            "Add the missing package to the code env, rebuild it and re-run the failing step."
        ),
        patterns=(
            re.compile(r"\bmodulenotfounderror\b", re.IGNORECASE),
            re.compile(r"\bimporterror\b", re.IGNORECASE),
            re.compile(r"\bno module named\b", re.IGNORECASE),
        ),
    ),
    FailureSignal(
        category="schema_mismatch",
        symptom="A schema mismatch was detected.",
        root_cause="The actual dataset schema no longer matches what the recipe or job expects.",
        recommended_fix=(
            "Refresh schemas, check renamed columns and align recipe logic with "
            "the current dataset structure."
        ),
        patterns=(
            re.compile(r"\bschema\b.*\bmismatch\b", re.IGNORECASE),
            re.compile(r"\bunknown column\b", re.IGNORECASE),
            re.compile(r"\bcolumn\b.*\bdoes not exist\b", re.IGNORECASE),
        ),
    ),
    FailureSignal(
        category="memory_error",
        symptom="The execution appears to have exhausted available memory.",
        root_cause="The recipe or job is processing more data in memory than the runtime can hold.",
        recommended_fix=(
            "Stream inputs, reduce batch sizes, avoid eager reads and increase "
            "runtime memory if needed."
        ),
        patterns=(
            re.compile(r"\boutofmemory\b", re.IGNORECASE),
            re.compile(r"\bmemoryerror\b", re.IGNORECASE),
            re.compile(r"\bkilled process\b", re.IGNORECASE),
        ),
    ),
    FailureSignal(
        category="timeout",
        symptom="The execution timed out or exceeded a wait threshold.",
        root_cause="The job or external service did not complete within the configured timeout.",
        recommended_fix=(
            "Inspect long-running steps, external dependencies and timeout thresholds."
        ),
        patterns=(
            re.compile(r"\btimeout\b", re.IGNORECASE),
            re.compile(r"\btimed out\b", re.IGNORECASE),
        ),
    ),
    FailureSignal(
        category="invalid_credentials",
        symptom="Credential validation failed.",
        root_cause="The configured secret, token or login used by the step is invalid or expired.",
        recommended_fix=(
            "Rotate the failing credential and verify the secret source used by the job."
        ),
        patterns=(
            re.compile(r"\binvalid credentials\b", re.IGNORECASE),
            re.compile(r"\bauthentication failed\b", re.IGNORECASE),
            re.compile(r"\b401\b", re.IGNORECASE),
        ),
    ),
    FailureSignal(
        category="api_error",
        symptom="An external API call failed.",
        root_cause="A downstream API returned an application or transport error.",
        recommended_fix=(
            "Inspect the failing API response, retry policy, request payload and network path."
        ),
        patterns=(
            re.compile(r"\bhttp error\b", re.IGNORECASE),
            re.compile(r"\b429\b", re.IGNORECASE),
            re.compile(r"\b5\d\d\b", re.IGNORECASE),
        ),
    ),
    FailureSignal(
        category="vector_store_error",
        symptom="A vector store or embedding index failure was detected.",
        root_cause=(
            "The vector database, FAISS index or retrieval layer is "
            "misconfigured or unavailable."
        ),
        recommended_fix=(
            "Validate index creation, embedding dimensions and vector store connectivity."
        ),
        patterns=(
            re.compile(r"\bfaiss\b", re.IGNORECASE),
            re.compile(r"\bvector store\b", re.IGNORECASE),
            re.compile(r"\bembedding dimension\b", re.IGNORECASE),
        ),
    ),
    FailureSignal(
        category="llm_connector_error",
        symptom="An LLM or model connector call failed.",
        root_cause="The configured LLM connector, endpoint or provider credentials are failing.",
        recommended_fix=(
            "Check provider credentials, endpoint health, quotas and connector configuration."
        ),
        patterns=(
            re.compile(r"\bopenai\b", re.IGNORECASE),
            re.compile(r"\bllm\b", re.IGNORECASE),
            re.compile(r"\bmodel provider\b", re.IGNORECASE),
        ),
    ),
)


def summarize_logs(
    *,
    log_text: str,
    failed_steps: list[str] | None = None,
    error_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract structured failure hints from raw logs."""

    explanation = explain_failure(
        log_text=log_text,
        failed_steps=failed_steps,
        error_details=error_details,
    )
    detected_errors = [
        {
            "category": finding["category"],
            "message": finding["symptom"],
            "evidence": finding["evidence"],
        }
        for finding in explanation["findings"]
    ]
    probable_root_cause = (
        explanation["root_causes"][0] if explanation["root_causes"] else None
    )
    return {
        "detected_errors": detected_errors,
        "probable_root_cause": probable_root_cause,
    }


def explain_failure(
    *,
    log_text: str,
    failed_steps: list[str] | None = None,
    error_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce a lightweight root-cause analysis from logs and run details."""

    evidence_pool = _build_evidence_pool(log_text=log_text, error_details=error_details)
    findings: list[dict[str, Any]] = []

    for signal in _SIGNALS:
        matched_evidence = _find_matching_evidence(signal, evidence_pool)
        if not matched_evidence:
            continue
        findings.append(
            {
                "category": signal.category,
                "symptom": signal.symptom,
                "root_cause": signal.root_cause,
                "recommended_fix": signal.recommended_fix,
                "evidence": matched_evidence,
            }
        )

    symptoms = [finding["symptom"] for finding in findings]
    root_causes = [finding["root_cause"] for finding in findings]
    evidence = [item for finding in findings for item in finding["evidence"]]
    recommended_fixes = [finding["recommended_fix"] for finding in findings]

    if failed_steps:
        steps_text = ", ".join(failed_steps)
        symptoms.insert(0, f"Failed scenario steps detected: {steps_text}.")
        evidence.insert(0, f"Failed steps: {steps_text}")

    if error_details:
        serialized_error = _serialize_error_details(error_details)
        if serialized_error:
            evidence.insert(0, serialized_error)

    if not findings and log_text.strip():
        symptoms.append(
            "The run failed, but no known failure signature matched the "
            "available logs."
        )
        root_causes.append("A generic execution failure occurred without a recognized signature.")
        recommended_fixes.append(
            "Inspect the full DSS log, the failing step details and upstream object state."
        )
        first_signal = _first_non_empty_log_line(log_text)
        if first_signal:
            evidence.append(first_signal)

    return {
        "symptoms": _dedupe(symptoms),
        "root_causes": _dedupe(root_causes),
        "evidence": _dedupe(evidence),
        "recommended_fixes": _dedupe(recommended_fixes),
        "findings": findings,
    }


def _build_evidence_pool(
    *,
    log_text: str,
    error_details: dict[str, Any] | None,
) -> list[str]:
    lines = [line.strip() for line in log_text.splitlines() if line.strip()]
    pool = lines[:]
    serialized_error = _serialize_error_details(error_details)
    if serialized_error:
        pool.append(serialized_error)
    return pool


def _serialize_error_details(error_details: dict[str, Any] | None) -> str | None:
    if not error_details:
        return None
    fields = []
    for key in ("title", "message", "clazz", "code", "fixability", "stack"):
        value = error_details.get(key)
        if value:
            fields.append(f"{key}: {value}")
    if not fields:
        return None
    return " | ".join(str(field) for field in fields)


def _find_matching_evidence(signal: FailureSignal, evidence_pool: list[str]) -> list[str]:
    matches: list[str] = []
    for line in evidence_pool:
        for pattern in signal.patterns:
            if pattern.search(line):
                matches.append(line)
                break
    return _dedupe(matches)[:3]


def _first_non_empty_log_line(log_text: str) -> str | None:
    for line in log_text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return deduped
