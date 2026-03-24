import os
import sys
import yaml
import logging
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, RichLog, Input, Select, Checkbox
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.screen import Screen
from textual.binding import Binding
from textual.validation import Validator, IntegerValidator, NumberValidator

# Add project root to path to import main.py components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the core system (assuming main.py contains the VideoDocumentationSystem class)
from main import VideoDocumentationSystem
from youtube.auth import OAuth2Authenticator


# --- Logging Setup for TUI ---
# We will use a custom handler to pipe logs to the RichLog widget
class TextualLogHandler(logging.Handler):
    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget
        self.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    def emit(self, record):
        msg = self.format(record)
        self.log_widget.write(msg)


# --- TUI Screens ---

class MainScreen(Screen):
    BINDINGS = [
        Binding("c", "switch_screen(\'config\')", "Configure"),
        Binding("a", "switch_screen(\'auth\')", "Authenticate"),
        Binding("r", "switch_screen(\'run\')", "Run Pipeline"),
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
                Button("YouTube Authentication (A)", id="btn_auth", variant="warning"),
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
        elif event.button.id == "btn_auth":
            self.app.switch_screen("auth")
        elif event.button.id == "btn_run":
            self.app.switch_screen("run")
        elif event.button.id == "btn_quit":
            self.app.exit()


class AuthScreen(Screen):
    BINDINGS = [
        Binding("escape", "switch_screen(\'main\')", "Back"),
        Binding("l", "login_youtube", "Login"),
        Binding("c", "check_status", "Check Status"),
    ]

    def on_mount(self) -> None:
        self.update_auth_status()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with ScrollableContainer(classes="auth-container"):
            Static("[b]YouTube Authentication[/b]", classes="title")
            Static("Manage your YouTube API login for video uploads.", classes="subtitle")
            Static("Status: [b red]Not Authenticated[/b]", id="auth_status")
            Button("Login to YouTube (L)", id="btn_login_youtube", variant="primary")
            Button("Check Authentication Status (C)", id="btn_check_auth", variant="default")

    def action_switch_screen(self, screen_name: str) -> None:
        self.app.switch_screen(screen_name)

    def update_auth_status(self) -> None:
        status_widget = self.query_one("#auth_status", Static)
        if self.app.system and self.app.system.uploader.is_authenticated():
            status_widget.update("Status: [b green]Authenticated[/b]")
        else:
            status_widget.update("Status: [b red]Not Authenticated[/b]")

    def action_login_youtube(self) -> None:
        self.app.log("Attempting to log in to YouTube...")
        if self.app.system:
            try:
                # This will open a browser for OAuth2 flow
                self.app.system.uploader.auth.get_credentials()
                self.update_auth_status()
                self.app.log("YouTube login process initiated. Check your browser.")
            except Exception as e:
                self.app.log(f"YouTube login failed: {e}")
        else:
            self.app.log("System not initialized. Cannot perform YouTube login.")

    def action_check_status(self) -> None:
        self.update_auth_status()
        self.app.log("Authentication status checked.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_login_youtube":
            self.action_login_youtube()
        elif event.button.id == "btn_check_auth":
            self.action_check_status()


class ConfigScreen(Screen):
    BINDINGS = [
        Binding("escape", "switch_screen(\'main\')", "Back"),
        Binding("s", "save_config", "Save"),
    ]

    def on_mount(self) -> None:
        self.load_config_to_tui()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with ScrollableContainer(classes="config-container"):
            Static("[b]Configuration Settings[/b]", classes="title")
            Static("Edit key settings from config.yaml below. Press ESC to go back.", classes="subtitle")

            with Vertical(classes="config-section"):
                Static("[b]Search Settings[/b]")
                Horizontal(
                    Static("Keywords (comma-separated):", classes="config-label"),
                    Input(id="input_search_keywords", classes="config-input"),
                )
                Horizontal(
                    Static("Start Date (YYYY-MM-DD):", classes="config-label"),
                    Input(id="input_search_start_date", classes="config-input"),
                )
                Horizontal(
                    Static("End Date (YYYY-MM-DD or 'today'):", classes="config-label"),
                    Input(id="input_search_end_date", classes="config-input"),
                )
                Horizontal(
                    Static("Region (e.g., US, GB):", classes="config-label"),
                    Input(id="input_search_region", classes="config-input"),
                )
                Horizontal(
                    Static("Language (e.g., en, es):", classes="config-label"),
                    Input(id="input_search_language", classes="config-input"),
                )
                Horizontal(
                    Static("Request Delay (seconds):", classes="config-label"),
                    Input(validators=[NumberValidator()], id="input_search_request_delay", classes="config-input"),
                )
                Horizontal(
                    Static("Max Results per Keyword:", classes="config-label"),
                    Input(validators=[IntegerValidator()], id="input_search_max_results_per_keyword", classes="config-input"),
                )

            with Vertical(classes="config-section"):
                Static("[b]Download Settings[/b]")
                Horizontal(
                    Static("Quality (e.g., best, 720p):", classes="config-label"),
                    Input(id="input_download_quality", classes="config-input"),
                )
                Horizontal(
                    Static("Format (e.g., mp4, webm):", classes="config-label"),
                    Input(id="input_download_format", classes="config-input"),
                )
                Horizontal(
                    Static("Max Filesize (e.g., 500M, 1G):", classes="config-label"),
                    Input(id="input_download_max_filesize", classes="config-input"),
                )
                Horizontal(
                    Static("Concurrent Downloads:", classes="config-label"),
                    Input(validators=[IntegerValidator()], id="input_download_concurrent_downloads", classes="config-input"),
                )
                Horizontal(
                    Static("Retry Attempts:", classes="config-label"),
                    Input(validators=[IntegerValidator()], id="input_download_retry_attempts", classes="config-input"),
                )

            with Vertical(classes="config-section"):
                Static("[b]Compilation Settings[/b]")
                Horizontal(
                    Static("Target Duration (minutes):", classes="config-label"),
                    Input(validators=[IntegerValidator()], id="input_compilation_target_duration_minutes", classes="config-input"),
                )
                Horizontal(
                    Static("Max Duration (minutes):", classes="config-label"),
                    Input(validators=[IntegerValidator()], id="input_compilation_max_duration_minutes", classes="config-input"),
                )
                Horizontal(
                    Static("Min Duration (minutes):", classes="config-label"),
                    Input(validators=[IntegerValidator()], id="input_compilation_min_duration_minutes", classes="config-input"),
                )
                Horizontal(
                    Static("Video Quality (e.g., 720p, 1080p):", classes="config-label"),
                    Input(id="input_compilation_video_quality", classes="config-input"),
                )
                Horizontal(
                    Static("Attribution Duration (seconds):", classes="config-label"),
                    Input(validators=[IntegerValidator()], id="input_compilation_attribution_duration", classes="config-input"),
                )
                Horizontal(
                    Static("Attribution Position (e.g., bottom, top):", classes="config-label"),
                    Input(id="input_compilation_attribution_position", classes="config-input"),
                )

            with Vertical(classes="config-section"):
                Static("[b]YouTube Upload Settings[/b]")
                Horizontal(
                    Static("Privacy Status:", classes="config-label"),
                    Select(
                        options=[("Public", "public"), ("Unlisted", "unlisted"), ("Private", "private")],
                        value="unlisted",
                        id="select_youtube_privacy_status",
                        classes="config-input"
                    ),
                )
                Horizontal(
                    Static("Category ID (e.g., 25 for News & Politics):", classes="config-label"),
                    Input(validators=[IntegerValidator()], id="input_youtube_category_id", classes="config-input"),
                )
                Horizontal(
                    Static("Default Tags (comma-separated):", classes="config-label"),
                    Input(id="input_youtube_default_tags", classes="config-input"),
                )

            with Vertical(classes="config-section"):
                Static("[b]Logging Settings[/b]")
                Horizontal(
                    Static("Log Level (e.g., INFO, DEBUG):", classes="config-label"),
                    Select(
                        options=[("DEBUG", "DEBUG"), ("INFO", "INFO"), ("WARNING", "WARNING"), ("ERROR", "ERROR"), ("CRITICAL", "CRITICAL")],
                        value="INFO",
                        id="select_logging_level",
                        classes="config-input"
                    ),
                )
                Horizontal(
                    Static("Log File:", classes="config-label"),
                    Input(id="input_logging_file", classes="config-input"),
                )

            with Vertical(classes="config-section"):
                Static("[b]Output Settings[/b]")
                Horizontal(
                    Static("Save Metadata:", classes="config-label"),
                    Checkbox(id="checkbox_output_save_metadata", classes="config-input"),
                )
                Horizontal(
                    Static("Save Thumbnails:", classes="config-label"),
                    Checkbox(id="checkbox_output_save_thumbnails", classes="config-input"),
                )
                Horizontal(
                    Static("Create Index File:", classes="config-label"),
                    Checkbox(id="checkbox_output_create_index", classes="config-input"),
                )
                Horizontal(
                    Static("Export Format (json, csv, xlsx):", classes="config-label"),
                    Select(
                        options=[("JSON", "json"), ("CSV", "csv"), ("XLSX", "xlsx")],
                        value="json",
                        id="select_output_export_format",
                        classes="config-input"
                    ),
                )

            Button("Save Configuration (S)", id="btn_save_config", variant="primary"),

    def load_config_to_tui(self) -> None:
        if not self.app.system:
            self.app.log("System not initialized, cannot load config.")
            return

        config_data = self.app.system.config

        # Search Settings
        self.query_one("#input_search_keywords", Input).value = ", ".join(config_data.get("search_settings", {}).get("keywords", []))
        self.query_one("#input_search_start_date", Input).value = config_data.get("search_settings", {}).get("start_date", "2010-01-01")
        self.query_one("#input_search_end_date", Input).value = config_data.get("search_settings", {}).get("end_date", "today")
        self.query_one("#input_search_region", Input).value = config_data.get("search_settings", {}).get("region", "US")
        self.query_one("#input_search_language", Input).value = config_data.get("search_settings", {}).get("language", "en")
        self.query_one("#input_search_request_delay", Input).value = str(config_data.get("search_settings", {}).get("request_delay", 1.0))
        self.query_one("#input_search_max_results_per_keyword", Input).value = str(config_data.get("search_settings", {}).get("max_results_per_keyword", 500))

        # Download Settings
        self.query_one("#input_download_quality", Input).value = config_data.get("download_settings", {}).get("quality", "best")
        self.query_one("#input_download_format", Input).value = config_data.get("download_settings", {}).get("format", "mp4")
        self.query_one("#input_download_max_filesize", Input).value = config_data.get("download_settings", {}).get("max_filesize", "500M")
        self.query_one("#input_download_concurrent_downloads", Input).value = str(config_data.get("download_settings", {}).get("concurrent_downloads", 3))
        self.query_one("#input_download_retry_attempts", Input).value = str(config_data.get("download_settings", {}).get("retry_attempts", 3))

        # Compilation Settings
        self.query_one("#input_compilation_target_duration_minutes", Input).value = str(config_data.get("compilation_settings", {}).get("target_duration_minutes", 15))
        self.query_one("#input_compilation_max_duration_minutes", Input).value = str(config_data.get("compilation_settings", {}).get("max_duration_minutes", 20))
        self.query_one("#input_compilation_min_duration_minutes", Input).value = str(config_data.get("compilation_settings", {}).get("min_duration_minutes", 10))
        self.query_one("#input_compilation_video_quality", Input).value = config_data.get("compilation_settings", {}).get("video_quality", "720p")
        self.query_one("#input_compilation_attribution_duration", Input).value = str(config_data.get("compilation_settings", {}).get("attribution_duration", 5))
        self.query_one("#input_compilation_attribution_position", Input).value = config_data.get("compilation_settings", {}).get("attribution_position", "bottom")

        # YouTube Upload Settings
        self.query_one("#select_youtube_privacy_status", Select).value = config_data.get("youtube_upload", {}).get("privacy_status", "unlisted")
        self.query_one("#input_youtube_category_id", Input).value = str(config_data.get("youtube_upload", {}).get("category_id", "25"))
        self.query_one("#input_youtube_default_tags", Input).value = ", ".join(config_data.get("youtube_upload", {}).get("default_tags", []))

        # Logging Settings
        self.query_one("#select_logging_level", Select).value = config_data.get("logging", {}).get("level", "INFO")
        self.query_one("#input_logging_file", Input).value = config_data.get("logging", {}).get("file", "logs/app.log")

        # Output Settings
        self.query_one("#checkbox_output_save_metadata", Checkbox).value = config_data.get("output", {}).get("save_metadata", True)
        self.query_one("#checkbox_output_save_thumbnails", Checkbox).value = config_data.get("output", {}).get("save_thumbnails", True)
        self.query_one("#checkbox_output_create_index", Checkbox).value = config_data.get("output", {}).get("create_index", True)
        self.query_one("#select_output_export_format", Select).value = config_data.get("output", {}).get("export_format", "json")

    def action_switch_screen(self, screen_name: str) -> None:
        self.app.switch_screen(screen_name)

    def action_save_config(self) -> None:
        if not self.app.system:
            self.app.log("System not initialized, cannot save config.")
            return

        try:
            config_data = self.app.system.config

            # Search Settings
            config_data["search_settings"]["keywords"] = [k.strip() for k in self.query_one("#input_search_keywords", Input).value.split(",") if k.strip()]
            config_data["search_settings"]["start_date"] = self.query_one("#input_search_start_date", Input).value
            config_data["search_settings"]["end_date"] = self.query_one("#input_search_end_date", Input).value
            config_data["search_settings"]["region"] = self.query_one("#input_search_region", Input).value
            config_data["search_settings"]["language"] = self.query_one("#input_search_language", Input).value
            config_data["search_settings"]["request_delay"] = float(self.query_one("#input_search_request_delay", Input).value)
            config_data["search_settings"]["max_results_per_keyword"] = int(self.query_one("#input_search_max_results_per_keyword", Input).value)

            # Download Settings
            config_data["download_settings"]["quality"] = self.query_one("#input_download_quality", Input).value
            config_data["download_settings"]["format"] = self.query_one("#input_download_format", Input).value
            config_data["download_settings"]["max_filesize"] = self.query_one("#input_download_max_filesize", Input).value
            config_data["download_settings"]["concurrent_downloads"] = int(self.query_one("#input_download_concurrent_downloads", Input).value)
            config_data["download_settings"]["retry_attempts"] = int(self.query_one("#input_download_retry_attempts", Input).value)

            # Compilation Settings
            config_data["compilation_settings"]["target_duration_minutes"] = int(self.query_one("#input_compilation_target_duration_minutes", Input).value)
            config_data["compilation_settings"]["max_duration_minutes"] = int(self.query_one("#input_compilation_max_duration_minutes", Input).value)
            config_data["compilation_settings"]["min_duration_minutes"] = int(self.query_one("#input_compilation_min_duration_minutes", Input).value)
            config_data["compilation_settings"]["video_quality"] = self.query_one("#input_compilation_video_quality", Input).value
            config_data["compilation_settings"]["attribution_duration"] = int(self.query_one("#input_compilation_attribution_duration", Input).value)
            config_data["compilation_settings"]["attribution_position"] = self.query_one("#input_compilation_attribution_position", Input).value

            # YouTube Upload Settings
            config_data["youtube_upload"]["privacy_status"] = self.query_one("#select_youtube_privacy_status", Select).value
            config_data["youtube_upload"]["category_id"] = int(self.query_one("#input_youtube_category_id", Input).value)
            config_data["youtube_upload"]["default_tags"] = [t.strip() for t in self.query_one("#input_youtube_default_tags", Input).value.split(",") if t.strip()]

            # Logging Settings
            config_data["logging"]["level"] = self.query_one("#select_logging_level", Select).value
            config_data["logging"]["file"] = self.query_one("#input_logging_file", Input).value

            # Output Settings
            config_data["output"]["save_metadata"] = self.query_one("#checkbox_output_save_metadata", Checkbox).value
            config_data["output"]["save_thumbnails"] = self.query_one("#checkbox_output_save_thumbnails", Checkbox).value
            config_data["output"]["create_index"] = self.query_one("#checkbox_output_create_index", Checkbox).value
            config_data["output"]["export_format"] = self.query_one("#select_output_export_format", Select).value

            # Save updated config to file
            with open(self.app.config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)

            # Update the core system's config
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
        Binding("escape", "switch_screen(\'main\')", "Back"),
        Binding("r", "run_pipeline", "Run"),
    ]

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
            self.app.log("Core system not initialized. Please check config.yaml.")

    async def _run_pipeline_async(self) -> None:
        """Async wrapper for running the pipeline in a worker thread."""
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self.app.system.run_full_pipeline)
            if result.get("success"):
                self.logger.info(f"Pipeline completed successfully! Session: {result.get("session_id")}")
            else:
                self.logger.error(f"Pipeline failed. Errors: {result.get("errors", [])}")
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
        "auth": AuthScreen,
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
            f.write("""
search_settings:
  keywords:
    - "police brutality"
  start_date: "2010-01-01"
  end_date: "today"
  region: "US"
  language: "en"
  request_delay: 1.0
  max_results_per_keyword: 500

download_settings:
  quality: "best"
  format: "mp4"
  output_dir: "downloads/raw_videos"
  metadata_dir: "downloads/metadata"
  max_filesize: "500M"
  concurrent_downloads: 3
  retry_attempts: 3

compilation_settings:
  output_dir: "compilations"
  target_duration_minutes: 15
  max_duration_minutes: 20
  min_duration_minutes: 10
  video_quality: "720p"
  attribution_duration: 5
  attribution_position: "bottom"

youtube_upload:
  client_secrets_file: client_secrets.json
  credentials_file: youtube_credentials.json
  privacy_status: unlisted
  category_id: 25
  default_tags:
    - "police misconduct"
    - "accountability"
    - "civil rights"
    - "documentation"

llm_settings:
  model: hardcoded_agent # Changed to reflect the built-in agent

categorization:
  categories:
    traffic_stop:
      keywords: ["traffic stop", "pulled over", "speeding", "dui", "checkpoint"]
      priority: 1
    protest:
      keywords: ["protest", "demonstration", "rally", "march", "blm", "black lives matter"]
      priority: 2
    arrest:
      keywords: ["arrest", "handcuffed", "detained", "custody", "booking"]
      priority: 3
    excessive_force:
      keywords: ["excessive force", "brutality", "beating", "taser", "pepper spray"]
      priority: 4
    shooting:
      keywords: ["shooting", "shot", "fired", "gun", "weapon"]
      priority: 5
    raid:
      keywords: ["raid", "swat", "no knock", "warrant", "search"]
      priority: 6
    misconduct:
      keywords: ["misconduct", "corruption", "abuse", "violation", "complaint"]
      priority: 7

logging:
  level: "INFO"
  file: "logs/app.log"
  max_size_mb: 10
  backup_count: 5

output:
  save_metadata: true
  save_thumbnails: true
  create_index: true
  export_format: "json"
""")
    
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
                height: 1fr;
            }
            .config-label {
                width: 30%;
                text-align: right;
                margin-right: 1;
            }
            .config-input {
                width: 60%;
            }
            .config-section {
                border: solid #333333;
                padding: 1;
                margin-bottom: 1;
            }
            .log-panel {
                height: 1fr;
                border: solid #555555;
                margin: 1;
            }
            .auth-container {
                align: center middle;
                padding: 2 5;
                height: 1fr;
            }
            """)

    app = VideoDocTUI()
    app.run()
