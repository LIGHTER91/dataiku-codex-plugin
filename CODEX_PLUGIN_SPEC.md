# Codex Plugin Specification

## Purpose

Define how the Dataiku DSS Copilot plugin is packaged for Codex.

## Plugin components

The plugin contains:

- `plugin.json`
- `skills/`
- MCP configuration
- optional hooks
- assets
- installation docs
- examples

## Expected plugin manifest

```json
{
  "name": "dataiku-dss-copilot",
  "version": "1.0.0",
  "description": "Codex plugin for inspecting, auditing, debugging and improving Dataiku DSS projects.",
  "author": "Lucien Lachaud",
  "license": "Apache-2.0",
  "keywords": ["dataiku", "dss", "codex", "mcp", "rag", "mlops"],
  "skills": [
    "./skills/dataiku-project-auditor",
    "./skills/dataiku-managed-folder-debugger",
    "./skills/dataiku-rag-pipeline-auditor",
    "./skills/dataiku-recipe-reviewer",
    "./skills/dataiku-flow-architect",
    "./skills/dataiku-scenario-debugger",
    "./skills/dataiku-code-env-doctor"
  ],
  "mcpServers": "./mcp/dataiku.mcp.json",
  "hooks": "./hooks/hooks.json",
  "interface": {
    "displayName": "Dataiku DSS Copilot",
    "shortDescription": "Inspect, audit and debug Dataiku DSS projects from Codex.",
    "longDescription": "A Codex plugin that connects to Dataiku DSS through MCP and provides expert skills for Flow analysis, recipe debugging, Managed Folder inspection, RAG pipeline auditing and documentation generation.",
    "developerName": "Lucien Lachaud",
    "category": "Developer Tools",
    "capabilities": ["Dataiku DSS", "MCP", "RAG", "MLOps", "Project Audit"]
  }
}
```

## Skill list

### dataiku-project-auditor

For project summaries, audits and architecture understanding.

### dataiku-managed-folder-debugger

For Managed Folder, file access, JSONL/CSV/PDF/DOCX, S3/HDFS/GCS path issues.

### dataiku-rag-pipeline-auditor

For RAG ingestion, chunking, metadata, embeddings, vector stores, retrieval and evaluation.

### dataiku-recipe-reviewer

For Python, SQL, PySpark and visual recipe analysis.

### dataiku-flow-architect

For Flow graph, object dependencies, modularity and architecture recommendations.

### dataiku-scenario-debugger

For failed scenarios, jobs and automation debugging.

### dataiku-code-env-doctor

For code environment dependency issues.

## MCP configuration

The plugin should include a local STDIO MCP configuration by default.

Example:

```json
{
  "mcp_servers": {
    "dataiku-dss": {
      "command": "dataiku-codex-mcp",
      "args": ["--stdio"],
      "env": {
        "DATAIKU_DSS_URL": "${DATAIKU_DSS_URL}",
        "DATAIKU_API_KEY": "${DATAIKU_API_KEY}",
        "DATAIKU_MODE": "readonly"
      }
    }
  }
}
```

## Hook policy

Hooks are optional.

Potential hooks:

- pre-tool-call safety logging.
- post-tool-call redaction validation.
- pre-write dry-run generation.
- post-write audit logging.

No hook should bypass the MCP server permission guard.

## Plugin installation docs

The plugin must provide:

- setup guide.
- environment variables.
- MCP configuration examples.
- read-only test command.
- troubleshooting section.
