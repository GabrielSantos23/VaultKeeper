@echo off
REM VaultKeeper Build Script for Windows
REM Creates a standalone executable for Windows

echo ==========================================
echo   VaultKeeper Build Script - Windows
echo ==========================================

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check Python
echo.
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found! Please install Python 3.11+
    pause
    exit /b 1
)
python --version

REM Create/activate virtual environment
echo.
echo [2/5] Setting up virtual environment...
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

REM Install dependencies
echo.
echo [3/5] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM Build
echo.
echo [4/5] Building executable...
pyinstaller vaultkeeper.spec --clean --noconfirm

REM Create distribution package
echo.
echo [5/5] Creating distribution package...
set VERSION=1.0.0
set DIST_NAME=VaultKeeper-%VERSION%-windows-x64

if not exist "dist\%DIST_NAME%" mkdir "dist\%DIST_NAME%"
copy "dist\VaultKeeper.exe" "dist\%DIST_NAME%\"
copy "README.md" "dist\%DIST_NAME%\" 2>nul

REM Create zip (requires PowerShell)
powershell -Command "Compress-Archive -Path 'dist\%DIST_NAME%' -DestinationPath 'dist\%DIST_NAME%.zip' -Force"

echo.
echo ==========================================
echo   Build Complete!
echo ==========================================
echo Executable: dist\VaultKeeper.exe
echo Package: dist\%DIST_NAME%.zip
echo.
echo To run: dist\VaultKeeper.exe
pause
