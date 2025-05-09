"""Debug tests for the function tracing system."""

import os
import sys
import tempfile
import time
from pathlib import Path
import pytest

from pytui.executor import ScriptExecutor
from pytui.tracer import trace_function, _collector
from pytui.collector import get_collector

@pytest.fixture
def minimal_script():
    """Create a minimal script with a simple function to trace."""
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
        f.write("""
# Simple script with a function to trace
def test_function(x):
    print(f"Processing {x}")
    return x * 2

# Call the function to ensure it's executed
result = test_function(21)
print(f"Result: {result}")
""")
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)

@pytest.mark.slow
def test_debug_function_tracing(minimal_script):
    """Debug test for function tracing in the executor."""
    executor = None
    try:
        executor = ScriptExecutor(minimal_script)
        
        # Add more debug output before starting
        print("\nDebug: Starting execution with tracing")
        print(f"Debug: Script path: {minimal_script}")
        
        executor.start()
        
        # Wait for execution to complete 
        max_wait = 5
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if any("Result: 42" in line.content for line in executor.collector.output):
                break
            time.sleep(0.1)
        
        # Output detailed debugging information
        print(f"Debug: Execution completed, elapsed: {time.time() - start_time:.2f}s")
        print(f"Debug: Output lines: {len(executor.collector.output)}")
        for i, line in enumerate(executor.collector.output):
            print(f"  Output[{i}]: {line.stream} - {line.content}")
        
        print(f"Debug: Function calls: {len(executor.collector.calls)}")
        for i, call in enumerate(executor.collector.calls):
            print(f"  Call[{i}]: {call.function_name} at {call.filename}:{call.line_no}")
            print(f"    Args: {call.args}")
            
        # Verify outputs
        outputs = [line.content for line in executor.collector.output]
        assert "Processing 21" in " ".join(outputs), "Function was not executed"
        assert "Result: 42" in " ".join(outputs), "Expected result not found"
        
        # Verify function call tracing
        assert len(executor.collector.calls) > 0, "No function calls were traced"
        assert any(call.function_name == "test_function" for call in executor.collector.calls), \
               "Expected function call 'test_function' not traced"
    finally:
        if executor:
            executor.stop()
            if executor.process and executor.process.poll() is None:
                executor.process.terminate()
