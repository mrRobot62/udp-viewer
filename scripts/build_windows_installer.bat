@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Build cx_Freeze EXE and create a single Setup.exe using Inno Setup
REM Recommended path: scripts\build_windows_installer.bat
REM Run from repo root.

set "APP_NAME=UDPLogViewer"
set "ISS_FILE=packaging\windows\installer.iss"

echo == UDPLogViewer Windows Installer Build ==
echo Repo: %CD%
echo.

REM 1) Ensure venv
if not exist ".venv\Scripts\activate.bat" (
  echo [1/4] Creating venv .venv
  py -3 -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo [2/4] Installing build dependencies
python -m pip install --upgrade pip setuptools wheel
python -m pip install --upgrade cx-Freeze .
if errorlevel 1 (
  echo [ERROR] Dependency installation failed.
  exit /b 1
)

for /f "usebackq delims=" %%i in (`python -c "from udp_log_viewer import __version__; print(__version__)"`) do set "APP_VERSION=%%i"
if not defined APP_VERSION (
  echo [ERROR] Could not determine application version.
  exit /b 1
)

echo [3/4] Building EXE via cx_Freeze
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python freeze_setup_win.py build_exe
if errorlevel 1 (
  echo [ERROR] cx_Freeze build failed.
  exit /b 1
)

set "BUILD_DIR="
for /d %%d in ("build\exe.*") do (
  set "BUILD_DIR=%%~fd"
)

if not defined BUILD_DIR (
  echo [ERROR] Could not locate cx_Freeze output in build\exe.*
  exit /b 1
)

REM 4) Compile installer with Inno Setup
set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe

if not exist "%ISCC%" (
  echo [ERROR] ISCC.exe not found. Please install Inno Setup 6.
  exit /b 1
)

if not exist "%ISS_FILE%" (
  echo [ERROR] Missing Inno Setup script: %ISS_FILE%
  exit /b 1
)

echo [4/4] Building installer via Inno Setup
"%ISCC%" /DAppName="%APP_NAME%" /DAppVersion="%APP_VERSION%" /DBuildDir="%BUILD_DIR%" "%ISS_FILE%"
if errorlevel 1 (
  echo [ERROR] Inno Setup build failed.
  exit /b 1
)

echo.
echo DONE.
echo Version: %APP_VERSION%
echo Build dir: %BUILD_DIR%
echo Installer is in: dist\
endlocal
