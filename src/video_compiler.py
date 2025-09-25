#!/usr/bin/env python3
"""
Video Compiler Module

This module provides functionality to compile downloaded YouTube videos into
compilation videos with source attribution, categorization, and quality control.
"""

import os
import json
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import time
import math
from datetime import datetime

from moviepy import (
    VideoFileClip, CompositeVideoClip, TextClip, 
    concatenate_videoclips, ColorClip, config
)


class VideoCompiler:
    """
    A class to compile downloaded videos into organized compilation videos.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the video compiler with configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary containing compilation settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Compilation configuration
        compilation_config = config.get('compilation_settings', {})
        self.output_dir = compilation_config.get('output_dir', 'compilations')
        self.target_duration = compilation_config.get('target_duration_minutes', 15) * 60  # Convert to seconds
        self.max_duration = compilation_config.get('max_duration_minutes', 20) * 60
        self.min_duration = compilation_config.get('min_duration_minutes', 10) * 60
        self.video_quality = compilation_config.get('video_quality', '720p')
        self.attribution_duration = compilation_config.get('attribution_duration', 5)
        self.attribution_position = compilation_config.get('attribution_position', 'bottom')
        
        # Categorization configuration
        self.categories = config.get('categorization', {}).get('categories', {})
        
        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Compilation tracking
        self.compiled_videos = []
        self.compilation_stats = {
            'total_compilations': 0,
            'total_source_videos': 0,
            'total_duration_seconds': 0,
            'categories_created': []
        }
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Check MoviePy dependencies
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """
        Check if required dependencies (ffmpeg) are available.
        """
        try:
            config.check()
            self.logger.info("MoviePy dependencies check passed")
        except Exception as e:
            self.logger.warning(f"MoviePy dependencies check failed: {str(e)}")
    
    def compile_videos(self, video_list: List[Dict[str, Any]], 
                      categorize: bool = True) -> Dict[str, Any]:
        """
        Compile videos into organized compilation videos.
        
        Args:
            video_list (List[Dict[str, Any]]): List of downloaded video information
            categorize (bool): Whether to categorize videos before compilation
            
        Returns:
            Dict[str, Any]: Compilation results and statistics
        """
        self.logger.info(f"Starting compilation of {len(video_list)} videos")
        
        if not video_list:
            self.logger.warning("No videos provided for compilation")
            return self._get_compilation_results()
        
        # Filter valid videos
        valid_videos = self._filter_valid_videos(video_list)
        
        if not valid_videos:
            self.logger.error("No valid videos found for compilation")
            return self._get_compilation_results()
        
        # Categorize videos if requested
        if categorize:
            categorized_videos = self._categorize_videos(valid_videos)
        else:
            categorized_videos = {'uncategorized': valid_videos}
        
        # Create compilations for each category
        for category, videos in categorized_videos.items():
            if not videos:
                continue
                
            self.logger.info(f"Creating compilations for category: {category}")
            
            try:
                category_compilations = self._create_category_compilations(category, videos)
                self.compiled_videos.extend(category_compilations)
                
                with self._lock:
                    self.compilation_stats['categories_created'].append(category)
                    
            except Exception as e:
                self.logger.error(f"Error creating compilations for category {category}: {str(e)}")
        
        results = self._get_compilation_results()
        self.logger.info(f"Compilation completed: {results['stats']['total_compilations']} compilations created")
        
        return results
    
    def _filter_valid_videos(self, video_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out videos that don't exist or are corrupted.
        
        Args:
            video_list (List[Dict[str, Any]]): List of video information
            
        Returns:
            List[Dict[str, Any]]: Filtered list of valid videos
        """
        valid_videos = []
        
        for video in video_list:
            filepath = video.get('filepath', '')
            
            if not filepath or not Path(filepath).exists():
                self.logger.warning(f"Video file not found: {filepath}")
                continue
            
            # Check if file is readable and has valid duration
            try:
                with VideoFileClip(filepath) as clip:
                    duration = clip.duration
                    if duration and duration > 0:
                        video['actual_duration'] = duration
                        valid_videos.append(video)
                    else:
                        self.logger.warning(f"Invalid duration for video: {filepath}")
            except Exception as e:
                self.logger.warning(f"Error reading video {filepath}: {str(e)}")
        
        self.logger.info(f"Filtered {len(video_list) - len(valid_videos)} invalid videos")
        return valid_videos
    
    def _categorize_videos(self, video_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize videos based on keywords in titles, descriptions, and tags.
        
        Args:
            video_list (List[Dict[str, Any]]): List of video information
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Categorized videos
        """
        categorized = {category: [] for category in self.categories.keys()}
        categorized['uncategorized'] = []
        
        for video in video_list:
            # Get text content for categorization
            title = (video.get('title') or '').lower()
            description = self._get_video_description(video)
            tags = self._get_video_tags(video)
            
            text_content = f"{title} {description} {' '.join(tags)}".lower()
            
            # Find matching category
            matched_category = None
            highest_priority = float('inf')
            
            for category, category_info in self.categories.items():
                keywords = category_info.get('keywords', [])
                priority = category_info.get('priority', 999)
                
                # Check if any keywords match
                if any(keyword.lower() in text_content for keyword in keywords):
                    if priority < highest_priority:
                        highest_priority = priority
                        matched_category = category
            
            # Add to appropriate category
            if matched_category:
                categorized[matched_category].append(video)
                self.logger.debug(f"Categorized video {video.get('video_id', 'unknown')} as {matched_category}")
            else:
                categorized['uncategorized'].append(video)
        
        # Remove empty categories
        categorized = {k: v for k, v in categorized.items() if v}
        
        # Log categorization results
        for category, videos in categorized.items():
            self.logger.info(f"Category '{category}': {len(videos)} videos")
        
        return categorized
    
    def _get_video_description(self, video: Dict[str, Any]) -> str:
        """
        Get video description from metadata.
        
        Args:
            video (Dict[str, Any]): Video information
            
        Returns:
            str: Video description
        """
        # Try to get description from metadata file
        metadata_path = video.get('metadata_path', '')
        if metadata_path and Path(metadata_path).exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    return metadata.get('yt_dlp_info', {}).get('description', '')
            except Exception:
                pass
        
        # Fallback to original metadata
        return video.get('description', '')
    
    def _get_video_tags(self, video: Dict[str, Any]) -> List[str]:
        """
        Get video tags from metadata.
        
        Args:
            video (Dict[str, Any]): Video information
            
        Returns:
            List[str]: Video tags
        """
        # Try to get tags from metadata file
        metadata_path = video.get('metadata_path', '')
        if metadata_path and Path(metadata_path).exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    return metadata.get('yt_dlp_info', {}).get('tags', [])
            except Exception:
                pass
        
        # Fallback to original metadata
        return video.get('tags', [])
    
    def _create_category_compilations(self, category: str, 
                                    videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create compilation videos for a specific category.
        
        Args:
            category (str): Category name
            videos (List[Dict[str, Any]]): Videos in this category
            
        Returns:
            List[Dict[str, Any]]: List of created compilation information
        """
        # Sort videos by upload date (oldest first for chronological order)
        sorted_videos = self._sort_videos_chronologically(videos)
        
        # Group videos into compilation batches
        compilation_groups = self._group_videos_for_compilation(sorted_videos)
        
        compilations = []
        
        for i, group in enumerate(compilation_groups, 1):
            compilation_name = f"{category}_compilation_{i:03d}"
            
            try:
                compilation_info = self._create_single_compilation(
                    compilation_name, group, category
                )
                compilations.append(compilation_info)
                
                with self._lock:
                    self.compilation_stats['total_compilations'] += 1
                    self.compilation_stats['total_source_videos'] += len(group)
                    self.compilation_stats['total_duration_seconds'] += compilation_info.get('duration', 0)
                
            except Exception as e:
                self.logger.error(f"Error creating compilation {compilation_name}: {str(e)}")
        
        return compilations
    
    def _sort_videos_chronologically(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort videos by upload date in chronological order.
        
        Args:
            videos (List[Dict[str, Any]]): List of videos
            
        Returns:
            List[Dict[str, Any]]: Sorted videos
        """
        def get_upload_date(video):
            # Try to get upload date from metadata
            metadata_path = video.get('metadata_path', '')
            if metadata_path and Path(metadata_path).exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        upload_date = metadata.get('yt_dlp_info', {}).get('upload_date', '')
                        if upload_date:
                            return datetime.strptime(upload_date, '%Y%m%d')
                except Exception:
                    pass
            
            # Fallback to current time (will be sorted last)
            return datetime.now()
        
        return sorted(videos, key=get_upload_date)
    
    def _group_videos_for_compilation(self, videos: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Group videos into compilation batches based on target duration.
        
        Args:
            videos (List[Dict[str, Any]]): Sorted list of videos
            
        Returns:
            List[List[Dict[str, Any]]]: Groups of videos for compilation
        """
        groups = []
        current_group = []
        current_duration = 0
        
        for video in videos:
            video_duration = video.get('actual_duration', 0)
            
            # Check if adding this video would exceed max duration
            if current_duration + video_duration > self.max_duration and current_group:
                # Start new group if current group meets minimum duration
                if current_duration >= self.min_duration:
                    groups.append(current_group)
                    current_group = [video]
                    current_duration = video_duration
                else:
                    # Current group too short, add video anyway
                    current_group.append(video)
                    current_duration += video_duration
            else:
                # Add video to current group
                current_group.append(video)
                current_duration += video_duration
                
                # Check if we've reached target duration
                if current_duration >= self.target_duration:
                    groups.append(current_group)
                    current_group = []
                    current_duration = 0
        
        # Add remaining videos as final group if it meets minimum duration
        if current_group and current_duration >= self.min_duration:
            groups.append(current_group)
        elif current_group and groups:
            # Add remaining videos to last group if too short
            groups[-1].extend(current_group)
        elif current_group:
            # First group, add even if short
            groups.append(current_group)
        
        return groups
    
    def _create_single_compilation(self, name: str, videos: List[Dict[str, Any]], 
                                 category: str) -> Dict[str, Any]:
        """
        Create a single compilation video from a group of videos.
        
        Args:
            name (str): Compilation name
            videos (List[Dict[str, Any]]): Videos to include
            category (str): Category name
            
        Returns:
            Dict[str, Any]: Compilation information
        """
        self.logger.info(f"Creating compilation: {name} with {len(videos)} videos")
        
        clips = []
        video_segments = []
        
        for i, video in enumerate(videos):
            try:
                # Load video clip (first 5 seconds for testing)
                video_clip = VideoFileClip(video["filepath"])

                
                # Create attribution text
                attribution_text = self._create_attribution_text(video)
                
                # Add attribution overlay
                clip_with_attribution = self._add_attribution_overlay(
                    video_clip, attribution_text
                )
                
                clips.append(clip_with_attribution)
                
                # Track segment information
                video_segments.append({
                    'video_id': video.get('video_id', ''),
                    'title': video.get('title', ''),
                    'start_time': sum(clip.duration for clip in clips[:-1]),
                    'duration': clip_with_attribution.duration,
                    'source_url': video.get('url', '')
                })
                
                self.logger.debug(f"Added video {i+1}/{len(videos)} to compilation")
                
            except Exception as e:
                self.logger.error(f"Error processing video {video.get('video_id', 'unknown')}: {str(e)}")
                continue
        
        if not clips:
            raise ValueError("No valid clips to compile")
        
        # Concatenate all clips
        final_compilation = concatenate_videoclips(clips, method="compose")
        
        # Set output resolution based on quality setting
        if self.video_quality == '720p':
            final_compilation = final_compilation.with_fps(30).resized(height=720)
        elif self.video_quality == '1080p':
            final_compilation = final_compilation.with_fps(30).resized(height=1080)
        elif self.video_quality == '480p':
            final_compilation = final_compilation.with_fps(30).resized(height=480)
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{name}_{timestamp}.mp4"
        output_path = Path(self.output_dir) / output_filename
        
        # Write the compilation video
        self.logger.info(f"Writing compilation to: {output_path}")
        final_compilation.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Clean up clips to free memory
        for clip in clips:
            clip.close()
        final_compilation.close()
        
        # Create compilation metadata
        compilation_info = {
            'name': name,
            'category': category,
            'filepath': str(output_path),
            'duration': sum(segment['duration'] for segment in video_segments),
            'video_count': len(video_segments),
            'segments': video_segments,
            'created_date': datetime.now().isoformat(),
            'quality': self.video_quality,
            'filesize': output_path.stat().st_size if output_path.exists() else 0
        }
        
        # Save compilation metadata
        metadata_filename = f"{name}_{timestamp}_metadata.json"
        metadata_path = Path(self.output_dir) / metadata_filename
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(compilation_info, f, indent=2, ensure_ascii=False)
            
            compilation_info['metadata_path'] = str(metadata_path)
            
        except Exception as e:
            self.logger.warning(f"Could not save compilation metadata: {str(e)}")
        
        self.logger.info(f"Successfully created compilation: {output_filename}")
        return compilation_info
    
    def _create_attribution_text(self, video: Dict[str, Any]) -> str:
        """
        Create attribution text for a video.
        
        Args:
            video (Dict[str, Any]): Video information
            
        Returns:
            str: Attribution text
        """
        video_id = video.get('video_id', '')
        title = video.get('title', 'Unknown Title')
        uploader = video.get('uploader', 'Unknown Channel')
        
        # Create source URL
        source_url = video.get('url', f"https://www.youtube.com/watch?v={video_id}")
        
        # Format attribution text
        attribution = f"Source: {title} by {uploader}\n{source_url}"
        
        return attribution
    
    def _add_attribution_overlay(self, video_clip: VideoFileClip, 
                               attribution_text: str) -> CompositeVideoClip:
        """
        Add attribution text overlay to a video clip.
        
        Args:
            video_clip (VideoFileClip): Original video clip
            attribution_text (str): Attribution text to overlay
            
        Returns:
            CompositeVideoClip: Video with attribution overlay
        """
        # Create text clip for attribution
        text_clip = TextClip(
            text=attribution_text,
            font_size=24,
            color='white',
            stroke_color='black',
            stroke_width=2,
            duration=self.attribution_duration
        )
        
        # Position the text based on configuration
        if self.attribution_position == 'bottom':
            text_clip = text_clip.with_position(('center', 'bottom'))
        elif self.attribution_position == 'top':
            text_clip = text_clip.with_position(('center', 'top'))
        else:
            text_clip = text_clip.with_position('center')
        
        # Create semi-transparent background for text
        bg_clip = ColorClip(
            size=(video_clip.w, 80),
            color=(0, 0, 0),
            duration=self.attribution_duration
        ).with_opacity(0.7)
        
        if self.attribution_position == 'bottom':
            bg_clip = bg_clip.with_position(('center', video_clip.h - 80))
        else:
            bg_clip = bg_clip.with_position(('center', 0))
        
        # Composite the video with attribution
        return CompositeVideoClip([video_clip, bg_clip, text_clip])
    
    def _get_compilation_results(self) -> Dict[str, Any]:
        """
        Get comprehensive compilation results and statistics.
        
        Returns:
            Dict[str, Any]: Compilation results
        """
        return {
            'stats': self.compilation_stats.copy(),
            'compilations': self.compiled_videos.copy(),
            'total_size_mb': sum(
                comp.get('filesize', 0) for comp in self.compiled_videos
            ) / (1024 * 1024),
            'average_duration_minutes': (
                self.compilation_stats['total_duration_seconds'] / 
                max(self.compilation_stats['total_compilations'], 1) / 60
            )
        }
    
    def save_compilation_report(self, filename: str) -> None:
        """
        Save a detailed compilation report to a JSON file.
        
        Args:
            filename (str): Output filename
        """
        report = {
            'compilation_session': {
                'timestamp': time.time(),
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'config': self.config
            },
            'results': self._get_compilation_results()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Saved compilation report to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving compilation report: {str(e)}")


def main():
    """
    Test function for the video compiler.
    """
    # Basic configuration for testing
    config = {
        'compilation_settings': {
            'output_dir': 'compilations',
            'target_duration_minutes': 2,  # Short for testing
            'max_duration_minutes': 3,
            'min_duration_minutes': 1,
            'video_quality': '720p',
            'attribution_duration': 3,
            'attribution_position': 'bottom'
        },
        'categorization': {
            'categories': {
                'test_category': {
                    'keywords': ['test', 'video'],
                    'priority': 1
                }
            }
        }
    }
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create compiler
    compiler = VideoCompiler(config)
    
    # Test with downloaded video (if it exists)
    test_video_path = Path('downloads/raw_videos/dQw4w9WgXcQ.mp4')
    
    if test_video_path.exists():
        test_videos = [
            {
                'video_id': 'dQw4w9WgXcQ',
                'filepath': str(test_video_path),
                'title': 'Test Video',
                'uploader': 'Test Channel',
                'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'metadata_path': 'downloads/metadata/dQw4w9WgXcQ.json'
            }
        ]
        
        print("Testing video compiler...")
        results = compiler.compile_videos(test_videos)
        
        print(f"\nCompilation Results:")
        print(f"Total compilations: {results['stats']['total_compilations']}")
        print(f"Total source videos: {results['stats']['total_source_videos']}")
        print(f"Total size: {results['total_size_mb']:.2f} MB")
        
    else:
        print("No test video found. Please run the downloader first.")


if __name__ == "__main__":
    main()
