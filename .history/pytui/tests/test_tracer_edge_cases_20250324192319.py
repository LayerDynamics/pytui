# pylint: disable=redefined-outer-name
import os
import tempfile
import time
import threading
import asyncio

import pytest
from pathlib import Path

from pytui.tracer import install_trace, _should_skip_file
from pytui.collector import DataCollector


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


@pytest.mark.slow
@pytest.mark.asyncio
async def test_complex_arguments_tracing(complex_args_script):
    """Test tracing of functions with complex arguments in a non-blocking manner."""
    from pytui.executor import (
        ScriptExecutor,
    )  # import inside test to prevent toplevel warnings

    executor = None
    try:
        executor = ScriptExecutor(complex_args_script)
        await asyncio.to_thread(executor.start)
        max_wait = 10
        start_time = time.time()
        completed = False
        while time.time() - start_time < max_wait and not completed:
            if any(
                "Result: Return value" in line.content
                for line in executor.collector.output
            ):
                completed = True
            await asyncio.sleep(0.1)
        assert completed, "Script did not complete in the expected time"
        calls = [
            call
            for call in executor.collector.calls
            if call.function_name == "function_with_complex_args"
        ]
        assert calls, "Complex function call was not traced"
        call0 = calls[0]
        for key in ["a_string", "a_list", "a_dict", "an_object"]:
            assert key in call0.args, f"{key} argument not captured"
        assert "..." in call0.args.get("a_list", ""), "Large list should be truncated"
        returns = [
            ret
            for ret in executor.collector.returns
            if ret.function_name == "function_with_complex_args"
        ]
        assert returns, "Complex function return was not traced"
        assert (
            "'Return value'" in returns[0].return_value
        ), "Return value not captured correctly"
    finally:
        if executor:
            await asyncio.to_thread(executor.stop)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_exception_tracing(exception_script):
    """Test tracing of various exception patterns in a non-blocking manner."""
    from pytui.executor import ScriptExecutor

    executor = None
    try:
        executor = ScriptExecutor(exception_script)
        await asyncio.to_thread(executor.start)
        max_wait = 10
        start_time = time.time()
        completed = False
        while time.time() - start_time < max_wait and not completed:
            if any(
                "Caught unhandled exception" in line.content
                for line in executor.collector.output
            ):
                completed = True
            await asyncio.sleep(0.1)
        assert completed, "Script did not complete as expected"
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
    finally:
        if executor:
            await asyncio.to_thread(executor.stop)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_module_import_tracing(module_import_script):
    """Test tracing of module imports in a non-blocking manner."""
    from pytui.executor import ScriptExecutor

    executor = None
    try:
        executor = ScriptExecutor(module_import_script)
        await asyncio.to_thread(executor.start)
        max_wait = 10
        start_time = time.time()
        completed = False
        while time.time() - start_time < max_wait and not completed:
            if any(
                "Result: 3.14" in line.content for line in executor.collector.output
            ):
                completed = True
            await asyncio.sleep(0.1)
        assert completed, "Import tracing script did not complete in time"
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
    finally:
        if executor:
            await asyncio.to_thread(executor.stop)


def test_skip_file_patterns():
    """Test that file path patterns are correctly skipped."""
    # Internal modules should be skipped.
    assert _should_skip_file("/path/to/pytui/tracer.py")
    assert _should_skip_file("/path/to/pytui/collector.py")
    # Other modules and user scripts should not.
    assert not _should_skip_file("/path/to/pytui/executor.py")
    assert not _should_skip_file("/path/to/pytui/ui/app.py")
    assert not _should_skip_file("/user/scripts/test.py")
    assert not _should_skip_file("/path/with/pytui_in_name/script.py")


def test_concurrent_tracing():
    """Test tracing in a multithreaded environment."""
    collector = DataCollector()
    tracer = install_trace(collector)
    assert tracer is collector, "Tracer should be set to provided collector"

    def traced_function(tid):
        collector.add_output(f"Thread {tid} running", "stdout")
        return tid * 2

    threads = [threading.Thread(target=traced_function, args=(i,)) for i in range(5)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    outputs = [
        line
        for line in collector.output
        if line.content.startswith("Thread ") and "running" in line.content
    ]
    assert len(outputs) == 5, "Not all thread outputs were captured"
