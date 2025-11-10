#!/usr/bin/env python3
"""
YouTube Content Generation Module

This module handles LLM-based content generation for YouTube videos.
"""

import json
from openai import OpenAI
from typing import Dict, Any

class ContentGenerator:
    """Handles content generation using LLM."""
    
    def __init__(self, model_name: str, llm_client=None):
        """
        Initialize the content generator.
        
        Args:
            model_name: Name of the LLM model to use
            llm_client: OpenAI client instance (optional)
        """
        self.model = model_name
        self.client = llm_client or OpenAI()

    def generate(self, compilation_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate title and description for a compilation.
        
        Args:
            compilation_info: Information about the compilation
            
        Returns:
            Dictionary with title and description
        """
        # Build system prompt
        system_prompt = """You are creating content for a YouTube video that documents police misconduct incidents. 
        Generate compelling, factual, and informative content that brings attention to accountability issues.
        Content should be professional yet impactful."""
        
        # Build user prompt with compilation details
        user_prompt = f"""
        Create a title and description for a video compilation with the following details:
        
        Title: {compilation_info.get('name', 'Police Misconduct Compilation')}
        Category: {compilation_info.get('category', 'police misconduct')}
        Number of videos: {compilation_info.get('video_count', 0)}
        Duration: {compilation_info.get('duration', 0)} seconds
        
        Please generate:
        1. A compelling title (under 100 characters)
        2. A detailed description (under 5000 characters)
        
        Format your response as JSON:
        {{
            "title": "Generated title here",
            "description": "Generated description here"
        }}
        """
        
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Validate and parse LLM response
            try:
                result = json.loads(resp.choices[0].message.content)
                # Validate required fields
                if not isinstance(result, dict) or 'title' not in result or 'description' not in result:
                    raise ValueError("LLM response missing required fields")
                return result
            except (json.JSONDecodeError, ValueError) as e:
                # Log the error and fall through to fallback
                raise Exception(f"Invalid LLM response format: {e}")
            
        except Exception as e:
            # Fallback content if LLM fails
            return {
                "title": f"Police Misconduct Compilation - {compilation_info.get('name', 'Document')}",
                "description": (
                    f"This video documents {compilation_info.get('video_count', 0)} incidents of police misconduct. "
                    f"Content is compiled for research and accountability purposes. For more information, "
                    f"please refer to the individual source videos included in this compilation."
                )
            }