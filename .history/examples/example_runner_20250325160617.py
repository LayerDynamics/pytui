"""Example runner for pytui demonstrations."""

import os
import sys
import argparse
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pytui.executor import ScriptExecutor
from pytui.ui.app import PyTUIApp

EXAMPLES = {
    "basic": "basic_example.py",
    "intermediate": "intermediate_example.py",
    "advanced": "advanced_example.py",
    "full": "full_demo.py"
}

def run_example(example_name: str) -> None:
    """Run a specific example with pytui."""
    if example_name not in EXAMPLES:
        print(f"Unknown example: {example_name}")
        print(f"Available examples: {', '.join(EXAMPLES.keys())}")
        return

    example_path = Path(__file__).parent / EXAMPLES[example_name]
    if not example_path.exists():
        print(f"Example file not found: {example_path}")
        return

    print(f"Running {example_name} example...")
    executor = ScriptExecutor(str(example_path))
    app = PyTUIApp()
    app.set_executor(executor)
    app.run()

def main():
    """Main entry point for example runner."""
    parser = argparse.ArgumentParser(description="Run pytui examples")
    parser.add_argument(
        "example",
        nargs="?",
        choices=list(EXAMPLES.keys()) + ["all"],
        default="basic",
        help="Which example to run"
    )
    
    args = parser.parse_args()
    
    if args.example == "all":
        for example in EXAMPLES:
            print(f"\nRunning {example} example...")
            run_example(example)
    else:
        run_example(args.example)

if __name__ == "__main__":
    main()