@echo off
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 tools\runtime\run_native_runtime_smoke.py %*
) else (
  python tools\runtime\run_native_runtime_smoke.py %*
)

if errorlevel 1 (
  pause
  exit /b 1
)
