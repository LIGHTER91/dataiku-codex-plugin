# Installation Guide

## Requirements

- Python 3.10+
- Codex CLI or Codex IDE integration
- Access to a Dataiku DSS instance
- Dataiku API key
- Network access to DSS
- `pip`

## Installation

Clone or create the repository.

```bash
git clone <repository-url>
cd dataiku-dss-copilot
```

Create virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install.

```bash
pip install -e ".[dev]"
```

## Configure environment

```bash
cp examples/sample_env.example .env
```

Edit `.env`:

```env
DATAIKU_DSS_URL=https://dss.company.com
DATAIKU_API_KEY=replace-me
DATAIKU_MODE=readonly
```

## Test connection

```bash
dataiku-codex-mcp validate-config
dataiku-codex-mcp ping
```

## Run MCP server locally

```bash
dataiku-codex-mcp --stdio
```

## Configure Codex

Use the provided MCP config:

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

## First test requests

- "Ping my Dataiku instance."
- "List my accessible Dataiku projects."
- "Summarize project PROJECT_KEY."
- "List recipes in project PROJECT_KEY."
- "Inspect Managed Folders in project PROJECT_KEY."

## Troubleshooting

### DSS unreachable

Check:

- `DATAIKU_DSS_URL`
- VPN/network access
- proxy settings
- SSL certificates

### Authentication error

Check:

- API key validity
- API key permissions
- Dataiku user permissions

### Tool denied

Check:

- `DATAIKU_MODE`
- tool permission level
- project allowlist/blocklist
- write/execute enable flags

### Managed Folder path issue

Do not assume the folder is local. Use file listing and stream APIs.
