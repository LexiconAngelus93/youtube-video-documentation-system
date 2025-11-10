#!/usr/bin/env python3
"""
Base Screen Module

This module provides the base screen class for TUI screens.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer

class BaseScreen(Screen):
    """Base screen class with common layout elements."""
    
    def compose(self) -> ComposeResult:
        """Compose the screen with header, footer, and body content."""
        yield Header()
        yield Footer()
        yield from self.body()

    def body(self) -> ComposeResult:
        """
        Get the body content for the screen.
        
        This method should be overridden by subclasses to provide
        the main content of the screen.
        
        Returns:
            ComposeResult: Body content widgets
        """
        raise NotImplementedError("Subclasses must implement body() method")