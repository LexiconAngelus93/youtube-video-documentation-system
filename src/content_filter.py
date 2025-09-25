#!/usr/bin/env python3
"""
Content Filter and Metadata Management Module

This module provides functionality to filter, validate, and manage video content
and metadata for the YouTube video documentation system.
"""

import os
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import time


class ContentFilter:
    """
    A class to filter and validate video content based on various criteria.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the content filter with configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Load filtering criteria
        self.categories = config.get('categorization', {}).get('categories', {})
        
        # Content validation settings
        self.min_duration = config.get('content_filter', {}).get('min_duration_seconds', 30)
        self.max_duration = config.get('content_filter', {}).get('max_duration_seconds', 3600)
        self.min_views = config.get('content_filter', {}).get('min_views', 100)
        self.blocked_channels = set(config.get('content_filter', {}).get('blocked_channels', []))
        self.required_keywords = config.get('content_filter', {}).get('required_keywords', [])
        self.excluded_keywords = config.get('content_filter', {}).get('excluded_keywords', [])
        
        # Quality filters
        self.min_resolution_height = config.get('content_filter', {}).get('min_resolution_height', 240)
        self.max_file_size_mb = config.get('content_filter', {}).get('max_file_size_mb', 500)
        
        # Duplicate detection
        self.duplicate_threshold = config.get('content_filter', {}).get('duplicate_threshold', 0.8)
        
        # Statistics tracking
        self.filter_stats = {
            'total_processed': 0,
            'passed_filters': 0,
            'failed_duration': 0,
            'failed_views': 0,
            'failed_keywords': 0,
            'failed_quality': 0,
            'failed_duplicates': 0,
            'blocked_channels': 0
        }
    
    def filter_videos(self, videos: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Filter a list of videos based on configured criteria.
        
        Args:
            videos (List[Dict[str, Any]]): List of video metadata
            
        Returns:
            Tuple[List[Dict[str, Any]], Dict[str, Any]]: Filtered videos and filter statistics
        """
        self.logger.info(f"Filtering {len(videos)} videos")
        
        filtered_videos = []
        self.filter_stats['total_processed'] = len(videos)
        
        # Track seen video IDs for duplicate detection
        seen_video_ids = set()
        
        for video in videos:
            # Check for duplicates first
            video_id = video.get('video_id', '')
            if video_id in seen_video_ids:
                self.filter_stats['failed_duplicates'] += 1
                self.logger.debug(f"Duplicate video ID: {video_id}")
                continue
            
            # Apply all filters
            if self._passes_all_filters(video):
                filtered_videos.append(video)
                seen_video_ids.add(video_id)
                self.filter_stats['passed_filters'] += 1
        
        self.logger.info(f"Filtered videos: {len(filtered_videos)}/{len(videos)} passed")
        return filtered_videos, self.filter_stats.copy()
    
    def _passes_all_filters(self, video: Dict[str, Any]) -> bool:
        """
        Check if a video passes all configured filters.
        
        Args:
            video (Dict[str, Any]): Video metadata
            
        Returns:
            bool: True if video passes all filters
        """
        # Duration filter
        if not self._passes_duration_filter(video):
            self.filter_stats['failed_duration'] += 1
            return False
        
        # Views filter
        if not self._passes_views_filter(video):
            self.filter_stats['failed_views'] += 1
            return False
        
        # Channel filter
        if not self._passes_channel_filter(video):
            self.filter_stats['blocked_channels'] += 1
            return False
        
        # Keyword filter
        if not self._passes_keyword_filter(video):
            self.filter_stats['failed_keywords'] += 1
            return False
        
        # Quality filter
        if not self._passes_quality_filter(video):
            self.filter_stats['failed_quality'] += 1
            return False
        
        return True
    
    def _passes_duration_filter(self, video: Dict[str, Any]) -> bool:
        """
        Check if video duration is within acceptable range.
        
        Args:
            video (Dict[str, Any]): Video metadata
            
        Returns:
            bool: True if duration is acceptable
        """
        duration = video.get('duration_seconds', 0)
        if isinstance(duration, str):
            try:
                duration = int(duration)
            except ValueError:
                duration = 0
        
        return self.min_duration <= duration <= self.max_duration
    
    def _passes_views_filter(self, video: Dict[str, Any]) -> bool:
        """
        Check if video has minimum required views.
        
        Args:
            video (Dict[str, Any]): Video metadata
            
        Returns:
            bool: True if views meet minimum requirement
        """
        views = video.get('view_count', 0)
        if isinstance(views, str):
            try:
                # Handle view count strings like "1.2M views"
                views = self._parse_view_count(views)
            except ValueError:
                views = 0
        
        return views >= self.min_views
    
    def _parse_view_count(self, view_string: str) -> int:
        """
        Parse view count string to integer.
        
        Args:
            view_string (str): View count string (e.g., "1.2M views", "500K")
            
        Returns:
            int: Parsed view count
        """
        if not view_string:
            return 0
        
        # Remove common suffixes
        view_string = view_string.lower().replace('views', '').replace('view', '').strip()
        
        # Handle multipliers
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000}
        
        for suffix, multiplier in multipliers.items():
            if view_string.endswith(suffix):
                number_part = view_string[:-1]
                try:
                    return int(float(number_part) * multiplier)
                except ValueError:
                    return 0
        
        # Try to parse as integer
        try:
            return int(view_string.replace(',', ''))
        except ValueError:
            return 0
    
    def _passes_channel_filter(self, video: Dict[str, Any]) -> bool:
        """
        Check if video channel is not in blocked list.
        
        Args:
            video (Dict[str, Any]): Video metadata
            
        Returns:
            bool: True if channel is not blocked
        """
        channel_title = (video.get('channel_title') or '').lower()
        channel_id = video.get('channel_id', '')
        
        return (channel_title not in self.blocked_channels and 
                channel_id not in self.blocked_channels)
    
    def _passes_keyword_filter(self, video: Dict[str, Any]) -> bool:
        """
        Check if video content matches keyword requirements.
        
        Args:
            video (Dict[str, Any]): Video metadata
            
        Returns:
            bool: True if keywords are acceptable
        """
        # Get text content for analysis
        title = (video.get('title') or '').lower()
        description = (video.get('description') or '').lower()
        tags = [tag.lower() for tag in video.get('tags', [])]
        
        text_content = f"{title} {description} {' '.join(tags)}"
        
        # Check required keywords
        if self.required_keywords:
            has_required = any(
                keyword.lower() in text_content 
                for keyword in self.required_keywords
            )
            if not has_required:
                return False
        
        # Check excluded keywords
        if self.excluded_keywords:
            has_excluded = any(
                keyword.lower() in text_content 
                for keyword in self.excluded_keywords
            )
            if has_excluded:
                return False
        
        return True
    
    def _passes_quality_filter(self, video: Dict[str, Any]) -> bool:
        """
        Check if video meets quality requirements.
        
        Args:
            video (Dict[str, Any]): Video metadata
            
        Returns:
            bool: True if quality is acceptable
        """
        # Check file size if available
        filesize = video.get('filesize', 0)
        if filesize > 0:
            filesize_mb = filesize / (1024 * 1024)
            if filesize_mb > self.max_file_size_mb:
                return False
        
        # Check resolution if available (from downloaded metadata)
        metadata_path = video.get('metadata_path', '')
        if metadata_path and Path(metadata_path).exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    height = metadata.get('yt_dlp_info', {}).get('height', 0)
                    if height > 0 and height < self.min_resolution_height:
                        return False
            except Exception:
                pass
        
        return True
    
    def detect_duplicates(self, videos: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Detect potential duplicate videos based on title similarity and duration.
        
        Args:
            videos (List[Dict[str, Any]]): List of video metadata
            
        Returns:
            List[List[Dict[str, Any]]]: Groups of potential duplicates
        """
        self.logger.info(f"Detecting duplicates in {len(videos)} videos")
        
        duplicate_groups = []
        processed_indices = set()
        
        for i, video1 in enumerate(videos):
            if i in processed_indices:
                continue
            
            current_group = [video1]
            processed_indices.add(i)
            
            for j, video2 in enumerate(videos[i+1:], i+1):
                if j in processed_indices:
                    continue
                
                if self._are_likely_duplicates(video1, video2):
                    current_group.append(video2)
                    processed_indices.add(j)
            
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
        
        self.logger.info(f"Found {len(duplicate_groups)} groups of potential duplicates")
        return duplicate_groups
    
    def _are_likely_duplicates(self, video1: Dict[str, Any], video2: Dict[str, Any]) -> bool:
        """
        Check if two videos are likely duplicates.
        
        Args:
            video1 (Dict[str, Any]): First video metadata
            video2 (Dict[str, Any]): Second video metadata
            
        Returns:
            bool: True if videos are likely duplicates
        """
        # Check title similarity
        title1 = (video1.get('title') or '').lower()
        title2 = (video2.get('title') or '').lower()
        
        title_similarity = self._calculate_text_similarity(title1, title2)
        
        # Check duration similarity (within 10% or 30 seconds)
        duration1 = video1.get('duration_seconds', 0)
        duration2 = video2.get('duration_seconds', 0)
        
        if duration1 > 0 and duration2 > 0:
            duration_diff = abs(duration1 - duration2)
            duration_similarity = 1 - (duration_diff / max(duration1, duration2))
            
            # Allow 30 seconds difference for short videos
            if duration_diff <= 30:
                duration_similarity = max(duration_similarity, 0.9)
        else:
            duration_similarity = 0.5  # Unknown duration
        
        # Check channel similarity
        channel1 = (video1.get('channel_title') or '').lower()
        channel2 = (video2.get('channel_title') or '').lower()
        channel_similarity = 1.0 if channel1 == channel2 else 0.0
        
        # Weighted similarity score
        overall_similarity = (
            title_similarity * 0.6 + 
            duration_similarity * 0.3 + 
            channel_similarity * 0.1
        )
        
        return overall_similarity >= self.duplicate_threshold
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings using Jaccard similarity.
        
        Args:
            text1 (str): First text
            text2 (str): Second text
            
        Returns:
            float: Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
        
        # Tokenize and create sets
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def categorize_videos(self, videos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize videos based on content analysis.
        
        Args:
            videos (List[Dict[str, Any]]): List of video metadata
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Categorized videos
        """
        self.logger.info(f"Categorizing {len(videos)} videos")
        
        categorized = {category: [] for category in self.categories.keys()}
        categorized['uncategorized'] = []
        
        for video in videos:
            category = self._determine_video_category(video)
            categorized[category].append(video)
        
        # Log categorization results
        for category, video_list in categorized.items():
            if video_list:
                self.logger.info(f"Category '{category}': {len(video_list)} videos")
        
        return categorized
    
    def _determine_video_category(self, video: Dict[str, Any]) -> str:
        """
        Determine the most appropriate category for a video.
        
        Args:
            video (Dict[str, Any]): Video metadata
            
        Returns:
            str: Category name
        """
        # Get text content for analysis
        title = (video.get('title') or '').lower()
        description = (video.get('description') or '').lower()
        tags = [tag.lower() for tag in video.get('tags', [])]
        
        text_content = f"{title} {description} {' '.join(tags)}"
        
        # Find best matching category
        best_category = 'uncategorized'
        highest_priority = float('inf')
        max_matches = 0
        
        for category, category_info in self.categories.items():
            keywords = category_info.get('keywords', [])
            priority = category_info.get('priority', 999)
            
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword.lower() in text_content)
            
            # Select category with most matches, then by priority
            if matches > max_matches or (matches == max_matches and priority < highest_priority):
                max_matches = matches
                highest_priority = priority
                best_category = category
        
        return best_category if max_matches > 0 else 'uncategorized'
    
    def validate_video_files(self, videos: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validate that video files exist and are accessible.
        
        Args:
            videos (List[Dict[str, Any]]): List of video metadata
            
        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: Valid videos and invalid videos
        """
        self.logger.info(f"Validating {len(videos)} video files")
        
        valid_videos = []
        invalid_videos = []
        
        for video in videos:
            filepath = video.get('filepath', '')
            
            if not filepath:
                invalid_videos.append({**video, 'validation_error': 'No filepath specified'})
                continue
            
            file_path = Path(filepath)
            
            if not file_path.exists():
                invalid_videos.append({**video, 'validation_error': 'File does not exist'})
                continue
            
            if not file_path.is_file():
                invalid_videos.append({**video, 'validation_error': 'Path is not a file'})
                continue
            
            if file_path.stat().st_size == 0:
                invalid_videos.append({**video, 'validation_error': 'File is empty'})
                continue
            
            # File appears valid
            valid_videos.append(video)
        
        self.logger.info(f"File validation: {len(valid_videos)} valid, {len(invalid_videos)} invalid")
        return valid_videos, invalid_videos
    
    def generate_content_report(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive content analysis report.
        
        Args:
            videos (List[Dict[str, Any]]): List of video metadata
            
        Returns:
            Dict[str, Any]: Content analysis report
        """
        report = {
            'summary': {
                'total_videos': len(videos),
                'total_duration_hours': sum(v.get('duration_seconds', 0) for v in videos) / 3600,
                'total_views': sum(v.get('view_count', 0) for v in videos),
                'unique_channels': len(set(v.get('channel_title', '') for v in videos)),
                'date_range': self._get_date_range(videos)
            },
            'categories': self._analyze_categories(videos),
            'quality_metrics': self._analyze_quality(videos),
            'temporal_distribution': self._analyze_temporal_distribution(videos),
            'channel_analysis': self._analyze_channels(videos),
            'filter_statistics': self.filter_stats.copy()
        }
        
        return report
    
    def _get_date_range(self, videos: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get the date range of videos."""
        dates = []
        for video in videos:
            # Try to extract date from metadata
            metadata_path = video.get('metadata_path', '')
            if metadata_path and Path(metadata_path).exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        upload_date = metadata.get('yt_dlp_info', {}).get('upload_date', '')
                        if upload_date:
                            dates.append(datetime.strptime(upload_date, '%Y%m%d'))
                except Exception:
                    pass
        
        if dates:
            return {
                'earliest': min(dates).strftime('%Y-%m-%d'),
                'latest': max(dates).strftime('%Y-%m-%d')
            }
        return {'earliest': 'Unknown', 'latest': 'Unknown'}
    
    def _analyze_categories(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze category distribution."""
        categorized = self.categorize_videos(videos)
        return {
            category: {
                'count': len(video_list),
                'percentage': len(video_list) / len(videos) * 100 if videos else 0,
                'total_duration_minutes': sum(v.get('duration_seconds', 0) for v in video_list) / 60
            }
            for category, video_list in categorized.items()
            if video_list
        }
    
    def _analyze_quality(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze video quality metrics."""
        durations = [v.get('duration_seconds', 0) for v in videos if v.get('duration_seconds', 0) > 0]
        views = [v.get('view_count', 0) for v in videos if v.get('view_count', 0) > 0]
        
        return {
            'duration_stats': {
                'min_seconds': min(durations) if durations else 0,
                'max_seconds': max(durations) if durations else 0,
                'avg_seconds': sum(durations) / len(durations) if durations else 0
            },
            'view_stats': {
                'min_views': min(views) if views else 0,
                'max_views': max(views) if views else 0,
                'avg_views': sum(views) / len(views) if views else 0
            }
        }
    
    def _analyze_temporal_distribution(self, videos: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze temporal distribution of videos."""
        year_counts = {}
        
        for video in videos:
            metadata_path = video.get('metadata_path', '')
            if metadata_path and Path(metadata_path).exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        upload_date = metadata.get('yt_dlp_info', {}).get('upload_date', '')
                        if upload_date:
                            year = upload_date[:4]
                            year_counts[year] = year_counts.get(year, 0) + 1
                except Exception:
                    pass
        
        return year_counts
    
    def _analyze_channels(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze channel distribution."""
        channel_stats = {}
        
        for video in videos:
            channel = video.get('channel_title', 'Unknown')
            if channel not in channel_stats:
                channel_stats[channel] = {
                    'video_count': 0,
                    'total_views': 0,
                    'total_duration': 0
                }
            
            channel_stats[channel]['video_count'] += 1
            channel_stats[channel]['total_views'] += video.get('view_count', 0)
            channel_stats[channel]['total_duration'] += video.get('duration_seconds', 0)
        
        # Sort by video count
        sorted_channels = sorted(
            channel_stats.items(), 
            key=lambda x: x[1]['video_count'], 
            reverse=True
        )
        
        return dict(sorted_channels[:20])  # Top 20 channels
    
    def save_filter_report(self, filename: str, videos: List[Dict[str, Any]]) -> None:
        """
        Save a comprehensive filtering and analysis report.
        
        Args:
            filename (str): Output filename
            videos (List[Dict[str, Any]]): Processed videos
        """
        report = {
            'filter_session': {
                'timestamp': time.time(),
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'config': self.config
            },
            'content_analysis': self.generate_content_report(videos)
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Saved filter report to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving filter report: {str(e)}")


def main():
    """
    Test function for the content filter.
    """
    # Basic configuration for testing
    config = {
        'categorization': {
            'categories': {
                'traffic_stop': {
                    'keywords': ['traffic stop', 'pulled over', 'speeding'],
                    'priority': 1
                },
                'protest': {
                    'keywords': ['protest', 'demonstration', 'blm'],
                    'priority': 2
                }
            }
        },
        'content_filter': {
            'min_duration_seconds': 30,
            'max_duration_seconds': 1800,
            'min_views': 100,
            'blocked_channels': ['spam_channel'],
            'required_keywords': ['police'],
            'excluded_keywords': ['fake', 'parody'],
            'min_resolution_height': 240,
            'max_file_size_mb': 500,
            'duplicate_threshold': 0.8
        }
    }
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create filter
    content_filter = ContentFilter(config)
    
    # Test with sample videos
    test_videos = [
        {
            'video_id': 'test1',
            'title': 'Police Traffic Stop Gone Wrong',
            'channel_title': 'News Channel',
            'duration_seconds': 300,
            'view_count': 50000,
            'description': 'A police officer conducts a traffic stop',
            'tags': ['police', 'traffic', 'stop']
        },
        {
            'video_id': 'test2',
            'title': 'Fake Police Prank Video',
            'channel_title': 'Prank Channel',
            'duration_seconds': 120,
            'view_count': 10000,
            'description': 'Fake police prank for entertainment',
            'tags': ['fake', 'prank', 'police']
        },
        {
            'video_id': 'test3',
            'title': 'BLM Protest Coverage',
            'channel_title': 'News Network',
            'duration_seconds': 600,
            'view_count': 100000,
            'description': 'Coverage of Black Lives Matter protest',
            'tags': ['protest', 'blm', 'police']
        }
    ]
    
    print("Testing content filter...")
    
    # Filter videos
    filtered_videos, stats = content_filter.filter_videos(test_videos)
    
    print(f"\nFilter Results:")
    print(f"Total processed: {stats['total_processed']}")
    print(f"Passed filters: {stats['passed_filters']}")
    print(f"Failed keywords: {stats['failed_keywords']}")
    
    # Categorize videos
    categorized = content_filter.categorize_videos(filtered_videos)
    
    print(f"\nCategorization:")
    for category, videos in categorized.items():
        if videos:
            print(f"{category}: {len(videos)} videos")
    
    # Generate report
    report = content_filter.generate_content_report(filtered_videos)
    print(f"\nContent Report Summary:")
    print(f"Total videos: {report['summary']['total_videos']}")
    print(f"Unique channels: {report['summary']['unique_channels']}")


if __name__ == "__main__":
    main()
