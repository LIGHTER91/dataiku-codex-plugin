[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pluginRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = if ($env:DATAIKU_CODEX_REPO_ROOT) {
    (Resolve-Path $env:DATAIKU_CODEX_REPO_ROOT).Path
} else {
    (Resolve-Path (Join-Path $pluginRoot "..\\..")).Path
}
$envFile = if ($env:DATAIKU_CODEX_ENV_FILE) {
    $env:DATAIKU_CODEX_ENV_FILE
} else {
    Join-Path $repoRoot ".env"
}

$cli = Join-Path $repoRoot ".venv\\Scripts\\dataiku-codex-mcp.exe"
if (Test-Path $cli) {
    & $cli "--env-file" $envFile "--stdio"
    exit $LASTEXITCODE
}

$python = Join-Path $repoRoot ".venv\\Scripts\\python.exe"
if (Test-Path $python) {
    Push-Location $repoRoot
    try {
        & $python "-m" "dataiku_codex_mcp" "--env-file" $envFile "--stdio"
        exit $LASTEXITCODE
    } finally {
        Pop-Location
    }
}

throw "Could not find the Dataiku DSS Copilot executable in $repoRoot\\.venv\\Scripts. Install the repo first with 'python -m venv .venv' and '.\\.venv\\Scripts\\python -m pip install -e "".[dev]""'."
