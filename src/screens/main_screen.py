#!/usr/bin/env python3
"""
Main Screen Module

This module provides the main menu screen for the TUI.
"""

from textual.containers import Container, Vertical
from textual.widgets import Static, Button
from textual.binding import Binding
from textual.app import ComposeResult

from ..base_screen import BaseScreen

class MainScreen(BaseScreen):
    """Main menu screen for the application."""
    
    BINDINGS = [
        Binding("c", "switch_screen('config')", "Configure"),
        Binding("r", "switch_screen('run')", "Run Pipeline"),
        Binding("q", "quit", "Quit"),
    ]

    def body(self) -> ComposeResult:
        """
        Provide the main menu body content.
        
        Returns:
            ComposeResult: Main menu widgets
        """
        yield Container(
            Static("[b]YouTube Video Documentation System[/b]", classes="title"),
            Static("TUI for managing the video pipeline.", classes="subtitle"),
            Vertical(
                Button("Configure (C)", id="btn_config", variant="primary"),
                Button("Run (R)", id="btn_run", variant="success"),
                Button("Quit (Q)", id="btn_quit", variant="error"),
                classes="menu-buttons"
            ),
            classes="main-menu"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle button press events.
        
        Args:
            event: Button press event
        """
        button_id = event.button.id
        
        if button_id == "btn_config":
            self.app.switch_screen("config")
        elif button_id == "btn_run":
            self.app.switch_screen("run")
        elif button_id == "btn_quit":
            self.app.exit()