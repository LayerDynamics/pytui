"""Tests for the data collector component."""

import asyncio
import pytest
from pytui.collector import DataCollector

@pytest.fixture
def collector():
    """Create a test collector instance."""
    return DataCollector()

def test_add_output(collector):
    """Test adding output to the collector."""
    collector.add_output("Test output", "stdout")
    assert len(collector.output) == 1
    assert collector.output[0].content == "Test output"
    assert collector.output[0].stream == "stdout"

def test_add_call(collector):
    """Test adding function calls to the collector."""
    collector.add_call("test_func", "test.py", 10, {"arg1": "value1"})
    assert len(collector.calls) == 1
    assert collector.calls[0].function_name == "test_func"
    assert collector.calls[0].filename == "test.py"
    assert collector.calls[0].line_no == 10
    assert collector.calls[0].args == {"arg1": "value1"}
    assert collector.calls[0].call_id == 1
    assert collector.calls[0].parent_id is None

def test_add_nested_call(collector):
    """Test adding nested function calls with proper parent IDs."""
    collector.add_call("parent_func", "test.py", 10, {})
    collector.add_call("child_func", "test.py", 20, {})
    
    assert len(collector.calls) == 2
    assert collector.calls[0].parent_id is None
    assert collector.calls[1].parent_id == 1
    assert collector.call_stack == [1, 2]

def test_add_return(collector):
    """Test adding return events."""
    collector.add_call("test_func", "test.py", 10, {})
    collector.add_return("test_func", "return_value")
    
    assert len(collector.returns) == 1
    assert collector.returns[0].function_name == "test_func"
    assert collector.returns[0].return_value == "return_value"
    assert collector.returns[0].call_id == 1
    assert collector.call_stack == []

def test_add_exception(collector):
    """Test adding exception events."""
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        collector.add_exception(e)
    
    assert len(collector.exceptions) == 1
    assert collector.exceptions[0].exception_type == "ValueError"
    assert collector.exceptions[0].message == "Test exception"
    assert len(collector.exceptions[0].traceback) > 0

def test_clear(collector):
    """Test clearing all collector data."""
    collector.add_output("Test output", "stdout")
    collector.add_call("test_func", "test.py", 10, {})
    collector.add_return("test_func", "return_value")
    
    assert len(collector.output) > 0
    assert len(collector.calls) > 0
    assert len(collector.returns) > 0
    
    collector.clear()
    
    assert len(collector.output) == 0
    assert len(collector.calls) == 0
    assert len(collector.returns) == 0
    assert len(collector.call_stack) == 0
    assert collector.next_call_id == 1

@pytest.mark.asyncio
async def test_event_queue(collector):
    """Test the event queue."""
    # Add events
    collector.add_output("Test output", "stdout")
    collector.add_call("test_func", "test.py", 10, {})
    
    # Get events from queue
    event_type1, event1 = await collector.get_event()
    event_type2, event2 = await collector.get_event()
    
    # Check event types and content
    assert event_type1 == "output"
    assert event1.content == "Test output"
    assert event_type2 == "call"
    assert event2.function_name == "test_func"
