"""Integration tests for more complex app interactions."""

# Standard library imports first
from unittest.mock import MagicMock
import asyncio
import functools

# Third-party imports
# pylint: disable=import-error
import pytest  # type: ignore

# Local imports
from pytui.app import PyTUIApp
from pytui.collector import DataCollector

# pylint: disable=protected-access, redefined-outer-name, unused-argument, broad-except
# pylint: disable=trailing-whitespace, line-too-long


@pytest.fixture
def debug_app():
    """Create a debug app fixture with mocked components."""
    app = PyTUIApp()

    # Store the original method for later restoration
    app._original_process_events = app.process_events

    # Mock process_events to avoid actual async operations
    async def mock_process_events():
        try:
            await app._original_process_events()
        except Exception as e:
            # In tests, we catch broadly to help with debugging
            print(f"Error processing events (expected in tests): {e}")

    app.process_events = mock_process_events
    return app


@pytest.fixture
def mock_collector():
    """Create a mock data collector."""
    collector = DataCollector()

    # Add testing utilities
    async def add_test_output(message, stream="stdout"):
        await asyncio.sleep(0.01)  # Small delay for async simulation
        collector.add_output(message, stream)

    collector.add_test_output = add_test_output

    async def add_test_function_call(
        func_name="test_func", filename="test.py", line_no=1, args=None
    ):
        await asyncio.sleep(0.01)  # Small delay for async simulation
        if args is None:
            args = {"arg1": "value1"}
        collector.add_call(func_name, filename, line_no, args)

    collector.add_test_function_call = add_test_function_call

    return collector


class TestException(Exception):
    """Custom exception class for testing purposes."""

    pass


@pytest.fixture
def controlled_executor():
    """Create a controlled executor for testing."""
    # Create a mock executor with a real collector
    executor = MagicMock()
    executor.collector = DataCollector()
    executor.is_running = True

    # Add testing utilities
    async def add_test_output(message, stream="stdout"):
        await asyncio.sleep(0.01)  # Small delay for async simulation
        executor.collector.add_output(message, stream)

    executor.add_test_output = add_test_output

    async def add_test_call(
        func_name="test_func", filename="test.py", line_no=1, args=None
    ):
        await asyncio.sleep(0.01)  # Small delay
        if args is None:
            args = {"param1": "value1"}
        executor.collector.add_call(func_name, filename, line_no, args)

    executor.add_test_call = add_test_call

    async def add_test_return(func_name="test_func", return_value="result"):
        await asyncio.sleep(0.01)  # Small delay
        executor.collector.add_return(func_name, return_value)

    executor.add_test_return = add_test_return

    async def add_test_exception(
        exc_type="ValueError", message="Test error", _traceback=None
    ):
        exception = TestException(message)
        exception.__class__.__name__ = exc_type
        await asyncio.sleep(0.01)  # Small delay
        executor.collector.add_exception(exception)

    executor.add_test_exception = add_test_exception

    # Mock the executor stopping/starting methods
    def mock_stop():
        executor.is_running = False

    executor.stop = mock_stop

    def mock_restart():
        executor.is_running = False
        executor.collector.clear()
        executor.is_running = True

    executor.restart = mock_restart

    return executor


def non_blocking(timeout=5):
    def decorator(test_func):
        @functools.wraps(test_func)
        async def wrapper(*args, **kwargs):
            return await asyncio.wait_for(
                asyncio.to_thread(test_func, *args, **kwargs), timeout
            )

        return wrapper

    return decorator


@pytest.mark.asyncio
async def test_app_initialization():
    """Test initial app setup."""
    app = PyTUIApp()

    # Initially, app should have no executor
    assert app.executor is None

    # After setting executor, it should be stored
    mock_exec = MagicMock()
    app.set_executor(mock_exec)
    assert app.executor == mock_exec

    # Test event processing task is None initially
    assert not hasattr(app, "event_task") or app.event_task is None


@pytest.mark.asyncio
async def test_output_processing(debug_app, controlled_executor):
    """Test that the app processes output events."""
    # Set up the app with our controlled executor
    debug_app.set_executor(controlled_executor)

    # Mock critical UI components
    debug_app.output_panel = MagicMock()
    debug_app.output_panel.add_output = MagicMock()

    # Start event processing
    debug_app.event_task = asyncio.create_task(debug_app.process_events())

    # Add test output
    await controlled_executor.add_test_output("Test message")
    await asyncio.sleep(0.1)  # Give time for event to process

    # Verify output was passed to panel
    debug_app.output_panel.add_output.assert_called()

    # Clean up
    debug_app.event_task.cancel()
    try:
        await debug_app.event_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_call_processing(debug_app, controlled_executor):
    """Test that the app processes function call events."""
    # Set up the app with our controlled executor
    debug_app.set_executor(controlled_executor)

    # Mock critical UI components
    debug_app.call_graph_panel = MagicMock()
    debug_app.call_graph_panel.add_call = MagicMock()

    # Start event processing
    debug_app.event_task = asyncio.create_task(debug_app.process_events())

    # Add test function call
    await controlled_executor.add_test_call(
        "test_function", "test.py", 42, {"arg": "value"}
    )
    await asyncio.sleep(0.1)  # Give time for event to process

    # Verify call was passed to panel
    debug_app.call_graph_panel.add_call.assert_called()

    # Clean up
    debug_app.event_task.cancel()
    try:
        await debug_app.event_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_return_processing(debug_app, controlled_executor):
    """Test that the app processes function return events."""
    # Set up the app with our controlled executor
    debug_app.set_executor(controlled_executor)

    # Mock critical UI components
    debug_app.call_graph_panel = MagicMock()
    debug_app.call_graph_panel.add_return = MagicMock()

    # Start event processing
    debug_app.event_task = asyncio.create_task(debug_app.process_events())

    # Mock the return event processing - create an actual return event
    from pytui.collector import ReturnEvent

    # Directly add a return event to the collector's queue
    return_event = ReturnEvent("test_function", "result_value", call_id=1)
    controlled_executor.collector._queue.put_nowait(("return", return_event))

    # Give time for event to process
    await asyncio.sleep(0.2)

    # Verify return was passed to panel
    debug_app.call_graph_panel.add_return.assert_called_once()

    # Clean up
    debug_app.event_task.cancel()
    try:
        await debug_app.event_task
    except (asyncio.CancelledError, RuntimeError):
        pass


@pytest.mark.asyncio
@non_blocking()
async def test_exception_processing(debug_app, controlled_executor):
    """Test that the app processes exception events."""
    # Set up the app with our controlled executor
    debug_app.set_executor(controlled_executor)

    # Mock critical UI components
    debug_app.exception_panel = MagicMock()
    debug_app.exception_panel.add_exception = MagicMock()
    debug_app.output_panel = MagicMock()
    debug_app.output_panel.add_exception = MagicMock()

    # Start event processing
    debug_app.event_task = asyncio.create_task(debug_app.process_events())

    # Add test exception
    await controlled_executor.add_test_exception("ValueError", "Test error message")
    await asyncio.sleep(0.1)  # Give time for event to process

    # Verify exception was passed to panels
    debug_app.exception_panel.add_exception.assert_called()
    debug_app.output_panel.add_exception.assert_called()

    # Clean up
    debug_app.event_task.cancel()
    try:
        await debug_app.event_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
@non_blocking()
async def test_pause_resume_functionality(debug_app, controlled_executor):
    """Test the app's pause/resume functionality."""
    # Set up the app with our controlled executor
    debug_app.set_executor(controlled_executor)
    debug_app.is_paused = False

    # Mock required components
    debug_app.output_panel = MagicMock()

    # Test pausing
    await debug_app.action_toggle_pause()

    # Verify pause state
    assert debug_app.is_paused is True
    controlled_executor.pause.assert_called_once()
    debug_app.output_panel.add_message.assert_called_with("Execution updates paused")

    # Test resuming
    await debug_app.action_toggle_pause()

    # Verify resume state
    assert debug_app.is_paused is False
    controlled_executor.resume.assert_called_once()
    debug_app.output_panel.add_message.assert_called_with("Execution updates resumed")


@pytest.mark.asyncio
@non_blocking()
async def test_restart_functionality(debug_app, controlled_executor):
    """Test the app's restart functionality."""
    # Set up the app with our controlled executor
    debug_app.set_executor(controlled_executor)

    # Mock required components
    debug_app.output_panel = MagicMock()
    debug_app.call_graph_panel = MagicMock()
    debug_app.exception_panel = MagicMock()

    # Test restart action
    await debug_app.action_restart()

    # Verify panels were cleared
    debug_app.output_panel.clear.assert_called_once()
    debug_app.call_graph_panel.clear.assert_called_once()
    debug_app.exception_panel.clear.assert_called_once()

    # Verify executor was restarted
    controlled_executor.restart.assert_called_once()

    # Verify message was added
    debug_app.output_panel.add_message.assert_called_with("Restarting execution...")


@pytest.mark.asyncio
@non_blocking()
async def test_search_functionality(debug_app, controlled_executor):
    """Test the app's search functionality."""
    # Set up the app with our controlled executor
    debug_app.set_executor(controlled_executor)

    # Mock required components
    debug_app.output_panel = MagicMock()

    # Test search action
    await debug_app.action_search()

    # Verify panel was focused and search activated
    debug_app.output_panel.focus.assert_called_once()
    debug_app.output_panel.action_search.assert_called_once()


@pytest.mark.asyncio
@non_blocking()
async def test_collapse_functionality(debug_app, controlled_executor):
    """Test panel collapse functionality."""
    # Set up the app with our controlled executor
    debug_app.set_executor(controlled_executor)

    # Mock required components
    debug_app.call_graph_panel = MagicMock()
    debug_app.call_graph_panel.styles = MagicMock()
    debug_app.call_graph_panel.styles.animate = MagicMock()

    # Set the focused component to call_graph_panel
    debug_app.focused = debug_app.call_graph_panel
    debug_app.collapsed_panels = {
        "call_graph": False,
        "output": False,
        "exception": False,
    }

    # Test collapse action
    await debug_app.action_toggle_collapse()

    # Verify panel was collapsed
    assert debug_app.collapsed_panels["call_graph"] is True
    debug_app.call_graph_panel.styles.animate.assert_called_with("height", 3)

    # Test expand action
    await debug_app.action_toggle_collapse()

    # Verify panel was expanded
    assert debug_app.collapsed_panels["call_graph"] is False
    debug_app.call_graph_panel.styles.animate.assert_called_with("height", 20)


@pytest.mark.asyncio
@non_blocking()
async def test_variable_display_toggle(debug_app, controlled_executor):
    """Test toggling variable display."""
    # Set up the app with our controlled executor
    debug_app.set_executor(controlled_executor)

    # Mock required components
    debug_app.call_graph_panel = MagicMock()
    debug_app.call_graph_panel.toggle_var_display = MagicMock()

    # Test variable display toggle
    await debug_app.action_toggle_vars()

    # Verify toggle method was called
    debug_app.call_graph_panel.toggle_var_display.assert_called_once()


@pytest.mark.asyncio
@non_blocking()
async def test_metrics_toggle(debug_app, controlled_executor):
    """Test toggling metrics panel visibility."""
    # Set up the app with our controlled executor
    debug_app.set_executor(controlled_executor)

    # Mock required components
    debug_app.view = MagicMock()
    debug_app.metrics_widget = MagicMock()
    debug_app._metrics_visible = False

    # Test metrics toggle (show)
    await debug_app.action_toggle_metrics()

    # Verify metrics were shown
    assert debug_app._metrics_visible is True
    debug_app.view.dock.assert_called_with(
        debug_app.metrics_widget, edge="right", size=30
    )

    # Test metrics toggle (hide)
    await debug_app.action_toggle_metrics()

    # Verify metrics were hidden
    assert debug_app._metrics_visible is False
    debug_app.view.remove_widget.assert_called_with(debug_app.metrics_widget)
