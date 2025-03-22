"""Tests for the script executor component."""

import os
import sys
import tempfile
import time
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from pytui.executor import ScriptExecutor

@pytest.fixture
def sample_script():
    """Create a temporary Python script for testing."""
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
        f.write("""
print("Hello stdout")
import sys
print("Hello stderr", file=sys.stderr)

def function1(arg1):
    print(f"Function with {arg1}")
    return arg1 * 2

result = function1(21)
print(f"Result: {result}")

try:
    raise ValueError("Test exception")
except ValueError:
    print("Caught exception")
""")
    yield Path(f.name)
    # Clean up the temporary file
    os.unlink(f.name)

def test_init():
    """Test executor initialization."""
    executor = ScriptExecutor("test.py", ["arg1", "arg2"])
    assert executor.script_path == Path("test.py").resolve()
    assert executor.script_args == ["arg1", "arg2"]
    assert not executor.is_running
    assert not executor.is_paused

def test_script_not_found():
    """Test handling of non-existent script."""
    executor = ScriptExecutor("nonexistent.py")
    with pytest.raises(FileNotFoundError):
        executor.start()

@pytest.mark.slow  # Can be run with --run-slow flag
def test_execution(sample_script):
    """Test basic script execution and output collection.
    
    This is a slow test that executes a real Python script and verifies:
    - stdout/stderr capture
    - function call tracing
    - execution completion
    
    Run with: pytest --run-slow
    """
    executor = ScriptExecutor(sample_script)
    
    # Start execution
    executor.start()
    
    # Give it time to execute
    time.sleep(1)
    
    # Check that output was collected
    assert any("Hello stdout" in line.content for line in executor.collector.output)
    assert any("Hello stderr" in line.content for line in executor.collector.output)
    assert any("Result: 42" in line.content for line in executor.collector.output)
    
    # Should have collected function calls
    assert any(call.function_name == "function1" for call in executor.collector.calls)

def test_stop():
    """Test stopping the execution."""
    executor = ScriptExecutor("test.py")
    
    # Mock the subprocess.Popen
    mock_process = MagicMock()
    executor.process = mock_process
    executor.is_running = True
    
    # Stop the execution
    executor.stop()
    
    # Check that process was terminated
    mock_process.terminate.assert_called_once()
    assert not executor.is_running

def test_pause_resume():
    """Test pausing and resuming execution updates."""
    executor = ScriptExecutor("test.py")
    
    assert not executor.is_paused
    
    executor.pause()
    assert executor.is_paused
    
    executor.resume()
    assert not executor.is_paused

@pytest.mark.slow  # Can be run with --run-slow flag
def test_restart(sample_script):
    """Test restarting execution of a script.
    
    This is a slow test that verifies the executor can:
    - Start execution
    - Collect initial output
    - Successfully restart
    - Collect new output after restart
    
    Run with: pytest --run-slow
    """
    executor = ScriptExecutor(sample_script)
    
    # Start execution
    executor.start()
    
    # Give it time to execute
    time.sleep(1)
    
    # Verify initial execution
    assert any("Hello stdout" in line.content for line in executor.collector.output)
    
    # Save output count
    output_count = len(executor.collector.output)
    
    # Restart execution
    executor.restart()
    
    # Give it time to execute again
    time.sleep(1)
    
    # Should have cleared previous output and executed again
    assert len(executor.collector.output) <= output_count * 2
    assert len(executor.collector.output) > 0
