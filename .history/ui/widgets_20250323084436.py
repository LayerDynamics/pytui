"""Custom widgets for the TUI application."""

from datetime import datetime
from textual.widgets import Static  # type: ignore
from rich.console import Console  # type: ignore
from rich.text import Text  # type: ignore

class StatusBar(Static):
    """Status bar widget showing execution state and statistics."""

    def __init__(self):
        """Initialize the status bar."""
        super().__init__("")
        self.last_update = datetime.now()
        self._setup_display()

    def _setup_display(self):
        """Set up the initial display configuration."""
        self.console = Console()
        self.update_required = True

    def update_status(self, status_text: str) -> None:
        """Update the status bar text."""
        self.last_update = datetime.now()
        self.update(Text(status_text))
        self.update_required = True

    async def on_mount(self) -> None:
        """Handle widget mount event."""
        self.update_status("Ready")

    def get_elapsed_time(self) -> float:
        """Get time elapsed since last update."""
        return (datetime.now() - self.last_update).total_seconds()

    async def on_click(self) -> None:
        """Handle click events on the status bar."""
        await self.toggle_display()

    async def toggle_display(self) -> None:
        """Toggle between different display modes."""
        if self.update_required:
            await self.refresh_display()
        self.update_required = False

    async def refresh_display(self) -> None:
        """Refresh the display content."""
        current_text = self.render()
        await self.update(current_text)

    def render(self) -> Text:
        """Render the current status."""
        return Text(f"Last updated: {self.last_update.strftime('%H:%M:%S')}")
