#!/usr/bin/env python3
"""Example runner for pytui demonstrations."""

import os
import sys
import argparse
import asyncio
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pytui.executor import ScriptExecutor
from pytui.app import PyTUIApp

EXAMPLES = {
    "basic": "basic_example.py",
    "intermediate": "intermediate_example.py",
    "advanced": "advanced_example.py",
    "full": "full_demo.py",
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
    
    # Set execution timeout for examples
    app.execution_timeout = 30  # seconds
    
    # Run the app and allow it to complete
    app.run()
    print(f"Finished running {example_name} example")
    
    # Give a small pause between examples
    time.sleep(1)


def main():
    """Main entry point for example runner."""
    parser = argparse.ArgumentParser(description="Run pytui examples")
    parser.add_argument(
        "example",
        nargs="?",
        choices=list(EXAMPLES.keys()) + ["all"],
        default="basic",
        help="Which example to run",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for each example"
    )

    args = parser.parse_args()

    if args.example == "all":
        for example in EXAMPLES:
            print(f"\nRunning {example} example...")
            try:
                run_example(example)
            except KeyboardInterrupt:
                print(f"\nExiting example runner")
                return
            except Exception as e:
                print(f"Error running {example}: {e}")
    else:
        run_example(args.example)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting example runner")
    except Exception as e:
        print(f"Error: {e}")
