"""
YouTube Video Documentation System

A Python package for searching, downloading, and compiling YouTube videos
related to police misconduct for journalistic documentation purposes.
"""

__version__ = "1.1.0"
__author__ = "Manus AI"
__description__ = "YouTube Video Documentation System for Police Misconduct Research"

from .youtube_searcher import YouTubeSearcher
from .video_downloader import VideoDownloader
from .content_filter import ContentFilter
from .video_compiler import VideoCompiler
from .youtube import YouTubeUploader, OAuth2Authenticator, ContentGenerator
from .tui import VideoDocTUI
from .tracker import VideoTracker

__all__ = [
    'YouTubeSearcher',
    'VideoDownloader',
    'ContentFilter',
    'VideoCompiler',
    'YouTubeUploader',
    'OAuth2Authenticator',
    'ContentGenerator',
    'VideoDocTUI',
    'VideoTracker'
]
