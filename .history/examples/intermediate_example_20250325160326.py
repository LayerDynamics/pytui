"""Intermediate example with more complex features."""

import time
from typing import List, Dict, Any
from dataclasses import dataclass

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
            "result": f"Processed task: {task.name}"
        }

def recursive_function(n: int, depth: int = 0) -> int:
    """Demonstrate recursive function calls."""
    if depth >= 3:
        return n
    return recursive_function(n + 1, depth + 1)

def main():
    """Main function demonstrating intermediate features."""
    # Class instance tracking
    manager = TaskManager()
    
    # Multiple method calls
    manager.add_task("Initialize system", 3)
    manager.add_task("Process data", 2)
    manager.add_task("Generate report", 1)

    # Process tasks and track results
    results = manager.process_tasks()
    for result in results:
        print(f"Task {result['task_id']}: {result['result']}")

    # Demonstrate recursion
    final_value = recursive_function(1)
    print(f"Recursive function result: {final_value}")

    # Exception handling with context
    try:
        raise ValueError("Demonstrating error handling")
    except ValueError as e:
        print(f"Handled error: {e}")

if __name__ == "__main__":
    main()
