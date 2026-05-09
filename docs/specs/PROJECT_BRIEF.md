# Project Brief — Dataiku DSS Copilot for Codex

## Vision

Build a complete Codex plugin that connects Codex to Dataiku DSS and allows developers, data scientists, AI engineers and MLOps teams to inspect, audit, debug, document and safely modify Dataiku projects.

## Product name

Dataiku DSS Copilot for Codex

## Product category

Developer tool / Data platform assistant / AI engineering assistant / MCP connector.

## Core idea

The plugin combines:

- Codex skills for Dataiku-specific reasoning.
- An MCP server exposing Dataiku DSS API tools.
- A Dataiku API client wrapper.
- A security and permission layer.
- A redaction layer.
- A test suite.
- Documentation and examples.

## Main users

- AI engineers
- Data scientists
- Data engineers
- MLOps engineers
- Dataiku administrators
- RAG engineers
- Enterprise data teams
- Technical project leads

## Main value

Reduce the time needed to understand and debug complex Dataiku DSS projects, especially projects involving Python recipes, Managed Folders, scenario automation, LLM connectors, RAG pipelines, vector databases and large document ingestion.

## Product promise

Give Codex enough Dataiku-specific context and tools to answer questions such as:

- "Analyze this Dataiku project and explain the Flow architecture."
- "Find why my Python recipe fails when reading a Managed Folder."
- "Audit my RAG pipeline: chunking, metadata, embeddings, vector store and reranking."
- "Inspect the latest scenario failure and explain the root cause."
- "Generate a technical README for this project."
- "Review my recipes for unsafe Dataiku API usage."

## Key differentiator

This is not just "Codex inside Dataiku". It is a Codex plugin that can understand and operate on a Dataiku DSS instance from Codex through a structured, safe and testable MCP server.
