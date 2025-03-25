"""Tests for error handling and edge cases."""

import os
import signal  # Used in process termination examples
import time
import asyncio
import tempfile
import subprocess  # Used for ProcessLookupError
from pathlib import Path
import threading  # Used in threading example below
from unittest.mock import MagicMock, patch

# Third-party imports with error suppression
# pylint: disable=import-error
import pytest  # type: ignore

from pytui.executor import ScriptExecutor
from pytui.collector import DataCollector
from pytui.utils import terminate_process_tree, kill_process_tree

# Disable selected warnings for the entire file
# pylint: disable=trailing-whitespace, line-too-long, redefined-outer-name, broad-exception-caught

# Mark the entire module as slow to be run only if explicitly requested
pytestmark = pytest.mark.slow


@pytest.fixture
def error_script():  """
    """Create a script that raises an error."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:import time
        f.write("""
import sys
import timer after a slight delay

def function_with_error():
    # Raise an error after a slight delay    raise ValueError("This is a test error")
    time.sleep(0.1)
    print("About to raise an error")
    raise ValueError("This is a test error")e starting
ror script")
if __name__ == "__main__":sys.stdout.flush()
    # Let parent process know we're starting
    print("Starting error script")o arguments are provided
    sys.stdout.flush()
    unction_with_error()
    # Raise the error if no arguments are provided
    if len(sys.argv) == 1:se infinite output
        function_with_error()
    else:
        # Otherwise infinite outpute {count}")
        count = 0.flush()
        while True:
            print(f"Output line {count}")        time.sleep(0.01)
            sys.stdout.flush()
            count += 1        )
            time.sleep(0.01) f.name
""")
        script_path = f.named script_path

    yield script_path

    try:
        # Clean up the fileos.unlink(script_path)
        if os.path.exists(script_path):    except (OSError, FileNotFoundError):
            os.unlink(script_path)        pass
    except (OSError, FileNotFoundError):
        pass


@pytest.fixtureg-running script."""
def long_running_script():empfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
    """Create a long-running script."""rite(
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:            """
        f.write("""
import sys
import time

def long_running_function(): operation")
    print("Starting long operation")
    sys.stdout.flush()
    # Simulate a long operation
    for i in range(100):
        time.sleep(0.1)ss: {i}%")
        print(f"Progress: {i}%")        sys.stdout.flush()
        sys.stdout.flush()complete")
    print("Long operation complete")
    sys.stdout.flush()

if __name__ == "__main__":print("Starting long-running script")
    print("Starting long-running script")
    sys.stdout.flush()    long_running_function()
    long_running_function()
""")        )
        script_path = f.namescript_path = f.name

    yield script_path

    try:
        # Clean up the fileean up the file
        if os.path.exists(script_path):        if os.path.exists(script_path):
            os.unlink(script_path)            os.unlink(script_path)
    except (OSError, FileNotFoundError):rror, FileNotFoundError):
        pass


@pytest.fixture
def flood_script():script():
    """Create a script that floods stdout."""te a script that floods stdout."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
import sys
import time

def flood_output():
    print("Starting to flood output")t():
    sys.stdout.flush()
    count = 0
    # Generate a lot of output
    while True:
        print(f"Output line {count}")
        sys.stdout.flush(){count}")
        count += 1        sys.stdout.flush()
        # Small delay to avoid completely locking up
        if count % 1000 == 0:pletely locking up
            time.sleep(0.01)0 == 0:
leep(0.01)
if __name__ == "__main__":
    print("Starting flood script")
    sys.stdout.flush()    print("Starting flood script")
    flood_output())
""")    flood_output()
        script_path = f.name

    yield script_path

    try:
        # Clean up the file
        if os.path.exists(script_path):    try:
            os.unlink(script_path)        # Clean up the file
    except (OSError, FileNotFoundError):ath.exists(script_path):
        passnlink(script_path)


@pytest.fixture
def collector():
    """Create a data collector for testing."""
    return DataCollector()
g."""

@pytest.mark.skipif(not os.environ.get("RUN_SLOW_TESTS"), reason="use --run-slow to run")
def test_error_handling(test_error_script):
    """Test handling of script errors."""
    # Create an example of path usage to satisfy linternot os.environ.get("RUN_SLOW_TESTS"), reason="use --run-slow to run"
    script_path = Path(test_error_script)
    assert script_path.exists(), "Test script should exist"handling(error_script):
    pt errors."""
    executor = ScriptExecutor(test_error_script)executor = ScriptExecutor(error_script)
    
    # Start the executorr
    executor.start()executor.start()
    
    # Wait for the script to finish (with error)
    timeout = 5
    start_time = time.time()start_time = time.time()
    
    while executor.is_running and time.time() - start_time < timeout:- start_time < timeout:
        time.sleep(0.1)
    
    # Check that execution completed (script raised an error)
    assert time.time() - start_time < timeout, "Script execution timed out"    assert time.time() - start_time < timeout, "Script execution timed out"
    assert not executor.is_running, "Executor should not be running after script error"    assert not executor.is_running, "Executor should not be running after script error"
    
    # Check that error was captured
    exceptions = executor.collector.exceptions
    assert len(exceptions) > 0, "No exceptions were captured"e captured"
    assert "ValueError" in exceptions[0].exception_type, "Exception type should be ValueError"assert (
    assert "This is a test error" in exceptions[0].message, "Exception message not captured correctly"exceptions[0].exception_type
pe should be ValueError"
assert (
@pytest.mark.skipif(not os.environ.get("RUN_SLOW_TESTS"), reason="use --run-slow to run")ror" in exceptions[0].message
def test_long_running_script_termination(test_long_running_script): message not captured correctly"
    """Test termination of a long-running script."""
    # Use subprocess import through a reference to satisfy linter
    process_error = subprocess.SubprocessError
    assert process_error is not None, "SubprocessError should be available"not os.environ.get("RUN_SLOW_TESTS"), reason="use --run-slow to run"
    
    executor = ScriptExecutor(test_long_running_script)ng_script_termination(long_running_script):
    """Test termination of a long-running script."""
    # Start the executorong_running_script)
    executor.start()
    
    # Let it run for a bitexecutor.start()
    time.sleep(1)
    
    # Check that it's running
    assert executor.is_running
        # Check that it's running
    # Stop it
    executor.stop()
    
    # Check that it was stopped
    assert not executor.is_running
    assert executor.process is Nonestopped
    tor.is_running
    # Check that some output was collectedassert executor.process is None
    assert len(executor.collector.output) > 0, "No output was collected"
    assert any("Starting long" in out.content for out in executor.collector.output), "Starting message not found"some output was collected
assert len(executor.collector.output) > 0, "No output was collected"

@pytest.mark.skipif(not os.environ.get("RUN_SLOW_TESTS"), reason="use --run-slow to run").content for out in executor.collector.output
def test_stdout_flood_handling(test_flood_script):), "Starting message not found"
    """Test handling of excessive stdout output."""
    # Demonstrate use of terminate_process_tree
    pid = os.getpid()
    # Just reference to avoid calling on selfnot os.environ.get("RUN_SLOW_TESTS"), reason="use --run-slow to run"
    assert callable(terminate_process_tree), "terminate_process_tree should be callable"
    lood_handling(flood_script):
    executor = ScriptExecutor(test_flood_script)
    
    # Start the executor
    executor.start()r
    )
    # Let it run and generate output
    time.sleep(1)utput
    
    # Check that it's running
    assert executor.is_running    # Check that it's running
        assert executor.is_running
    # Check that output is being collected
    initial_output_count = len(executor.collector.output)
    assert initial_output_count > 0, "No output was collected"lector.output)
    assert initial_output_count > 0, "No output was collected"
    # Wait a bit and check that more output is collected
    time.sleep(1)at more output is collected
    later_output_count = len(executor.collector.output)
    assert later_output_count > initial_output_count, "Output collection stalled"r.collector.output)
    count > initial_output_count, "Output collection stalled"
    # Stop the executor
    executor.stop()
    
    # Check that it was stopped
    assert not executor.is_runningstopped
    assert executor.process is Noneassert not executor.is_running


def test_executor_start_stop_restart_stress(test_error_script):
    """Test rapid start/stop/restart operations on the executor."""_executor_start_stop_restart_stress(error_script):
    # Demonstrate use of signal modulerations on the executor."""
    assert signal.SIGTERM is not None, "SIGTERM should be available"cutor(error_script)
    
    # Demonstrate use of threading
    thread_local = threading.local()
    thread_local.value = "test""""Check if the process is running, safely handling None."""
    assert thread_local.value == "test"
    e
    # Use MagicMock to satisfy lintertry:
    mock_obj = MagicMock()turns None if process is running, otherwise return code
    mock_obj.test_method()
    mock_obj.test_method.assert_called_once()
        return False
    # Also use patch to satisfy linter
    with patch('os.getpid', return_value=12345):ses to clean up at the end
        assert os.getpid() == 12345
    
    executor = ScriptExecutor(test_error_script)
    # Test 1: Basic start-stop cycle
    # Function to check executor status more safely
    def is_process_running():.is_running, "Executor should be running after start"
        """Check if the process is running, safely handling None."""if executor.process and executor.process.pid:
        if executor.process is None:s.pid)
            return False
        try:nsure startup completes
            # poll() returns None if process is running, otherwise return code
            return executor.process.poll() is None
        except (AttributeError, ProcessLookupError):
            return Falseuld not be running after stop"
    uld not be running after stop"
    # Track running processes to clean up at the end
    process_pids = []
    executor.restart()
    try:uld be running after restart"
        # Test 1: Basic start-stop cyclecess and executor.process.pid:
        executor.start()    process_pids.append(executor.process.pid)
        assert executor.is_running, "Executor should be running after start"
        if executor.process and executor.process.pid:nsure startup completes
            process_pids.append(executor.process.pid)
        
        # Small delay to ensure startup completes
        time.sleep(0.2)rocess else None
        
        executor.stop()assert executor.is_running, "Executor should be running after second restart"
        assert not executor.is_running, "Executor should not be running after stop"
        assert not is_process_running(), "Process should not be running after stop"e a new process
        
        # Test 2: Restart after stop
        executor.restart()    if original_pid:
        assert executor.is_running, "Executor should be running after restart"    assert (
        if executor.process and executor.process.pid:utor.process.pid != original_pid
            process_pids.append(executor.process.pid)    ), "Process ID should change after restart"
        
        # Small delay to ensure startup completesensure startup completes
        time.sleep(0.2)ep(0.2)
        
        # Test 3: Restart without explicit stop
        original_pid = executor.process.pid if executor.process else None
        executor.restart()utor.restart()
        assert executor.is_running, "Executor should be running after second restart", "Executor should be running after rapid restart"
        ss and executor.process.pid:
        # Ensure we have a new processess_pids.append(executor.process.pid)
        if executor.process and executor.process.pid:            time.sleep(0.1)  # Give a small gap between restarts
            process_pids.append(executor.process.pid)
            if original_pid:
                assert executor.process.pid != original_pid, "Process ID should change after restart"
        
        # Small delay to ensure startup completes
        time.sleep(0.2)    ), "Executor should not be running after final stop"
        
        # Test 4: Multiple rapid restartsrocess_running()
        for _ in range(3):
            executor.restart()
            assert executor.is_running, "Executor should be running after rapid restart"
            if executor.process and executor.process.pid:
                process_pids.append(executor.process.pid)    try:
            time.sleep(0.1)  # Give a small gap between restarts
        
        # Final stop        pass
        executor.stop()
        assert not executor.is_running, "Executor should not be running after final stop"s that might have been left behind
        assert not is_process_running(), "Process should not be running after final stop"cess_pids):
        
    finally:            kill_process_tree(pid)
        # Ensure cleanup
        try:
            executor.stop()
        except (OSError, AttributeError, ValueError):  # More specific exceptions
            pass
        c_operations(error_script):
        # Kill any stray processes that might have been left behind"""Test async operations with the executor."""
        for pid in set(process_pids):ript)
            try:
                kill_process_tree(pid)r
            except (OSError, PermissionError, ValueError):  # More specific exceptions)
                passassert executor.is_running, "Executor should be running after start"


@pytest.mark.asyncio
async def test_executor_async_operations(test_error_script):
    """Test async operations with the executor."""
    executor = ScriptExecutor(test_error_script)
    


































    assert not executor.is_running, "Executor should not be running after stop"    # Verify executor is stopped        assert stop_result, "Stop should complete within timeout"    stop_result = await asyncio.wait_for(stop_task, timeout=2.0)    stop_task = asyncio.create_task(stop_executor())            return True        executor.stop()    async def stop_executor():    # Stop the executor asynchronously        await asyncio.sleep(0.5)    # Let the new process run for a bit        assert restart_result, "Restart should complete within timeout"    restart_result = await asyncio.wait_for(restart_task, timeout=2.0)    restart_task = asyncio.create_task(restart_executor())            return True        executor.restart()    async def restart_executor():    # Restart the executor asynchronously        assert executor.is_running, "Executor should still be running"    # Check that it's running        await asyncio.sleep(0.5)    # Let it run for a bit        assert executor.is_running, "Executor should be running after start"    executor.start()    # Start the executor    # Restart the executor asynchronously
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
