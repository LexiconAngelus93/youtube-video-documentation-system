import logging
from typing import Dict, Any


class ContentGenerator:
    """
    Generates compelling titles and descriptions for video compilations using a built-in, rule-based agent.
    """

    def __init__(self):
        """
        Initialize the content generator.
        """
        self.logger = logging.getLogger(__name__)

    def generate(self, compilation_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a title and description for a video compilation using a rule-based approach.

        Args:
            compilation_info: Dictionary containing compilation metadata including:
                - category: The category of the compilation
                - video_count: Number of videos in the compilation
                - total_duration: Total duration in seconds
                - video_segments: List of video segment information

        Returns:
            Dictionary with 'title' and 'description' keys
        """
        self.logger.info("Generating content using built-in agent...")
        return self._generate_content(compilation_info)

    def _generate_content(self, compilation_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate content based on compilation info.
        """
        category = compilation_info.get("category", "General")
        video_count = compilation_info.get("video_count", 0)
        total_duration = compilation_info.get("total_duration", 0)
        segments = compilation_info.get("video_segments", [])

        # Format duration
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        duration_str = f"{minutes}:{seconds:02d}"

        # Build segment summaries for description
        segment_summaries = []
        for i, seg in enumerate(segments[:5]):  # Limit to first 5 for brevity
            title = seg.get("title", f"Video {i+1}")
            url = seg.get("url", "")
            segment_summaries.append(f"- {title} ({url})")

        segments_text = "\n".join(segment_summaries) if segment_summaries else "No specific video details available."

        title = f"Police Misconduct Documentation: {category.title()} Incidents ({video_count} Videos, {duration_str})"
        description = f"""This compilation documents {video_count} incidents of police misconduct 
        categorized under '{category}'. The total duration of this compilation is {duration_str}.

        This video is part of an ongoing journalistic documentation project aimed at promoting 
        transparency and accountability in law enforcement.

        Featured incidents include:
        {segments_text}

        All footage is sourced from publicly available videos with proper attribution provided 
        for each segment. This content is for educational and journalistic purposes.

        #PoliceMisconduct #Accountability #CivilRights #Documentation #Journalism #{category.replace(' ', '')}"""

        return {"title": title, "description": description}
