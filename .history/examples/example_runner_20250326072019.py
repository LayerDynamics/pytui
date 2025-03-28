"""PyTUI Example Runner

This script runs all PyTUI examples in sequence or individually,
providing a clean interface and proper cleanup between runs.
"""

import sys
import os
import asyncio
import time
from pathlib import Path
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pytui.rich_text_ui import (
    Color, Text, List as UIList, Progress
)
from examples.shared_components import (
    App, Button, Label, TextInput, VBox, HBox
)


@dataclass
class ExampleInfo:
    """Information about an example script."""
    name: str
    filename: str
    description: str
    module: Optional[str] = None


class ExampleRunner:
    """Manages the execution of PyTUI examples."""

    def __init__(self):
        """Initialize the example runner."""
        self.examples: Dict[str, ExampleInfo] = {
            "basic": ExampleInfo(
                "Basic Form",
                "basic_Example.py",
                "Simple form with validation and basic UI components"
            ),
            "intermediate": ExampleInfo(
                "Data Management",
                "intermediate_example.py",
                "Table display and data filtering demonstration"
            ),
            "advanced": ExampleInfo(
                "Advanced Features",
                "advanced_example.py",
                "Tabs, modals, and async operations showcase"
            ),
            "full": ExampleInfo(
                "Full Demo",
                "full_demo.py",
                "Comprehensive demo with all features"
            )
        }
        self.current_example: Optional[str] = None
        self.running = True
        self.continuous_mode = False
        
    def create_ui(self) -> None:
        """Create the runner UI."""
        self.app = App(title="PyTUI Example Runner")
        self.container = VBox()
        
        # Title
        title = Label("PyTUI Example Runner", Color.CYAN)
        title.set_align("center")
        self.container.add(title)
        
        # Description
        desc = Label("Run and test PyTUI examples interactively")
        desc.set_align("center")
        self.container.add(desc)
        
        # Example list
        self.example_list = UIList()
        self.update_example_list()
        self.container.add(self.example_list)
        
        # Controls
        controls = HBox()
        controls.add(Button("Run Selected", self.run_selected))
        controls.add(Button("Run All", self.run_all))
        controls.add(Button("Toggle Continuous", self.toggle_continuous))
        controls.add(Button("Exit", self.exit))
        self.container.add(controls)
        
        # Status
        self.status = Label("")
        self.status.set_align("center")
        self.container.add(self.status)
        
        # Progress
        self.progress = Progress()
        self.container.add(self.progress)
        
        self.app.set_root(self.container)

    def update_example_list(self) -> None:
        """Update the example list display."""
        self.example_list.clear()
        for key, info in self.examples.items():
            status = " [RUNNING]" if key == self.current_example else ""
            self.example_list.add_item(
                f"{info.name}: {info.description}{status}",
                color=Color.CYAN if key == self.current_example else None
            )

    def update_status(self, message: str, color: str = Color.WHITE) -> None:
        """Update status message."""
        self.status.set_text(message)
        self.status.set_color(color)
        
    async def run_example(self, key: str) -> None:
        """Run a single example."""
        info = self.examples[key]
        self.current_example = key
        self.update_example_list()
        
        try:
            # Import and run the example
            self.update_status(f"Running {info.name}...", Color.YELLOW)
            
            # Import the example module
            example_path = Path(__file__).parent / info.filename
            if not example_path.exists():
                raise FileNotFoundError(f"Example file not found: {example_path}")
                
            # Run the example
            self.update_status(f"Starting {info.name}...", Color.BLUE)
            if info.filename == "full_demo.py":
                # Full demo uses asyncio
                await self._run_async_example(example_path)
            else:
                # Other examples are synchronous
                await self._run_sync_example(example_path)
                
            self.update_status(f"Completed {info.name}", Color.GREEN)
            
        except Exception as e:
            self.update_status(f"Error running {info.name}: {e}", Color.RED)
            
        finally:
            self.current_example = None
            self.update_example_list()
            await asyncio.sleep(1)  # Pause between examples

    async def _run_sync_example(self, path: Path) -> None:
        """Run a synchronous example."""
        namespace = {}
        with open(path) as f:
            exec(f.read(), namespace)
        if "main" in namespace:
            namespace["main"]()

    async def _run_async_example(self, path: Path) -> None:
        """Run an async example."""
        namespace = {}
        with open(path) as f:
            exec(f.read(), namespace)
        if "main" in namespace:
            await namespace["main"]()

    async def run_all_examples(self) -> None:
        """Run all examples in sequence."""
        for key in self.examples.keys():
            if not self.running:
                break
            await self.run_example(key)
            
            if self.continuous_mode:
                self.update_status("Starting next example in 3 seconds...", Color.BLUE)
                await asyncio.sleep(3)
            else:
                break

    def run_selected(self) -> None:
        """Run the selected example."""
        # Get selected example
        selected_idx = self.example_list.get_selected()
        if selected_idx is not None:
            key = list(self.examples.keys())[selected_idx]
            asyncio.create_task(self.run_example(key))

    def run_all(self) -> None:
        """Start running all examples."""
        asyncio.create_task(self.run_all_examples())

    def toggle_continuous(self) -> None:
        """Toggle continuous mode."""
        self.continuous_mode = not self.continuous_mode
        state = "ON" if self.continuous_mode else "OFF"
        self.update_status(f"Continuous mode: {state}", Color.YELLOW)

    def exit(self) -> None:
        """Exit the runner."""
        self.running = False
        self.app.exit()

    def run(self) -> None:
        """Run the example runner."""
        self.create_ui()
        self.update_status("Select an example to run", Color.BLUE)
        self.app.run()


def main():
    """Main entry point."""
    try:
        runner = ExampleRunner()
        runner.run()
    except KeyboardInterrupt:
        print("\nExiting Example Runner")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
