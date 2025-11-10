#!/usr/bin/env python3
"""
YouTube Authentication Module

This module handles OAuth2 authentication for YouTube API access.
"""

import os
import logging
from typing import List, Optional

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

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

    def get_service(self, api_name: str, api_version: str) -> Optional[object]:
        """
        Get authenticated YouTube service.
        
        This method attempts to load existing credentials and refresh them if needed.
        It does not handle interactive OAuth flows - credentials must be generated
        separately and placed in the credentials file.
        
        Args:
            api_name: API service name
            api_version: API version
            
        Returns:
            Authenticated service object or None if authentication fails
        """
        creds = None
        
        # 1) Try loading existing credentials
        if os.path.exists(self.credentials_file):
            try:
                creds = Credentials.from_authorized_user_file(self.credentials_file, self.scopes)
            except Exception as e:
                self.logger.warning(f"Couldn't load credentials ({e}), will fail fast")

        # 2) Attempt a silent refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                self.logger.warning(f"Failed to refresh credentials ({e})")
                creds = None

        # 3) If still no valid creds, fail fast
        if not creds or not creds.valid:
            self.logger.error(
                f"No valid credentials found. "
                f"Please run the OAuth flow locally to generate {self.credentials_file}"
            )
            return None

        # 4) Persist refreshed creds and build service
        with open(self.credentials_file, "w") as token:
            token.write(creds.to_json())

        return build(api_name, api_version, credentials=creds)
