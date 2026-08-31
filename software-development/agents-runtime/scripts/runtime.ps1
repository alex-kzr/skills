[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet('doctor', 'bootstrap', 'sync', 'status', 'clean-cache', 'export-diagnostics')]
    [string]$Action,
    [string]$RuntimeRoot,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-DefaultRuntimeRoot {
    $directory = Split-Path -Parent $PSScriptRoot
    while ($directory) {
        if ((Test-Path (Join-Path $directory 'runtime')) -and (Test-Path (Join-Path $directory 'skills'))) { return (Join-Path $directory 'runtime') }
        $parent = Split-Path -Parent $directory
        if ($parent -eq $directory) { break }
        $directory = $parent
    }
    throw 'Unable to locate the shared agents runtime.'
}

function Get-ToolVersion([string]$Tool) {
    $command = Get-Command $Tool -ErrorAction Stop
    $version = & $command.Source --version
    if ($LASTEXITCODE -ne 0) { throw "Unable to determine $Tool version." }
    return $version.Trim()
}

function Invoke-Checked([string]$FilePath, [string[]]$Arguments) {
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$FilePath failed with exit code $LASTEXITCODE." }
}

$runtime = if ($RuntimeRoot) { [IO.Path]::GetFullPath($RuntimeRoot) } else { Get-DefaultRuntimeRoot }
$nodeDirectory = Join-Path $runtime 'node'
$pythonDirectory = Join-Path $runtime 'python'
$cacheDirectory = Join-Path $runtime 'cache'

function Test-Runtime {
    if (-not (Test-Path $runtime)) { throw "Runtime root is missing: $runtime" }
    $nodeVersion = Get-ToolVersion 'node'
    if (-not $nodeVersion.StartsWith('v24.')) { throw "Node 24 LTS is required; found $nodeVersion." }
    $uvVersion = Get-ToolVersion 'uv'
    foreach ($path in @((Join-Path $nodeDirectory 'package.json'), (Join-Path $nodeDirectory 'package-lock.json'), (Join-Path $pythonDirectory 'pyproject.toml'), (Join-Path $pythonDirectory 'uv.lock'))) {
        if (-not (Test-Path $path)) { throw "Required runtime file is missing: $path" }
    }
    [pscustomobject]@{ runtime = $runtime; node = $nodeVersion; uv = $uvVersion }
}

switch ($Action) {
    'doctor' { Test-Runtime | ConvertTo-Json -Compress; break }
    'status' { Test-Runtime | ConvertTo-Json -Compress; break }
    'export-diagnostics' { $state = Test-Runtime; [pscustomobject]@{ runtime = '<shared-runtime>'; node = $state.node; uv = $state.uv } | ConvertTo-Json -Compress; break }
    'bootstrap' {
        Test-Runtime | Out-Null
        if ($DryRun) { 'Would install Python and Node dependencies from committed lockfiles.'; break }
        Push-Location $pythonDirectory; try { Invoke-Checked 'uv' @('sync', '--locked', '--no-install-project') } finally { Pop-Location }
        Push-Location $nodeDirectory; try { Invoke-Checked 'npm' @('ci', '--ignore-scripts') } finally { Pop-Location }
        break
    }
    'sync' {
        Test-Runtime | Out-Null
        if ($DryRun) { 'Would synchronize Python and Node dependencies from committed lockfiles.'; break }
        Push-Location $pythonDirectory; try { Invoke-Checked 'uv' @('sync', '--locked', '--no-install-project') } finally { Pop-Location }
        Push-Location $nodeDirectory; try { Invoke-Checked 'npm' @('ci', '--ignore-scripts') } finally { Pop-Location }
        break
    }
    'clean-cache' {
        if ($DryRun) { "Would remove cache contents under $cacheDirectory."; break }
        if (Test-Path $cacheDirectory) { Get-ChildItem -Force $cacheDirectory | Remove-Item -Recurse -Force }
        break
    }
}
