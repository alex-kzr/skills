$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'runtime.ps1'
$agentsRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
$runtime = Join-Path $agentsRoot 'runtime'

function Get-RuntimeFingerprint {
    $paths = @(
        (Join-Path $runtime 'node/package.json'),
        (Join-Path $runtime 'node/package-lock.json'),
        (Join-Path $runtime 'python/pyproject.toml'),
        (Join-Path $runtime 'python/uv.lock')
    )
    $hashes = $paths | ForEach-Object { (Get-FileHash $_).Hash }
    $cacheFiles = @(Get-ChildItem -Recurse -Force (Join-Path $runtime 'cache') -ErrorAction SilentlyContinue).Count
    return "$($hashes -join ':'):$cacheFiles"
}

foreach ($action in @('doctor', 'status', 'export-diagnostics')) {
    $before = Get-RuntimeFingerprint
    $output = & $script $action -RuntimeRoot $runtime
    if ($LASTEXITCODE -ne 0) { throw "$action failed." }
    $after = Get-RuntimeFingerprint
    if ($before -ne $after) { throw "$action modified the runtime." }
    if ($action -eq 'export-diagnostics' -and $output -match [regex]::Escape($env:USERPROFILE)) { throw 'Diagnostics expose a user path.' }
}

foreach ($action in @('bootstrap', 'sync', 'clean-cache')) {
    & $script $action -RuntimeRoot $runtime -DryRun
    if ($LASTEXITCODE -ne 0) { throw "$action dry run failed." }
}

'agents-runtime tests passed'
