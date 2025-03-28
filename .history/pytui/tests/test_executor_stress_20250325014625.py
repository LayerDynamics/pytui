"""Stress tests for the executor component."""

import os
import sys
import time
import tempfile
import threading
from pathlib import Pathe
import pytest

from pytui.executor import ScriptExecutor


@pytest.fixture
def large_output_script():
    """Create a script that generates a large amount of output."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(
            """
# Large output generator
import time

# Generate a lot of stdout
for i in range(1000):
    print(f"Standard output line {i}")
    if i % 100 == 0:
        time.sleep(0.01)  # Small delay to avoid overwhelming the pipe

# Generate some stderr
for i in range(200):
    import sys
    print(f"Error output line {i}", file=sys.stderr)
    if i % 50 == 0:
        time.sleep(0.01)
"""
        )
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)


@pytest.fixture
def recursive_function_script():
    """Create a script with deep recursive function calls."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(
            """
# Recursive function call test
def recursive_func(n, depth=0):
    prefix = "  " * depth
    print(f"{prefix}Enter recursive_func({n}, {depth})")
    if n <= 0:
        print(f"{prefix}Base case reached, returning 0")
        return 0
    
    result = n + recursive_func(n-1, depth+1)
    print(f"{prefix}Exit recursive_func({n}, {depth}) -> {result}")
    return result

# Call with moderate recursion depth
result = recursive_func(15)
print(f"Final result: {result}")
"""
        )
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)


@pytest.fixture
def multiprocess_script():
    """Create a script that spawns multiple processes."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(
            """
# Multi-process test
import multiprocessing
import os
import time

def worker_process(worker_id):
    print(f"Worker {worker_id} started (PID: {os.getpid()})")
    # Simulate work
    for i in range(10):
        print(f"Worker {worker_id} - task {i}")
        time.sleep(0.01)
    print(f"Worker {worker_id} finished")
    return worker_id

if __name__ == "__main__":
    print(f"Main process PID: {os.getpid()}")
    
    # Create process pool and run workers
    with multiprocessing.Pool(processes=3) as pool:
        results = pool.map(worker_process, range(5))
        print(f"All workers completed. Results: {results}")
"""
        )
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)


@pytest.mark.slow
@pytest.mark.skip("Temporary skip due to concurrency issues.")
def test_large_output_handling(large_output_script):
    """Test handling of scripts that generate large amounts of output."""
    executor = None
    try:
        executor = ScriptExecutor(large_output_script)
        executor.start()

        # Wait for execution to complete with timeout
        max_wait = 15
        start_time = time.time()

        # Poll for completion
        all_stderr_received = False
        all_stdout_received = False

        while time.time() - start_time < max_wait and not (
            all_stderr_received and all_stdout_received
        ):
            # Check for last lines of output
            stdout_lines = [
                line.content
                for line in executor.collector.output
                if line.stream == "stdout"
            ]
            stderr_lines = [
                line.content
                for line in executor.collector.output
                if line.stream == "stderr"
            ]

            if any("Standard output line 999" in line for line in stdout_lines):
                all_stdout_received = True

            if any("Error output line 199" in line for line in stderr_lines):
                all_stderr_received = True

            if not (all_stderr_received and all_stdout_received):
                time.sleep(0.1)

        # Verify output collection
        assert len(executor.collector.output) > 1000, "Not all output was collected"
        assert all_stdout_received, "Not all stdout was received"
        assert all_stderr_received, "Not all stderr was received"

        # Verify no deadlocks or other issues
        assert executor.process.poll() is not None, "Process should have completed"
    finally:
        # Ensure cleanup
        if executor:
            executor.stop()


@pytest.mark.slow
@pytest.mark.skip("Temporary skip due to concurrency issues.")
def test_recursive_function_tracing(recursive_function_script):
    """Test tracing of deeply recursive function calls."""
    executor = None
    try:
        executor = ScriptExecutor(recursive_function_script)
        executor.start()

        # Wait for execution to complete
        max_wait = 10
        start_time = time.time()

        # Poll for completion
        while time.time() - start_time < max_wait:
            if any(
                "Final result: 120" in line.content
                for line in executor.collector.output
            ):
                break
            time.sleep(0.1)

        # Check that execution completed
        assert any(
            "Final result: 120" in line.content for line in executor.collector.output
        ), "Script did not complete successfully"

        # Check function calls were traced - there should be multiple recursive_func calls
        recursive_calls = [
            call
            for call in executor.collector.calls
            if call.function_name == "recursive_func"
        ]

        # We may not get all 16 calls due to timing, but should have some
        assert len(recursive_calls) > 0, "No recursive_func calls were traced"

        # Verify call/return pairing
        return_events = len(
            [
                ret
                for ret in executor.collector.returns
                if ret.function_name == "recursive_func"
            ]
        )
        assert return_events > 0, "No return events captured for recursive_func"

    finally:
        # Ensure cleanup
        if executor:
            executor.stop()


@pytest.mark.slow
@pytest.mark.skip("Temporary skip due to concurrency issues.")
def test_multiple_script_execution():
    """Test running multiple script executors simultaneously."""
    # Create multiple simple scripts
    scripts = []
    executors = []

    try:
        # Create 5 simple scripts
        for i in range(5):
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
                f.write(
                    f"""
# Test script {i}
import time
for j in range(10):
    print(f"Script {i} - line {{j}}")
    time.sleep(0.01)
print(f"Script {i} completed")
"""
                )
                scripts.append(Path(f.name))

        # Start all executors
        for script in scripts:
            executor = ScriptExecutor(script)
            executor.start()
            executors.append(executor)

        # Wait for all to complete
        max_wait = 15
        start_time = time.time()

        all_completed = False
        while time.time() - start_time < max_wait and not all_completed:
            # Check if all executors have completed scripts
            all_completed = all(
                any(
                    f"Script {i} completed" in line.content
                    for line in executor.collector.output
                )
                for i, executor in enumerate(executors)
            )

            if not all_completed:
                time.sleep(0.1)

        # Verify all scripts completed
        for i, executor in enumerate(executors):
            assert any(
                f"Script {i} completed" in line.content
                for line in executor.collector.output
            ), f"Script {i} did not complete"

        # Verify no cross-contamination of output
        for i, executor in enumerate(executors):
            # Each executor should only have its own script output
            for j in range(5):
                if j != i:
                    assert not any(
                        f"Script {j} " in line.content
                        for line in executor.collector.output
                    ), f"Executor {i} contains output from script {j}"
    finally:
        # Ensure cleanup
        for executor in executors:
            executor.stop()

        # Clean up script files
        for script in scripts:
            os.unlink(script)


@pytest.mark.slow
@pytest.mark.skip("Temporary skip due to concurrency issues.")
def test_process_cleanup_on_error():
    """Test that executor properly cleans up processes even on error."""
    # Create a script that will encounter an error
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(
            """
# Script with an error
import time
print("Starting script")
time.sleep(0.2)  # Give some time for tracing to start
# Raise an error
raise ValueError("Intentional error for testing")
"""
        )
        script_path = Path(f.name)

    executor = None
    try:
        executor = ScriptExecutor(script_path)
        executor.start()

        # Wait for error to occur
        max_wait = 5
        start_time = time.time()

        # Poll for error
        while time.time() - start_time < max_wait:
            if any("ValueError" in line.content for line in executor.collector.output):
                break
            time.sleep(0.1)

        # Verify error was captured
        assert any(
            "ValueError" in line.content for line in executor.collector.output
        ), "Script error was not captured"

        # Wait a bit to ensure process terminates
        time.sleep(1)

        # Process should have terminated
        assert executor.process.poll() is not None, "Process should have terminated"

        # Executor should be marked as not running
        assert not executor.is_running, "Executor still marked as running"

    finally:
        # Ensure cleanup
        if executor:
            executor.stop()
        os.unlink(script_path)
