@echo off
REM YouTube Video Documentation System - Quick Install Script (Windows)
REM This script will download and set up the complete system

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

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Note: The YouTube Uploader requires the user to manually complete the OAuth 2.0 flow
REM to generate the 'youtube_credentials.json' file. See USER_GUIDE.md for details.

echo ✅ Dependencies installed

REM Create necessary directories
echo 📁 Creating necessary directories...
mkdir downloads\raw_videos 2>nul
mkdir downloads\metadata 2>nul
mkdir compilations 2>nul
mkdir sessions 2>nul
mkdir logs 2>nul

echo ✅ Directory structure created

REM Test installation
echo 🧪 Testing installation...
python main.py --help >nul 2>&1
if not errorlevel 1 (
    echo ✅ Installation test passed
) else (
    echo ⚠️  Installation test failed, but files are installed
)

echo.
echo 🎉 Installation Complete!
echo ==================================================
echo.
echo 📍 Project installed in: %CD%
echo.
echo 🚀 Quick Start:
echo    python main.py --max-videos 10
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
