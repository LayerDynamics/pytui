"""Intermediate example demonstrating task management with PyTUI components."""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from examples.shared_components import App, Button, Label, TextInput, VBox, HBox
from pytui.rich_text_ui.colors import Color
from pytui.rich_text_ui.list import List as UIList


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


def main():
    """Main function demonstrating intermediate UI features."""
    # Create a new terminal UI application
    app = App(title="PyTUI Task Manager Demo")
    
    # Create task manager instance
    task_manager = TaskManager()
    
    # Create main container with a vertical layout
    main_container = VBox()
    
    # Add a title
    title = Label("Task Manager Demo", Color.CYAN)
    title.set_align("center")
    main_container.add(title)
    
    # Add a separator
    separator = Label("─" * 50)
    separator.set_align("center")
    main_container.add(separator)
    
    # Create task input form
    form_container = VBox()
    
    task_input_container = HBox()
    task_label = Label("Task Name: ")
    task_input = TextInput(width=30, placeholder="Enter task name")
    task_input_container.add(task_label)
    task_input_container.add(task_input)
    
    priority_container = HBox()
    priority_label = Label("Priority (1-5): ")
    priority_input = TextInput(width=5, value="1")
    priority_container.add(priority_label)
    priority_container.add(priority_input)
    
    form_container.add(task_input_container)
    form_container.add(priority_container)
    
    main_container.add(form_container)
    
    # Task list display
    task_list_label = Label("Current Tasks:", Color.BLUE)
    main_container.add(task_list_label)
    
    task_list = TaskList()
    main_container.add(task_list)
    
    # Results display
    results_container = VBox()
    results_label = Label("Processing Results:", Color.BLUE)
    results_label.set_align("center")
    results_container.add(results_label)
    
    results_display = Label("")
    results_container.add(results_display)
    
    main_container.add(results_container)
    
    # Create button container
    button_container = HBox()
    
    # Status message
    status_message = Label("")
    status_message.set_align("center")
    
    # Add task button
    def on_add_task():
        task_name = task_input.get_value()
        if not task_name:
            status_message.set_text("Please enter a task name!")
            status_message.set_color(Color.RED)
            return
            
        try:
            priority = int(priority_input.get_value())
            if priority < 1 or priority > 5:
                raise ValueError("Priority must be between 1 and 5")
        except ValueError:
            status_message.set_text("Priority must be a number between 1 and 5!")
            status_message.set_color(Color.RED)
            return
            
        task_manager.add_task(task_name, priority)
        task_input.set_value("")
        priority_input.set_value("1")
        status_message.set_text(f"Added task: {task_name}")
        status_message.set_color(Color.GREEN)
        
        # Update the task list
        task_list.update_tasks(task_manager.tasks)
    
    add_button = Button("Add Task", on_add_task)
    button_container.add(add_button)
    
    # Process tasks button
    def on_process_tasks():
        if not task_manager.tasks:
            status_message.set_text("No tasks to process!")
            status_message.set_color(Color.YELLOW)
            return
            
        status_message.set_text("Processing tasks...")
        status_message.set_color(Color.BLUE)
        
        # Process tasks
        results = task_manager.process_tasks()
        
        # Update task list with new statuses
        task_list.update_tasks(task_manager.tasks)
        
        # Show results
        results_text = "\n".join([f"Task {r['task_id']}: {r['result']}" for r in results])
        results_display.set_text(results_text)
        
        status_message.set_text(f"Processed {len(results)} tasks successfully!")
        status_message.set_color(Color.GREEN)
    
    process_button = Button("Process Tasks", on_process_tasks)
    button_container.add(process_button)
    
    # Clear button
    def on_clear():
        task_manager.tasks.clear()
        task_manager._counter = 0
        task_list.update_tasks([])
        results_display.set_text("")
        status_message.set_text("Cleared all tasks")
        status_message.set_color(Color.BLUE)
    
    clear_button = Button("Clear All", on_clear)
    button_container.add(clear_button)
    
    # Exit button
    exit_button = Button("Exit", lambda: app.exit())
    button_container.add(exit_button)
    
    main_container.add(button_container)
    main_container.add(status_message)
    
    # Add a footer
    footer = Label("Navigate with TAB/SHIFT+TAB | Use ENTER to activate buttons | ESC to exit")
    footer.set_align("center")
    footer.set_color(Color.BLUE)
    main_container.add(footer)
    
    # Set the root and run the app
    app.set_root(main_container)
    app.run()


if __name__ == "__main__":
    main()
