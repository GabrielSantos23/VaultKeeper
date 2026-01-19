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
set VERSION=1.0.4
set DIST_NAME=VaultKeeper-%VERSION%-windows-x64

REM In OneDir mode, the output is a folder "dist\VaultKeeper"
REM We want to zip this folder
if exist "dist\%DIST_NAME%.zip" del "dist\%DIST_NAME%.zip"

REM Create zip (requires PowerShell)
echo Compressing %DIST_NAME%.zip ...
powershell -Command "Compress-Archive -Path 'dist\VaultKeeper\*' -DestinationPath 'dist\%DIST_NAME%.zip' -Force"

REM Create Installer (if Inno Setup is available)
set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if exist "%ISCC_PATH%" (
    echo.
    echo [Optional] Compiling Installer...
    "%ISCC_PATH%" /DMyAppVersion=%VERSION% installer.iss
    if not errorlevel 1 (
        echo Installer created: dist\VaultKeeper_Setup_v%VERSION%.exe
    )
) else (
    echo.
    echo [Info] Inno Setup not found. Skipper installer creation.
    echo To create an installer, install Inno Setup and compile 'installer.iss'.
)

echo.
echo ==========================================
echo   Build Complete!
echo ==========================================
echo Executable: dist\VaultKeeper\VaultKeeper.exe
echo ZIP Package: dist\%DIST_NAME%.zip
if exist "dist\VaultKeeper_Setup_v%VERSION%.exe" echo Installer: dist\VaultKeeper_Setup_v%VERSION%.exe
echo.
echo To run: dist\VaultKeeper\VaultKeeper.exe
pause
