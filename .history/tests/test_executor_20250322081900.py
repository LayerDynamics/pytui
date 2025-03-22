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

@pytest.mark.slow
def test_execution(sample_script):
    """Test basic script execution and output collection."""
    executor = None
    try:
        executor = ScriptExecutor(sample_script)
        executor.start()
        
        # Increase wait time and add verification loop
        max_wait = 5  # Maximum seconds to wait
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if any("Hello stdout" in line.content for line in executor.collector.output):
                break
            time.sleep(0.1)
        
        # Verify output
        outputs = [line.content for line in executor.collector.output]
        assert "Hello stdout" in " ".join(outputs), f"Expected output not found in: {outputs}"
        
        # Verify other outputs
        assert any("Hello stderr" in line.content for line in executor.collector.output)
        assert any("Result: 42" in line.content for line in executor.collector.output)
        assert any(call.function_name == "function1" for call in executor.collector.calls)
    finally:
        # Ensure cleanup
        if executor:
            executor.stop()
            if executor.process:
                executor.process.wait(timeout=1)

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

@pytest.mark.slow
def test_restart(sample_script):
    """Test restarting execution of a script."""
    executor = None
    try:
        executor = ScriptExecutor(sample_script)
        executor.start()
        
        # Wait for initial output with verification loop
        max_wait = 5
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if any("Hello stdout" in line.content for line in executor.collector.output):
                break
            time.sleep(0.1)
        
        # Verify initial execution
        initial_outputs = [line.content for line in executor.collector.output]
        assert "Hello stdout" in " ".join(initial_outputs), f"Initial output not found in: {initial_outputs}"
        
        # Save output count and restart
        output_count = len(executor.collector.output)
        executor.restart()
        
        # Wait for new output
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if len(executor.collector.output) > 0:
                break
            time.sleep(0.1)
        
        # Verify new execution
        assert len(executor.collector.output) > 0, "No output after restart"
        new_outputs = [line.content for line in executor.collector.output]
        assert "Hello stdout" in " ".join(new_outputs), f"Output after restart not found in: {new_outputs}"
    finally:
        # Ensure cleanup
        if executor:
            executor.stop()
            if executor.process:
                executor.process.wait(timeout=1)
