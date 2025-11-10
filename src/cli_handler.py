#!/usr/bin/env python3
"""
CLI Handler Module

This module handles command-line argument parsing and mode dispatch.
"""

import sys
import argparse
from typing import Dict, Any

class CLIHandler:
    """Handles command-line interface operations."""
    
    def __init__(self):
        """Initialize the CLI handler."""
        self.parser = self._setup_parser()
    
    def _setup_parser(self) -> argparse.ArgumentParser:
        """
        Setup the argument parser with subcommands.
        
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

        # Create subparsers for different modes
        subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
        
        # Full pipeline mode
        full_parser = subparsers.add_parser('full', help='Run full pipeline')
        full_parser.add_argument('--max-videos', '-n', type=int, help='Maximum number of videos to process')
        
        # Search only mode
        search_parser = subparsers.add_parser('search', help='Search for videos only')
        search_parser.add_argument('--max-videos', '-n', type=int, help='Maximum number of videos')
        
        # Download mode
        download_parser = subparsers.add_parser('download', help='Download videos from file')
        download_parser.add_argument('--input-file', '-i', required=True, help='Input file with video list')
        
        # Compile mode
        compile_parser = subparsers.add_parser('compile', help='Create compilations from downloads')
        compile_parser.add_argument('--downloads-dir', '-d', help='Downloads directory')
        
        # Upload mode
        upload_parser = subparsers.add_parser('upload', help='Upload compilations to YouTube')
        upload_parser.add_argument('--input-file', '-i', required=True, help='Compilation report file')
        
        return parser
    
    def _handle_full_mode(self, system, args) -> Dict[str, Any]:
        """Handle full pipeline mode."""
        print("Running full pipeline...")
        results = system.run_full_pipeline(max_videos=getattr(args, 'max_videos', None))

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
        
        return results

    def _handle_search_mode(self, system, args) -> Dict[str, Any]:
        """Handle search only mode."""
        print("Running search only...")
        videos = system.search_only(max_results=getattr(args, 'max_videos', None))
        print(f"Found {len(videos)} videos")
        return {'videos': videos}

    def _handle_download_mode(self, system, args) -> Dict[str, Any]:
        """Handle download mode."""
        print(f"Downloading from file: {args.input_file}")
        results = system.download_from_file(args.input_file)
        print(f"Downloaded {results.get('stats', {}).get('successful', 0)} videos")
        return results

    def _handle_compile_mode(self, system, args) -> Dict[str, Any]:
        """Handle compile mode."""
        print("Creating compilations from downloads...")
        results = system.compile_from_downloads(downloads_dir=getattr(args, 'downloads_dir', None))
        print(f"Created {results.get('stats', {}).get('total_compilations', 0)} compilations")
        return results

    def _handle_upload_mode(self, system, args) -> Dict[str, Any]:
        """Handle upload mode."""
        print(f"Uploading from file: {args.input_file}")
        system.upload_from_file(args.input_file)
        return {'status': 'upload_initiated'}

    def _show_session_summary(self, system) -> None:
        """Display session summary."""
        summary = system.get_session_summary()
        print(f"\nSession Summary:")
        print(f"Session ID: {summary['session_id']}")
        print(f"Session directory: {summary['session_dir']}")
        print(f"Files created: {len(summary['files_created'])}")
    
    def handle_cli(self) -> None:
        """
        Handle command-line interface execution.
        """
        args = self.parser.parse_args()

        # Check if mode was provided
        if not args.mode:
            self.parser.print_help()
            sys.exit(1)

        try:
            # Import from separate module to avoid circular imports
            from src.video_documentation_system import VideoDocumentationSystem
            
            # Initialize system
            system = VideoDocumentationSystem(args.config)

            # Dispatch map for different modes
            dispatch = {
                'full': self._handle_full_mode,
                'search': self._handle_search_mode,
                'download': self._handle_download_mode,
                'compile': self._handle_compile_mode,
                'upload': self._handle_upload_mode,
            }

            # Execute the appropriate mode handler
            if args.mode in dispatch:
                dispatch[args.mode](system, args)
            else:
                print(f"Unknown mode: {args.mode}")
                sys.exit(1)

            # Show session summary
            self._show_session_summary(system)

        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
