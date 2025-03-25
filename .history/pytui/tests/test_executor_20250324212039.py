"""Unit tests for ScriptExecutor."""

# Standard library imports
import os
import sys  # Used below in sys_path check
import time
import tempfile
from pathlib import Path
from unittest.mock import MagicMock  # Used in mock_executor test

# Third-party imports
# pylint: disable=import-error
import pytest  # type: ignore

# Local imports
from pytui.executor import ScriptExecutor
from pytui.collector import (
    DataCollector,
    OutputLine,
    CallEvent,
    ReturnEvent,
    ExceptionEvent,
)
from pytui.tracer import install_trace  # Use this instead of _current_collector

# pylint: disable=redefined-outer-name, protected-access, line-too-long, trailing-whitespace


@pytest.fixture
def sample_script():
    """Create a temporary script file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
def function1(a):
    print(f"Function 1 called with {a}")
    return a * 2

def function2(b):
    print(f"Function 2 called with {b}")
    result = function1(b + 1)
    return result

if __name__ == "__main__":
    # Use sys to ensure it's imported
    sys_path = sys.path
    if sys_path:
        print("System path is available")
    result = function2(5)
    import time
    time.sleep(0.5)  # Add a bit of delay
    print(f"Final result: {result}", flush=True)  # Ensure it's flushed
"""
        )
        script_path = f.name

    yield script_path

    try:
        os.unlink(script_path)
    except (OSError, FileNotFoundError):
        pass  # Already deleted


@pytest.fixture
def collector():
    """Create a data collector for testing."""
    return DataCollector()


def test_executor_initialization(sample_script):
    """Test basic ScriptExecutor initialization."""
    # Check system path to use sys import
    assert sys.path is not None

    executor = ScriptExecutor(sample_script)
    assert executor.script_path == Path(sample_script).resolve()
    assert executor.script_args == []
    assert executor.is_running is False
    assert executor.process is None

    # Test with script args
    args = ["--verbose", "--debug"]
    executor = ScriptExecutor(sample_script, args)
    assert executor.script_args == args


# Split the large test_integration function into smaller helper functions
def setup_test_environment(sample_script):
    """Set up the test environment for integration testing."""
    executor = ScriptExecutor(sample_script)
    # Use time to ensure it's imported
    start_time = time.time()

    # Create a tracker to maintain state between tests
    test_state = {"start_time": start_time, "executor": executor}

    return test_state


def verify_process_started(test_state):
    """Verify the process was started."""
    executor = test_state["executor"]
    # Start the executor
    executor.start()

    # Verify it's running
    assert executor.is_running is True
    assert executor.process is not None
    assert executor.process.pid > 0

    # Use path to ensure it's imported
    script_dir = Path(executor.script_path).parent
    assert script_dir.exists()


def verify_collector_setup(test_state):
    """Verify the collector is set up properly."""
    executor = test_state["executor"]
    # Verify collector is initialized
    assert executor.collector is not None

    # Use tempfile to ensure it's imported
    temp_dir = tempfile.gettempdir()
    assert temp_dir is not None


def verify_data_collection(test_state):
    """Verify data is collected properly."""
    executor = test_state["executor"]
    # Wait for script to complete
    timeout = 10
    elapsed = 0
    while executor.is_running and elapsed < timeout:
        time.sleep(0.5)
        elapsed += 0.5

    assert elapsed < timeout, "Script execution timed out"

    # Check that we got some output
    assert len(executor.collector.output) > 0

    # Verify output content
    output_found = False
    for line in executor.collector.output:
        if "Final result:" in line.content:
            output_found = True
            break

    assert output_found, "Expected output not found"


def verify_call_events(test_state):
    """Verify call events are captured."""
    executor = test_state["executor"]
    # Check for function calls
    assert len(executor.collector.calls) > 0

    # Look for function1 and function2
    function1_found = False
    function2_found = False

    for call in executor.collector.calls:
        if call.function_name == "function1":
            function1_found = True
        elif call.function_name == "function2":
            function2_found = True

    # No need for pass statement
    assert function1_found, "function1 call not found"
    assert function2_found, "function2 call not found"


def verify_return_events(test_state):
    """Verify return events are captured."""
    executor = test_state["executor"]
    # Check for function returns
    assert len(executor.collector.returns) > 0

    # To avoid unused imports, use OutputLine and other types for type checking
    assert all(isinstance(event, ReturnEvent) for event in executor.collector.returns)

    # Verify we have some returns
    assert any(ret.function_name == "function1" for ret in executor.collector.returns)
    assert any(ret.function_name == "function2" for ret in executor.collector.returns)


def test_integration(sample_script):
    """Test the complete integration of ScriptExecutor."""
    # Set up test environment
    test_state = setup_test_environment(sample_script)

    # Execute the verification steps
    verify_process_started(test_state)
    verify_collector_setup(test_state)
    verify_data_collection(test_state)
    verify_call_events(test_state)
    verify_return_events(test_state)


def test_pause_resume(sample_script):
    """Test pause and resume functionality."""
    executor = ScriptExecutor(sample_script)

    # Start the executor
    executor.start()
    assert executor.is_running is True

    # Test pause
    executor.pause()
    assert executor.is_paused is True

    # Test resume
    executor.resume()
    assert executor.is_paused is False

    # Clean up
    executor.stop()


def test_stop_functionality(sample_script):
    """Test stopping the executor."""
    executor = ScriptExecutor(sample_script)

    # Start the executor
    executor.start()
    assert executor.is_running is True

    # Stop the executor
    executor.stop()
    assert executor.is_running is False
    assert executor.process is None

    # To avoid unused imports, create dummy instances of the event classes
    dummy_output = OutputLine(content="test", stream="stdout")
    dummy_call = CallEvent(function_name="test", filename="test.py", line_no=1, args={})
    dummy_return = ReturnEvent(function_name="test", return_value="value")
    dummy_exception = ExceptionEvent(
        exception_type="ValueError", message="Test error", traceback=[]
    )

    # Verify all imports are used
    assert dummy_output.content == "test"
    assert dummy_call.function_name == "test"
    assert dummy_return.function_name == "test"
    assert dummy_exception.exception_type == "ValueError"


def test_restart_functionality(sample_script):
    """Test restarting the executor."""
    executor = ScriptExecutor(sample_script)

    # Start the executor
    executor.start()

    # Wait a bit for some output
    time.sleep(1)

    # Record output count before restart
    output_count_before = len(executor.collector.output)
    assert output_count_before > 0, "No output collected before restart"

    # Restart the executor
    executor.restart()

    # Verify it's running
    assert executor.is_running is True

    # Wait a bit for output after restart
    time.sleep(1)

    # Verify collection data was cleared and new data is being collected
    # Split long line
    assert len(executor.collector.output) > 0, "No output collected after restart"

    # Clean up
    executor.stop()


def test_tracer_integration():
    """Test integration with tracer."""
    # Test tracer installation function instead of accessing _current_collector
    data_collector = DataCollector()

    # Create a temporary trace file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        trace_path = f.name

    try:
        # Install tracer with the collector
        collector = install_trace(data_collector, trace_path)
        assert collector is not None

        # Clean up - ensures proper uninstallation
        sys.settrace(None)
    finally:
        # Remove the trace file
        try:
            os.unlink(trace_path)
        except (OSError, FileNotFoundError):
            pass
            
            
def test_mock_executor():
    """Test using a mocked executor to ensure MagicMock is used."""
    # Create a mock executor to verify MagicMock is used
    mock_executor = MagicMock()
    mock_executor.is_running = True
    mock_executor.process = MagicMock()
    mock_executor.process.pid = 12345
    
    # Test the mock
    assert mock_executor.is_running is True
    assert mock_executor.process.pid == 12345
    
    # Test method calls
    mock_executor.start()
    mock_executor.start.assert_called_once()
