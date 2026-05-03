# ADR-001 — Use Codex Plugin + MCP Server Architecture

## Status

Accepted.

## Context

The project needs to provide both behavior guidance to Codex and live interaction with Dataiku DSS.

Codex skills are useful for domain-specific reasoning, but they cannot directly access a Dataiku instance.

An MCP server can expose Dataiku API capabilities as structured tools.

## Decision

Use a Codex plugin containing:

- skills.
- MCP server configuration.
- documentation.
- optional hooks.

Use a Python MCP server to expose Dataiku DSS operations.

## Consequences

Positive:

- clean separation between reasoning and tool execution.
- testable Dataiku integration.
- security enforced server-side.
- extensible tool catalog.

Negative:

- more complex than a simple script.
- requires careful permission model.
- requires MCP packaging and config.
