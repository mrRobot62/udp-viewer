@echo off
setlocal

REM Safe to run multiple times.
REM Safe to run from any working directory.
for %%i in ("%~dp0..\..") do set "REPO_ROOT=%%~fi"

cd /d "%REPO_ROOT%"
if errorlevel 1 (
  echo [ERROR] Could not change to repo root: %REPO_ROOT%
  exit /b 1
)

if not exist dist mkdir dist
if not exist build mkdir build

REM Build folder via cx_Freeze
python freeze_setup.py build

echo OK: build\exe.*\
endlocal
