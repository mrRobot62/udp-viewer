Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir "..")).Path

# Config (mirrors scripts/common.env)
$VenvPath = Join-Path $HOME "workspace\venv\udp-viewer"
$PythonExe = "py"  # uses Python Launcher if available
$PipExtras = ".[dev]"

Write-Host "[BOOTSTRAP] Repo: $RepoRoot"
Write-Host "[BOOTSTRAP] Venv: $VenvPath"

if (-not (Test-Path (Join-Path $RepoRoot "pyproject.toml")) -and -not (Test-Path (Join-Path $RepoRoot "setup.py"))) {
  throw "Could not find pyproject.toml or setup.py at repo root."
}

# Pick python
$pyOk = $false
try {
  & $PythonExe -3 --version | Out-Null
  $pyOk = $true
} catch {
  $pyOk = $false
}

if (-not $pyOk) {
  $PythonExe = "python"
  try {
    & $PythonExe --version | Out-Null
  } catch {
    throw "Python not found. Install Python 3 first."
  }
}

# Create venv
$VenvParent = Split-Path -Parent $VenvPath
if (-not (Test-Path $VenvParent)) { New-Item -ItemType Directory -Force -Path $VenvParent | Out-Null }

if (-not (Test-Path $VenvPath)) {
  Write-Host "[BOOTSTRAP] Creating venv..."
  if ($PythonExe -eq "py") {
    & py -3 -m venv $VenvPath
  } else {
    & python -m venv $VenvPath
  }
} else {
  Write-Host "[BOOTSTRAP] Venv already exists."
}

# Activate
$Activate = Join-Path $VenvPath "Scripts\Activate.ps1"
. $Activate

Write-Host "[BOOTSTRAP] Python:" (python -V)
Write-Host "[BOOTSTRAP] Upgrading pip tooling..."
python -m pip install --upgrade pip setuptools wheel

Write-Host "[BOOTSTRAP] Installing project (editable) + dev deps: $PipExtras"
python -m pip install -e $PipExtras

# Optional tools
Write-Host "[BOOTSTRAP] Installing/refreshing optional tooling (best-effort)..."
try { python -m pip install --upgrade pre-commit ruff mypy | Out-Null } catch {}

# Pre-commit (best-effort)
try {
  pre-commit --version | Out-Null
  Write-Host "[BOOTSTRAP] Setting up pre-commit hooks..."
  Push-Location $RepoRoot
  try { pre-commit install | Out-Null } catch {}
  Pop-Location
} catch {}

Write-Host ""
Write-Host "[DONE] Bootstrap complete."
Write-Host "Next:"
Write-Host "  - Run app:   .\scripts\dev_run.ps1"
Write-Host "  - Run tests: .\scripts\dev_test.ps1"