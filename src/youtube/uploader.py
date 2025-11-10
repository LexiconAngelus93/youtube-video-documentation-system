#!/usr/bin/env python3
"""
YouTube Upload Module

This module handles video uploads to YouTube using the refactored architecture.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from .auth import OAuth2Authenticator
from .content import ContentGenerator

# The CLIENT_SECRETS_FILE is the file downloaded from the Google Developers Console
# It should be placed in the project root directory
CLIENT_SECRETS_FILE = "client_secrets.json"

# This scope allows full write access to the authenticated user's YouTube account
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

class YouTubeUploader:
    """
    Refactored YouTube uploader that coordinates authentication and content generation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the YouTube Uploader with configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize authentication
        auth_cfg = config.get('youtube_upload', {})
        self.auth = OAuth2Authenticator(
            auth_cfg.get('client_secrets_file', CLIENT_SECRETS_FILE),
            auth_cfg.get('credentials_file', 'youtube_credentials.json'),
            SCOPES
        )
        
        # Initialize content generator
        llm_cfg = config.get('llm_settings', {})
        self.generator = ContentGenerator(llm_cfg.get('model', 'gpt-3.5-turbo'))
        
        # Get YouTube service
        self.youtube = self._get_authenticated_service()

    def _get_authenticated_service(self):
        """
        Get authenticated YouTube service.
        
        Returns:
            Authenticated service object or None
        """
        try:
            return self.auth.get_service(API_SERVICE_NAME, API_VERSION)
        except Exception as e:
            self.logger.error(f"Failed to get authenticated service: {e}")
            return None

    def _build_metadata(self, compilation_info: Dict[str, Any], content: Dict[str, str]) -> Dict[str, Any]:
        """
        Build video metadata for upload.
        
        Args:
            compilation_info: Compilation information
            content: Generated content (title and description)
            
        Returns:
            Metadata dictionary
        """
        tags = [
            compilation_info.get('category', 'misconduct'), 
            "police brutality", 
            "police misconduct", 
            "journalism", 
            "accountability"
        ]

        return {
            "snippet": {
                "title": content['title'],
                "description": content['description'],
                "tags": tags,
                "categoryId": "25"  # News & Politics
            },
            "status": {
                "privacyStatus": "unlisted",  # Start as unlisted for review
                "selfDeclaredMadeForKids": False
            },
            "recordingDetails": {
                "recordingDate": datetime.now().isoformat()
            }
        }

    def _execute_upload(self, body: Dict[str, Any], filepath: str) -> Dict[str, Any]:
        """
        Execute the actual upload to YouTube.
        
        Args:
            body: Video metadata
            filepath: Path to video file
            
        Returns:
            Upload response or error
        """
        try:
            media_file = MediaFileUpload(filepath, chunksize=-1, resumable=True)

            self.logger.info(f"Starting upload for: {body['snippet']['title']}")

            insert_request = self.youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media_file
            )

            # Execute the upload
            response = insert_request.execute()

            self.logger.info(f"Upload successful. Video ID: {response['id']}")
            return {
                "status": "success",
                "video_id": response['id'],
                "url": f"https://youtu.be/{response['id']}",
                "title": body['snippet']['title'],
                "description": body['snippet']['description']
            }

        except HttpError as e:
            self.logger.error(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return {"status": "failed", "reason": f"HTTP Error: {e.resp.status}"}
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during upload: {e}")
            return {"status": "failed", "reason": f"Unexpected Error: {e}"}

    def upload_video(self, compilation_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload a video to YouTube.

        Args:
            compilation_info (Dict[str, Any]): Metadata about the compilation video.

        Returns:
            Dict[str, Any]: Upload status and YouTube video ID.
        """
        if not self.youtube:
            self.logger.error("YouTube service not initialized. Cannot upload video.")
            return {"status": "failed", "reason": "YouTube service not initialized"}

        # 1. Generate Title and Description
        content = self.generator.generate(compilation_info)
        
        # 2. Prepare Video Metadata
        body = self._build_metadata(compilation_info, content)
        
        # 3. Execute Upload
        return self._execute_upload(body, compilation_info['filepath'])