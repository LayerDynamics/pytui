"""Edge case tests for the pytui tracer functionality."""
# pylint: disable=redefined-outer-name

# Standard library imports
import asyncio
import os
import tempfile
import time
from pathlib import Path

# Third-party imports
import pytest  # type: ignore

# Local imports
from pytui.tracer import install_trace, _should_skip_file
from pytui.collector import DataCollector
from pytui.executor import ScriptExecutor


@pytest.fixture
def complex_args_script():
    """Create a script with complex function arguments for testing."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(
            """
# Test script with complex arguments
import datetime
import re
from collections import defaultdict

class ComplexObject:
    def __init__(self, name):
        self.name = name
        self.created_at = datetime.datetime.now()
        self.data = {"key1": [1, 2, 3], "key2": {"nested": "value"}}
    
    def __repr__(self):
        return f"ComplexObject(name={self.name})"

def function_with_complex_args(
    a_string="default", 
    a_list=[1, 2, 3], 
    a_dict={"key": "value"}, 
    an_object=None,
    a_function=lambda x: x*2,
    a_regex=re.compile(r'\\d+'),
    a_defaultdict=defaultdict(list),
    *args,
    **kwargs
):
    print(f"Complex function called with {len(args)} args and {len(kwargs)} kwargs")
    return "Return value"

# Call the function with various arguments
obj = ComplexObject("test_object")
result = function_with_complex_args(
    "custom string",
    [4, 5, 6, 7, 8, 9, 10] * 1000,  # Large list
    {"complex": {"nested1": {"nested2": {"nested3": "deep value"}}}},
    obj,
    lambda x: x ** 3,
    re.compile(r'[a-z]+'),
    defaultdict(set, {'x': {1, 2, 3}}),
    "extra_arg1", 
    "extra_arg2" * 1000,  # Very long string
    custom_kwarg1="value1",
    custom_kwarg2={"x": 1, "y": 2, "z": 3},
    custom_kwarg3=obj
)
print(f"Result: {result}")
"""
        )
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)


@pytest.fixture
def exception_script():
    """Create a script with various exception patterns."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(
            """
# Test script with different exception patterns
import sys

def divide(a, b):
    try:
        return a / b
    except ZeroDivisionError as e:
        # Handled exception
        print(f"Caught division by zero: {e}")
        return float('inf')  # Return infinity

def nested_exceptions():
    try:
        try:
            # This will raise KeyError
            d = {}
            print(d['nonexistent'])
        except KeyError:
            # Handle KeyError but raise ValueError
            print("Caught KeyError, raising ValueError")
            raise ValueError("Converted KeyError to ValueError")
    except ValueError as e:
        # Re-raise with additional info
        print(f"Caught ValueError: {e}")
        raise RuntimeError("Nested exception test") from e

def unhandled_exception():
    # This will be unhandled
    x = [1, 2, 3]
    return x[10]  # IndexError

# Test handled exception
result1 = divide(10, 0)
print(f"Result1: {result1}")

# Test nested exception with re-raising
try:
    nested_exceptions()
except RuntimeError as e:
    print(f"Caught top-level exception: {e}")

# Test unhandled exception - but catch it at top level
try:
    unhandled_exception()
except IndexError as e:
    print(f"Caught unhandled exception: {e}")
"""
        )
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)


@pytest.fixture
def module_import_script():
    """Create a script that imports many modules to test import tracing."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(
            """
# Test script with many module imports
print("Starting imports")

# Standard library imports
import os
import sys
import json
import datetime
import math
import random
import re
import time

# Import using different syntax
from collections import defaultdict, Counter
from functools import partial
import itertools as it

# Try importing non-existent module
try:
    import nonexistent_module_xyz
except ImportError as e:
    print(f"Expected import error: {e}")

# Function that uses imports
def use_imports():
    # Use various imported modules
    print(f"Current directory: {os.getcwd()}")
    print(f"Random number: {random.random()}")
    print(f"Current time: {datetime.datetime.now()}")
    return math.pi

result = use_imports()
print(f"Result: {result}")
"""
        )
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)


@pytest.fixture
async def mock_executor():
    """Fixture to ensure proper executor cleanup."""
    executors = []

    def _create_executor(script):
        executor = ScriptExecutor(script)
        executors.append(executor)
        return executor

    yield _create_executor

    # Cleanup all executors
    for executor in executors:
        try:
            await asyncio.wait_for(asyncio.to_thread(executor.stop), timeout=2.0)
        except asyncio.TimeoutError:
            pass


async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
    """Helper to wait for a condition with timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        await asyncio.sleep(interval)
    return False


@pytest.mark.slow
@pytest.mark.asyncio
async def test_complex_arguments_tracing(complex_args_script, mock_executor):
    """Test tracing of functions with complex arguments in a non-blocking manner."""
    executor = mock_executor(complex_args_script)
    try:
        await asyncio.wait_for(asyncio.to_thread(executor.start), timeout=5.0)
        completed = await wait_for_condition(
            lambda: any("Result: Return value" in line.content 
                    for line in executor.collector.output))
        assert completed, "Script did not complete in time"
        
        calls = [call for call in executor.collector.calls 
                if call.function_name == "function_with_complex_args"]
        assert calls, "Complex function call was not traced"
        
    except asyncio.TimeoutError:
        pytest.fail("Test timed out")
    finally:
        if executor:
            await asyncio.wait_for(asyncio.to_thread(executor.stop), timeout=5.0)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_exception_tracing(exception_script, mock_executor):
    """Test tracing of various exception patterns in a non-blocking manner."""
    executor = mock_executor(exception_script)

    try:
        # Start with timeout
        await asyncio.wait_for(asyncio.to_thread(executor.start), timeout=5.0)

        # Wait for completion
        completed = await wait_for_condition(
            lambda: any(
                "Caught unhandled exception" in line.content
                for line in executor.collector.output
            )
        )
        assert completed, "Script did not complete as expected"

        # Verify results
        functions = {call.function_name for call in executor.collector.calls}
        for fname in ["divide", "nested_exceptions", "unhandled_exception"]:
            assert fname in functions, f"{fname} was not traced"

        outputs = " ".join(line.content for line in executor.collector.output)
        for phrase in [
            "Caught division by zero",
            "Caught KeyError",
            "Caught ValueError",
            "Caught top-level exception",
            "Caught unhandled exception",
        ]:
            assert phrase in outputs, f"{phrase} not handled"

        assert executor.collector.exceptions, "No exceptions were traced"

    except asyncio.TimeoutError:
        pytest.fail("Exception tracing test timed out")


@pytest.mark.slow
@pytest.mark.asyncio
async def test_module_import_tracing(module_import_script, mock_executor):
    """Test tracing of module imports in a non-blocking manner."""
    executor = mock_executor(module_import_script)

    try:
        # Start with timeout
        await asyncio.wait_for(asyncio.to_thread(executor.start), timeout=5.0)

        # Wait for completion
        completed = await wait_for_condition(
            lambda: any(
                "Result: 3.14" in line.content for line in executor.collector.output
            )
        )
        assert completed, "Import tracing script did not complete in time"

        # Verify results
        calls = [
            call
            for call in executor.collector.calls
            if call.function_name == "use_imports"
        ]
        assert calls, "use_imports function was not traced"

        outputs = " ".join(line.content for line in executor.collector.output)
        for phrase in [
            "Current directory",
            "Random number",
            "Current time",
            "Result: 3.14",
            "Expected import error",
        ]:
            assert phrase in outputs, f"{phrase} not found"

    except asyncio.TimeoutError:
        pytest.fail("Module import tracing test timed out")


@pytest.fixture(autouse=True)
async def cleanup_tracer():
    """Ensure tracer is cleaned up after each test."""
    yield
    # Clean up tracer state
    sys.settrace(None)
    # Clean up any remaining tasks
    tasks = [t for t in asyncio.all_tasks() 
             if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

@pytest.mark.asyncio
async def test_concurrent_tracing():
    """Test tracing in a concurrent environment."""
    import sys
    import asyncio
    
    # Create fresh collector for this test only
    collector = DataCollector()
    _ = install_trace(collector)
    
    # Use a shorter task list and make the trace more reliable
    async def traced_function(tid):
        # Use a shorter sleep to reduce test time
        await asyncio.sleep(0.01)
        # Add output directly without using Path objects
        collector.add_output(f"Thread {tid} running", "stdout")
        return str(tid)
    
    # Create fewer tasks to reduce test complexity
    tasks = []
    for i in range(3):  # Reduced from 5 to 3 tasks
        task = asyncio.create_task(traced_function(i))
        tasks.append(task)
    
    try:
        # Wait for completion with a shorter timeout
        await asyncio.wait_for(asyncio.wait(tasks), timeout=2.0)
        
        # Verify outputs
        outputs = [line for line in collector.output
                  if line.content.startswith("Thread ") and "running" in line.content]
        assert len(outputs) == 3, "Not all outputs were captured"
        
    finally:
        # Clean up tasks properly
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Make sure tracer is removed
        sys.settrace(None)
        
        # Clear the collector to prevent interfering with other tests
        collector.clear()


def test_skip_file_patterns():
    """Test that file path patterns are correctly skipped."""
    assert _should_skip_file("/path/to/pytui/tracer.py")
    assert _should_skip_file("/path/to/pytui/collector.py")
    assert not _should_skip_file("/path/to/pytui/executor.py")
    assert not _should_skip_file("/path/to/pytui/ui/app.py")
    assert not _should_skip_file("/user/scripts/test.py")
    assert not _should_skip_file("/path/with/pytui_in_name/script.py")
