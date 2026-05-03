[CmdletBinding()]
param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000,
    [string]$Path = "/mcp"
)

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
    & $cli "--env-file" $envFile "serve-http" "--host" $Host "--port" $Port "--path" $Path
    exit $LASTEXITCODE
}

$python = Join-Path $repoRoot ".venv\\Scripts\\python.exe"
if (Test-Path $python) {
    Push-Location $repoRoot
    try {
        & $python "-m" "dataiku_codex_mcp" "--env-file" $envFile "serve-http" "--host" $Host "--port" $Port "--path" $Path
        exit $LASTEXITCODE
    } finally {
        Pop-Location
    }
}

throw "Could not find the Dataiku DSS Copilot executable in $repoRoot\\.venv\\Scripts."
