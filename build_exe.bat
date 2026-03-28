\
@echo off
setlocal enabledelayedexpansion

rem Build Windows EXE via cx_Freeze.
rem Safe to run from any working directory.

set APP_NAME=UDPLogViewer
for %%i in ("%~dp0.") do set "REPO_ROOT=%%~fi"

cd /d "%REPO_ROOT%"
if errorlevel 1 (
  echo [ERROR] Could not change to repo root: %REPO_ROOT%
  exit /b 1
)

if "%1"=="clean" (
  echo Cleaning build/ and dist/...
  rmdir /s /q build 2>nul
  rmdir /s /q dist 2>nul
)

echo Building EXE (cx_Freeze)...
python freeze_setup.py build

echo Done. Check build\ for the output folder.
endlocal
