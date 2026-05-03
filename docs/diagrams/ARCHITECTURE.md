# Architecture Diagrams

## High-level architecture

```mermaid
flowchart TD
    U[User] --> C[Codex]
    C --> S[Codex Skills]
    C --> MCP[MCP Server]
    MCP --> P[Permission Guard]
    P --> A[Dataiku API Adapter]
    A --> DSS[Dataiku DSS]
    A --> R[Result Normalizer]
    R --> X[Redaction Layer]
    X --> C
```

## Tool call flow

```mermaid
sequenceDiagram
    participant User
    participant Codex
    participant Skill
    participant MCP
    participant Guard
    participant Dataiku
    participant Redactor

    User->>Codex: Ask Dataiku question
    Codex->>Skill: Select relevant skill
    Codex->>MCP: Call tool
    MCP->>Guard: Check permission
    Guard-->>MCP: Allowed
    MCP->>Dataiku: API call
    Dataiku-->>MCP: Raw result
    MCP->>Redactor: Redact output
    Redactor-->>MCP: Safe output
    MCP-->>Codex: Tool result
    Codex-->>User: Explanation/report
```

## Permission model

```mermaid
flowchart LR
    Tool[Tool Request] --> Mode{Mode}
    Mode -->|readonly| Read[Read allowed]
    Mode -->|write| Write[Write requires approval]
    Mode -->|execute| Exec[Execute requires approval]
    Mode -->|admin| Admin[Admin requires explicit enable]
    Write --> Approval{Approved?}
    Exec --> Approval
    Approval -->|yes| Run[Run tool]
    Approval -->|no| Reject[Reject]
```

## RAG audit workflow

```mermaid
flowchart TD
    Project[Dataiku Project] --> Recipes[Recipes]
    Recipes --> Ingestion[Ingestion]
    Recipes --> Chunking[Chunking]
    Recipes --> Embeddings[Embeddings]
    Recipes --> VectorStore[Vector Store]
    Recipes --> Retrieval[Retrieval]
    Recipes --> Generation[LLM Generation]
    Ingestion --> Audit[RAG Audit Report]
    Chunking --> Audit
    Embeddings --> Audit
    VectorStore --> Audit
    Retrieval --> Audit
    Generation --> Audit
```
