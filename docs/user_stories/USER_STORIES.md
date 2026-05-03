# User Stories

## Project audit

As an AI engineer, I want to summarize a Dataiku project so that I can understand its purpose, structure and technical risks.

Acceptance criteria:

- project objects are listed.
- Flow dependencies are summarized.
- risks are identified.
- recommendations are produced.

## Managed Folder debugging

As a developer, I want to inspect Managed Folder usage so that I can detect path and stream bugs.

Acceptance criteria:

- folders are listed.
- file listing works.
- recipes using folders are inspected.
- bad `get_path()` usage is flagged.

## RAG audit

As a RAG engineer, I want to inspect a Dataiku RAG pipeline so that I can improve retrieval and answer quality.

Acceptance criteria:

- RAG signals are detected.
- chunking and metadata are reviewed.
- vector store and embeddings are reviewed.
- evaluation plan is generated.

## Scenario failure

As an MLOps engineer, I want to explain a failed scenario so that I can fix automation issues.

Acceptance criteria:

- recent runs are retrieved.
- logs are summarized.
- root cause is proposed.
- fix is suggested.

## Documentation generation

As a project lead, I want to generate documentation from the project so that onboarding is easier.

Acceptance criteria:

- README generated.
- Flow documentation generated.
- RAG audit documentation generated when applicable.

## Controlled write

As a user, I want write operations to require approval so that Codex does not accidentally modify Dataiku projects.

Acceptance criteria:

- write tools fail in readonly mode.
- write tools require approval.
- dry-run summary is shown.
