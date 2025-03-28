"""Advanced example demonstrating tabs, modals, and async operations."""

import sys
import os
import asyncio
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from examples.shared_components import App, Button, Label, TextInput, VBox, HBox, TabView, Modal
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


class NumberInput(TextInput):
    def __init__(self, value=0, min_value=1, max_value=100):
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
        
        # Initialize async components
        self.running_tasks = []
        self.task_results = []
        
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
        # Tasks tab
        tasks_container = VBox()
        tasks_container.add(Label("Running Tasks"))
        task_list = UIList()
        tasks_container.add(task_list)
        self.tab_view.add_tab("Tasks", tasks_container)
        
        # Monitor tab
        monitor_container = VBox()
        monitor_container.add(Label("System Monitor"))
        monitor = Progress()
        monitor_container.add(monitor)
        self.tab_view.add_tab("Monitor", monitor_container)
        
        # Results tab
        results_container = VBox()
        results_container.add(Label("Task Results"))
        results_list = UIList()
        results_container.add(results_list)
        self.tab_view.add_tab("Results", results_container)
        
    def setup_modal(self):
        """Set up the modal dialog."""
        content = VBox()
        content.add(Label("Task Details"))
        content.add(Label("Status: Running"))
        content.add(Button("Close", self.modal.hide))
        self.modal.add(content)
        
    def run(self):
        """Run the dashboard."""
        self.build_ui()
        self.app.run()

def main():
    """Run the advanced example."""
    dashboard = AsyncDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
