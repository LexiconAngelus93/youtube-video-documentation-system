"""
Content Generator Module

Handles LLM-based generation of titles and descriptions for YouTube videos.
"""

import json
import logging
from typing import Dict, Any, Optional

from openai import OpenAI


class ContentGenerator:
    """
    Generates compelling titles and descriptions for video compilations using LLM.
    """

    def __init__(self, model_name: str = "gpt-4.1-mini", llm_client: Optional[OpenAI] = None):
        """
        Initialize the content generator.

        Args:
            model_name: Name of the LLM model to use
            llm_client: Optional pre-configured OpenAI client
        """
        self.model = model_name
        self.client = llm_client or OpenAI()
        self.logger = logging.getLogger(__name__)

    def generate(self, compilation_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a title and description for a video compilation.

        Args:
            compilation_info: Dictionary containing compilation metadata including:
                - category: The category of the compilation
                - video_count: Number of videos in the compilation
                - total_duration: Total duration in seconds
                - video_segments: List of video segment information

        Returns:
            Dictionary with 'title' and 'description' keys
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(compilation_info)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1000
            )

            content = json.loads(response.choices[0].message.content)
            self.logger.info(f"Generated content: {content.get('title', 'N/A')[:50]}...")
            return content

        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            return self._generate_fallback_content(compilation_info)

    def _build_system_prompt(self) -> str:
        """Build the system prompt for content generation."""
        return """You are a professional journalist and documentary filmmaker specializing in 
civil rights and police accountability. Your task is to create compelling, factual, and 
journalistic titles and descriptions for video compilations documenting police misconduct.

Guidelines:
- Titles should be informative, attention-grabbing, and factual
- Descriptions should provide context, explain the content, and maintain journalistic integrity
- Use neutral, professional language appropriate for documentary content
- Include relevant keywords for discoverability
- Avoid sensationalism while still conveying the importance of the content

You must respond with a JSON object containing exactly two keys:
- "title": A compelling title (max 100 characters)
- "description": A detailed description (max 5000 characters)"""

    def _build_user_prompt(self, compilation_info: Dict[str, Any]) -> str:
        """Build the user prompt with compilation details."""
        category = compilation_info.get('category', 'general')
        video_count = compilation_info.get('video_count', 0)
        total_duration = compilation_info.get('total_duration', 0)
        segments = compilation_info.get('video_segments', [])

        # Format duration
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        duration_str = f"{minutes}:{seconds:02d}"

        # Build segment summaries
        segment_summaries = []
        for seg in segments[:10]:  # Limit to first 10 for prompt length
            title = seg.get('title', 'Unknown')
            segment_summaries.append(f"- {title}")

        segments_text = "\n".join(segment_summaries) if segment_summaries else "No segment details available"

        return f"""Create a title and description for this police misconduct documentation compilation:

Category: {category}
Number of Videos: {video_count}
Total Duration: {duration_str}

Video Segments Included:
{segments_text}

Generate a professional, journalistic title and description that:
1. Accurately represents the content
2. Maintains documentary integrity
3. Is suitable for YouTube publication
4. Includes relevant tags and keywords in the description"""

    def _generate_fallback_content(self, compilation_info: Dict[str, Any]) -> Dict[str, str]:
        """Generate fallback content if LLM fails."""
        category = compilation_info.get('category', 'General')
        video_count = compilation_info.get('video_count', 0)

        title = f"Police Misconduct Documentation: {category.title()} Incidents Compilation"
        description = f"""This compilation documents {video_count} incidents of police misconduct 
in the category of {category}. 

This video is part of an ongoing journalistic documentation project aimed at promoting 
transparency and accountability in law enforcement.

All footage is sourced from publicly available videos with proper attribution provided 
for each segment.

#PoliceMisconduct #Accountability #CivilRights #Documentation #Journalism"""

        return {"title": title, "description": description}
