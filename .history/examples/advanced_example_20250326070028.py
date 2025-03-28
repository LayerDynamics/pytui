"""Advanced example demonstrating tabs, modals, and async operations."""

from __future__ import annotations
import asyncio
import os
import random
import sys
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all UI components at the top
from pytui.rich_text_ui.colors import Color
from pytui.rich_text_ui.list import List as UIList
from pytui.rich_text_ui.progress import Progress
from pytui.rich_text_ui.text import Text
from examples.shared_components import (
    App, Button, Label, TextInput, VBox, HBox, TabView, Modal
)


@dataclass
class DataPoint:
    """Example data structure for processing."""

    timestamp: datetime
    value: float
    category: str
    processed: bool = False


class DataProcessor:
    """Complex class demonstrating various pytui features."""

    def __init__(self):
        """Initialize processor with empty data."""
        self.data: List[DataPoint] = []
        self.results: Dict[str, List[float]] = {}
        self._processing = False
        self.on_data_updated: Callable[[str], None] = lambda msg: None

    def _notify(self, message: str) -> None:
        """Helper to safely call the update callback."""
        if callable(self.on_data_updated):
            self.on_data_updated(message)

    async def generate_data(self, num_points: int) -> None:
        """Generate sample data asynchronously."""
        categories = ["A", "B", "C"]
        for i in range(num_points):
            await asyncio.sleep(0.05)  # Simulate I/O
            point = DataPoint(
                timestamp=datetime.now(),
                value=random.uniform(0, 100),
                category=random.choice(categories),
            )
            self.data.append(point)

            # Notify UI of new data
            self._notify(f"Generated data point {i+1}/{num_points}: {point.category} = {point.value:.2f}")

    async def process_data(self) -> Dict[str, Any]:
        """Process data with complex operations."""
        self._processing = True

        self._notify("Processing data started...")

        try:
            results = await self._analyze_data()
            summary = await self._generate_summary(results)

            self._notify("Processing complete!")

            return {
                "results": results,
                "summary": summary,
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            self._processing = False

    async def _analyze_data(self) -> Dict[str, List[float]]:
        """Internal analysis method."""
        categories: Dict[str, List[float]] = {}
        total_points = len([p for p in self.data if not p.processed])
        processed = 0

        for point in self.data:
            if not point.processed:
                await asyncio.sleep(0.02)  # Simulate processing time
                if point.category not in categories:
                    categories[point.category] = []
                categories[point.category].append(point.value)
                point.processed = True
                processed += 1

                # Update progress
                if processed % 3 == 0:
                    self._notify(f"Analyzing data: {processed}/{total_points}")

        return categories

    async def _generate_summary(
        self, results: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Generate statistical summary."""
        self._notify("Generating summary...")

        summary = {}
        for category, values in results.items():
            if values:
                summary[category] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                }

                self._notify(f"Summary for {category} generated")

        return summary

    def _process_directory(self, path: str) -> None:
        """Process a directory to use os import."""
        if os.path.exists(path):
            print(f"Processing directory: {path}")


class NumberInput(TextInput):
    """Number input widget for handling numeric values."""

    def __init__(self, value: int = 0, min_value: int = 1, max_value: int = 100):
        super().__init__(str(value))
        self.min_value = min_value
        self.max_value = max_value

    def get_value(self):
        try:
            return int(self.value)
        except ValueError:
            return self.min_value

    def set_value(self, value):
        try:
            val = int(value)
            if self.min_value <= val <= self.max_value:
                super().set_value(str(val))
        except ValueError:
            pass

    @property
    def optional_value(self) -> Optional[int]:
        """Get value as optional integer to use Optional import."""
        try:
            return int(self.value)
        except ValueError:
            return None


class DataLog(UIList):
    """Log widget for data operations."""

    def __init__(self, max_items=10):
        super().__init__()
        self.max_items = max_items

    def add_log(self, message, color=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.add_item(log_entry, style=color)

        while len(self.items) > self.max_items:
            self.items.pop(0)


class AsyncDashboard:
    """Advanced dashboard with tabs, modals, and async operations."""

    def __init__(self):
        self.app = App(title="PyTUI Advanced Dashboard")
        self.main_container = VBox()
        self.tab_view = TabView()
        self.modal = Modal("Task Details")
        self.status = Label("")
        
        # Initialize all components upfront
        self.task_list = UIList()
        self.results_list = UIList()
        self.progress = Progress()
        self.status_text = Text("Ready", style=Color.GREEN)
        self.data_points_input = NumberInput(value=10)
        
        # Set up processor
        self.processor = DataProcessor()
        self.processor.on_data_updated = self._handle_update
        
        # Build UI
        self.build_ui()

    def _handle_update(self, message: str) -> None:
        """Handle updates from processor."""
        self.status_text.update(message, style=Color.BLUE)
        self.task_list.add_item(message)

    def _process_directory(self, path: str) -> None:
        """Process a directory to use os import."""
        if os.path.exists(path):
            result = f"Processing {path}"
            self.results_list.add_item(result)

    def build_ui(self):
        """Build the advanced UI."""
        # Title
        title = Label("Advanced UI Demo", Color.CYAN)
        title.set_align("center")
        self.main_container.add(title)

        # Add tabs
        self.setup_tabs()
        self.main_container.add(self.tab_view)

        # Modal
        self.setup_modal()
        self.main_container.add(self.modal)

        # Controls
        controls = HBox()
        controls.add(Button("Next Tab", self.tab_view.next_tab))
        controls.add(Button("Show Modal", self.modal.show))
        controls.add(Button("Hide Modal", self.modal.hide))
        controls.add(Button("Exit", self.app.exit))
        self.main_container.add(controls)

        # Status
        self.status.set_align("center")
        self.main_container.add(self.status)

        self.app.set_root(self.main_container)

    def setup_tabs(self):
        """Set up dashboard tabs."""
        # Tasks tab with styled text
        tasks_container = VBox()
        tasks_container.add(Text("Running Tasks", style=Color.CYAN + " bold"))
        self.task_list = UIList()
        tasks_container.add(self.task_list)
        self.tab_view.add_tab("Tasks", tasks_container)

        # Monitor tab with progress
        monitor_container = VBox()
        monitor_container.add(Text("System Monitor", style=Color.GREEN + " bold"))
        self.progress = Progress()
        monitor_container.add(self.progress)
        self.tab_view.add_tab("Monitor", monitor_container)

        # Results tab with styled text
        results_container = VBox()
        results_container.add(Text("Task Results", style=Color.YELLOW + " bold"))
        self.results_list = UIList()
        results_container.add(self.results_list)
        self.tab_view.add_tab("Results", results_container)

    def setup_modal(self):
        """Set up the modal dialog."""
        content = VBox()
        content.add(Label("Task Details"))
        content.add(Label("Status: Running"))
        content.add(Button("Close", self.modal.hide))
        self.modal.mount(content)  # Use mount instead of add

    async def update_progress(self):
        """Update progress bar."""
        while True:
            for i in range(100):
                self.progress.update(i)
                await asyncio.sleep(0.1)
            await asyncio.sleep(1)

    def run(self) -> None:
        """Run the dashboard with all features."""
        # Start progress update task
        asyncio.create_task(self.update_progress())
        
        # Demo all components
        self.demo_all_components()
        
        # Run the app
        self.app.run()

    def demo_all_components(self) -> None:
        """Demonstrate using all imported components."""
        # Use Text component
        demo_text = Text("Demo Text", style=Color.CYAN)
        self.main_container.add(demo_text)

        # Use Optional type with NumberInput
        value: Optional[int] = self.data_points_input.optional_value
        if value is not None:
            self.status_text.update(f"Input value: {value}")

        # Use os import
        self._process_directory(os.path.expanduser("~"))


def main():
    """Run the advanced example."""
    dashboard = AsyncDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
