# ADR-004 - Prefer command catalog over ad-hoc code generation

## Status

Accepted.

## Context

The project needs to launch recurring Dataiku workflows quickly from Codex.

If Codex regenerates setup scripts for every similar request, the product becomes:

- slower.
- harder to audit.
- less deterministic.
- more fragile across DSS versions.

The desired user experience is closer to:

- "set up xgboost on project X using dataset Y"
- "show me what I can predict from dataset Y"
- "run a random forest baseline quickly"

These intents should map to stable commands and blueprints rather than bespoke Python scaffolding.

## Decision

Adopt a command-catalog-first architecture:

- the Codex plugin is responsible for UI, prompts, skills and discoverability.
- the MCP server is responsible for resolving intent into standardized commands.
- the Dataiku adapter is responsible for executing Dataiku-native mutations through stable blueprints.

Prefer:

- Visual ML tasks.
- Prepare recipes.
- scenario templates.
- structured plans and reports.

Avoid ad-hoc code generation for recurring workflows.

Generate or edit code directly only when:

- patching an existing recipe.
- applying a narrow fix.
- renaming variables or similar maintenance changes.
- no suitable Dataiku-native or command-catalog path exists.

## Consequences

Positive:

- faster repeated execution.
- more predictable outputs.
- easier approval and audit.
- easier testing.
- lower maintenance cost.

Negative:

- upfront work to design and maintain the command catalog.
- some advanced edge cases may still require custom code paths.
