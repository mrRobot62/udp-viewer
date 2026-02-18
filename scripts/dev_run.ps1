Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$VenvPath  = Join-Path $HOME "workspace\venv\udp-viewer"

. (Join-Path $VenvPath "Scripts\Activate.ps1")

Set-Location $RepoRoot
python -m udp_log_viewer.main