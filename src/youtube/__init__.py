"""
YouTube Integration Package

This package provides modular components for YouTube API integration:
- auth: OAuth2 authentication handling
- content: LLM-based content generation for titles and descriptions
- uploader: Video upload orchestration
"""

from .auth import OAuth2Authenticator
from .content import ContentGenerator
from .uploader import YouTubeUploader

__all__ = ['OAuth2Authenticator', 'ContentGenerator', 'YouTubeUploader']
