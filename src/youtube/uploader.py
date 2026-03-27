"""
YouTube Uploader Module

Orchestrates video uploads to YouTube using the YouTube Data API v3.
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from .auth import OAuth2Authenticator
from .content import ContentGenerator


# YouTube API constants
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Retry configuration
MAX_RETRIES = 10
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


class YouTubeUploader:
    """
    Orchestrates video uploads to YouTube with automatic content generation.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the YouTube uploader.

        Args:
            config: Configuration dictionary containing youtube_upload and llm_settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # YouTube upload configuration
        upload_config = config.get('youtube_upload', {})
        self.client_secrets_file = upload_config.get('client_secrets_file', 'client_secrets.json')
        self.credentials_file = upload_config.get('credentials_file', 'youtube_credentials.json')
        self.privacy_status = upload_config.get('privacy_status', 'unlisted')
        self.category_id = upload_config.get('category_id', '25')  # News & Politics
        self.default_tags = upload_config.get('default_tags', [
            'police misconduct', 'accountability', 'civil rights', 'documentation'
        ])

        # Initialize authenticator
        self.auth = OAuth2Authenticator(
            self.client_secrets_file,
            self.credentials_file,
            SCOPES
        )

        # Initialize content generator
        self.content_generator = ContentGenerator() # Initialize the hardcoded ContentGenerator    # YouTube service (initialized on first use)
        self._youtube = None

        # Upload statistics
        self.upload_stats = {
            'total_uploads': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'uploaded_videos': []
        }

    @property
    def youtube(self):
        """Lazy initialization of YouTube service."""
        if self._youtube is None:
            self._youtube = self.auth.get_service(API_SERVICE_NAME, API_VERSION)
        return self._youtube

    def upload_compilation(self, compilation_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload a single compilation video to YouTube.

        Args:
            compilation_info: Dictionary containing:
                - filepath: Path to the video file
                - category: Category of the compilation
                - video_count: Number of source videos
                - total_duration: Total duration in seconds
                - video_segments: List of segment information

        Returns:
            Dictionary with upload result including video_id if successful
        """
        filepath = compilation_info.get('filepath', '')

        if not filepath or not Path(filepath).exists():
            self.logger.error(f"Video file not found: {filepath}")
            return {"status": "error", "message": "Video file not found"}

        if not self.youtube:
            self.logger.error("YouTube service not initialized. Check authentication.")
            return {"status": "error", "message": "Authentication failed"}

        # Generate content using LLM
        self.logger.info("Generating title and description...")
        content = self.content_generator.generate(compilation_info)

        # Build video metadata
        body = self._build_video_metadata(compilation_info, content)

        # Create media upload
        media = MediaFileUpload(
            filepath,
            chunksize=1024 * 1024,  # 1MB chunks
            resumable=True
        )

        # Execute upload with retry logic
        try:
            self.logger.info(f"Starting upload: {content.get('title', 'Untitled')}")
            result = self._execute_upload(body, media)
            
            self.upload_stats['total_uploads'] += 1
            self.upload_stats['successful_uploads'] += 1
            self.upload_stats['uploaded_videos'].append({
                'video_id': result.get('id'),
                'title': content.get('title'),
                'filepath': filepath
            })

            return {
                "status": "success",
                "video_id": result.get('id'),
                "title": content.get('title'),
                "url": f"https://www.youtube.com/watch?v={result.get('id')}"
            }

        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            self.upload_stats['total_uploads'] += 1
            self.upload_stats['failed_uploads'] += 1
            return {"status": "error", "message": str(e)}

    def upload_compilations(self, compilations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload multiple compilation videos to YouTube.

        Args:
            compilations: List of compilation info dictionaries

        Returns:
            Dictionary with overall upload results and statistics
        """
        results = []

        for i, compilation in enumerate(compilations):
            self.logger.info(f"Uploading compilation {i + 1}/{len(compilations)}")
            result = self.upload_compilation(compilation)
            results.append(result)

            # Add delay between uploads to avoid rate limiting
            if i < len(compilations) - 1:
                time.sleep(5)

        return {
            "results": results,
            "stats": self.upload_stats
        }

    def _build_video_metadata(self, compilation_info: Dict[str, Any], 
                               content: Dict[str, str]) -> Dict[str, Any]:
        """Build the video metadata for YouTube upload."""
        title = content.get('title', 'Police Misconduct Documentation')
        description = content.get('description', '')

        # Add source attribution to description
        segments = compilation_info.get('video_segments', [])
        if segments:
            description += "\n\n--- Source Videos ---\n"
            for seg in segments:
                source_url = seg.get('source_url', '')
                seg_title = seg.get('title', 'Unknown')
                if source_url:
                    description += f"\n• {seg_title}: {source_url}"

        # Build tags
        category = compilation_info.get('category', '')
        tags = list(self.default_tags)
        if category:
            tags.append(category.replace('_', ' '))

        return {
            'snippet': {
                'title': title[:100],  # YouTube title limit
                'description': description[:5000],  # YouTube description limit
                'tags': tags[:500],  # YouTube tags limit
                'categoryId': self.category_id
            },
            'status': {
                'privacyStatus': self.privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }

    def _execute_upload(self, body: Dict[str, Any], media: MediaFileUpload) -> Dict[str, Any]:
        """Execute the upload with exponential backoff retry logic."""
        insert_request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )

        response = None
        retry = 0

        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    self.logger.info(f"Upload progress: {progress}%")

            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    retry += 1
                    if retry > MAX_RETRIES:
                        raise Exception(f"Max retries exceeded: {e}")
                    
                    sleep_seconds = 2 ** retry
                    self.logger.warning(f"Retry {retry}/{MAX_RETRIES} in {sleep_seconds}s: {e}")
                    time.sleep(sleep_seconds)
                else:
                    raise

        self.logger.info(f"Upload complete! Video ID: {response.get('id')}")
        return response

    def is_authenticated(self) -> bool:
        """Check if YouTube authentication is set up."""
        return self.auth.is_authenticated()

    def get_upload_stats(self) -> Dict[str, Any]:
        """Get current upload statistics."""
        return self.upload_stats
