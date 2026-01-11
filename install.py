#!/usr/bin/env python3
"""
YouTube Video Documentation System - Cross-Platform Installer
This script provides a cross-platform installation method using Python virtual environments
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
import venv
from pathlib import Path

def print_header():
    print("🚀 YouTube Video Documentation System - Quick Install")
    print("=" * 50)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Found: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_venv():
    """Check if venv module is available"""
    try:
        import venv
        print("✅ venv module available")
        return True
    except ImportError:
        print("❌ venv module is required but not available")
        print("   Install it with: apt install python3-venv (Debian/Ubuntu)")
        return False

def download_project():
    """Download project files from GitHub"""
    project_dir = "youtube-video-documentation-system"
    
    print(f"📁 Creating project directory: {project_dir}")
    
    # Remove existing directory if it exists
    if os.path.exists(project_dir):
        print("⚠️  Directory already exists. Removing...")
        shutil.rmtree(project_dir)
    
    os.makedirs(project_dir)
    os.chdir(project_dir)
    
    print("⬇️  Downloading project files from GitHub...")
    
    # Try git first, then fallback to direct download
    try:
        subprocess.run(["git", "clone", 
                       "https://github.com/LexiconAngelus93/youtube-video-documentation-system.git", 
                       "."], check=True, capture_output=True)
        print("✅ Downloaded using git")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to direct download
        try:
            url = "https://github.com/LexiconAngelus93/youtube-video-documentation-system/archive/main.zip"
            urllib.request.urlretrieve(url, "project.zip")
            
            with zipfile.ZipFile("project.zip", 'r') as zip_ref:
                zip_ref.extractall(".")
            
            # Move files from subdirectory to current directory
            subdir = "youtube-video-documentation-system-main"
            if os.path.exists(subdir):
                for item in os.listdir(subdir):
                    shutil.move(os.path.join(subdir, item), ".")
                os.rmdir(subdir)
            
            os.remove("project.zip")
            print("✅ Downloaded using direct download")
            
        except Exception as e:
            print(f"❌ Failed to download project: {e}")
            return False
    
    return True

def create_virtual_environment():
    """Create a Python virtual environment"""
    print("🐍 Creating Python virtual environment...")
    
    try:
        venv.create("venv", with_pip=True)
        print("✅ Virtual environment created")
        return True
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def get_venv_python():
    """Get the path to the Python executable in the virtual environment"""
    if os.name == 'nt':  # Windows
        return os.path.join("venv", "Scripts", "python.exe")
    else:  # Unix/Linux/Mac
        return os.path.join("venv", "bin", "python")

def get_venv_pip():
    """Get the path to pip in the virtual environment"""
    if os.name == 'nt':  # Windows
        return os.path.join("venv", "Scripts", "pip.exe")
    else:  # Unix/Linux/Mac
        return os.path.join("venv", "bin", "pip")

def install_dependencies():
    """Install dependencies in the virtual environment"""
    print("📦 Installing Python dependencies in virtual environment...")
    
    venv_pip = get_venv_pip()
    venv_python = get_venv_python()
    
    try:
        # Upgrade pip first
        subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Install dependencies
        subprocess.run([venv_pip, "install", "-r", "requirements.txt"], 
                      check=True)
        print("✅ Dependencies installed")
        
        print("\nNote: The YouTube Uploader requires the user to manually complete the OAuth 2.0 flow")
        print("to generate the 'youtube_credentials.json' file. See USER_GUIDE.md for details.")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary project directories"""
    print("📁 Creating necessary directories...")
    
    directories = [
        "downloads/raw_videos",
        "downloads/metadata", 
        "compilations",
        "sessions",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directory structure created")

def create_launcher_scripts():
    """Create launcher scripts that activate the virtual environment"""
    print("📝 Creating launcher scripts...")
    
    if os.name == 'nt':  # Windows
        # Create run.bat
        with open("run.bat", "w") as f:
            f.write('@echo off\n')
            f.write('REM Launcher script for YouTube Video Documentation System\n')
            f.write('cd /d "%~dp0"\n')
            f.write('call venv\\Scripts\\activate.bat\n')
            f.write('python main.py %*\n')
        
        # Create run_tui.bat
        with open("run_tui.bat", "w") as f:
            f.write('@echo off\n')
            f.write('REM TUI Launcher script for YouTube Video Documentation System\n')
            f.write('cd /d "%~dp0"\n')
            f.write('call venv\\Scripts\\activate.bat\n')
            f.write('python main.py\n')
    else:  # Unix/Linux/Mac
        # Create run.sh
        with open("run.sh", "w") as f:
            f.write('#!/bin/bash\n')
            f.write('# Launcher script for YouTube Video Documentation System\n')
            f.write('SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n')
            f.write('source "$SCRIPT_DIR/venv/bin/activate"\n')
            f.write('python3 "$SCRIPT_DIR/main.py" "$@"\n')
        os.chmod("run.sh", 0o755)
        
        # Create run_tui.sh
        with open("run_tui.sh", "w") as f:
            f.write('#!/bin/bash\n')
            f.write('# TUI Launcher script for YouTube Video Documentation System\n')
            f.write('SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n')
            f.write('source "$SCRIPT_DIR/venv/bin/activate"\n')
            f.write('python3 "$SCRIPT_DIR/main.py"\n')
        os.chmod("run_tui.sh", 0o755)
    
    print("✅ Launcher scripts created")

def make_executable():
    """Make main script executable on Unix systems"""
    if os.name != 'nt':  # Not Windows
        try:
            os.chmod("main.py", 0o755)
        except:
            pass  # Ignore errors

def test_installation():
    """Test if installation was successful"""
    print("🧪 Testing installation...")
    
    venv_python = get_venv_python()
    
    try:
        result = subprocess.run([venv_python, "main.py", "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Installation test passed")
            return True
        else:
            print("⚠️  Installation test failed, but files are installed")
            return False
    except Exception:
        print("⚠️  Could not test installation, but files are installed")
        return False

def print_completion_message():
    """Print completion message with usage instructions"""
    print()
    print("🎉 Installation Complete!")
    print("=" * 50)
    print()
    print(f"📍 Project installed in: {os.getcwd()}")
    print()
    print("🚀 Quick Start (choose one):")
    print()
    
    if os.name == 'nt':  # Windows
        print("   Option 1 - Use launcher script:")
        print("      run.bat --max-videos 10")
        print()
        print("   Option 2 - Activate venv manually:")
        print("      venv\\Scripts\\activate.bat")
        print("      python main.py --max-videos 10")
        print()
        print("   Option 3 - Launch TUI (interactive mode):")
        print("      run_tui.bat")
    else:  # Unix/Linux/Mac
        print("   Option 1 - Use launcher script:")
        print("      ./run.sh --max-videos 10")
        print()
        print("   Option 2 - Activate venv manually:")
        print("      source venv/bin/activate")
        print("      python3 main.py --max-videos 10")
        print()
        print("   Option 3 - Launch TUI (interactive mode):")
        print("      ./run_tui.sh")
    
    print()
    print("📖 Documentation:")
    print("   - README.md - Project overview")
    print("   - USER_GUIDE.md - Comprehensive user guide") 
    print("   - TECHNICAL_DOCS.md - Developer documentation")
    print()
    print("⚙️  Configuration:")
    print("   - Edit config.yaml to customize settings")
    print()
    print("🆘 Need help? Check the USER_GUIDE.md file")
    print()
    print("Happy documenting! 📹✊")

def main():
    """Main installation function"""
    print_header()
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_venv():
        sys.exit(1)
    
    # Download project
    if not download_project():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    create_directories()
    create_launcher_scripts()
    make_executable()
    test_installation()
    print_completion_message()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)
