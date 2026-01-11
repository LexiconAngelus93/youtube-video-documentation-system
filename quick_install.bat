@echo off
REM YouTube Video Documentation System - Quick Install Script (Windows)
REM This script will download and set up the complete system using a virtual environment

echo 🚀 YouTube Video Documentation System - Quick Install
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python detected

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is required but not installed. Please install pip first.
    pause
    exit /b 1
)

echo ✅ pip detected

REM Create project directory
set PROJECT_DIR=youtube-video-documentation-system
echo 📁 Creating project directory: %PROJECT_DIR%

if exist "%PROJECT_DIR%" (
    echo ⚠️  Directory %PROJECT_DIR% already exists. Removing...
    rmdir /s /q "%PROJECT_DIR%"
)

mkdir "%PROJECT_DIR%"
cd "%PROJECT_DIR%"

REM Download project files from GitHub
echo ⬇️  Downloading project files from GitHub...

REM Check if git is available
git --version >nul 2>&1
if not errorlevel 1 (
    REM Use git if available
    git clone https://github.com/LexiconAngelus93/youtube-video-documentation-system.git .
) else (
    REM Use PowerShell to download as fallback
    echo Using PowerShell to download...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/LexiconAngelus93/youtube-video-documentation-system/archive/main.zip' -OutFile 'project.zip'"
    powershell -Command "Expand-Archive -Path 'project.zip' -DestinationPath '.'"
    move youtube-video-documentation-system-main\* .
    rmdir /s /q youtube-video-documentation-system-main
    del project.zip
)

echo ✅ Project files downloaded

REM Create virtual environment
echo 🐍 Creating Python virtual environment...
python -m venv venv

echo ✅ Virtual environment created

REM Activate virtual environment and install dependencies
echo 📦 Installing Python dependencies in virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip first
python -m pip install --upgrade pip

REM Install dependencies
pip install -r requirements.txt

echo ✅ Dependencies installed

REM Create necessary directories
echo 📁 Creating necessary directories...
mkdir downloads\raw_videos 2>nul
mkdir downloads\metadata 2>nul
mkdir compilations 2>nul
mkdir sessions 2>nul
mkdir logs 2>nul

echo ✅ Directory structure created

REM Create launcher batch file
echo 📝 Creating launcher scripts...
(
echo @echo off
echo REM Launcher script for YouTube Video Documentation System
echo cd /d "%%~dp0"
echo call venv\Scripts\activate.bat
echo python main.py %%*
) > run.bat

REM Create TUI launcher batch file
(
echo @echo off
echo REM TUI Launcher script for YouTube Video Documentation System
echo cd /d "%%~dp0"
echo call venv\Scripts\activate.bat
echo python main.py
) > run_tui.bat

echo ✅ Launcher scripts created

REM Test installation
echo 🧪 Testing installation...
python main.py --help >nul 2>&1
if not errorlevel 1 (
    echo ✅ Installation test passed
) else (
    echo ⚠️  Installation test failed, but files are installed
)

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat 2>nul

echo.
echo 🎉 Installation Complete!
echo ==================================================
echo.
echo 📍 Project installed in: %CD%
echo.
echo 🚀 Quick Start (choose one):
echo.
echo    Option 1 - Use launcher script:
echo       run.bat --max-videos 10
echo.
echo    Option 2 - Activate venv manually:
echo       venv\Scripts\activate.bat
echo       python main.py --max-videos 10
echo.
echo    Option 3 - Launch TUI (interactive mode):
echo       run_tui.bat
echo.
echo 📖 Documentation:
echo    - README.md - Project overview
echo    - USER_GUIDE.md - Comprehensive user guide
echo    - TECHNICAL_DOCS.md - Developer documentation
echo.
echo ⚙️  Configuration:
echo    - Edit config.yaml to customize settings
echo.
echo 🆘 Need help? Check the USER_GUIDE.md file
echo.
echo Happy documenting! 📹✊
echo.
pause
