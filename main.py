#!/usr/bin/env python3
"""
YouTube Video Documentation System - Main Application

This is the main entry point for the YouTube video documentation system.
It orchestrates the search, download, filtering, and compilation processes.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List
import yaml
from datetime import datetime
import time

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

from youtube_searcher import YouTubeSearcher
from video_downloader import VideoDownloader
from video_compiler import VideoCompiler
from content_filter import ContentFilter
from youtube_uploader import YouTubeUploader
from tracker import VideoTracker


# Import VideoDocumentationSystem from separate module
from src.video_documentation_system import VideoDocumentationSystem

def main():
    """
    Main entry point for the application.
    """
    if len(sys.argv) > 1:
        # Use CLI handler for command-line operations
        try:
            from src.cli_handler import CLIHandler
            cli = CLIHandler()
            cli.handle_cli()
        except Exception as e:
            print(f"Error initializing CLI: {e}")
            sys.exit(1)
    else:
        # Launch the TUI if no arguments are provided
        try:
            from src.tui import VideoDocTUI
            app = VideoDocTUI()
            app.run()
        except Exception as e:
            print(f"Error launching TUI: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
