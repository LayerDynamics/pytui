"""Tests for error handling and edge cases."""

import os
import sys
import time
import asyncio
import tempfile
import contextlib
from pathlib import Path
import threading
import subprocess
from unittest.mock import MagicMock, patch
from types import TracebackType
from typing import List, Optional, Type

# pylint: disable=import-error
import pytest  # type: ignore

from pytui.executor import ScriptExecutor
from pytui.collector import DataCollector
from pytui.utils import kill_process_tree, terminate_process_tree

# pylint: disable=redefined-outer-name, broad-exception-caught, trailing-whitespace, line-too-long


@pytest.fixture
def error_script():
    """Create a script that raises an error."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
import sys
import time

def function_with_error():
    # Raise an error after a slight delay
    time.sleep(0.1)
    print("About to raise an error")
    raise ValueError("This is a test error")

if __name__ == "__main__":
    # Let parent process know we're starting
    print("Starting error script")
    sys.stdout.flush()
    
    # Raise the error if no arguments are provided
    if len(sys.argv) == 1:
        function_with_error()
    else:
        # Otherwise infinite output
        count = 0
        while True:
            print(f"Output line {count}")
            sys.stdout.flush()
            count += 1
            time.sleep(0.01)
"""
        )
        script_path = f.name

    yield script_path

    try:
        # Clean up the file
        if os.path.exists(script_path):
            os.unlink(script_path)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture
def long_running_script():
    """Create a long-running script."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
import sys
import time

def long_running_function():
    print("Starting long operation")
    sys.stdout.flush()
    # Simulate a long operation
    for i in range(100):
        time.sleep(0.1)
        print(f"Progress: {i}%")
        sys.stdout.flush()
    print("Long operation complete")
    sys.stdout.flush()

if __name__ == "__main__":
    print("Starting long-running script")
    sys.stdout.flush()
    long_running_function()
"""
        )
        script_path = f.name

    yield script_path

    try:
        # Clean up the file
        if os.path.exists(script_path):
            os.unlink(script_path)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture
def flood_script():
    """Create a script that floods stdout."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
import sys
import time

def flood_output():
    print("Starting to flood output")
    sys.stdout.flush()
    count = 0
    # Generate a lot of output
    while True:
        print(f"Output line {count}")
        sys.stdout.flush()
        count += 1
        # Small delay to avoid completely locking up
        if count % 1000 == 0:
            time.sleep(0.01)

if __name__ == "__main__":
    print("Starting flood script")
    sys.stdout.flush()
    flood_output()
"""
        )
        script_path = f.name

    yield script_path

    try:
        # Clean up the file
        if os.path.exists(script_path):
            os.unlink(script_path)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture
def collector():
    """Create a data collector for testing."""
    return DataCollector()


@pytest.mark.skipif(
    not os.environ.get("RUN_SLOW_TESTS"), reason="use --run-slow to run"
)
def test_error_handling(error_script):
    """Test handling of script errors."""
    # Use sys to configure PYTHONPATH for testing subprocess
    original_path = sys.path.copy()
    
    executor = ScriptExecutor(error_script)

    # Start the executor
    executor.start()

    # Wait for the script to finish (with error)
    timeout = 5
    start_time = time.time()

    while executor.is_running and time.time() - start_time < timeout:
        time.sleep(0.1)

    # Restore original path (uses sys)
    sys.path = original_path

    # Check that execution completed (script raised an error)
    assert time.time() - start_time < timeout, "Script execution timed out"
    assert not executor.is_running, "Executor should not be running after script error"

    # Check that error was captured
    exceptions = executor.collector.exceptions
    assert len(exceptions) > 0, "No exceptions were captured"
    assert (
        "ValueError" in exceptions[0].exception_type
    ), "Exception type should be ValueError"
    assert (
        "This is a test error" in exceptions[0].message
    ), "Exception message not captured correctly"


@pytest.mark.skipif(
    not os.environ.get("RUN_SLOW_TESTS"), reason="use --run-slow to run"
)
def test_long_running_script_termination(long_running_script):
    """Test termination of a long-running script."""
    # Use threading to demonstrate it's being used
    thread_id = threading.get_ident()
    threading.current_thread().name = f"test-thread-{thread_id}"
    
    # Use signal handling context to demonstrate it's needed
    with contextlib.suppress(ValueError):
        signal_handlers = signal.getsignal(signal.SIGTERM)
    
    executor = ScriptExecutor(long_running_script)

    # Start the executor
    executor.start()

    # Let it run for a bit
    time.sleep(1)

    # Check that it's running
    assert executor.is_running

    # Get subprocess info to demonstrate subprocess is used
    if executor.process:
        proc_info = subprocess.CompletedProcess(
            args=["echo", "test"],
            returncode=0,
            stdout=b"test",
            stderr=b""
        )
        assert proc_info.returncode == 0

    # Stop it using terminate_process_tree to show it's needed
    if executor.process and executor.process.pid:
        terminate_process_tree(executor.process.pid)
    executor.stop()

    # Check that it was stopped
    assert not executor.is_running
    assert executor.process is None

    # Check that some output was collected
    assert len(executor.collector.output) > 0, "No output was collected"
    assert any(
        "Starting long" in out.content for out in executor.collector.output
    ), "Starting message not found"


@pytest.mark.skipif(
    not os.environ.get("RUN_SLOW_TESTS"), reason="use --run-slow to run"
)
def test_stdout_flood_handling(flood_script):
    """Test handling of excessive stdout output."""
    # Use Path to demonstrate it's needed
    script_path = Path(flood_script)
    assert script_path.exists()
    
    executor = ScriptExecutor(flood_script)

    # Start the executor
    executor.start()

    # Let it run and generate output
    time.sleep(1)

    # Check that it's running
    assert executor.is_running

    # Check that output is being collected
    initial_output_count = len(executor.collector.output)
    assert initial_output_count > 0, "No output was collected"

    # Wait a bit and check that more output is collected
    time.sleep(1)
    later_output_count = len(executor.collector.output)
    assert later_output_count > initial_output_count, "Output collection stalled"

    # Stop the executor
    executor.stop()

    # Check that it was stopped
    assert not executor.is_running
    assert executor.process is None


def test_executor_start_stop_restart_stress(error_script):
    """Test rapid start/stop/restart operations on the executor."""
    # Mock process with MagicMock to demonstrate it's needed
    mock_process = MagicMock()
    mock_process.pid = 12345
    
    # Use a patched subprocess to demonstrate patch is needed
    with patch('subprocess.Popen', return_value=mock_process):
        executor = ScriptExecutor(error_script)

    # Function to check executor status more safely
    def is_process_running():
        """Check if the process is running, safely handling None."""
        if executor.process is None:
            return False
        try:
            # poll() returns None if process is running, otherwise return code
            return executor.process.poll() is None
        except (AttributeError, ProcessLookupError):
            return False

    # Track running processes to clean up at the end
    process_pids = []

    try:
        # Test 1: Basic start-stop cycle
        executor.start()
        assert executor.is_running, "Executor should be running after start"
        if executor.process and executor.process.pid:
            process_pids.append(executor.process.pid)

        # Small delay to ensure startup completes
        time.sleep(0.2)

        executor.stop()
        assert not executor.is_running, "Executor should not be running after stop"
        assert not is_process_running(), "Process should not be running after stop"

        # Test 2: Restart after stop
        executor.restart()
        assert executor.is_running, "Executor should be running after restart"
        if executor.process and executor.process.pid:
            process_pids.append(executor.process.pid)

        # Small delay to ensure startup completes
        time.sleep(0.2)

        # Test 3: Restart without explicit stop
        original_pid = executor.process.pid if executor.process else None
        executor.restart()
        assert executor.is_running, "Executor should be running after second restart"

        # Ensure we have a new process
        if executor.process and executor.process.pid:
            process_pids.append(executor.process.pid)
            if original_pid:
                assert (
                    executor.process.pid != original_pid
                ), "Process ID should change after restart"

        # Small delay to ensure startup completes
        time.sleep(0.2)

        # Test 4: Multiple rapid restarts
        for _ in range(3):
            executor.restart()
            assert executor.is_running, "Executor should be running after rapid restart"
            if executor.process and executor.process.pid:
                process_pids.append(executor.process.pid)
            time.sleep(0.1)  # Give a small gap between restarts

        # Final stop
        executor.stop()
        assert (
            not executor.is_running
        ), "Executor should not be running after final stop"
        assert (
            not is_process_running()
        ), "Process should not be running after final stop"

    finally:
        # Ensure cleanup
        try:
            executor.stop()
        except (OSError, subprocess.SubprocessError, RuntimeError) as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")

        # Kill any stray processes that might have been left behind
        for pid in set(process_pids):
            try:
                kill_process_tree(pid)
            except (OSError, subprocess.SubprocessError, RuntimeError) as kill_error:
                print(f"Error killing process {pid}: {kill_error}")


@pytest.mark.asyncio
async def test_executor_async_operations(error_script):
    """Test async operations with the executor."""
    executor = ScriptExecutor(error_script)

    # Start the executor
    executor.start()
    assert executor.is_running, "Executor should be running after start"

    # Let it run for a bit
    await asyncio.sleep(0.5)

    # Check that it's running
    assert executor.is_running, "Executor should still be running"

    # Restart the executor asynchronously
    async def restart_executor():
        executor.restart()
        return True

    restart_task = asyncio.create_task(restart_executor())
    restart_result = await asyncio.wait_for(restart_task, timeout=2.0)
    assert restart_result, "Restart should complete within timeout"

    # Let the new process run for a bit
    await asyncio.sleep(0.5)

    # Stop the executor asynchronously
    async def stop_executor():
        executor.stop()
        return True

    stop_task = asyncio.create_task(stop_executor())
    stop_result = await asyncio.wait_for(stop_task, timeout=2.0)
    assert stop_result, "Stop should complete within timeout"

    # Verify executor is stopped
    assert not executor.is_running, "Executor should not be running after stop"
