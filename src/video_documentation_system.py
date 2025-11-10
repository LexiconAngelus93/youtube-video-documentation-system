#!/usr/bin/env python3
"""
Video Documentation System Module

This module contains the main VideoDocumentationSystem class.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List
import yaml
from datetime import datetime
import time
from youtube_searcher import YouTubeSearcher
from video_downloader import VideoDownloader
from video_compiler import VideoCompiler
from content_filter import ContentFilter
from youtube_uploader import YouTubeUploader
from tracker import VideoTracker

class VideoDocumentationSystem:
    """
    Main controller class for the YouTube video documentation system.
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize the video documentation system.
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize the tracker first
        self.tracker = VideoTracker(self.config)
        
        # Initialize components
        self.searcher = YouTubeSearcher(self.config)
        self.downloader = VideoDownloader(self.config)
        self.content_filter = ContentFilter(self.config)
        self.compiler = VideoCompiler(self.config)
        self.uploader = YouTubeUploader(self.config)
        
        # Session tracking
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_dir = Path('sessions') / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Initialized video documentation system - Session: {self.session_id}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Error loading config file {self.config_path}: {str(e)}")
            sys.exit(1)
    
    def _setup_logging(self) -> None:
        """
        Set up logging configuration.
        """
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_file = log_config.get('file', 'logs/app.log')
        
        # Create logs directory
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_full_pipeline(self, max_videos: int = None) -> Dict[str, Any]:
        """
        Run the complete video documentation pipeline.
        
        Args:
            max_videos (int, optional): Maximum number of videos to process
            
        Returns:
            Dict[str, Any]: Pipeline results
        """
        self.logger.info("Starting full video documentation pipeline")
        
        results = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'search_results': {},
            'download_results': {},
            'filter_results': {},
            'compilation_results': {},
            'upload_results': {},
            'errors': []
        }
        
        try:
            # Step 1: Search for videos
            self.logger.info("Step 1: Searching for videos")
            search_limit = max_videos or self.config.get('search_settings', {}).get('max_results_per_keyword', 500)
            videos = self.searcher.search_videos(max_results=search_limit)
            
            results['search_results'] = {
                'total_found': len(videos),
                'statistics': self.searcher.get_video_statistics()
            }
            
            # Save search results
            search_file = self.session_dir / 'search_results.json'
            self.searcher.save_results(str(search_file))
            
            if not videos:
                self.logger.warning("No videos found in search")
                return results
            
            # Step 2: Filter videos
            self.logger.info("Step 2: Filtering videos")
            filtered_videos, filter_stats = self.content_filter.filter_videos(videos)
            
            results['filter_results'] = {
                'total_filtered': len(filtered_videos),
                'filter_statistics': filter_stats
            }
            
            # Save filter report
            filter_report_file = self.session_dir / 'filter_report.json'
            self.logger.info("Saving filter report...")
            self.content_filter.save_filter_report(str(filter_report_file), filtered_videos)
            self.logger.info("Filter report saved.")
            
            if not filtered_videos:
                self.logger.warning("No videos passed filtering")
                return results
            
            # Limit videos if specified
            if max_videos and len(filtered_videos) > max_videos:
                filtered_videos = filtered_videos[:max_videos]
                self.logger.info(f"Limited to {max_videos} videos for processing")
            
            # Step 3: Download videos
            self.logger.info("Step 3: Downloading videos")
            download_results = self.downloader.download_videos(filtered_videos)
            
            results['download_results'] = download_results
            
            # Save download report
            download_report_file = self.session_dir / 'download_report.json'
            self.downloader.save_download_report(str(download_report_file))
            
            if download_results['stats']['successful'] == 0:
                self.logger.warning("No videos were successfully downloaded")
                return results
            
            # Step 4: Validate downloaded videos
            self.logger.info("Step 4: Validating downloaded videos")
            downloaded_videos = self.downloader.get_downloaded_videos_list()
            valid_videos, invalid_videos = self.content_filter.validate_video_files(downloaded_videos)
            
            if invalid_videos:
                self.logger.warning(f"Found {len(invalid_videos)} invalid video files")
            
            if not valid_videos:
                self.logger.error("No valid video files for compilation")
                return results
            
            # Step 5: Create compilations
            self.logger.info("Step 5: Creating video compilations")
            compilation_results = self.compiler.compile_videos(valid_videos, categorize=True)
            
            results['compilation_results'] = compilation_results
            
            # Save compilation report
            compilation_report_file = self.session_dir / 'compilation_report.json'
            self.compiler.save_compilation_report(str(compilation_report_file))

            # Step 6: Upload compilations
            self.logger.info("Step 6: Uploading compilations to YouTube")
            compilations_to_upload = compilation_results.get("compilations", [])
            upload_results_list = []
            for comp in compilations_to_upload:
                upload_result = self.uploader.upload_video(comp)
                upload_results_list.append(upload_result)
            results['upload_results'] = upload_results_list
            
            results['end_time'] = datetime.now().isoformat()
            results['success'] = True
            
            self.logger.info("Pipeline completed successfully")
            
        except Exception as e:
            self.logger.error(f"Pipeline error: {str(e)}")
            results['errors'].append(str(e))
            results['success'] = False
        
        # Save final results
        results_file = self.session_dir / 'pipeline_results.json'
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            self.logger.error(f"Error saving pipeline results: {str(e)}")
        
        return results
    
    def search_only(self, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Run only the search phase.
        
        Args:
            max_results (int, optional): Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Search results
        """
        self.logger.info("Running search-only mode")
        
        search_limit = max_results or self.config.get('search_settings', {}).get('max_results_per_keyword', 500)
        videos = self.searcher.search_videos(max_results=search_limit)
        
        # Save results
        search_file = self.session_dir / 'search_only_results.json'
        self.searcher.save_results(str(search_file))
        
        return videos
    
    def download_from_file(self, search_results_file: str) -> Dict[str, Any]:
        """
        Download videos from a saved search results file.
        
        Args:
            search_results_file (str): Path to search results JSON file
            
        Returns:
            Dict[str, Any]: Download results
        """
        self.logger.info(f"Downloading from file: {search_results_file}")
        
        try:
            videos = self.searcher.load_results(search_results_file)
            
            if not videos:
                self.logger.error("No videos loaded from file")
                return {}
            
            # Filter videos
            filtered_videos, _ = self.content_filter.filter_videos(videos)
            
            # Download videos
            download_results = self.downloader.download_videos(filtered_videos)
            
            # Save download report
            download_report_file = self.session_dir / 'download_from_file_report.json'
            self.downloader.save_download_report(str(download_report_file))
            
            return download_results
            
        except Exception as e:
            self.logger.error(f"Error downloading from file: {str(e)}")
            return {}
    
    def compile_from_downloads(self, downloads_dir: str = None) -> Dict[str, Any]:
        """
        Create compilations from existing downloaded videos.
        
        Args:
            downloads_dir (str, optional): Directory containing downloaded videos
            
        Returns:
            Dict[str, Any]: Compilation results
        """
        self.logger.info("Creating compilations from existing downloads")
        
        try:
            # Get downloaded videos list
            downloaded_videos = self.downloader.get_downloaded_videos_list()
            
            if not downloaded_videos:
                self.logger.error("No downloaded videos found")
                return {}
            
            # Validate video files
            valid_videos, invalid_videos = self.content_filter.validate_video_files(downloaded_videos)
            
            if invalid_videos:
                self.logger.warning(f"Found {len(invalid_videos)} invalid video files")
            
            if not valid_videos:
                self.logger.error("No valid video files for compilation")
                return {}
            
            # Create compilations
            compilation_results = self.compiler.compile_videos(valid_videos, categorize=True)
            
            # Save compilation report
            compilation_report_file = self.session_dir / 'compile_from_downloads_report.json'
            self.compiler.save_compilation_report(str(compilation_report_file))
            
            return compilation_results
            
        except Exception as e:
            self.logger.error(f"Error creating compilations: {str(e)}")
            return {}

    def upload_from_file(self, compilation_report_file: str) -> None:
        """
        Upload compilations from a saved compilation report file.

        Args:
            compilation_report_file (str): Path to compilation report JSON file
        """
        self.logger.info(f"Uploading from file: {compilation_report_file}")

        try:
            with open(compilation_report_file, "r", encoding="utf-8") as f:
                compilations = json.load(f).get("compilations", [])

            if not compilations:
                self.logger.warning("No compilations found in the report file.")
                return

            upload_results = []
            for compilation in compilations:
                self.logger.info(f"Uploading compilation: {compilation.get('name')}")
                upload_result = self.uploader.upload_video(compilation)
                upload_results.append(upload_result)

            # Save upload report
            upload_report_file = self.session_dir / "upload_from_file_report.json"
            with open(upload_report_file, "w", encoding="utf-8") as f:
                json.dump(upload_results, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Error uploading from file: {str(e)}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current session.
        
        Returns:
            Dict[str, Any]: Session summary
        """
        summary = {
            'session_id': self.session_id,
            'session_dir': str(self.session_dir),
            'config_file': self.config_path,
            'files_created': []
        }
        
        # List files in session directory
        if self.session_dir.exists():
            summary['files_created'] = [
                str(f.relative_to(self.session_dir)) 
                for f in self.session_dir.iterdir() 
                if f.is_file()
            ]
        
        return summary


