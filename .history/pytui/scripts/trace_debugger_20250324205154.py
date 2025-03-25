"""
Diagnostic tool to debug tracing issues.

This script helps diagnose issues with the pytui tracer by providing
detailed logs and test scenarios that validate tracer behavior.
"""

import sys
import os
import timetr
from pathlib import Path

# Add the parent directory to sys.path to allow importing pytui modules
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from pytui.tracer import install_trace, trace_function, _should_skip_file
from pytui.collector import DataCollector


def run_test_case(name, func):
    """Run a test case and report results."""
    print(f"\n=== Running test: {name} ===")
    start_time = time.time()

    # Create a fresh collector
    collector = DataCollector()
    install_trace(collector)

    try:
        # Run the test function
        result = func()
        duration = time.time() - start_time

        # Output stats
        print(f"- Duration: {duration:.4f}s")
        print(f"- Output events: {len(collector.output)}")
        print(f"- Call events: {len(collector.calls)}")
        print(f"- Return events: {len(collector.returns)}")
        print(f"- Exception events: {len(collector.exceptions)}")

        # Show all captured function calls
        if collector.calls:
            print("\nCaptured function calls:")
            for call in collector.calls:
                print(f"  - {call.function_name} @ {call.filename}:{call.line_no}")

        return True, result
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False, None
    finally:
        # Clean up
        sys.settrace(None)


def test_simple_function():
    """Test tracing a simple function."""

    def simple_function(x, y):
        return x + y

    result = simple_function(5, 10)
    return result


def test_exception_handling():
    """Test capturing exceptions."""

    def function_with_exception():
        try:
            1 / 0
        except ZeroDivisionError as e:
            # Handled exception
            return f"Caught: {e}"

    result = function_with_exception()
    return result


def test_skip_internal():
    """Test that internal modules are skipped."""
    filename1 = "/path/to/pytui/tracer.py"
    filename2 = "/path/to/user/script.py"

    print(f"Should skip {filename1}: {_should_skip_file(filename1)}")
    print(f"Should skip {filename2}: {_should_skip_file(filename2)}")
    return _should_skip_file(filename1) and not _should_skip_file(filename2)


def main():
    """Run all diagnostics."""
    print("PyTUI Tracer Diagnostic Tool")
    print("============================")

    # Run all test cases
    tests = [
        ("Simple Function", test_simple_function),
        ("Exception Handling", test_exception_handling),
        ("Skip Internal Modules", test_skip_internal),
    ]

    results = []
    for name, func in tests:
        success, result = run_test_case(name, func)
        results.append((name, success, result))

    # Print summary
    print("\n=== Summary ===")
    for name, success, result in results:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {name}")

    # Print any failures
    failures = [name for name, success, _ in results if not success]
    if failures:
        print(f"\n{len(failures)} tests failed: {', '.join(failures)}")
        return 1
    else:
        print("\nAll tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
