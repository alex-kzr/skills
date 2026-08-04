param(
    [Parameter(Mandatory = $true)]
    [string]$Question
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..\..\..") -ErrorAction Stop
$GraphWorkspace = Join-Path $RootDir "graphify-graph"

Set-Location $GraphWorkspace

if (-not (Test-Path "graphify-out\graph.json")) {
    Write-Error "Graph file not found: graphify-out\graph.json. Build the graph first using build.ps1"
    exit 1
}

graphify query $Question
