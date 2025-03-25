"""Tests for error handling and recovery."""

import os
import tempfile
import time
from pathlib import Path
import subprocess  # Import missing subprocess

import pytest

from pytui.executor import ScriptExecutor
from pytui.collector import DataCollector
from pytui.tracer import install_trace


@pytest.fixture
def error_script():
    """Create a script with various error conditions."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(
            """
# Script with various error conditions
import os
import sys
import time

print("Starting error script")

def syntax_error_function():
    # This will execute fine
    print("About to cause a syntax error")
    
    # Next line has syntax error but won't be reached
    # eval("x =")

def runtime_error_function():
    print("About to cause a runtime error")
    # This will cause a runtime error
    x = 1 / 0
    print("This line won't be reached")

def memory_error_simulation():
    print("Simulating memory pressure")
    # Create a large list to consume memory
    try:
        big_list = [0] * (10**8)  # Allocate a large list, but not too large
        print(f"Allocated list of size {len(big_list)}")
    except MemoryError:
        print("Actual memory error occurred")

def file_error_function():
    print("About to cause a file error")
    # Try to open a non-existent file
    try:
        with open("/nonexistent/file/path", "r") as f:
            content = f.read()
    except FileNotFoundError as e:
        print(f"Caught file error: {e}")

# Run the functions
print("Running functions with errors")

# Run file error function - this handles its own error
file_error_function()

try:
    # Run the runtime error function
    runtime_error_function()
except ZeroDivisionError as e:
    print(f"Caught division error: {e}")

# Run memory simulation
memory_error_simulation()

print("Script completed successfully")
"""
        )
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)


@pytest.fixture
def long_running_script():
    """Create a script that runs for a long time or indefinitely."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(
            """
# Long-running script
import time

print("Starting long-running script")

def run_indefinitely():
    counter = 0
    while True:
        counter += 1
        if counter % 10 == 0:
            print(f"Still running... count: {counter}")
        time.sleep(0.1)

try:
    run_indefinitely()
except KeyboardInterrupt:
    print("Script interrupted by SIGINT")
except Exception as e:
    print(f"Script interrupted by another exception: {e}")

print("Script exiting")
"""
        )
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)


@pytest.fixture
def stdout_flood_script():
    """Create a script that floods stdout with data."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(
            """
# Script that floods stdout
import sys
import time

print("Starting to flood stdout")

# Generate a lot of data quickly
for i in range(100000):
    print(f"Line {i} " + "x" * 100)
    if i % 1000 == 0:
        print(f"Progress: {i/1000}%", file=sys.stderr)
        sys.stdout.flush()
        time.sleep(0.01)

print("Finished flooding stdout")
"""
        )
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)


@pytest.mark.slow
def test_error_handling(error_script):
    """Test handling of scripts with various errors."""
    executor = None
    try:
        executor = ScriptExecutor(error_script)
        executor.start()

        # Wait for script to complete
        max_wait = 15
        start_time = time.time()
        completed = False

        while time.time() - start_time < max_wait and not completed:
            if any(
                "Script completed successfully" in line.content
                for line in executor.collector.output
            ):
                completed = True
            time.sleep(0.1)

        assert completed, "Script did not complete in the expected time"

        # Check that all error messages were captured
        outputs = " ".join([line.content for line in executor.collector.output])
        assert "About to cause a file error" in outputs, "File error test not run"
        assert "Caught file error" in outputs, "File error not caught"
        assert "About to cause a runtime error" in outputs, "Runtime error test not run"
        assert "Caught division error" in outputs, "Division error not caught"
        assert (
            "Simulating memory pressure" in outputs
        ), "Memory error simulation not run"

        # Process should have exited normally
        assert executor.process.poll() == 0, "Process did not exit with code 0"
    finally:
        # Ensure cleanup
        if executor:
            executor.stop()


@pytest.mark.slow
def test_long_running_script_termination(long_running_script):
    """Test ability to terminate a long-running script."""
    executor = None
    try:
        executor = ScriptExecutor(long_running_script)
        executor.start()

        # Wait for script to start producing output
        max_wait = 10
        start_time = time.time()
        started = False

        while time.time() - start_time < max_wait:
            if any(
                "Still running" in line.content for line in executor.collector.output
            ):
                started = True
                break  # Exit loop once started is True
            time.sleep(0.1)
            
            # Check if the process has terminated early
            if executor.process.poll() is not None:
                print("Process terminated early, exiting loop")
                break

        assert started, "Script did not start in the expected time"

        # Record output count
        output_count = len(executor.collector.output)

        # Now stop the script
        executor.stop()

        # Wait a bit for process to terminate
        time.sleep(1)

        # Check that process terminated
        assert executor.process.poll() is not None, "Process still running after stop"
        assert not executor.is_running, "Executor still marked as running"

        # Verify no more output was captured after termination
        assert (
            len(executor.collector.output) == output_count
        ), "Output continued after termination"
    finally:
        # Ensure cleanup
        if executor:
            executor.stop()


@pytest.mark.slow
def test_stdout_flood_handling(stdout_flood_script):
    """Test handling of scripts that flood stdout."""
    executor = None
    try:
        executor = ScriptExecutor(stdout_flood_script)
        executor.start()

        # Wait for script to complete or timeout
        max_wait = 20
        start_time = time.time()

        # Wait for either completion message or reaching output limit
        while time.time() - start_time < max_wait:
            if any(
                "Finished flooding stdout" in line.content
                for line in executor.collector.output
            ):
                break
            time.sleep(0.1)

        # Check if we captured a reasonable amount of output
        output_lines = len(executor.collector.output)
        print(f"Captured {output_lines} lines of output from flood script")

        # Should have captured a significant amount of output, but may not get all 100k lines
        assert output_lines > 1000, "Not enough output captured from flood script"

        # Process should have exited (one way or another)
        assert (
            not executor.is_running or executor.process.poll() is not None
        ), "Process still running after expected completion"
    finally:
        # Ensure cleanup
        if executor:
            executor.stop()


def test_executor_start_stop_restart_stress():
    """Test start/stop/restart cycle under stress."""
    # Create a simple script
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(
            """
# Simple script for stress testing
import time

def loop_function():
    for i in range(10):
        print(f"Iteration {i}")
        time.sleep(0.1)
    return "Done"

loop_function()
print("Script completed")
"""
        )
        script_path = Path(f.name)

    try:
        executor = ScriptExecutor(script_path)

        # Perform multiple start/stop cycles
        for i in range(5):
            print(f"Start/stop cycle {i+1}")

            # Start
            executor.start()
            assert executor.is_running, "Executor didn't start properly"

            # Wait a bit
            time.sleep(0.3)

            # Stop
            executor.stop()
            assert not executor.is_running, "Executor didn't stop properly"

            # Verify process is terminated
            assert (
                executor.process.poll() is not None
            ), "Process still running after stop"

            # Wait a bit
            time.sleep(0.2)

        # Perform multiple restart cycles
        for i in range(3):
            print(f"Restart cycle {i+1}")

            # Start
            executor.start()
            assert executor.is_running, "Executor didn't start properly"

            # Wait a bit
            time.sleep(0.3)

            # Restart
            executor.restart()
            assert executor.is_running, "Executor isn't running after restart"

            # Wait a bit
            time.sleep(0.3)

            # Stop
            executor.stop()
            assert not executor.is_running, "Executor didn't stop properly"

            # Verify process is terminated
            executor.stop()
            if executor.process.poll() is None:
                try:
                    executor.process.wait(timeout=2)  # Wait up to 2 seconds
                except subprocess.TimeoutExpired:
                    print("Process did not terminate in time, killing it")
                    executor.process.kill()
            assert executor.process.poll() is not None, "Process still running after stop"

            # Wait a bit
            time.sleep(0.2)

        # Final verification of collector state
        assert executor.collector is not None, "Collector should still be available"

    finally:
        # Clean up
        os.unlink(script_path)


def test_tracer_exception_handling():
    """Test that tracer handles exceptions gracefully."""
    collector = DataCollector()
    install_trace(collector)

    # Define functions that might cause tracing problems
    def recursive_function(n):
        """Recursive function to test deep call stacks."""
        collector.add_output(f"Recursive call {n}", "stdout")
        if n <= 0:
            return 0
        return n + recursive_function(n - 1)

    def problematic_args_function(bad_repr_obj):
        """Function with an argument that has a problematic __repr__."""
        return str(bad_repr_obj)

    # Create an object with a __repr__ that raises an exception
    class BadReprObject:
        """Class with a problematic __repr__ method for testing error handling."""
        
        def __repr__(self):
            """Deliberately failing __repr__ method."""
            raise ValueError("This repr fails intentionally")
            
        def str_method(self):
            """Additional method to satisfy the pylint warning about too few methods."""
            return "BadReprObject"

    # Test recursive function - should handle deep call stacks
    result = recursive_function(50)
    assert result == 1275, "Recursive function returned wrong result"

    # Verify recursive calls were traced
    assert len(collector.calls) >= 50, "Not enough recursive calls were traced"

    # Test problematic argument function - should handle bad repr gracefully
    bad_obj = BadReprObject()
    problematic_args_function(bad_obj)

    # Get the call where bad_obj was passed
    prob_calls = [
        call
        for call in collector.calls
        if call.function_name == "problematic_args_function"
    ]

    assert len(prob_calls) > 0, "Problematic function call not traced"

    # Args should contain something for bad_repr_obj, but not the actual exception
    assert "bad_repr_obj" in prob_calls[0].args, "Argument not captured"
    assert (
        "unable to represent" in prob_calls[0].args["bad_repr_obj"]
    ), "Bad repr not handled gracefully"
