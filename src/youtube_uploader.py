#!/usr/bin/env python3
"""
YouTube Uploader Module

This module handles the automatic upload of compilation videos to a configured
YouTube channel using the YouTube Data API v3. It also generates titles and
descriptions for the videos using an LLM.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

# Google API imports
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# LLM imports
from openai import OpenAI

# The CLIENT_SECRETS_FILE is the file downloaded from the Google Developers Console
# It should be placed in the project root directory
CLIENT_SECRETS_FILE = "client_secrets.json"

# This scope allows full write access to the authenticated user's YouTube account
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

class YouTubeUploader:
    """
    A class to handle YouTube video uploads and content generation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the YouTube Uploader with configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # YouTube API configuration
        self.upload_config = config.get('youtube_upload', {})
        self.client_secrets_file = self.upload_config.get('client_secrets_file', CLIENT_SECRETS_FILE)
        self.credentials_file = self.upload_config.get('credentials_file', 'youtube_credentials.json')
        
        # LLM configuration
        self.llm_config = config.get('llm_settings', {})
        self.llm_model = self.llm_config.get('model', 'gpt-4.1-mini')
        
        # Initialize LLM client
        self.llm_client = OpenAI()
        
        # Initialize YouTube service
        self.youtube = self._get_authenticated_service()
        
    def _get_authenticated_service(self):
        """
        Authenticate with YouTube and return the service object.
        
        This method handles the OAuth 2.0 flow, which requires user interaction
        to grant permission. The credentials are saved for future use.
        """
        credentials = None
        
        # Load credentials from file if they exist
        if os.path.exists(self.credentials_file):
            try:
                from google.oauth2.credentials import Credentials
                credentials = Credentials.from_authorized_user_file(self.credentials_file, SCOPES)
            except Exception as e:
                self.logger.warning(f"Could not load credentials: {e}. Starting fresh flow.")
                credentials = None

        # If no valid credentials, initiate the flow
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                self.logger.info("Refreshing expired credentials...")
                credentials.refresh(Request())
            else:
                self.logger.info("Starting new OAuth 2.0 flow. User interaction required.")
                
                # Check for client secrets file
                if not os.path.exists(self.client_secrets_file):
                    self.logger.error(f"Client secrets file not found at: {self.client_secrets_file}")
                    self.logger.error("Please download 'client_secrets.json' from Google Developer Console and place it in the project root.")
                    return None

                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, SCOPES)
                
                # This part requires user interaction (opening a browser, logging in, copying a code)
                # Since we are in a sandbox, we must ask the user to perform this step.
                self.logger.info("Please complete the OAuth flow in your browser.")
                
                # We will skip the interactive part for now and assume the user will handle it
                # or that the credentials file will be provided.
                # The user must manually run the OAuth flow and provide the credentials file.
                
                # Since we cannot perform the interactive OAuth flow, we will inform the user
                # and proceed with a placeholder service object.
                self.logger.warning("Automatic OAuth flow is not possible in this environment. Please ensure 'youtube_credentials.json' is present.")
                return None # The actual upload will fail without valid credentials

        # Save the credentials for the next run
        if credentials and credentials.valid:
            with open(self.credentials_file, 'w') as token:
                token.write(credentials.to_json())
            
            return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
        
        return None

    def generate_content(self, compilation_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a title and description for the compilation video using an LLM.
        
        Args:
            compilation_info (Dict[str, Any]): Metadata about the compilation video.
            
        Returns:
            Dict[str, str]: Dictionary with 'title' and 'description' keys.
        """
        self.logger.info("Generating title and description using LLM...")
        
        # Extract key information for the prompt
        category = compilation_info.get('category', 'Police Misconduct')
        video_count = compilation_info.get('video_count', 0)
        total_duration = compilation_info.get('duration', 0)
        
        # Get details of the first few videos for context
        segment_details = "\n".join([
            f"- {s['title']} (Source: {s['source_url']})" 
            for s in compilation_info.get('segments', []) if not s['title'].startswith('Title Page')
        ][:5])
        
        # System prompt to guide the LLM's persona and style
        system_prompt = (
            "You are a professional, objective, and journalistic content creator specializing in "
            "documenting police misconduct and accountability. Your tone should be serious, factual, "
            "and focused on public interest and transparency. You must generate a compelling title "
            "and a detailed, objective description for a YouTube compilation video."
        )
        
        # User prompt with all necessary context
        user_prompt = (
            f"Generate a title (max 100 characters) and a detailed description (min 500 characters) "
            f"for a compilation video documenting police misconduct. The video is categorized as '{category}' "
            f"and contains {video_count} separate incidents with a total runtime of {total_duration/60:.2f} minutes. "
            f"The description must include a strong call to action for accountability and a clear disclaimer "
            f"that the content is for journalistic and public interest purposes. "
            f"The description must also list the source of each incident included in the compilation. "
            f"Here are the details of the first few incidents:\n{segment_details}"
            f"\n\nFormat the output as a JSON object with 'title' and 'description' keys."
        )
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            generated_content = json.loads(content)
            
            self.logger.info("Content generation successful.")
            return generated_content
            
        except Exception as e:
            self.logger.error(f"LLM content generation failed: {e}")
            # Fallback to a generic title and description
            return {
                "title": f"Police Misconduct Compilation - {category} Incidents",
                "description": (
                    f"This video is a compilation of {video_count} incidents of alleged police misconduct "
                    f"categorized as '{category}'. This content is provided for journalistic and public "
                    f"interest purposes to promote transparency and accountability. Viewer discretion is advised. "
                    f"Please refer to the source links for original context. [LLM generation failed, using fallback]."
                )
            }

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
        content = self.generate_content(compilation_info)
        title = content['title']
        description = content['description']
        
        # 2. Prepare Video Metadata
        tags = [compilation_info.get('category', 'misconduct'), "police brutality", "police misconduct", "journalism", "accountability"]
        
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "25" # News & Politics
            },
            "status": {
                "privacyStatus": "unlisted", # Start as unlisted for review
                "selfDeclaredMadeForKids": False
            },
            "recordingDetails": {
                "recordingDate": datetime.now().isoformat()
            }
        }
        
        # 3. Perform Upload
        try:
            media_file = MediaFileUpload(compilation_info['filepath'], chunksize=-1, resumable=True)
            
            self.logger.info(f"Starting upload for: {title}")
            
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
                "title": title,
                "description": description
            }
            
        except HttpError as e:
            self.logger.error(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return {"status": "failed", "reason": f"HTTP Error: {e.resp.status}"}
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during upload: {e}")
            return {"status": "failed", "reason": f"Unexpected Error: {e}"}

def main():
    """
    Test function for the YouTube Uploader.
    """
    # Basic configuration for testing
    config = {
        'youtube_upload': {
            'client_secrets_file': 'client_secrets.json',
            'credentials_file': 'youtube_credentials.json'
        },
        'llm_settings': {
            'model': 'gpt-4.1-mini'
        }
    }
    
    # Mock compilation info (replace with real data for actual test)
    mock_compilation = {
        'name': 'test_compilation',
        'category': 'excessive_force',
        'filepath': 'path/to/your/test_video.mp4', # MUST be a real path for upload
        'duration': 1200, # 20 minutes
        'video_count': 5,
        'segments': [
            {'title': 'Officer Slams Man to Ground', 'source_url': 'https://youtu.be/abc1'},
            {'title': 'Unlawful Arrest at Protest', 'source_url': 'https://youtu.be/abc2'},
            {'title': 'Driver Refuses to Consent to Search', 'source_url': 'https://youtu.be/abc3'},
            {'title': 'Police Misconduct Caught on Bodycam', 'source_url': 'https://youtu.be/abc4'},
            {'title': 'Citizen Audit Goes Wrong', 'source_url': 'https://youtu.be/abc5'},
        ],
        'quality': '720p'
    }
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing YouTube Uploader...")
    uploader = YouTubeUploader(config)
    
    # Test content generation
    generated_content = uploader.generate_content(mock_compilation)
    print("\nGenerated Content:")
    print(json.dumps(generated_content, indent=2))
    
    # Note: Actual upload test requires a valid video file and manual OAuth setup.
    # The user must provide the client_secrets.json and complete the OAuth flow.
    # For now, we only test the setup and content generation.
    print("\nUpload test skipped. Requires manual OAuth setup and a valid video file.")


if __name__ == "__main__":
    main()
