"""
YouTube package for the video documentation system.

This package handles YouTube authentication, content generation, and video uploads.
"""

from .auth import OAuth2Authenticator
from .content import ContentGenerator
from .uploader import YouTubeUploader

__all__ = ['OAuth2Authenticator', 'ContentGenerator', 'YouTubeUploader']