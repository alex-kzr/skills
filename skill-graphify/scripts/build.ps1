param(
    [Parameter(Mandatory = $true)]
    [string]$SkillsDir
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SkillsDir)) {
    Write-Error "Skills folder does not exist: $SkillsDir"
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..\..\..") -ErrorAction Stop
$GraphWorkspace = Join-Path $RootDir "graphify-graph"
$SkillsGraphOut = Join-Path $SkillsDir "graphify-out"
$TargetGraphOut = Join-Path $GraphWorkspace "graphify-out"

if (-not (Test-Path $GraphWorkspace)) {
    New-Item -ItemType Directory -Path $GraphWorkspace -Force | Out-Null
}

Write-Host "Building Graphify knowledge graph for skills folder only..."
Write-Host "Skills folder: $SkillsDir"
Write-Host "Graph workspace: $GraphWorkspace"

# Remove visualization node limit to generate graph.html for large graphs
$env:GRAPHIFY_VIZ_NODE_LIMIT = "5000"

Set-Location $SkillsDir

graphify update .

# Move graphify-out to the correct location
if (Test-Path $SkillsGraphOut) {
    Write-Host "Moving graph output to $TargetGraphOut"
    if (Test-Path $TargetGraphOut) {
        Remove-Item -Path $TargetGraphOut -Recurse -Force
    }
    Move-Item -Path $SkillsGraphOut -Destination $TargetGraphOut -Force
    Write-Host "Graph output moved successfully"
}

Write-Host "Skills graph build completed."
Write-Host "Expected outputs:"
Write-Host "- $TargetGraphOut\graph.html"
Write-Host "- $TargetGraphOut\GRAPH_REPORT.md"
Write-Host "- $TargetGraphOut\graph.json"
