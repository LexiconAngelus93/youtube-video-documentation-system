#!/usr/bin/env python3
"""
CLI Handler Module

This module handles command-line argument parsing and mode dispatch.
"""

import sys
import argparse
from typing import Dict, Any, Optional

class CLIHandler:
    """Handles command-line interface operations."""
    
    def __init__(self):
        """Initialize the CLI handler."""
        self.parser = self._setup_parser()
    
    def _setup_parser(self) -> argparse.ArgumentParser:
        """
        Setup the argument parser.
        
        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description='YouTube Video Documentation System for Police Misconduct Research'
        )

        parser.add_argument(
            '--config', '-c',
            default='config.yaml',
            help='Configuration file path (default: config.yaml)'
        )

        parser.add_argument(
            '--mode', '-m',
            choices=["full", "search", "download", "compile", "upload"],
            default='full',
            help='Operation mode (default: full)'
        )

        parser.add_argument(
            '--max-videos', '-n',
            type=int,
            help='Maximum number of videos to process'
        )

        parser.add_argument(
            '--input-file', '-i',
            help='Input file for download or compile modes'
        )

        parser.add_argument(
            '--downloads-dir', '-d',
            help='Downloads directory for compile mode'
        )
        
        return parser
    
    def handle_cli(self) -> None:
        """
        Handle command-line interface execution.
        """
        args = self.parser.parse_args()

        try:
            # Import here to avoid circular imports
            from main import VideoDocumentationSystem
            
            # Initialize system
            system = VideoDocumentationSystem(args.config)

            # Execute based on mode
            if args.mode == 'full':
                print("Running full pipeline...")
                results = system.run_full_pipeline(max_videos=args.max_videos)

                if results.get('success'):
                    print(f"\nPipeline completed successfully!")
                    print(f"Session ID: {results['session_id']}")
                    print(f"Videos found: {results['search_results'].get('total_found', 0)}")
                    print(f"Videos downloaded: {results['download_results'].get('stats', {}).get('successful', 0)}")
                    print(f"Compilations created: {results['compilation_results'].get('stats', {}).get('total_compilations', 0)}")
                    print(f"Uploads: {len(results.get('upload_results', []))}")
                else:
                    print(f"\nPipeline failed. Check logs for details.")
                    if results.get('errors'):
                        print(f"Errors: {results['errors']}")

            elif args.mode == 'search':
                print("Running search only...")
                videos = system.search_only(max_results=args.max_videos)
                print(f"Found {len(videos)} videos")

            elif args.mode == 'download':
                if not args.input_file:
                    print("Error: --input-file required for download mode")
                    sys.exit(1)

                print(f"Downloading from file: {args.input_file}")
                results = system.download_from_file(args.input_file)
                print(f"Downloaded {results.get('stats', {}).get('successful', 0)} videos")

            elif args.mode == 'compile':
                print("Creating compilations from downloads...")
                results = system.compile_from_downloads(downloads_dir=args.downloads_dir)
                print(f"Created {results.get('stats', {}).get('total_compilations', 0)} compilations")

            elif args.mode == 'upload':
                if not args.input_file:
                    print("Error: --input-file required for upload mode (e.g., a compilation_report.json)")
                    sys.exit(1)
                print(f"Uploading from file: {args.input_file}")
                system.upload_from_file(args.input_file)

            # Show session summary
            summary = system.get_session_summary()
            print(f"\nSession Summary:")
            print(f"Session ID: {summary['session_id']}")
            print(f"Session directory: {summary['session_dir']}")
            print(f"Files created: {len(summary['files_created'])}")

        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)