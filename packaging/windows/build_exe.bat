@echo off
setlocal

REM Safe to run multiple times.
if not exist dist mkdir dist
if not exist build mkdir build

REM Build folder via cx_Freeze
python freeze_setup.py build

echo OK: build\exe.*\
endlocal
