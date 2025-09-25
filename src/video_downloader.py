#!/usr/bin/env python3
"""
Video Downloader Module

This module provides functionality to download YouTube videos using yt-dlp
with metadata extraction, quality control, and batch processing capabilities.
"""

import os
import json
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
import hashlib

import yt_dlp


class VideoDownloader:
    """
    A class to download YouTube videos using yt-dlp with advanced features.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the video downloader with configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary containing download settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Download configuration
        download_config = config.get('download_settings', {})
        self.quality = download_config.get('quality', 'best')
        self.format = download_config.get('format', 'mp4')
        self.output_dir = download_config.get('output_dir', 'downloads/raw_videos')
        self.metadata_dir = download_config.get('metadata_dir', 'downloads/metadata')
        self.max_filesize = download_config.get('max_filesize', '500M')
        self.concurrent_downloads = download_config.get('concurrent_downloads', 3)
        self.retry_attempts = download_config.get('retry_attempts', 3)
        
        # Create directories
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.metadata_dir).mkdir(parents=True, exist_ok=True)
        
        # Download tracking
        self.downloaded_videos = []
        self.failed_downloads = []
        self.download_stats = {
            'total_attempted': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_size_bytes': 0
        }
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Progress callback
        self.progress_callback: Optional[Callable] = None
    
    def set_progress_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set a callback function to receive download progress updates.
        
        Args:
            callback: Function that receives progress information
        """
        self.progress_callback = callback
    
    def download_videos(self, videos: List[Dict[str, Any]], 
                       skip_existing: bool = True) -> Dict[str, Any]:
        """
        Download a list of videos with concurrent processing.
        
        Args:
            videos (List[Dict[str, Any]]): List of video metadata from YouTube searcher
            skip_existing (bool): Whether to skip already downloaded videos
            
        Returns:
            Dict[str, Any]: Download results and statistics
        """
        self.logger.info(f"Starting download of {len(videos)} videos")
        
        # Filter videos if skipping existing
        if skip_existing:
            videos = self._filter_existing_videos(videos)
        
        self.download_stats['total_attempted'] = len(videos)
        
        if not videos:
            self.logger.info("No videos to download")
            return self._get_download_results()
        
        # Download videos concurrently
        with ThreadPoolExecutor(max_workers=self.concurrent_downloads) as executor:
            # Submit download tasks
            future_to_video = {
                executor.submit(self._download_single_video, video): video 
                for video in videos
            }
            
            # Process completed downloads
            for future in as_completed(future_to_video):
                video = future_to_video[future]
                try:
                    result = future.result()
                    if result['success']:
                        with self._lock:
                            self.downloaded_videos.append(result)
                            self.download_stats['successful'] += 1
                            self.download_stats['total_size_bytes'] += result.get('filesize', 0)
                    else:
                        with self._lock:
                            self.failed_downloads.append(result)
                            self.download_stats['failed'] += 1
                            
                except Exception as e:
                    self.logger.error(f"Unexpected error downloading {video.get('video_id', 'unknown')}: {str(e)}")
                    with self._lock:
                        self.download_stats['failed'] += 1
        
        results = self._get_download_results()
        self.logger.info(f"Download completed: {results['stats']['successful']} successful, "
                        f"{results['stats']['failed']} failed")
        
        return results
    
    def _filter_existing_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out videos that have already been downloaded.
        
        Args:
            videos (List[Dict[str, Any]]): List of video metadata
            
        Returns:
            List[Dict[str, Any]]: Filtered list excluding existing videos
        """
        filtered_videos = []
        
        for video in videos:
            video_id = video.get('video_id', '')
            if not video_id:
                continue
                
            # Check if video file exists
            video_filename = self._get_video_filename(video_id)
            video_path = Path(self.output_dir) / video_filename
            
            # Check if metadata file exists
            metadata_filename = f"{video_id}.json"
            metadata_path = Path(self.metadata_dir) / metadata_filename
            
            if video_path.exists() and metadata_path.exists():
                self.logger.debug(f"Skipping existing video: {video_id}")
                self.download_stats['skipped'] += 1
            else:
                filtered_videos.append(video)
        
        self.logger.info(f"Filtered {len(videos) - len(filtered_videos)} existing videos")
        return filtered_videos
    
    def _download_single_video(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """
        Download a single video with metadata extraction.
        
        Args:
            video (Dict[str, Any]): Video metadata
            
        Returns:
            Dict[str, Any]: Download result
        """
        video_id = video.get('video_id', '')
        video_url = video.get('url', f"https://www.youtube.com/watch?v={video_id}")
        
        result = {
            'video_id': video_id,
            'url': video_url,
            'success': False,
            'error': None,
            'filepath': None,
            'metadata_path': None,
            'filesize': 0,
            'duration': 0,
            'download_time': 0
        }
        
        start_time = time.time()
        
        try:
            # Configure yt-dlp options
            ydl_opts = self._get_ydl_options(video_id)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info first
                info = ydl.extract_info(video_url, download=False)
                
                # Check file size before downloading
                filesize = info.get('filesize') or info.get('filesize_approx', 0)
                if filesize > self._parse_filesize(self.max_filesize):
                    result['error'] = f"File too large: {filesize} bytes"
                    self.logger.warning(f"Skipping {video_id}: {result['error']}")
                    return result
                
                # Download the video
                ydl.download([video_url])
                
                # Save metadata
                metadata_path = self._save_video_metadata(video_id, info, video)
                
                # Get downloaded file path
                video_filename = self._get_video_filename(video_id)
                filepath = Path(self.output_dir) / video_filename
                
                if filepath.exists():
                    result.update({
                        'success': True,
                        'filepath': str(filepath),
                        'metadata_path': metadata_path,
                        'filesize': filepath.stat().st_size,
                        'duration': info.get('duration', 0),
                        'download_time': time.time() - start_time
                    })
                    
                    self.logger.info(f"Successfully downloaded: {video_id}")
                    
                    # Call progress callback if set
                    if self.progress_callback:
                        self.progress_callback({
                            'video_id': video_id,
                            'status': 'completed',
                            'filepath': str(filepath)
                        })
                else:
                    result['error'] = "Downloaded file not found"
                    
        except yt_dlp.DownloadError as e:
            result['error'] = f"yt-dlp error: {str(e)}"
            self.logger.error(f"Download error for {video_id}: {str(e)}")
            
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected error downloading {video_id}: {str(e)}")
        
        return result
    
    def _get_ydl_options(self, video_id: str) -> Dict[str, Any]:
        """
        Get yt-dlp options for downloading.
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            Dict[str, Any]: yt-dlp options
        """
        video_filename = self._get_video_filename(video_id)
        output_template = str(Path(self.output_dir) / video_filename)
        
        options = {
            'format': f'{self.quality}[ext={self.format}]/{self.quality}',
            'outtmpl': output_template,
            'writeinfojson': False,  # We'll handle metadata separately
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'ignoreerrors': False,
            'no_warnings': False,
            'extractflat': False,
            'writethumbnail': True,
            'retries': self.retry_attempts,
            'fragment_retries': self.retry_attempts,
            'skip_unavailable_fragments': True,
            'keep_fragments': False,
            'concurrent_fragment_downloads': 4,
            'progress_hooks': [self._progress_hook],
        }
        
        return options
    
    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """
        Progress hook for yt-dlp downloads.
        
        Args:
            d (Dict[str, Any]): Progress information from yt-dlp
        """
        if self.progress_callback and d['status'] in ['downloading', 'finished']:
            # Extract video ID from filename
            filename = d.get('filename', '')
            video_id = Path(filename).stem.split('_')[0] if filename else 'unknown'
            
            progress_info = {
                'video_id': video_id,
                'status': d['status'],
                'downloaded_bytes': d.get('downloaded_bytes', 0),
                'total_bytes': d.get('total_bytes', 0),
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0)
            }
            
            self.progress_callback(progress_info)
    
    def _get_video_filename(self, video_id: str) -> str:
        """
        Generate a standardized filename for a video.
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            str: Filename for the video
        """
        return f"{video_id}.{self.format}"
    
    def _save_video_metadata(self, video_id: str, yt_info: Dict[str, Any], 
                           original_metadata: Dict[str, Any]) -> str:
        """
        Save comprehensive video metadata to a JSON file.
        
        Args:
            video_id (str): YouTube video ID
            yt_info (Dict[str, Any]): Information from yt-dlp
            original_metadata (Dict[str, Any]): Original metadata from search
            
        Returns:
            str: Path to the saved metadata file
        """
        metadata = {
            'video_id': video_id,
            'download_timestamp': time.time(),
            'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'original_metadata': original_metadata,
            'yt_dlp_info': {
                'title': yt_info.get('title'),
                'description': yt_info.get('description'),
                'uploader': yt_info.get('uploader'),
                'upload_date': yt_info.get('upload_date'),
                'duration': yt_info.get('duration'),
                'view_count': yt_info.get('view_count'),
                'like_count': yt_info.get('like_count'),
                'comment_count': yt_info.get('comment_count'),
                'tags': yt_info.get('tags', []),
                'categories': yt_info.get('categories', []),
                'thumbnail': yt_info.get('thumbnail'),
                'webpage_url': yt_info.get('webpage_url'),
                'format_id': yt_info.get('format_id'),
                'ext': yt_info.get('ext'),
                'filesize': yt_info.get('filesize'),
                'fps': yt_info.get('fps'),
                'width': yt_info.get('width'),
                'height': yt_info.get('height'),
                'resolution': yt_info.get('resolution')
            }
        }
        
        metadata_filename = f"{video_id}.json"
        metadata_path = Path(self.metadata_dir) / metadata_filename
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.debug(f"Saved metadata for {video_id}")
            return str(metadata_path)
            
        except Exception as e:
            self.logger.error(f"Error saving metadata for {video_id}: {str(e)}")
            return ""
    
    def _parse_filesize(self, size_str: str) -> int:
        """
        Parse a filesize string (e.g., "500M", "1G") to bytes.
        
        Args:
            size_str (str): Size string with unit
            
        Returns:
            int: Size in bytes
        """
        size_str = size_str.upper().strip()
        
        if size_str.endswith('K'):
            return int(float(size_str[:-1]) * 1024)
        elif size_str.endswith('M'):
            return int(float(size_str[:-1]) * 1024 * 1024)
        elif size_str.endswith('G'):
            return int(float(size_str[:-1]) * 1024 * 1024 * 1024)
        else:
            return int(size_str)
    
    def _get_download_results(self) -> Dict[str, Any]:
        """
        Get comprehensive download results and statistics.
        
        Returns:
            Dict[str, Any]: Download results
        """
        return {
            'stats': self.download_stats.copy(),
            'successful_downloads': self.downloaded_videos.copy(),
            'failed_downloads': self.failed_downloads.copy(),
            'total_size_mb': round(self.download_stats['total_size_bytes'] / (1024 * 1024), 2),
            'success_rate': (
                self.download_stats['successful'] / max(self.download_stats['total_attempted'], 1) * 100
            )
        }
    
    def save_download_report(self, filename: str) -> None:
        """
        Save a detailed download report to a JSON file.
        
        Args:
            filename (str): Output filename
        """
        report = {
            'download_session': {
                'timestamp': time.time(),
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'config': self.config
            },
            'results': self._get_download_results()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Saved download report to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving download report: {str(e)}")
    
    def get_downloaded_videos_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all successfully downloaded videos with their metadata.
        
        Returns:
            List[Dict[str, Any]]: List of downloaded video information
        """
        videos_list = []
        
        for download_result in self.downloaded_videos:
            video_info = {
                'video_id': download_result['video_id'],
                'filepath': download_result['filepath'],
                'metadata_path': download_result['metadata_path'],
                'filesize': download_result['filesize'],
                'duration': download_result['duration']
            }
            
            # Load additional metadata if available
            if download_result['metadata_path'] and Path(download_result['metadata_path']).exists():
                try:
                    with open(download_result['metadata_path'], 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        video_info.update({
                            'title': metadata.get('yt_dlp_info', {}).get('title', ''),
                            'uploader': metadata.get('yt_dlp_info', {}).get('uploader', ''),
                            'upload_date': metadata.get('yt_dlp_info', {}).get('upload_date', ''),
                            'view_count': metadata.get('yt_dlp_info', {}).get('view_count', 0),
                            'tags': metadata.get('yt_dlp_info', {}).get('tags', [])
                        })
                except Exception as e:
                    self.logger.warning(f"Could not load metadata for {download_result['video_id']}: {str(e)}")
            
            videos_list.append(video_info)
        
        return videos_list
    
    def cleanup_failed_downloads(self) -> None:
        """
        Clean up any partial or failed download files.
        """
        cleanup_count = 0
        
        for failed_download in self.failed_downloads:
            video_id = failed_download['video_id']
            
            # Remove partial video file
            video_filename = self._get_video_filename(video_id)
            video_path = Path(self.output_dir) / video_filename
            
            if video_path.exists():
                try:
                    video_path.unlink()
                    cleanup_count += 1
                    self.logger.debug(f"Removed partial file: {video_path}")
                except Exception as e:
                    self.logger.warning(f"Could not remove partial file {video_path}: {str(e)}")
            
            # Remove partial metadata file
            metadata_filename = f"{video_id}.json"
            metadata_path = Path(self.metadata_dir) / metadata_filename
            
            if metadata_path.exists():
                try:
                    metadata_path.unlink()
                    self.logger.debug(f"Removed partial metadata: {metadata_path}")
                except Exception as e:
                    self.logger.warning(f"Could not remove partial metadata {metadata_path}: {str(e)}")
        
        if cleanup_count > 0:
            self.logger.info(f"Cleaned up {cleanup_count} failed download files")


def main():
    """
    Test function for the video downloader.
    """
    # Basic configuration for testing
    config = {
        'download_settings': {
            'quality': 'best[height<=720]',  # Limit quality for testing
            'format': 'mp4',
            'output_dir': 'downloads/raw_videos',
            'metadata_dir': 'downloads/metadata',
            'max_filesize': '100M',  # Smaller limit for testing
            'concurrent_downloads': 2,
            'retry_attempts': 2
        }
    }
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create downloader
    downloader = VideoDownloader(config)
    
    # Test with a small set of videos (you would normally get these from the searcher)
    test_videos = [
        {
            'video_id': 'dQw4w9WgXcQ',  # Rick Roll for testing
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'title': 'Test Video'
        }
    ]
    
    print("Testing video downloader...")
    
    # Set up progress callback
    def progress_callback(info):
        if info['status'] == 'downloading':
            print(f"Downloading {info['video_id']}: {info.get('downloaded_bytes', 0)} bytes")
        elif info['status'] == 'finished':
            print(f"Finished downloading {info['video_id']}")
    
    downloader.set_progress_callback(progress_callback)
    
    # Download videos
    results = downloader.download_videos(test_videos)
    
    print(f"\nDownload Results:")
    print(f"Successful: {results['stats']['successful']}")
    print(f"Failed: {results['stats']['failed']}")
    print(f"Total size: {results['total_size_mb']} MB")
    print(f"Success rate: {results['success_rate']:.1f}%")


if __name__ == "__main__":
    main()
