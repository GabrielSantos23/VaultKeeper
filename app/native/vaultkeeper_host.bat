@echo off
setlocal

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Go up two directories to project root (app/native -> app -> project_root)
set "PROJECT_DIR=%SCRIPT_DIR%..\.."

REM Try venv first, then fallback to system Python
if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    "%PROJECT_DIR%\.venv\Scripts\python.exe" "%SCRIPT_DIR%host.py"
) else if exist "%PROJECT_DIR%\venv\Scripts\python.exe" (
    "%PROJECT_DIR%\venv\Scripts\python.exe" "%SCRIPT_DIR%host.py"
) else (
    REM Fallback to system Python
    python "%SCRIPT_DIR%host.py"
)
