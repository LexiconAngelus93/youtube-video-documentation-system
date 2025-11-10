#!/usr/bin/env python3
"""
YouTube Authentication Module

This module handles OAuth2 authentication for YouTube API access.
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import logging
from typing import List

class OAuth2Authenticator:
    """Handles OAuth2 authentication for YouTube API."""
    
    def __init__(self, client_secrets_file: str, credentials_file: str, scopes: List[str]):
        """
        Initialize the authenticator.
        
        Args:
            client_secrets_file: Path to client secrets file
            credentials_file: Path to credentials file
            scopes: List of required scopes
        """
        self.client_secrets_file = client_secrets_file
        self.credentials_file = credentials_file
        self.scopes = scopes
        self.logger = logging.getLogger(__name__)

    def get_service(self, api_name: str, api_version: str):
        """
        Get authenticated YouTube service.
        
        Args:
            api_name: API service name
            api_version: API version
            
        Returns:
            Authenticated service object or None
        """
        creds = None
        if os.path.exists(self.credentials_file):
            try:
                creds = Credentials.from_authorized_user_file(self.credentials_file, self.scopes)
            except Exception as e:
                self.logger.warning(f"Could not load credentials: {e}. Starting fresh flow.")
                creds = None

        # If no valid credentials, initiate the flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                self.logger.info("Starting new OAuth 2.0 flow. User interaction required.")

                # Check for client secrets file
                if not os.path.exists(self.client_secrets_file):
                    self.logger.error(f"Client secrets file not found at: {self.client_secrets_file}")
                    self.logger.error("Please download 'client_secrets.json' from Google Developer Console and place it in the project root.")
                    return None

                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, self.scopes)

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
        if creds and creds.valid:
            with open(self.credentials_file, 'w') as token:
                token.write(creds.to_json())

            return build(api_name, api_version, credentials=creds)

        return None