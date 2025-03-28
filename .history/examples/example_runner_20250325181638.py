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

    # Print a clear header for the current example
    example_header = f" Running {example_name.upper()} example "
    print("\n" + "=" * 60)
    print(example_header.center(60))
    print("=" * 60 + "\n")
    
    # Run the example
    executor = ScriptExecutor(str(example_path))
    app = PyTUIApp()
    app.set_executor(executor)
    
    # Set execution timeout for examples
    app.execution_timeout = 15  # shorter timeout for demo purposes
    
    # Run the app with close_loop=False to keep the event loop open
    app.run(close_loop=False)
    
    print(f"\n{'=' * 20} FINISHED {example_name.upper()} {'=' * 20}\n")
    
    # Give a small pause between examples
    time.sleep(2)  # 2 second pause between examples


def main():
    """Main entry point for example runner."""
    parser = argparse.ArgumentParser(description="Run pytui examples")
    parser.add_argument(
        "example",
        nargs="?",
        choices=list(EXAMPLES.keys()) + ["all"],
        default="all",  # Default to running all examples
        help="Which example to run (default: all)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Timeout in seconds for each example"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Continuously cycle through all examples"
    )

    args = parser.parse_args()

    # Print welcome message
    print("\n" + "*" * 70)
    print("*" + " PYTUI EXAMPLES RUNNER ".center(68) + "*")
    print("*" + " Press Ctrl+C to exit at any time ".center(68) + "*")
    print("*" * 70 + "\n")

    try:
        if args.example == "all":
            # Reset the event loop for the whole sequence
            if asyncio.get_event_loop().is_closed():
                asyncio.set_event_loop(asyncio.new_event_loop())
            
            # Run all examples in sequence
            cycle_count = 0
            while True:
                if cycle_count > 0:
                    print(f"\n\nStarting cycle {cycle_count+1} of all examples\n\n")
                
                # Run through all examples in sequence
                for example in EXAMPLES:
                    try:
                        run_example(example)
                    except KeyboardInterrupt:
                        print("\nInterrupted. Exiting examples runner.")
                        return
                    except Exception as e:
                        print(f"Error running {example}: {e}")
                
                cycle_count += 1
                
                # If not in continuous mode, exit after one cycle
                if not args.continuous:
                    break
                
                print("\nCompleted full cycle of examples. 5 second pause before next cycle...\n")
                time.sleep(5)
        else:
            # Run just the selected example
            run_example(args.example)
            
    except KeyboardInterrupt:
        print("\nExiting examples runner")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up the event loop at the very end
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.close()
        except Exception:
            pass
        print("\nThank you for checking out the PyTUI examples!")


if __name__ == "__main__":
    main()
