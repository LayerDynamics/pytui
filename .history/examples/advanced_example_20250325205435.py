"""Advanced example demonstrating a data dashboard with PyTUI components."""

import sys
import os
import asyncio
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import from the project's rich_text_ui module
from pytui.rich_text_ui.application import Application
from pytui.rich_text_ui.widget import Widget
from pytui.rich_text_ui.text import Text
from pytui.rich_text_ui.static import Static
from pytui.rich_text_ui.container import Container
from pytui.rich_text_ui.colors import Color
from pytui.rich_text_ui.list import List as UIList
from pytui.rich_text_ui.progress import Progress


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
        self.on_data_updated = None  # Callback for UI updates

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
            if self.on_data_updated:
                self.on_data_updated(f"Generated data point {i+1}/{num_points}: {point.category} = {point.value:.2f}")

    async def process_data(self) -> Dict[str, Any]:
        """Process data with complex operations."""
        self._processing = True
        
        if self.on_data_updated:
            self.on_data_updated("Processing data started...")
            
        try:
            results = await self._analyze_data()
            summary = await self._generate_summary(results)
            
            if self.on_data_updated:
                self.on_data_updated("Processing complete!")
                
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
                if self.on_data_updated and processed % 3 == 0:
                    self.on_data_updated(f"Analyzing data: {processed}/{total_points}")

        return categories

    async def _generate_summary(
        self, results: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Generate statistical summary."""
        if self.on_data_updated:
            self.on_data_updated("Generating summary...")
            
        summary = {}
        for category, values in results.items():
            if values:
                summary[category] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                }
                
                if self.on_data_updated:
                    self.on_data_updated(f"Summary for {category} generated")
                    
        return summary


# UI Component Wrappers
class App(Application):
    def set_root(self, element):
        self.view = element


class Button(Widget):
    def __init__(self, label="Button", on_click=None):
        super().__init__()
        self.label = label
        self.on_click = on_click
    
    def render(self):
        return f"[{self.label}]"


class Label(Static):
    def __init__(self, text="", color=None):
        super().__init__(text)
        self.color = color
        self.style = color if color else ""
    
    def set_text(self, text):
        self.update(text)
        
    def set_align(self, align):
        self.justify = align
        
    def set_color(self, color):
        self.style = f"{color}"


class NumberInput(Widget):
    def __init__(self, value=0, min_value=1, max_value=100):
        super().__init__()
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        
    def get_value(self):
        return self.value
        
    def set_value(self, value):
        try:
            val = int(value)
            if self.min_value <= val <= self.max_value:
                self.value = val
        except ValueError:
            pass
            
    def render(self):
        return f"[{self.value}]"


class VBox(Container):
    def __init__(self):
        super().__init__()
        self.layout = "vertical"
        
    def add(self, widget):
        return self.mount(widget)
        
    def set_align(self, align):
        for child in self.children:
            if hasattr(child, 'set_align'):
                child.set_align(align)


class HBox(Container):
    def __init__(self):
        super().__init__()
        self.layout = "horizontal"
        
    def add(self, widget):
        return self.mount(widget)


class DataLog(UIList):
    """Log widget for data operations."""
    
    def __init__(self, max_items=10):
        super().__init__()
        self.max_items = max_items
        
    def add_log(self, message, color=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.add_item(log_entry, style=color)
        
        # Keep log at max size
        while len(self.items) > self.max_items:
            self.items.pop(0)


class Dashboard:
    """UI Dashboard for data processing visualization."""
    
    def __init__(self):
        self.app = App(title="PyTUI Data Dashboard")
        self.processor = DataProcessor()
        self.main_container = VBox()
        self.data_log = None
        self.summary_display = None
        self.progress_bar = None
        self.status = None
        
        # Set up the processor callback
        self.processor.on_data_updated = self.update_log
        
    def build_ui(self):
        """Build the dashboard UI."""
        # Add a title
        title = Label("Data Processing Dashboard", Color.CYAN)
        title.set_align("center")
        self.main_container.add(title)
        
        # Add a separator
        separator = Label("═" * 60)
        separator.set_align("center")
        self.main_container.add(separator)
        
        # Create control panel
        controls = HBox()
        
        # Data generation controls
        gen_label = Label("Generate data points: ")
        self.data_points_input = NumberInput(value=10, min_value=1, max_value=100)
        gen_button = Button("Generate", self.on_generate_data)
        
        controls.add(gen_label)
        controls.add(self.data_points_input)
        controls.add(gen_button)
        
        # Process button
        process_button = Button("Process Data", self.on_process_data)
        controls.add(process_button)
        
        # Clear button
        clear_button = Button("Clear All", self.on_clear)
        controls.add(clear_button)
        
        self.main_container.add(controls)
        
        # Status display
        self.status = Label("Ready", Color.GREEN)
        self.status.set_align("center")
        self.main_container.add(self.status)
        
        # Progress indicator
        self.progress_bar = Progress()
        self.main_container.add(self.progress_bar)
        
        # Create data visualization section
        viz_container = VBox()
        
        # Data log
        log_label = Label("Operation Log:", Color.BLUE)
        viz_container.add(log_label)
        
        self.data_log = DataLog(max_items=10)
        viz_container.add(self.data_log)
        
        # Summary display
        summary_label = Label("Data Summary:", Color.BLUE)
        viz_container.add(summary_label)
        
        self.summary_display = Label("No data processed yet")
        viz_container.add(self.summary_display)
        
        self.main_container.add(viz_container)
        
        # Exit button
        exit_button = Button("Exit", lambda: self.app.exit())
        exit_container = HBox()
        exit_container.add(exit_button)
        self.main_container.add(exit_container)
        
        # Footer
        footer = Label("Data Dashboard - Press ESC to exit")
        footer.set_align("center")
        footer.set_color(Color.BLUE)
        self.main_container.add(footer)
        
    async def on_generate_data(self):
        """Generate data button handler."""
        num_points = self.data_points_input.get_value()
        self.update_status(f"Generating {num_points} data points...", Color.YELLOW)
        self.progress_bar.update(0)
        
        # Create task for data generation
        asyncio.create_task(self._generate_data_task(num_points))
        
    async def _generate_data_task(self, num_points):
        """Background task for data generation."""
        try:
            await self.processor.generate_data(num_points)
            self.progress_bar.update(100)
            self.update_status(f"Generated {num_points} data points", Color.GREEN)
            self.update_log(f"Completed generating {num_points} data points")
        except Exception as e:
            self.update_status(f"Error: {e}", Color.RED)
            
    async def on_process_data(self):
        """Process data button handler."""
        if not self.processor.data:
            self.update_status("No data to process!", Color.RED)
            return
            
        unprocessed = len([d for d in self.processor.data if not d.processed])
        if unprocessed == 0:
            self.update_status("All data already processed!", Color.YELLOW)
            return
            
        self.update_status("Processing data...", Color.BLUE)
        self.progress_bar.update(0)
        
        # Create task for data processing
        asyncio.create_task(self._process_data_task())
        
    async def _process_data_task(self):
        """Background task for data processing."""
        try:
            results = await self.processor.process_data()
            self.progress_bar.update(100)
            
            # Update summary display
            summary_text = self._format_summary(results["summary"])
            self.summary_display.set_text(summary_text)
            
            self.update_status("Data processing complete", Color.GREEN)
        except Exception as e:
            self.update_status(f"Processing error: {e}", Color.RED)
            
    def _format_summary(self, summary):
        """Format summary data for display."""
        if not summary:
            return "No summary data available"
            
        text = []
        for category, stats in summary.items():
            text.append(f"Category {category}:")
            for key, value in stats.items():
                formatted_value = f"{value:.2f}" if isinstance(value, float) else value
                text.append(f"  - {key}: {formatted_value}")
                
        return "\n".join(text)
            
    def on_clear(self):
        """Clear all data button handler."""
        self.processor.data.clear()
        self.processor.results.clear()
        self.summary_display.set_text("No data processed yet")
        self.update_status("All data cleared", Color.BLUE)
        self.update_log("Data cleared", Color.YELLOW)
        self.progress_bar.update(0)
        
    def update_status(self, message, color=None):
        """Update status display."""
        self.status.set_text(message)
        if color:
            self.status.set_color(color)
            
    def update_log(self, message, color=None):
        """Add message to log display."""
        if self.data_log:
            self.data_log.add_log(message, color)
            
    def run(self):
        """Run the dashboard application."""
        self.build_ui()
        self.app.set_root(self.main_container)
        self.app.run()


async def main_async():
    """Async main function."""
    dashboard = Dashboard()
    dashboard.run()


def main():
    """Main entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
