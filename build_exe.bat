\
@echo off
setlocal enabledelayedexpansion

rem Build Windows EXE via cx_Freeze.
rem Run inside an activated venv.

set APP_NAME=UDPLogViewer

if "%1"=="clean" (
  echo Cleaning build/ and dist/...
  rmdir /s /q build 2>nul
  rmdir /s /q dist 2>nul
)

echo Building EXE (cx_Freeze)...
python freeze_setup.py build

echo Done. Check build\ for the output folder.
endlocal
