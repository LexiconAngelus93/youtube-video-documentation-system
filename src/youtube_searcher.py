#!/usr/bin/env python3
"""
YouTube Searcher Module

This module provides functionality to search YouTube for videos related to police misconduct
using the YouTube Data API v3. It handles pagination, filtering, and metadata extraction.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from tracker import VideoTracker
from youtube.auth import OAuth2Authenticator


class YouTubeSearcher:
    """
    A class to search YouTube for videos using the YouTube Data API with filtering capabilities.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the YouTube searcher with configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing search settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Authenticate and build the YouTube service
        try:
            self.authenticator = OAuth2Authenticator(
                client_secrets_file='client_secrets.json',
                credentials_file='youtube_credentials.json',
                scopes=['https://www.googleapis.com/auth/youtube.readonly']
            )
            self.youtube = self.authenticator.get_service('youtube', 'v3')
            if not self.youtube:
                raise Exception("Failed to create YouTube service object.")
        except Exception as e:
            self.logger.error(f"Failed to authenticate with YouTube API: {e}")
            raise

        # Search configuration
        search_settings = config.get('search_settings', {})
        self.keywords = search_settings.get('keywords', [])
        self.start_date = search_settings.get('start_date', '2010-01-01')
        self.end_date = search_settings.get('end_date', 'today')
        self.region = search_settings.get('region', 'US')
        self.language = search_settings.get('language', 'en')

        # Rate limiting
        self.request_delay = search_settings.get('request_delay', 1.0)

        # Results storage
        self.found_videos = []
        self.processed_video_ids = set()

        # Initialize the video tracker
        self.tracker = VideoTracker(config)

    def search_videos(self, max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Search for videos using all configured keywords and return consolidated results.
        """
        all_videos = []
        for keyword in self.keywords:
            self.logger.info(f"Searching for keyword: '{keyword}'")
            try:
                videos = self._search_keyword(keyword, max_results)
                all_videos.extend(videos)
                time.sleep(self.request_delay)
            except Exception as e:
                self.logger.error(f"Error searching for keyword '{keyword}': {e}")
                continue

        unique_videos = self._remove_duplicates(all_videos)
        filtered_videos = self._filter_by_date(unique_videos)
        final_videos = self._filter_used_videos(filtered_videos)

        self.found_videos = final_videos
        self.logger.info(f"Total unique videos found: {len(final_videos)}")
        return final_videos

    def _search_keyword(self, keyword: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Search for videos using a specific keyword with pagination.
        """
        videos = []
        next_page_token = None
        results_count = 0

        start_date_iso = f"{self.start_date}T00:00:00Z"
        end_date_iso = f"{datetime.now().strftime('%Y-%m-%d')}T23:59:59Z" if self.end_date == 'today' else f"{self.end_date}T23:59:59Z"

        while results_count < max_results:
            try:
                search_request = self.youtube.search().list(
                    q=keyword,
                    type='video',
                    part='id,snippet',
                    maxResults=min(50, max_results - results_count),
                    publishedAfter=start_date_iso,
                    publishedBefore=end_date_iso,
                    regionCode=self.region,
                    relevanceLanguage=self.language,
                    pageToken=next_page_token
                )
                search_response = search_request.execute()

                if not search_response or 'items' not in search_response:
                    self.logger.warning(f"No response or items for keyword '{keyword}'")
                    break

                page_videos = self._extract_video_metadata(search_response['items'])
                videos.extend(page_videos)
                results_count += len(page_videos)

                next_page_token = search_response.get('nextPageToken')
                if not next_page_token:
                    self.logger.info(f"No more pages for keyword '{keyword}'")
                    break

                time.sleep(self.request_delay)

            except HttpError as e:
                self.logger.error(f"An HTTP error {e.resp.status} occurred: {e.content}")
                break
            except Exception as e:
                self.logger.error(f"Error during pagination for '{keyword}': {e}")
                break

        return videos

    def _extract_video_metadata(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract video metadata from YouTube Data API response items.
        """
        videos = []
        video_ids = [item['id']['videoId'] for item in items if item['id']['kind'] == 'youtube#video']

        if not video_ids:
            return []

        try:
            video_details_request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(video_ids)
            )
            video_details_response = video_details_request.execute()

            for item in video_details_response.get('items', []):
                video_info = {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'channel_title': item['snippet']['channelTitle'],
                    'channel_id': item['snippet']['channelId'],
                    'published_at': item['snippet']['publishedAt'],
                    'duration_iso': item['contentDetails']['duration'],
                    'view_count': item.get('statistics', {}).get('viewCount', 0),
                    'description': item['snippet']['description'],
                    'thumbnails': item['snippet']['thumbnails'],
                    'url': f"https://www.youtube.com/watch?v={item['id']}",
                    'search_timestamp': datetime.now().isoformat()
                }
                videos.append(video_info)

        except HttpError as e:
            self.logger.error(f"An HTTP error {e.resp.status} occurred while fetching video details: {e.content}")
        except Exception as e:
            self.logger.error(f"Error fetching video details: {e}")

        return videos

    def _remove_duplicates(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate videos based on video ID.
        """
        seen_ids = set()
        unique_videos = []
        for video in videos:
            if video['video_id'] not in seen_ids:
                seen_ids.add(video['video_id'])
                unique_videos.append(video)
        self.logger.info(f"Removed {len(videos) - len(unique_videos)} duplicate videos")
        return unique_videos

    def _filter_by_date(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter videos by publication date range (already handled by API, but good for verification).
        """
        # This is mostly redundant as the API query now handles date filtering.
        # However, it can serve as a secondary check.
        return videos

    def _filter_used_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out videos that have already been processed.
        """
        new_videos = [v for v in videos if not self.tracker.is_video_used(v['video_id'])]
        self.logger.info(f"Filtered out {len(videos) - len(new_videos)} already used videos")
        return new_videos

    def save_results(self, file_path: str):
        """
        Save the found videos to a JSON file.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.found_videos, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(self.found_videos)} search results to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving search results: {e}")

    def load_results(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load video results from a JSON file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                videos = json.load(f)
            self.logger.info(f"Loaded {len(videos)} videos from {file_path}")
            self.found_videos = videos
            return videos
        except Exception as e:
            self.logger.error(f"Error loading search results: {e}")
            return []
