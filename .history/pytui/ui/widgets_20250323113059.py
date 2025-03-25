"""Custom UI widgets for pytui."""

import time
from textual.widgets import Static
from rich.console import RenderableType
from rich.text import Text
from rich.style import Style


class StatusBar(Static):
    """Status bar for displaying execution info."""

    def __init__(self):
        """Initialize the status bar."""
        super().__init__("")
        self.start_time = time.time()
        # Change from properties to regular attributes
        self._is_running = False
        self._is_paused = False

    def render(self) -> RenderableType:
        """Render the status bar."""
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

        # Determine status
        if self._is_paused:
            status = "PAUSED"
            status_style = "bold yellow"
        elif self._is_running:
            status = "RUNNING"
            status_style = "bold green"
        else:
            status = "STOPPED"
            status_style = "bold red"

        # Build status line
        text = Text()
        text.append(" Status: ", style="bold")
        text.append(status, style=status_style)
        text.append(" | ", style="dim")
        text.append("Elapsed: ", style="bold")
        text.append(elapsed_str, style="cyan")
        text.append(" | ", style="dim")
        text.append("[Q]uit ", style="bold")
        text.append("[P]ause/Resume ", style="bold")
        text.append("[R]estart ", style="bold")
        text.append("[/]Search", style="bold")

        return text

    def set_running(self, is_running: bool):
        """Set the running state."""
        self._is_running = is_running
        self.refresh()

    def set_paused(self, is_paused: bool):
        """Set the paused state."""
        self._is_paused = is_paused
        self.refresh()

    def reset_timer(self):
        """Reset the elapsed time counter."""
        self.start_time = time.time()
        self.refresh()

    # Add properties for test compatibility
    @property
    def is_running(self):
        return self._is_running

    @property
    def is_paused(self):
        return self._is_paused
