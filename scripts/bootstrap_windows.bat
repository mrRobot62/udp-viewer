@echo off setlocal ENABLEDELAYEDEXPANSION

echo =========================================== echo UDP Log Viewer -
Windows Bootstrap echo =========================================== echo.

REM Configuration set VENV_PATH=%USERPROFILE%-viewer set
PYTHON_LAUNCHER=py

echo [BOOTSTRAP] Repo: %CD% echo [BOOTSTRAP] Venv: %VENV_PATH% echo.

REM Check Python %PYTHON_LAUNCHER% -3 –version >nul 2>&1 if errorlevel 1
( echo [ERROR] Python 3 not found via ‘py -3’. echo Please install
Python 3.12+ from python.org. exit /b 1 )

REM Create parent directory if needed if not exist “%USERPROFILE%” (
mkdir “%USERPROFILE%” )

REM Create venv if it does not exist if not exist “%VENV_PATH%.bat” (
echo [BOOTSTRAP] Creating virtual environment… %PYTHON_LAUNCHER% -3 -m
venv “%VENV_PATH%” ) else ( echo [BOOTSTRAP] Using existing virtual
environment. )

REM Activate venv call “%VENV_PATH%.bat”

echo [BOOTSTRAP] Python: python –version

echo [BOOTSTRAP] Upgrading pip/setuptools/wheel… python -m pip install
–upgrade pip setuptools wheel

echo [BOOTSTRAP] Installing project in editable mode with dev extras…
python -m pip install -e .[dev]

if errorlevel 1 ( echo. echo [ERROR] Installation failed. exit /b 1 )

echo. echo =========================================== echo Bootstrap
completed successfully echo ===========================================
echo. echo Next steps: echo Run application: udp-log-viewer echo Run
tests: python -m pytest echo.

endlocal
