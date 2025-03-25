"""Complex integration tests for pytui components."""

import os
import sys
import tempfile
import time
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from pytui.executor import ScriptExecutor
from pytui.ui.app import PyTUIApp
from pytui.collector import DataCollector, OutputLine, CallEvent, ExceptionEvent

@pytest.fixture
def debug_app():
    """Create a PyTUI app with debug instrumentation."""
    app = PyTUIApp()
    
    # Add event tracking for test validation
    app.events = []
    app._original_process_events = app.process_events
    
    async def tracked_process_events():
        """Wrapper for process_events that tracks events."""
        app.events.append("process_events_started")
        try:
            await app._original_process_events()
        except Exception as e:
            app.events.append(f"process_events_error: {e}")
        finally:
            app.events.append("process_events_ended")
    
    app.process_events = tracked_process_events
    
    # Add mock panels that record what they receive
    app.output_panel = MagicMock()
    app.output_panel.add_output = AsyncMock()
    app.output_panel.add_message = AsyncMock()
    app.output_panel.add_exception = AsyncMock()
    app.output_panel.clear = AsyncMock()
    
    app.call_graph_panel = MagicMock()
    app.call_graph_panel.add_call = AsyncMock()
    app.call_graph_panel.add_return = AsyncMock()
    app.call_graph_panel.clear = AsyncMock()
    
    app.exception_panel = MagicMock()
    app.exception_panel.add_exception = AsyncMock()
    app.exception_panel.clear = AsyncMock()
    
    return app

@pytest.fixture
def controlled_executor():
    """Create a controlled executor that simulates script execution."""
    # Create mock executor
    executor = MagicMock()
    executor.is_running = True
    executor.is_paused = False
    
    # Create a collector that app's process_events will read from
    collector = DataCollector()
    executor.collector = collector
    
    # Add methods to control test flow
    def add_output(content, stream="stdout"):
        collector.add_output(content, stream)
    
    def add_call(func_name, filename, line_no, args=None):
        collector.add_call(func_name, filename, line_no, args or {})
    
    def add_return(func_name, return_value, call_id=None):
        collector.add_return(func_name, return_value, call_id)
    
    def add_exception(exc_type, message, traceback=None):
        exc = Exception(message)
        exc.__class__.__name__ = exc_type
        collector.add_exception(exc)
    
    def stop():
        executor.is_running = False
    
    def pause():
        executor.is_paused = True
    
    def resume():
        executor.is_paused = False
    
    # Attach control methods to the executor
    executor.add_output = add_output
    executor.add_call = add_call
    executor.add_return = add_return
    executor.add_exception = add_exception
    executor.control_stop = stop
    executor.control_pause = pause
    executor.control_resume = resume
    
    return executor

@pytest.mark.asyncio
async def test_app_executor_integration(debug_app, controlled_executor):
    """Test integration between app and executor with controlled event flow."""
    # Set executor on app
    debug_app.set_executor(controlled_executor)
    
    # Mount app
    await debug_app.on_mount()
    
    # Start event processing task
    events_task = asyncio.create_task(debug_app.process_events())
    
    # Wait a bit for task to initialize
    await asyncio.sleep(0.1)
    
    # Simulate script execution events
    controlled_executor.add_output("Script started")
    
    # Add a function call
    controlled_executor.add_call("test_function", "test.py", 42, {"arg1": "value1"})
    
    # Add a function return
    controlled_executor.add_return("test_function", "result_value")
    
    # Add an exception
    controlled_executor.add_exception("ValueError", "Test exception")
    
    # Add more output
    controlled_executor.add_output("Error encountered", "stderr")
    controlled_executor.add_output("Script continuing")
    
    # Wait for events to be processed
    await asyncio.sleep(0.2)
    
    # Check that panels received events
    debug_app.output_panel.add_output.assert_called()
    debug_app.call_graph_panel.add_call.assert_called()
    debug_app.call_graph_panel.add_return.assert_called()
    debug_app.exception_panel.add_exception.assert_called()
    
    # Test pause and resume functionality
    await debug_app.action_toggle_pause()
    assert controlled_executor.pause.called, "Executor pause not called"
    
    # Add more output while paused
    controlled_executor.add_output("This should be buffered while paused")
    
    # Wait a bit to ensure paused state is effective
    await asyncio.sleep(0.1)
    
    # Capture current call count
    output_call_count = debug_app.output_panel.add_output.call_count
    
    # Wait to verify no new events are processed while paused
    await asyncio.sleep(0.2)
    assert debug_app.output_panel.add_output.call_count == output_call_count, \
        "Events should not be processed while paused"
    
    # Resume
    await debug_app.action_toggle_pause()
    assert controlled_executor.resume.called, "Executor resume not called"
    
    # Allow time for the buffered event to be processed
    await asyncio.sleep(0.2)
    assert debug_app.output_panel.add_output.call_count > output_call_count, \
        "Buffered events not processed after resume"
    
    # Test restart functionality
    await debug_app.action_restart()
    
    # Panels should be cleared
    debug_app.output_panel.clear.assert_called()
    debug_app.call_graph_panel.clear.assert_called()
    debug_app.exception_panel.clear.assert_called()
    
    # Executor restart should be called
    assert controlled_executor.restart.called, "Executor restart not called"
    
    # Clean up
    controlled_executor.control_stop()
    events_task.cancel()
    try:
        await events_task
    except asyncio.CancelledError:
        pass
    await debug_app.on_unmount()

@pytest.mark.asyncio
async def test_error_handling_during_event_processing(debug_app, controlled_executor):
    """Test app's error handling during event processing."""
    # Set executor on app
    debug_app.set_executor(controlled_executor)
    
    # Mount app
    await debug_app.on_mount()
    
    # Cause panels to raise exceptions when processing events
    debug_app.output_panel.add_output.side_effect = ValueError("Test output panel error")
    debug_app.call_graph_panel.add_call.side_effect = KeyError("Test call graph panel error")
    debug_app.exception_panel.add_exception.side_effect = RuntimeError("Test exception panel error")
    
    # Start event processing task
    events_task = asyncio.create_task(debug_app.process_events())
    
    # Wait a bit for task to initialize
    await asyncio.sleep(0.1)
    
    # Simulate script execution events that will cause errors in panels
    controlled_executor.add_output("This will cause an error")
    controlled_executor.add_call("error_function", "test.py", 42, {})
    controlled_executor.add_exception("TestException", "This will cause another error")
    
    # Wait for errors to be handled
    await asyncio.sleep(0.5)
    
    # Process_events should still be running despite errors
    assert not events_task.done(), "Events task should still be running"
    
    # Clean up
    controlled_executor.control_stop()
    events_task.cancel()
    try:
        await events_task
    except asyncio.CancelledError:
        pass
    await debug_app.on_unmount()

@pytest.mark.asyncio
async def test_high_volume_event_processing(debug_app, controlled_executor):
    """Test processing of high volume of events."""
    # Set executor on app
    debug_app.set_executor(controlled_executor)
    
    # Mount app
    await debug_app.on_mount()
    
    # Fix mock panels to track events without failing
    debug_app.output_panel.add_output = AsyncMock()
    debug_app.call_graph_panel.add_call = AsyncMock()
    debug_app.call_graph_panel.add_return = AsyncMock()
    
    # Start event processing task
    events_task = asyncio.create_task(debug_app.process_events())
    
    # Wait for task to initialize
    await asyncio.sleep(0.1)
    
    # Generate high volume of events
    for i in range(500):
        controlled_executor.add_output(f"Output line {i}")
        if i % 50 == 0:
            await asyncio.sleep(0.01)  # Small delay to avoid overwhelming the event loop
            
    for i in range(100):
        controlled_executor.add_call(f"function_{i}", "test.py", i, {"index": i})
        controlled_executor.add_return(f"function_{i}", f"result_{i}")
        if i % 20 == 0:
            await asyncio.sleep(0.01)
    
    # Wait for events to be processed
    await asyncio.sleep(1.0)
    
    # Verify events were processed
    assert debug_app.output_panel.add_output.call_count >= 500, \
        "Not all output events were processed"
    assert debug_app.call_graph_panel.add_call.call_count >= 100, \
        "Not all call events were processed"
    assert debug_app.call_graph_panel.add_return.call_count >= 100, \
        "Not all return events were processed"
    
    # Clean up
    controlled_executor.control_stop()
    events_task.cancel()
    try:
        await events_task
    except asyncio.CancelledError:
        pass
    await debug_app.on_unmount()
