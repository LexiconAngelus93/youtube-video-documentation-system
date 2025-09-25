#!/usr/bin/env python3
"""
YouTube Video Documentation System - Cross-Platform Installer
This script provides a cross-platform installation method using Python
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
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

def check_pip():
    """Check if pip is available"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("✅ pip detected")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip is required but not available")
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

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✅ Dependencies installed")
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
    
    try:
        result = subprocess.run([sys.executable, "main.py", "--help"], 
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
    print("🚀 Quick Start:")
    print("   python main.py --max-videos 10")
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
    
    if not check_pip():
        sys.exit(1)
    
    # Download and install
    if not download_project():
        sys.exit(1)
    
    if not install_dependencies():
        sys.exit(1)
    
    create_directories()
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
