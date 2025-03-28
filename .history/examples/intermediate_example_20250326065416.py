"""Intermediate example demonstrating table and data management."""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from examples.shared_components import App, Button, Label, TextInput, VBox, HBox, Table
from pytui.rich_text_ui.colors import Color
from pytui.rich_text_ui.list import List as UIList
from pytui.rich_text_ui.text import Text


@dataclass
class Task:
    """Example task class for demonstration."""

    id: int
    name: str
    priority: int
    status: str = "pending"


class TaskManager:
    """Class to demonstrate object tracking and method calls."""

    def __init__(self):
        """Initialize task manager."""
        self.tasks: List[Task] = []
        self._counter = 0

    def add_task(self, name: str, priority: int = 1) -> Task:
        """Add a new task."""
        self._counter += 1
        task = Task(self._counter, name, priority)
        self.tasks.append(task)
        return task

    def process_tasks(self) -> List[Dict[str, Any]]:
        """Process all pending tasks."""
        results = []
        for task in self.tasks:
            result = self._process_single_task(task)
            results.append(result)
        return results

    def _process_single_task(self, task: Task) -> Dict[str, Any]:
        """Process a single task with artificial delay."""
        time.sleep(0.1)  # Simulate work
        task.status = "completed"
        return {
            "task_id": task.id,
            "name": task.name,
            "result": f"Processed task: {task.name}",
        }


class TaskList(UIList):
    """Custom UI list for displaying tasks."""
    
    def __init__(self):
        super().__init__()
        
    def update_tasks(self, tasks):
        self.clear()
        for task in tasks:
            status_color = Color.GREEN if task.status == "completed" else Color.YELLOW
            self.add_item(f"Task {task.id}: {task.name} - Priority: {task.priority} [Status: {task.status}]", style=status_color)


class DataViewer:
    """Data viewer with table display and filtering."""
    
    def __init__(self):
        self.app = App(title="PyTUI Data Viewer")
        self.main_container = VBox()
        self.data_table = Table(headers=["ID", "Name", "Category", "Value"])
        self.filter_input = TextInput(placeholder="Filter by name...")
        self.status = Label("")
        self.status_text = Text()  # Add styled text component
        
        # Sample data
        self.data = [
            (1, "Alpha Project", "Development", 1500),
            (2, "Beta Testing", "QA", 800),
            (3, "Cloud Migration", "Infrastructure", 2000),
            (4, "Data Analysis", "Research", 1200),
            (5, "Email Campaign", "Marketing", 500)
        ]
        
    def build_ui(self):
        """Build the data viewer interface."""
        # Title
        title = Label("Data Viewer Demo", Color.CYAN)
        title.set_align("center")
        self.main_container.add(title)
        
        # Filter section
        filter_box = HBox()
        filter_label = Label("Filter: ")
        filter_box.add(filter_label)
        filter_box.add(self.filter_input)
        
        def on_filter_change():
            self.update_table(self.filter_input.get_value())
            
        self.filter_input.on_change = on_filter_change
        self.main_container.add(filter_box)
        
        # Add formatted text section
        text_container = VBox()
        stats_text = Text("Statistics", style=Color.CYAN + " bold")
        help_text = Text("Use the filter above to search data", style=Color.BLUE + " italic")
        text_container.add(stats_text)
        text_container.add(help_text)
        self.main_container.add(text_container)
        
        # Table
        self.main_container.add(self.data_table)
        self.update_table()
        
        # Controls
        controls = HBox()
        controls.add(Button("Refresh", self.update_table))
        controls.add(Button("Sort by Name", lambda: self.sort_data("name")))
        controls.add(Button("Sort by Value", lambda: self.sort_data("value")))
        controls.add(Button("Exit", self.app.exit))
        self.main_container.add(controls)
        
        # Status
        self.status.set_align("center")
        self.main_container.add(self.status)
        
        # Add status with rich text
        self.status_text = Text("Ready", style=Color.GREEN)
        self.main_container.add(self.status_text)
        
        self.app.set_root(self.main_container)
        
    def update_table(self, filter_text=""):
        """Update table with filtered data."""
        self.data_table.rows.clear()
        filtered_data = [
            row for row in self.data
            if filter_text.lower() in str(row[1]).lower()
        ]
        for row in filtered_data:
            self.data_table.add_row(row)
        
        self.status.set_text(f"Showing {len(filtered_data)} of {len(self.data)} items")
        self.status_text.update(f"Showing {len(filtered_data)} of {len(self.data)} items", 
                              style=Color.BLUE if filtered_data else Color.RED)
        
    def sort_data(self, key):
        """Sort data by specified key."""
        idx = 1 if key == "name" else 3
        self.data.sort(key=lambda x: x[idx])
        self.update_table(self.filter_input.get_value())
        self.status.set_text(f"Sorted by {key}")
        
    def run(self):
        """Run the data viewer."""
        self.build_ui()
        self.app.run()

def main():
    """Run the intermediate example."""
    viewer = DataViewer()
    viewer.run()

if __name__ == "__main__":
    main()
