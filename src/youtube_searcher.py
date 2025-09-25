#!/usr/bin/env python3
"""
YouTube Searcher Module

This module provides functionality to search YouTube for videos related to police misconduct
using the Manus YouTube Search API. It handles pagination, filtering, and metadata extraction.
"""

import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time

# Add the Manus API client path
sys.path.append('/opt/.manus/.sandbox-runtime')
from data_api import ApiClient


class YouTubeSearcher:
    """
    A class to search YouTube for videos using the Manus API with filtering capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the YouTube searcher with configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary containing search settings
        """
        self.config = config
        self.client = ApiClient()
        self.logger = logging.getLogger(__name__)
        
        # Search configuration
        self.keywords = config.get('search_settings', {}).get('keywords', [])
        self.start_date = config.get('search_settings', {}).get('start_date', '2010-01-01')
        self.end_date = config.get('search_settings', {}).get('end_date', 'today')
        self.region = config.get('search_settings', {}).get('region', 'US')
        self.language = config.get('search_settings', {}).get('language', 'en')
        
        # Rate limiting
        self.request_delay = config.get('search_settings', {}).get('request_delay', 1.0)
        
        # Results storage
        self.found_videos = []
        self.processed_video_ids = set()
        
    def search_videos(self, max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Search for videos using all configured keywords and return consolidated results.
        
        Args:
            max_results (int): Maximum number of videos to retrieve per keyword
            
        Returns:
            List[Dict[str, Any]]: List of video metadata dictionaries
        """
        all_videos = []
        
        for keyword in self.keywords:
            self.logger.info(f"Searching for keyword: '{keyword}'")
            
            try:
                videos = self._search_keyword(keyword, max_results)
                all_videos.extend(videos)
                
                # Rate limiting between keyword searches
                time.sleep(self.request_delay)
                
            except Exception as e:
                self.logger.error(f"Error searching for keyword '{keyword}': {str(e)}")
                continue
        
        # Remove duplicates based on video ID
        unique_videos = self._remove_duplicates(all_videos)
        
        # Filter by date range
        filtered_videos = self._filter_by_date(unique_videos)
        
        # Filter by region/content
        final_videos = self._filter_by_region(filtered_videos)
        
        self.found_videos = final_videos
        self.logger.info(f"Total unique videos found: {len(final_videos)}")
        
        return final_videos
    
    def _search_keyword(self, keyword: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Search for videos using a specific keyword with pagination.
        
        Args:
            keyword (str): Search keyword
            max_results (int): Maximum number of results to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of video metadata
        """
        videos = []
        cursor = None
        results_count = 0
        
        while results_count < max_results:
            try:
                # Prepare search query
                query_params = {
                    'q': keyword,
                    'hl': self.language,
                    'gl': self.region
                }
                
                if cursor:
                    query_params['cursor'] = cursor
                
                # Make API call
                response = self.client.call_api('Youtube/search', query=query_params)
                
                if not response:
                    self.logger.warning(f"No response for keyword '{keyword}'")
                    break
                
                # Extract videos from response
                contents = response.get('contents', [])
                page_videos = self._extract_video_metadata(contents)
                
                videos.extend(page_videos)
                results_count += len(page_videos)
                
                # Check for next page
                cursor = response.get('cursorNext', '')
                if not cursor:
                    self.logger.info(f"No more pages for keyword '{keyword}'")
                    break
                
                self.logger.debug(f"Retrieved {len(page_videos)} videos for '{keyword}' (total: {results_count})")
                
                # Rate limiting between requests
                time.sleep(self.request_delay)
                
            except Exception as e:
                self.logger.error(f"Error in pagination for keyword '{keyword}': {str(e)}")
                break
        
        return videos
    
    def _extract_video_metadata(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract video metadata from API response contents.
        
        Args:
            contents (List[Dict[str, Any]]): Raw API response contents
            
        Returns:
            List[Dict[str, Any]]: Processed video metadata
        """
        videos = []
        
        for item in contents:
            if item.get('type') == 'video':
                video_data = item.get('video', {})
                
                # Extract relevant metadata
                video_info = {
                    'video_id': video_data.get('videoId', ''),
                    'title': video_data.get('title', ''),
                    'channel_title': video_data.get('channelTitle', ''),
                    'channel_id': video_data.get('channelId', ''),
                    'published_time': video_data.get('publishedTimeText', ''),
                    'duration_seconds': video_data.get('lengthSeconds', 0),
                    'view_count': video_data.get('stats', {}).get('views', 0),
                    'description': video_data.get('descriptionSnippet', ''),
                    'thumbnails': video_data.get('thumbnails', []),
                    'url': f"https://www.youtube.com/watch?v={video_data.get('videoId', '')}",
                    'is_live': video_data.get('isLiveNow', False),
                    'badges': video_data.get('badges', []),
                    'search_timestamp': datetime.now().isoformat()
                }
                
                # Only add if we have a valid video ID
                if video_info['video_id']:
                    videos.append(video_info)
        
        return videos
    
    def _remove_duplicates(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate videos based on video ID.
        
        Args:
            videos (List[Dict[str, Any]]): List of video metadata
            
        Returns:
            List[Dict[str, Any]]: Deduplicated list
        """
        seen_ids = set()
        unique_videos = []
        
        for video in videos:
            video_id = video.get('video_id', '')
            if video_id and video_id not in seen_ids:
                seen_ids.add(video_id)
                unique_videos.append(video)
        
        self.logger.info(f"Removed {len(videos) - len(unique_videos)} duplicate videos")
        return unique_videos
    
    def _filter_by_date(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter videos by publication date range.
        
        Args:
            videos (List[Dict[str, Any]]): List of video metadata
            
        Returns:
            List[Dict[str, Any]]: Filtered list
        """
        if self.start_date == 'today' and self.end_date == 'today':
            return videos
        
        filtered_videos = []
        
        # Parse start date
        if self.start_date == 'today':
            start_date = datetime.now()
        else:
            start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
        
        # Parse end date
        if self.end_date == 'today':
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
        
        for video in videos:
            published_time = video.get('published_time', '')
            
            # Try to parse the published time (YouTube format can vary)
            video_date = self._parse_youtube_date(published_time)
            
            if video_date and start_date <= video_date <= end_date:
                filtered_videos.append(video)
        
        self.logger.info(f"Filtered {len(videos) - len(filtered_videos)} videos outside date range")
        return filtered_videos
    
    def _parse_youtube_date(self, date_string: str) -> Optional[datetime]:
        """
        Parse YouTube's date format to datetime object.
        
        Args:
            date_string (str): Date string from YouTube API
            
        Returns:
            Optional[datetime]: Parsed datetime or None if parsing fails
        """
        if not date_string:
            return None
        
        # Common YouTube date formats
        formats = [
            '%Y-%m-%d',
            '%b %d, %Y',
            '%B %d, %Y'
        ]
        
        # Handle relative dates like "2 days ago", "1 week ago", etc.
        if 'ago' in date_string.lower():
            return self._parse_relative_date(date_string)
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        self.logger.warning(f"Could not parse date: {date_string}")
        return None
    
    def _parse_relative_date(self, date_string: str) -> Optional[datetime]:
        """
        Parse relative date strings like "2 days ago".
        
        Args:
            date_string (str): Relative date string
            
        Returns:
            Optional[datetime]: Calculated datetime or None
        """
        now = datetime.now()
        date_string = date_string.lower()
        
        try:
            if 'day' in date_string:
                days = int(date_string.split()[0])
                return now - timedelta(days=days)
            elif 'week' in date_string:
                weeks = int(date_string.split()[0])
                return now - timedelta(weeks=weeks)
            elif 'month' in date_string:
                months = int(date_string.split()[0])
                return now - timedelta(days=months * 30)  # Approximate
            elif 'year' in date_string:
                years = int(date_string.split()[0])
                return now - timedelta(days=years * 365)  # Approximate
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _filter_by_region(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter videos by region/content indicators for US content.
        
        Args:
            videos (List[Dict[str, Any]]): List of video metadata
            
        Returns:
            List[Dict[str, Any]]: Filtered list
        """
        if self.region != 'US':
            return videos
        
        # Keywords that indicate US content
        us_indicators = [
            'police', 'cop', 'sheriff', 'deputy', 'officer',
            'usa', 'america', 'united states', 'us',
            'state', 'county', 'city', 'department',
            'pd', 'sheriff\'s office'
        ]
        
        filtered_videos = []
        
        for video in videos:
            title = (video.get('title') or '').lower()
            description = (video.get('description') or '').lower()
            channel = (video.get('channel_title') or '').lower()
            
            # Check if any US indicators are present
            text_to_check = f"{title} {description} {channel}"
            
            if any(indicator in text_to_check for indicator in us_indicators):
                filtered_videos.append(video)
        
        self.logger.info(f"Filtered {len(videos) - len(filtered_videos)} videos without US indicators")
        return filtered_videos
    
    def save_results(self, filename: str) -> None:
        """
        Save search results to a JSON file.
        
        Args:
            filename (str): Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.found_videos, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(self.found_videos)} videos to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving results to {filename}: {str(e)}")
    
    def load_results(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load search results from a JSON file.
        
        Args:
            filename (str): Input filename
            
        Returns:
            List[Dict[str, Any]]: Loaded video metadata
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.found_videos = json.load(f)
            
            self.logger.info(f"Loaded {len(self.found_videos)} videos from {filename}")
            return self.found_videos
            
        except Exception as e:
            self.logger.error(f"Error loading results from {filename}: {str(e)}")
            return []
    
    def get_video_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the found videos.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        if not self.found_videos:
            return {}
        
        total_videos = len(self.found_videos)
        total_duration = sum(video.get('duration_seconds', 0) for video in self.found_videos)
        total_views = sum(video.get('view_count', 0) for video in self.found_videos)
        
        # Channel statistics
        channels = {}
        for video in self.found_videos:
            channel = video.get('channel_title', 'Unknown')
            channels[channel] = channels.get(channel, 0) + 1
        
        top_channels = sorted(channels.items(), key=lambda x: x[1], reverse=True)[:10]
        
        stats = {
            'total_videos': total_videos,
            'total_duration_seconds': total_duration,
            'total_duration_hours': round(total_duration / 3600, 2),
            'total_views': total_views,
            'average_duration_seconds': round(total_duration / total_videos, 2) if total_videos > 0 else 0,
            'average_views': round(total_views / total_videos, 2) if total_videos > 0 else 0,
            'unique_channels': len(channels),
            'top_channels': top_channels
        }
        
        return stats


def main():
    """
    Test function for the YouTube searcher.
    """
    # Basic configuration for testing
    config = {
        'search_settings': {
            'keywords': [
                'police brutality',
                'police misconduct'
            ],
            'start_date': '2020-01-01',
            'end_date': 'today',
            'region': 'US',
            'language': 'en',
            'request_delay': 1.0
        }
    }
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create searcher and test
    searcher = YouTubeSearcher(config)
    
    print("Testing YouTube searcher...")
    videos = searcher.search_videos(max_results=50)
    
    print(f"\nFound {len(videos)} videos")
    
    if videos:
        print("\nFirst video:")
        print(json.dumps(videos[0], indent=2))
        
        print("\nStatistics:")
        stats = searcher.get_video_statistics()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
