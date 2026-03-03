@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

set "PROJECT_DIR=%SCRIPT_DIR%..\.."

if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    "%PROJECT_DIR%\.venv\Scripts\python.exe" "%SCRIPT_DIR%host.py"
) else if exist "%PROJECT_DIR%\venv\Scripts\python.exe" (
    "%PROJECT_DIR%\venv\Scripts\python.exe" "%SCRIPT_DIR%host.py"
) else (
    python "%SCRIPT_DIR%host.py"
)
