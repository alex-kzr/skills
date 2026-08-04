$ErrorActionPreference = "Stop"

Write-Host "Installing Graphify for skills knowledge graph..."

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is required but was not found. Install uv first: https://docs.astral.sh/uv/"
    exit 1
}

uv tool install "graphifyy[pdf,office,openai]"

Write-Host "Checking Graphify CLI..."
graphify --help

Write-Host "Graphify installation completed."
