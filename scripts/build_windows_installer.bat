@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Build cx_Freeze EXE and create a single Setup.exe using Inno Setup
REM Recommended path: scripts\build_windows_installer.bat
REM Run from repo root.

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
python -m pip install --upgrade cx-Freeze

echo [3/4] Building EXE via cx_Freeze
python freeze_setup_win.py build
if errorlevel 1 (
  echo [ERROR] cx_Freeze build failed.
  exit /b 1
)

REM 4) Compile installer with Inno Setup
set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe

if not exist "%ISCC%" (
  echo [ERROR] ISCC.exe not found. Please install Inno Setup 6.
  exit /b 1
)

if not exist "packaging\windows\installer.iss" (
  echo [ERROR] Missing Inno Setup script: packaging\windows\installer.iss
  exit /b 1
)

echo [4/4] Building installer via Inno Setup
"%ISCC%" "packaging\windows\installer.iss"

echo.
echo DONE.
echo Installer is in: dist\
endlocal
