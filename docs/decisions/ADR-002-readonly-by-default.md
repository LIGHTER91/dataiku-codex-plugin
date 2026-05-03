# ADR-002 — Read-only by Default

## Status

Accepted.

## Context

Dataiku DSS projects can contain production workflows, sensitive data, credentials and business-critical pipelines.

An AI assistant must not modify or execute workflows accidentally.

## Decision

The plugin is read-only by default.

Write and execute operations require:

- explicit mode activation.
- enable flags.
- explicit user approval.
- server-side permission check.

## Consequences

Positive:

- safer adoption.
- easier enterprise acceptance.
- lower risk during testing.

Negative:

- write workflows require extra setup.
- users may need to approve actions manually.
