import os
import sys
import yaml
import logging
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, RichLog, Input, Select
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.binding import Binding

# Add project root to path to import main.py components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the core system (assuming main.py contains the VideoDocumentationSystem class)
from main import VideoDocumentationSystem


# --- Logging Setup for TUI ---
# We will use a custom handler to pipe logs to the RichLog widget
class TextualLogHandler(logging.Handler):
    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record)
        self.log_widget.write(msg)


# --- TUI Screens ---

class MainScreen(Screen):
    BINDINGS = [
        Binding("c", "switch_screen('config')", "Configure"),
        Binding("r", "switch_screen('run')", "Run Pipeline"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Container(
            Static("[b]YouTube Video Documentation System[/b]", classes="title"),
            Static("A Text-based User Interface (TUI) for managing the video pipeline.", classes="subtitle"),
            Vertical(
                Button("Configure Settings (C)", id="btn_config", variant="primary"),
                Button("Run Pipeline (R)", id="btn_run", variant="success"),
                Button("Quit (Q)", id="btn_quit", variant="error"),
                classes="menu-buttons"
            ),
            classes="main-menu"
        )

    def action_switch_screen(self, screen_name: str) -> None:
        self.app.switch_screen(screen_name)

    def action_quit(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn_config":
            self.app.switch_screen("config")
        elif event.button.id == "btn_run":
            self.app.switch_screen("run")
        elif event.button.id == "btn_quit":
            self.app.exit()


class ConfigScreen(Screen):
    BINDINGS = [
        Binding("escape", "switch_screen('main')", "Back"),
        Binding("s", "save_config", "Save"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Vertical(
            Static("[b]Configuration Settings[/b]", classes="title"),
            Static("Edit key settings from config.yaml below. Press ESC to go back.", classes="subtitle"),
            
            Static("[b]Search Settings[/b]"),
            Horizontal(
                Static("Max Videos:"),
                Input(value="10", id="input_max_videos", classes="config-input"),
            ),
            
            Static("[b]Compilation Settings[/b]"),
            Horizontal(
                Static("Target Duration (min):"),
                Input(value="15", id="input_target_duration", classes="config-input"),
            ),
            
            Static("[b]YouTube Upload[/b]"),
            Horizontal(
                Static("Privacy Status:"),
                Select(
                    options=[("Unlisted", "unlisted"), ("Public", "public"), ("Private", "private")],
                    value="unlisted",
                    id="select_privacy_status",
                    classes="config-input"
                ),
            ),
            
            Button("Save Configuration (S)", id="btn_save_config", variant="primary"),
            classes="config-container"
        )

    def action_switch_screen(self, screen_name: str) -> None:
        self.app.switch_screen(screen_name)

    def action_save_config(self) -> None:
        try:
            # 1. Get values from TUI inputs
            max_videos = int(self.query_one("#input_max_videos", Input).value)
            target_duration = int(self.query_one("#input_target_duration", Input).value)
            privacy_status = self.query_one("#select_privacy_status", Select).value

            # 2. Load and update config data
            with open(self.app.config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            config_data['search_settings']['max_videos'] = max_videos
            config_data['compilation_settings']['target_duration_minutes'] = target_duration
            config_data['youtube_upload']['privacy_status'] = privacy_status

            # 3. Save updated config
            with open(self.app.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)

            # 4. Update the core system's config (if initialized)
            if self.app.system:
                self.app.system.config = config_data

            self.app.bell()
            self.app.log("Configuration saved successfully!")
            self.app.switch_screen("main")
        except Exception as e:
            self.app.log(f"Error saving config: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn_save_config":
            self.action_save_config()


class RunScreen(Screen):
    BINDINGS = [
        Binding("escape", "switch_screen('main')", "Back"),
        Binding("r", "run_pipeline", "Run"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Vertical(
            Static("[b]Pipeline Execution[/b]", classes="title"),
            Horizontal(
                Button("Start Full Pipeline (R)", id="btn_start_run", variant="success"),
                Button("Stop (Ctrl+C)", id="btn_stop_run", variant="error"),
            ),
            RichLog(id="log_output", classes="log-panel"),
            classes="run-container"
        )

    def on_mount(self) -> None:
        # Set up logging to pipe to the RichLog widget
        self.log_handler = TextualLogHandler(self.query_one("#log_output", RichLog))
        self.logger = logging.getLogger("system_log")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.log_handler)

    def action_switch_screen(self, screen_name: str) -> None:
        self.app.switch_screen(screen_name)

    def action_run_pipeline(self) -> None:
        self.logger.info("Starting full pipeline execution...")
        if self.app.system:
            # The core system's run_full_pipeline is blocking, so we need to run it in a worker thread
            # to keep the TUI responsive.
            # Pass the coroutine object (with parentheses) not the function reference
            self.run_worker(self._run_pipeline_async(), exclusive=True)
            self.logger.info("Pipeline execution started in background.")
        else:
            self.logger.error("Core system not initialized. Please check config.yaml.")

    async def _run_pipeline_async(self) -> None:
        """Async wrapper for running the pipeline in a worker thread."""
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self.app.system.run_full_pipeline)
            if result.get('success'):
                self.logger.info(f"Pipeline completed successfully! Session: {result.get('session_id')}")
            else:
                self.logger.error(f"Pipeline failed. Errors: {result.get('errors', [])}")
        except Exception as e:
            self.logger.error(f"Pipeline error: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn_start_run":
            self.action_run_pipeline()
        elif event.button.id == "btn_stop_run":
            self.logger.info("Stop requested. Use Ctrl+C to interrupt.")


# --- Main Application ---

class VideoDocTUI(App):
    CSS_PATH = "tui_styles.css"
    SCREENS = {
        "main": MainScreen,
        "config": ConfigScreen,
        "run": RunScreen,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.system = None
        self.config_path = "config.yaml"

    def on_mount(self) -> None:
        try:
            self.system = VideoDocumentationSystem(self.config_path)
            self.title = f"VideoDocTUI - Session: {self.system.session_id}"
        except Exception as e:
            self.title = "VideoDocTUI - ERROR"
            self.log(f"Error initializing core system: {e}")
        
        # Push the main screen after initialization (inside or outside try/except)
        # This ensures the UI is shown even if system initialization fails
        self.push_screen("main")

    def action_log(self, message: str) -> None:
        self.log(message)


if __name__ == "__main__":
    # Create a dummy config.yaml for testing the TUI structure
    if not Path("config.yaml").exists():
        with open("config.yaml", "w") as f:
            f.write("search_settings:\n  max_videos: 10\ncompilation_settings:\n  target_duration_minutes: 15\nyoutube_upload:\n  privacy_status: unlisted\n")
    
    # Create a dummy style file
    if not Path("tui_styles.css").exists():
        with open("tui_styles.css", "w") as f:
            f.write("""
            Screen {
                background: #1e1e1e;
                color: white;
            }
            .title {
                text-align: center;
                color: #ffcc00;
                margin-top: 3;
                margin-bottom: 1;
            }
            .subtitle {
                text-align: center;
                color: #aaaaaa;
                margin-bottom: 3;
            }
            .menu-buttons {
                align: center middle;
                height: 10;
            }
            Button {
                width: 30;
                margin-top: 1;
            }
            .config-container {
                padding: 2 5;
            }
            .config-input {
                width: 50%;
                margin-left: 2;
            }
            .log-panel {
                height: 1fr;
                border: solid #555555;
                margin: 1;
            }
            """)

    app = VideoDocTUI()
    app.run()
