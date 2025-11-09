import json
import logging
from pathlib import Path
from typing import Set, Dict, Any

class VideoTracker:
    """
    Manages a persistent list of video IDs that have already been processed
    (downloaded and used in a compilation) to prevent duplicates in future runs.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.tracker_file = Path(self.config.get('general_settings', {}).get('tracker_file', 'used_videos.json'))
        self._used_video_ids: Set[str] = set()
        self._load_tracker()
        
    def _load_tracker(self) -> None:
        """
        Loads the set of used video IDs from the persistent file.
        """
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._used_video_ids = set(data.get('video_ids', []))
                self.logger.info(f"Loaded {len(self._used_video_ids)} used video IDs from {self.tracker_file}")
            except Exception as e:
                self.logger.error(f"Error loading video tracker file: {e}")
        else:
            self.logger.info("Video tracker file not found. Starting with an empty tracker.")

    def _save_tracker(self) -> None:
        """
        Saves the current set of used video IDs to the persistent file.
        """
        try:
            with open(self.tracker_file, 'w', encoding='utf-8') as f:
                json.dump({'video_ids': list(self._used_video_ids)}, f, indent=2)
            self.logger.info(f"Saved {len(self._used_video_ids)} used video IDs to {self.tracker_file}")
        except Exception as e:
            self.logger.error(f"Error saving video tracker file: {e}")

    def is_used(self, video_id: str) -> bool:
        """
        Checks if a video ID has already been used.
        """
        return video_id in self._used_video_ids

    def mark_as_used(self, video_id: str) -> None:
        """
        Marks a video ID as used and saves the tracker.
        """
        if video_id not in self._used_video_ids:
            self._used_video_ids.add(video_id)
            self._save_tracker()

    def get_used_ids(self) -> Set[str]:
        """
        Returns the set of all used video IDs.
        """
        return self._used_video_ids

    def mark_compilation_videos_as_used(self, compilation_info: Dict[str, Any]) -> None:
        """
        Marks all source videos in a successful compilation as used.
        """
        if compilation_info.get('status') == 'success':
            for compilation in compilation_info.get('compilations', []):
                for segment in compilation.get('segments', []):
                    video_id = segment.get('video_id')
                    # Only mark if it's a real video segment, not a title page
                    if video_id and not segment.get('title', '').startswith('Title Page'):
                        self.mark_as_used(video_id)
            self.logger.info("Successfully marked all source videos from compilation as used.")
        else:
            self.logger.warning("Compilation was not successful, skipping marking videos as used.")

# Test function for the tracker
def main():
    logging.basicConfig(level=logging.INFO)
    
    # Mock config
    config = {'general_settings': {'tracker_file': 'test_used_videos.json'}}
    
    # Initialize tracker
    tracker = VideoTracker(config)
    
    # Test marking
    tracker.mark_as_used('video_a')
    tracker.mark_as_used('video_b')
    
    print(f"Is video_a used? {tracker.is_used('video_a')}")
    print(f"Is video_c used? {tracker.is_used('video_c')}")
    
    # Test compilation marking
    mock_compilation = {
        'status': 'success',
        'compilations': [
            {
                'segments': [
                    {'video_id': 'video_d', 'title': 'Real Video'},
                    {'video_id': 'video_d', 'title': 'Title Page: Real Video'},
                    {'video_id': 'video_e', 'title': 'Real Video 2'},
                ]
            }
        ]
    }
    tracker.mark_compilation_videos_as_used(mock_compilation)
    
    print(f"Is video_d used? {tracker.is_used('video_d')}")
    
    # Clean up test file
    Path('test_used_videos.json').unlink(missing_ok=True)

if __name__ == "__main__":
    main()
