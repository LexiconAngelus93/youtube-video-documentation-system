#!/bin/bash

# YouTube Video Documentation System - Quick Install Script
# This script will download and set up the complete system using a virtual environment

set -e  # Exit on any error

echo "🚀 YouTube Video Documentation System - Quick Install"
echo "=================================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Check if python3-venv is available (needed for virtual environments)
if ! python3 -m venv --help &> /dev/null; then
    echo "⚠️  python3-venv is not installed. Attempting to install..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3-venv
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-venv
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-venv
    else
        echo "❌ Could not install python3-venv. Please install it manually:"
        echo "   Debian/Ubuntu: sudo apt install python3-venv"
        echo "   Fedora: sudo dnf install python3-venv"
        echo "   RHEL/CentOS: sudo yum install python3-venv"
        exit 1
    fi
fi

echo "✅ python3-venv available"

# Create project directory
PROJECT_DIR="youtube-video-documentation-system"
echo "📁 Creating project directory: $PROJECT_DIR"

if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️  Directory $PROJECT_DIR already exists. Removing..."
    rm -rf "$PROJECT_DIR"
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Download project files from GitHub
echo "⬇️  Downloading project files from GitHub..."
if command -v git &> /dev/null; then
    # Use git if available
    git clone https://github.com/LexiconAngelus93/youtube-video-documentation-system.git .
else
    # Use curl/wget as fallback
    if command -v curl &> /dev/null; then
        curl -L https://github.com/LexiconAngelus93/youtube-video-documentation-system/archive/main.zip -o project.zip
        unzip project.zip
        mv youtube-video-documentation-system-main/* .
        rm -rf youtube-video-documentation-system-main project.zip
    elif command -v wget &> /dev/null; then
        wget https://github.com/LexiconAngelus93/youtube-video-documentation-system/archive/main.zip -O project.zip
        unzip project.zip
        mv youtube-video-documentation-system-main/* .
        rm -rf youtube-video-documentation-system-main project.zip
    else
        echo "❌ Git, curl, or wget is required to download the project. Please install one of them."
        exit 1
    fi
fi

echo "✅ Project files downloaded"

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

echo "✅ Virtual environment created"

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies in virtual environment..."
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

echo "✅ Dependencies installed"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p downloads/raw_videos
mkdir -p downloads/metadata
mkdir -p compilations
mkdir -p sessions
mkdir -p logs

echo "✅ Directory structure created"

# Make main script executable
chmod +x main.py

# Create a launcher script that activates venv automatically
echo "📝 Creating launcher script..."
cat > run.sh << 'EOF'
#!/bin/bash
# Launcher script for YouTube Video Documentation System
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/main.py" "$@"
EOF
chmod +x run.sh

# Create TUI launcher script
cat > run_tui.sh << 'EOF'
#!/bin/bash
# TUI Launcher script for YouTube Video Documentation System
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/main.py"
EOF
chmod +x run_tui.sh

echo "✅ Launcher scripts created"

# Test installation
echo "🧪 Testing installation..."
if python3 main.py --help > /dev/null 2>&1; then
    echo "✅ Installation test passed"
else
    echo "⚠️  Installation test failed, but files are installed"
fi

# Deactivate virtual environment
deactivate

echo ""
echo "🎉 Installation Complete!"
echo "=================================================="
echo ""
echo "📍 Project installed in: $(pwd)"
echo ""
echo "🚀 Quick Start (choose one):"
echo ""
echo "   Option 1 - Use launcher script:"
echo "      ./run.sh --max-videos 10"
echo ""
echo "   Option 2 - Activate venv manually:"
echo "      source venv/bin/activate"
echo "      python3 main.py --max-videos 10"
echo ""
echo "   Option 3 - Launch TUI (interactive mode):"
echo "      ./run_tui.sh"
echo ""
echo "📖 Documentation:"
echo "   - README.md - Project overview"
echo "   - USER_GUIDE.md - Comprehensive user guide"
echo "   - TECHNICAL_DOCS.md - Developer documentation"
echo ""
echo "⚙️  Configuration:"
echo "   - Edit config.yaml to customize settings"
echo ""
echo "🆘 Need help? Check the USER_GUIDE.md file"
echo ""
echo "Happy documenting! 📹✊"
