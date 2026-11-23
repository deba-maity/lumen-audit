@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 run.py --demo-only
) else (
  python run.py --demo-only
)
if errorlevel 1 pause
