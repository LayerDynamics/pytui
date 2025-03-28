"""Progress related widgets."""

import time
import asyncio
from typing import Optional, Any, TypeVar, List, Dict
from textual.widget import Widget  # Changed from Static to Widget
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text
from rich.spinner import Spinner
from rich.console import RenderableType  # This is the correct import now

TRenderable = TypeVar("TRenderable")


class ProgressBarWidget(Widget):  # Changed from Static to Widget
    """Progress bar widget for showing execution progress."""

    def __init__(
        self,
        total: int = 100,
        description: str = "Progress",
        show_percentage: bool = True,
        show_time: bool = True,
    ):
        """Initialize progress bar widget.

        Args:
            total: Total steps for completion
            description: Description of the progress
            show_percentage: Whether to show percentage
            show_time: Whether to show elapsed time
        """
        super().__init__(name=description)  # Changed from empty string to description
        self.total = total
        self.description = description
        self.show_percentage = show_percentage
        self.show_time = show_time
        self.completed = 0
        self.start_time = time.time()
        self._task: Optional[asyncio.Task] = None

    def render(self) -> RenderableType:
        """Render the progress bar."""
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            (
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
                if self.show_percentage
                else None
            ),
            TimeElapsedColumn() if self.show_time else None,
        )

        task_id = progress.add_task(self.description, total=self.total)
        progress.update(task_id, completed=self.completed)
        return progress

    def update(self, completed: int, description: Optional[str] = None):
        """Update progress completion."""
        self.completed = min(completed, self.total)
        if description:
            self.description = description
        self.refresh()

    def increment(self, amount: int = 1):
        """Increment progress by an amount."""
        self.completed = min(self.completed + amount, self.total)
        self.refresh()

    def reset(self, total: Optional[int] = None, description: Optional[str] = None):
        """Reset the progress bar."""
        if total is not None:
            self.total = total
        if description is not None:
            self.description = description
        self.completed = 0
        self.start_time = time.time()
        self.refresh()

    async def auto_pulse(self, interval: float = 0.2, pulse_size: int = 1):
        """Automatically pulse the progress bar for indeterminate progress."""
        if self._task and not self._task.done():
            self._task.cancel()

        async def _pulse():
            try:
                while True:
                    self.completed = (self.completed + pulse_size) % (self.total + 1)
                    self.refresh()
                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                pass

        self._task = asyncio.create_task(_pulse())

    async def stop_pulse(self):
        """Stop the auto-pulse animation."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


class SpinnerWidget(Widget):  # Changed from Static to Widget
    """A spinner widget for showing progress."""

    SPINNERS = ["dots", "line", "pulse", "dots2", "dots3"]

    def __init__(self, text: str = "Working...", spinner_type: str = "dots"):
        """Initialize the spinner widget.

        Args:
            text: Text to display alongside the spinner
            spinner_type: Type of spinner animation to use
        """
        super().__init__("")
        self.text = text
        self.spinner_type = spinner_type if spinner_type in self.SPINNERS else "dots"
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def render(self) -> RenderableType:
        """Render the spinner."""
        if not self._running:
            return Text(f"{self.text} (stopped)")
        spinner = Spinner(self.spinner_type, text=self.text)
        return spinner

    async def start(self):
        """Start the spinner animation."""
        self._running = True
        self.refresh()
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = asyncio.create_task(self._refresh_spinner())

    async def stop(self):
        """Stop the spinner animation."""
        self._running = False
        self.refresh()
        if self._task and not self._task.done():
            self._task.cancel()

    async def _refresh_spinner(self):
        """Continuously refresh the spinner while running."""
        try:
            while self._running:
                self.refresh()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass


class AnimatedSpinnerWidget(Widget):  # Changed from Static to Widget
    """Enhanced spinner widget with richer animation options."""

    SPINNERS = {
        "dots": {
            "frames": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "interval": 0.08,
        },
        "line": {"frames": ["-", "\\", "|", "/"], "interval": 0.1},
        "pulse": {
            "frames": [
                "[    ]",
                "[=   ]",
                "[==  ]",
                "[=== ]",
                "[ ===]",
                "[  ==]",
                "[   =]",
                "[    ]",
                "[   =]",
                "[  ==]",
                "[ ===]",
                "[====]",
                "[=== ]",
                "[==  ]",
                "[=   ]",
            ],
            "interval": 0.1,
        },
        "dots2": {"frames": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"], "interval": 0.08},
        "dots3": {"frames": ["⣷", "⣯", "⣟", "⡿", "⢿", "⣻", "⣽", "⣾"], "interval": 0.08},
        "clock": {
            "frames": [
                "🕛",
                "🕐",
                "🕑",
                "🕒",
                "🕓",
                "🕔",
                "🕕",
                "🕖",
                "🕗",
                "🕘",
                "🕙",
                "🕚",
            ],
            "interval": 0.1,
        },
        "moon": {
            "frames": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
            "interval": 0.1,
        },
        "bounce": {"frames": ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"], "interval": 0.1},
    }

    def __init__(
        self,
        text: str = "Working...",
        spinner_type: str = "dots",
        show_elapsed: bool = True,
    ):
        super().__init__()  # Remove empty string argument
        self.text = text
        self.show_elapsed = show_elapsed

        if spinner_type in self.SPINNERS:
            self.spinner_config = self.SPINNERS[spinner_type]
        else:
            self.spinner_config = self.SPINNERS["dots"]

        self.current_frame = 0
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.start_time = time.time()

    def render(self) -> RenderableType:
        """Render the spinner."""
        if not self._running:
            return Text(f"{self.text} (stopped)")

        frames = self.spinner_config["frames"]
        frame_char = frames[self.current_frame % len(frames)]

        text = Text()
        text.append(frame_char, style="bold cyan")
        text.append(" ")
        text.append(self.text)

        if self.show_elapsed:
            elapsed = time.time() - self.start_time
            elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
            text.append(" (")
            text.append(elapsed_str, style="dim")
            text.append(")")

        return text

    async def start(self):
        """Start the spinner animation."""
        self._running = True
        self.start_time = time.time()
        self.refresh()

        if self._task and not self._task.done():
            self._task.cancel()

        self._task = asyncio.create_task(self._animate_spinner())

    async def stop(self):
        """Stop the spinner animation."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self.refresh()

    async def _animate_spinner(self):
        """Continuously animate the spinner while running."""
        try:
            while self._running:
                self.current_frame += 1
                self.refresh()
                interval = self.spinner_config.get("interval", 0.1)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass


"""Progress indicator widget."""

from .widget import Widget

class Progress(Widget):
    """Progress bar widget."""

    def __init__(self):
        """Initialize progress bar."""
        super().__init__()
        self._value = 0

    def update(self, value: int) -> None:
        """Update progress value (0-100)."""
        self._value = max(0, min(100, value))

    def render(self) -> str:
        """Render progress bar."""
        width = 20
        filled = int(width * self._value / 100)
        empty = width - filled
        return f"[{'=' * filled}{' ' * empty}] {self._value}%"
