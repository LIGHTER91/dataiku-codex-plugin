# Command-First Audit

Date: 2026-05-03

## Scope

This audit checks whether the plugin follows the intended product direction:

- Codex plugin for UI and discoverability
- MCP server for executing reusable commands
- Dataiku native visual components before custom code
- direct code edits reserved for targeted maintenance such as renames and fixes

## Findings

### Aligned

- The repository now ships both a native Codex UI plugin bundle and a Python MCP server.
- The ML bootstrap path is exposed as a reusable command catalog instead of ad-hoc setup scripts.
- The main docs explicitly describe a command-first and visual-first operating model.
- Direct code tools remain available, but only as controlled write operations.

### Fixed in this audit

- The real DSS write-path for `run-ml-command` now creates a native Prepare recipe with `with_new_output(...)`, materializes its dataset, and only then creates the Visual ML task.
- This removes the previous dependency on an incompatible recipe creation path that failed on DSS cloud with `creationInfo` output suppression errors.

## Residual constraints

- Direct recipe code editing still exists for legitimate maintenance tasks and should remain gated by approval.
- The ML catalog currently covers baseline prediction flows only. Time series, scoring, deployment and evaluation still belong to later roadmap steps.

## Decision

Keep the architecture centered on:

1. plugin UI for prompts, skills and user intent
2. MCP command catalog for repeatable actions
3. native DSS visual assets for project mutations
4. direct code generation only as a fallback for narrow maintenance work
