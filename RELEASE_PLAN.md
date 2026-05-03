# Release Plan

## Alpha

Goal: internal developer testing with mocked Dataiku API.

Scope:

- local STDIO MCP server.
- read-only tools.
- skills.
- tests.
- mocked fixtures.

Exit criteria:

- all read-only tool tests pass.
- plugin can be loaded locally.
- no secret leakage in tests.

## Beta

Goal: test with a real Dataiku DSS instance in read-only mode.

Scope:

- project inspection.
- recipe reading.
- Managed Folder listing.
- scenario listing.
- logs.
- RAG audit.

Exit criteria:

- works on at least 2 real projects.
- handles permission errors gracefully.
- no write operations possible.

## Release Candidate

Goal: hardening and packaging.

Scope:

- documentation finalization.
- installation guide.
- security review.
- acceptance criteria validation.
- versioned release notes.

Exit criteria:

- tests pass.
- docs complete.
- security review completed.
- plugin package ready.

## Stable

Goal: public or private enterprise release.

Scope:

- version tag.
- changelog.
- installation package.
- demo examples.
- known limitations.

## Post-stable

- controlled write tools.
- remote MCP deployment.
- enterprise policy engine.
