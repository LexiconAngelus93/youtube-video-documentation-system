"""
OAuth2 Authenticator Module

Handles YouTube API authentication using OAuth 2.0.
"""

import os
import logging
from typing import Optional, List

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource


class OAuth2Authenticator:
    """
    Handles OAuth2 authentication for YouTube API access.
    """

    def __init__(self, client_secrets_file: str, credentials_file: str, scopes: List[str]):
        """
        Initialize the OAuth2 authenticator.

        Args:
            client_secrets_file: Path to the client secrets JSON file from Google Cloud Console
            credentials_file: Path to store/load the user credentials
            scopes: List of OAuth2 scopes required for the application
        """
        self.client_secrets_file = client_secrets_file
        self.credentials_file = credentials_file
        self.scopes = scopes
        self.logger = logging.getLogger(__name__)

    def get_credentials(self) -> Optional[Credentials]:
        """
        Get valid OAuth2 credentials, refreshing or creating new ones as needed.

        Returns:
            Valid Credentials object, or None if authentication fails
        """
        creds = None

        # Load existing credentials if available
        if os.path.exists(self.credentials_file):
            try:
                creds = Credentials.from_authorized_user_file(self.credentials_file, self.scopes)
                self.logger.info("Loaded existing credentials from file")
            except Exception as e:
                self.logger.warning(f"Failed to load credentials: {e}")

        # Refresh or create new credentials if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.logger.info("Refreshed expired credentials")
                except Exception as e:
                    self.logger.warning(f"Failed to refresh credentials: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.client_secrets_file):
                    self.logger.error(f"Client secrets file not found: {self.client_secrets_file}")
                    return None

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secrets_file, self.scopes
                    )
                    creds = flow.run_local_server(open_browser=True)
                    self.logger.info("Created new credentials via OAuth flow")
                except Exception as e:
                    self.logger.error(f"OAuth flow failed: {e}")
                    return None

            # Save credentials for future use
            try:
                with open(self.credentials_file, 'w') as f:
                    f.write(creds.to_json())
                self.logger.info(f"Saved credentials to {self.credentials_file}")
            except Exception as e:
                self.logger.warning(f"Failed to save credentials: {e}")

        return creds

    def get_service(self, api_name: str, api_version: str) -> Optional[Resource]:
        """
        Build and return an authenticated API service.

        Args:
            api_name: Name of the API (e.g., 'youtube')
            api_version: Version of the API (e.g., 'v3')

        Returns:
            Authenticated API service resource, or None if authentication fails
        """
        creds = self.get_credentials()
        if not creds:
            return None

        try:
            service = build(api_name, api_version, credentials=creds)
            self.logger.info(f"Built {api_name} {api_version} service")
            return service
        except Exception as e:
            self.logger.error(f"Failed to build API service: {e}")
            return None

    def is_authenticated(self) -> bool:
        """
        Check if valid credentials exist.

        Returns:
            True if valid credentials are available, False otherwise
        """
        if not os.path.exists(self.credentials_file):
            return False

        try:
            creds = Credentials.from_authorized_user_file(self.credentials_file, self.scopes)
            return creds.valid or (creds.expired and creds.refresh_token)
        except Exception:
            return False
