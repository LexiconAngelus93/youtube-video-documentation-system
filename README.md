# YouTube Video Documentation System

A comprehensive Python application designed for journalistic documentation of police misconduct incidents. This system automatically searches YouTube for relevant videos, downloads them, filters content based on configurable criteria, and creates organized compilation videos with proper source attribution.

The system is built to help journalists, researchers, and activists document patterns of police misconduct through systematic video collection and analysis from publicly available sources on YouTube, covering incidents from 2010 to present in the United States.

## Features

- **YouTube Search:** Searches YouTube for videos based on a customizable list of keywords.
- **Video Download:** Downloads the searched videos, along with their metadata.
- **Content Filtering:** Filters videos based on duration, view count, and other criteria.
- **Automatic Categorization:** Categorizes videos into predefined topics.
- **Video Compilation:** Creates compilation videos from the downloaded clips with title pages.
- **Source Attribution:** Adds a text overlay to each video with source information.
- **YouTube Upload:** Automatically uploads compilations to a configured YouTube channel with AI-generated titles/descriptions.
- **Duplicate Prevention:** Tracks used videos to prevent duplicates across sessions.
- **Terminal UI:** An interactive terminal-based user interface for easy management.

## Quick Installation

The installation scripts automatically create a **Python virtual environment** to avoid conflicts with system packages.

### Option 1: One-Command Install (Recommended)

**Linux/macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/LexiconAngelus93/youtube-video-documentation-system/main/quick_install.sh | bash
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/LexiconAngelus93/youtube-video-documentation-system/main/quick_install.bat" -OutFile "install.bat" && .\install.bat
```

**Cross-Platform (Python):**
```bash
curl -sSL https://raw.githubusercontent.com/LexiconAngelus93/youtube-video-documentation-system/main/install.py | python3
```

### Option 2: Manual Installation

1. **Clone the repository:**
```bash
git clone https://github.com/LexiconAngelus93/youtube-video-documentation-system.git
cd youtube-video-documentation-system
```

2. **Create and activate a virtual environment:**
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate.bat
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create directories:**
```bash
mkdir -p downloads/{raw_videos,metadata} compilations sessions logs
```

## Usage

After installation, use the launcher scripts to run the application (they automatically activate the virtual environment).

### Using Launcher Scripts (Recommended)

**Linux/macOS:**
```bash
# Launch TUI (interactive mode)
./run_tui.sh

# Run with CLI arguments
./run.sh --max-videos 10
```

**Windows:**
```batch
REM Launch TUI (interactive mode)
run_tui.bat

REM Run with CLI arguments
run.bat --max-videos 10
```

### Using Virtual Environment Manually

**Linux/macOS:**
```bash
source venv/bin/activate
python3 main.py           # Launch TUI
python3 main.py --max-videos 10  # CLI mode
```

**Windows:**
```batch
venv\Scripts\activate.bat
python main.py           # Launch TUI
python main.py --max-videos 10  # CLI mode
```

### CLI Modes

```bash
# Run full pipeline
./run.sh --mode full --max-videos 50

# Search only
./run.sh --mode search --max-videos 50

# Download from a previous search file
./run.sh --mode download --input-file sessions/20231027_153000/search_results.json

# Compile from existing downloads
./run.sh --mode compile

# Upload compiled videos to YouTube
./run.sh --mode upload --input-file sessions/20231027_153000/compilation_report.json
```

## Configuration

The `config.yaml` file allows for customization of the search, download, compilation, and upload settings.

## Project Structure

```
youtube-video-documentation-system/
├── config.yaml
├── main.py
├── requirements.txt
├── quick_install.sh
├── quick_install.bat
├── install.py
├── run.sh              # Launcher script (Linux/macOS)
├── run_tui.sh          # TUI launcher (Linux/macOS)
├── run.bat             # Launcher script (Windows)
├── run_tui.bat         # TUI launcher (Windows)
├── venv/               # Virtual environment (created during install)
├── README.md
├── USER_GUIDE.md
├── TECHNICAL_DOCS.md
└── src/
    ├── __init__.py
    ├── content_filter.py
    ├── video_compiler.py
    ├── video_downloader.py
    ├── youtube_searcher.py
    ├── tracker.py
    ├── tui.py
    └── youtube/
        ├── __init__.py
        ├── auth.py
        ├── content.py
        └── uploader.py
```

## Dependencies

- **yt-dlp** - A command-line program to download videos from YouTube and other sites.
- **MoviePy** - A library for video editing, which is used to create the compilation videos.
- **PyYAML** - A YAML parser and emitter for Python.
- **google-api-python-client** - Google API client for YouTube uploads.
- **google-auth-oauthlib** - OAuth 2.0 authentication for Google APIs.
- **openai** - OpenAI API client for AI-generated titles and descriptions.
- **textual** - A TUI (Text User Interface) framework for Python.

## Documentation

- **USER_GUIDE.md** - Comprehensive user documentation
- **TECHNICAL_DOCS.md** - Developer and technical documentation

## Troubleshooting

### "externally-managed-environment" Error
If you see this error when installing, it means your system uses PEP 668 to protect system packages. The quick install scripts automatically handle this by using a virtual environment. If you're installing manually, make sure to create and activate a virtual environment first (see Manual Installation above).

### Missing python3-venv
On Debian/Ubuntu systems, you may need to install the venv module:
```bash
sudo apt install python3-venv
```

## License

This project is unlicensed. Use at your own risk.
