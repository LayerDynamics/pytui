"""Tests for edge cases in the tracer functionality."""

# Standard library imports
import os
import tempfile
import time
import threading
import asyncio
from pathlib import Path

# Third-party imports
import pytest  # type: ignore

# Local imports (unused imports removed)
from pytui.tracer import install_trace, _should_skip_file
from pytui.collector import DataCollector

@pytest.fixture
def complex_args_script():
    """Create a script with complex function arguments for testing."""
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
        f.write("""
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
""")
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)

@pytest.fixture
def exception_script():
    """Create a script with various exception patterns."""
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
        f.write("""
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
""")
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)

@pytest.fixture
def module_import_script():
    """Create a script that imports many modules to test import tracing."""
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
        f.write("""
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
""")
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)

@pytest.mark.slow
@pytest.mark.asyncio
async def test_complex_arguments_tracing(complex_args_script):
    """Test tracing of functions with complex arguments in a non blocking manner."""
    from pytui.executor import ScriptExecutor
    executor = None
    try:
        executor = ScriptExecutor(complex_args_script)
        await asyncio.to_thread(executor.start)
        
        max_wait = 10
        start_time = time.time()
        completed = False
        while time.time() - start_time < max_wait and not completed:
            if any("Result: Return value" in line.content for line in executor.collector.output):
                completed = True
            await asyncio.sleep(0.1)
            
        assert completed, "Script did not complete in the expected time"
        
        complex_func_calls = [
            call for call in executor.collector.calls 
            if call.function_name == "function_with_complex_args"
        ]
        assert len(complex_func_calls) > 0, "Complex function call was not traced"
        complex_call = complex_func_calls[0]
        assert "a_string" in complex_call.args, "String argument not captured"
        assert "a_list" in complex_call.args, "List argument not captured"
        assert "a_dict" in complex_call.args, "Dict argument not captured"
        assert "an_object" in complex_call.args, "Object argument not captured"
        assert "..." in complex_call.args.get("a_list", ""), "Large list should be truncated"
        
        complex_func_returns = [
            ret for ret in executor.collector.returns 
            if ret.function_name == "function_with_complex_args"
        ]
        assert len(complex_func_returns) > 0, "Complex function return was not traced"
        assert "'Return value'" in complex_func_returns[0].return_value, "Return value not captured correctly"
    finally:
        if executor:
            await asyncio.to_thread(executor.stop)

@pytest.mark.slow
@pytest.mark.asyncio
async def test_exception_tracing(exception_script):
    """Test tracing of various exception patterns in a non blocking manner."""
    from pytui.executor import ScriptExecutor
    executor = None
    try:
        executor = ScriptExecutor(exception_script)
        await asyncio.to_thread(executor.start)
        
        max_wait = 10
        start_time = time.time()
        completed = False
        while time.time() - start_time < max_wait and not completed:
            if any("Caught unhandled exception" in line.content for line in executor.collector.output):
                completed = True
            await asyncio.sleep(0.1)
            
        assert completed, "Script did not complete in the expected time"
        
        function_names = {call.function_name for call in executor.collector.calls}
        assert "divide" in function_names, "divide function was not traced"
        assert "nested_exceptions" in function_names, "nested_exceptions function was not traced"
        assert "unhandled_exception" in function_names, "unhandled_exception function was not traced"
        
        outputs = " ".join([line.content for line in executor.collector.output])
        assert "Caught division by zero" in outputs, "ZeroDivisionError not handled"
        assert "Caught KeyError" in outputs, "KeyError not handled"
        assert "Caught ValueError" in outputs, "ValueError not handled"
        assert "Caught top-level exception" in outputs, "RuntimeError not handled"
        assert "Caught unhandled exception" in outputs, "IndexError not handled"
        
        assert len(executor.collector.exceptions) > 0, "No exceptions were traced"
    finally:
        if executor:
            await asyncio.to_thread(executor.stop)

@pytest.mark.slow
@pytest.mark.asyncio
async def test_module_import_tracing(module_import_script):
    """Test tracing of module imports in a non blocking manner."""
    from pytui.executor import ScriptExecutor
    executor = None
    try:
        executor = ScriptExecutor(module_import_script)
        await asyncio.to_thread(executor.start)
        
        max_wait = 10
        start_time = time.time()
        completed = False
        while time.time() - start_time < max_wait and not completed:
            if any("Result: 3.14" in line.content for line in executor.collector.output):
                completed = True
            await asyncio.sleep(0.1)
            
        assert completed, "Script did not complete in the expected time"
        
        function_calls = [call for call in executor.collector.calls if call.function_name == "use_imports"]
        assert len(function_calls) > 0, "use_imports function was not traced"
        
        outputs = " ".join([line.content for line in executor.collector.output])
        assert "Current directory" in outputs, "os.getcwd() result not found"
        assert "Random number" in outputs, "random.random() result not found"
        assert "Current time" in outputs, "datetime.datetime.now() result not found"
        assert "Result: 3.14" in outputs, "math.pi result not found"
        assert "Expected import error" in outputs, "Import error handling not found"
    finally:
        if executor:
            await asyncio.to_thread(executor.stop)

def test_skip_file_patterns():
    """Test file path patterns that should be skipped."""
    # Internal module paths should be skipped
    assert _should_skip_file("/path/to/pytui/tracer.py") is True
    assert _should_skip_file("/path/to/pytui/collector.py") is True
    
    # Other pytui modules shouldn't be skipped
    assert _should_skip_file("/path/to/pytui/executor.py") is False
    assert _should_skip_file("/path/to/pytui/ui/app.py") is False
    
    # User scripts shouldn't be skipped
    assert _should_skip_file("/user/scripts/test.py") is False
    assert _should_skip_file("/path/with/pytui_in_name/script.py") is False

def test_concurrent_tracing():
    """Test tracing in multithreaded environment."""
    collector = DataCollector()
    
    # Install trace for this thread
    tracer_collector = install_trace(collector)
    assert tracer_collector is collector, "Tracer should use the provided collector"
    
    # Function to run in threads with tracing
    def traced_function(thread_id):
        # This will be traced
        collector.add_output(f"Thread {thread_id} running", "stdout")
        return thread_id * 2
    
    # Create and run threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=traced_function, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify outputs from all threads
    thread_outputs = [
        line for line in collector.output 
        if line.content.startswith("Thread ") and "running" in line.content
    ]
    assert len(thread_outputs) == 5, "Not all thread outputs were captured"
