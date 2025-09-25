# YouTube Video Documentation System

A comprehensive Python application designed for journalistic documentation of police misconduct incidents. This system automatically searches YouTube for relevant videos, downloads them, filters content based on configurable criteria, and creates organized compilation videos with proper source attribution.

The system is built to help journalists, researchers, and activists document patterns of police misconduct through systematic video collection and analysis from publicly available sources on YouTube, covering incidents from 2010 to present in the United States.

## Features

- **YouTube Search:** Searches YouTube for videos based on a customizable list of keywords.
- **Video Download:** Downloads the searched videos, along with their metadata.
- **Content Filtering:** Filters videos based on duration, view count, and other criteria.
- **Automatic Categorization:** Categorizes videos into predefined topics.
- **Video Compilation:** Creates compilation videos from the downloaded clips.
- **Source Attribution:** Adds a text overlay to each video with source information.

## Quick Installation

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

2. **Install dependencies:**
```bash
pip3 install -r requirements.txt
```

3. **Create directories:**
```bash
mkdir -p downloads/{raw_videos,metadata} compilations sessions logs
```

## Usage

To run the full pipeline, use the following command:

```shell
python3 main.py --max-videos 10
```

## Configuration

The `config.yaml` file allows for customization of the search, download, and compilation settings.

## Project Structure

```
video-documentation-system/
├── config.yaml
├── main.py
├── requirements.txt
├── quick_install.sh
├── quick_install.bat
├── install.py
├── README.md
├── USER_GUIDE.md
├── TECHNICAL_DOCS.md
└── src/
    ├── __init__.py
    ├── content_filter.py
    ├── video_compiler.py
    ├── video_downloader.py
    └── youtube_searcher.py
```

## Dependencies

- **yt-dlp** - A command-line program to download videos from YouTube and other sites.
- **MoviePy** - A library for video editing, which is used to create the compilation videos.
- **PyYAML** - A YAML parser and emitter for Python.

## Documentation

- **USER_GUIDE.md** - Comprehensive user documentation
- **TECHNICAL_DOCS.md** - Developer and technical documentation

## License

This project is unlicensed. Use at your own risk.
