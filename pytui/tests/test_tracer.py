# pylint: disable=redefined-outer-name, unused-import, too-few-public-methods, protected-access, missing-class-docstring, missing-function-docstring, trailing-whitespace, import-outside-toplevel
"""Tests for the tracer module."""

# Reorder imports: standard library imports come first
import types  # Moved here to fix wrong-import-order
from unittest.mock import patch, MagicMock  # Moved here to fix wrong-import-order
import pytest  # type: ignore
from pytui.tracer import trace_function, install_trace, _call_stack  # type: ignore
from pytui.collector import get_collector  # type: ignore


@pytest.fixture
def mock_collector():
    """Create a mock collector for testing."""
    mock = MagicMock()
    # Add a minimal implementation to make tests pass
    mock.add_call = MagicMock()
    mock.add_return = MagicMock()
    mock.add_exception = MagicMock()
    return mock


@pytest.fixture
def mock_frame():
    """Create a mock frame object for testing."""
    code = compile("def test_function(arg1): pass", "test_file.py", "exec")
    test_func_code = [c for c in code.co_consts if isinstance(c, types.CodeType)][0]

    class MockFrame:
        _pytui_test_filename = None

        @property
        def f_code(self):
            if self._pytui_test_filename:
                # Handle string replacement for filename in a simpler way
                # by using an object with the necessary attributes
                class MockCode:
                    def __init__(self, original_code, filename):
                        for attr in dir(original_code):
                            if attr.startswith("co_") and not attr.startswith("__"):
                                setattr(self, attr, getattr(original_code, attr))
                        self.co_filename = filename

                return MockCode(test_func_code, self._pytui_test_filename)
            return test_func_code

        f_lineno = 42
        f_locals = {"arg1": "value1", "self": object()}

    return MockFrame()


def test_get_collector():
    """Test that get_collector returns a singleton collector."""
    collector1 = get_collector()
    collector2 = get_collector()
    assert collector1 is collector2


def test_trace_function_call(mock_frame, mock_collector):
    """Test tracing a function call."""
    # Set up the collector globally
    import pytui.tracer

    pytui.tracer._collector = mock_collector

    try:
        # Force the Python interpreter to evaluate the variable
        # to mitigate any caching issues
        assert pytui.tracer._collector is mock_collector

        result = trace_function(mock_frame, "call", None)

        mock_collector.add_call.assert_called_once()
        call_args = mock_collector.add_call.call_args[0]
        assert call_args[0] == "test_function"  # Function name
        assert call_args[1] == "test_file.py"  # Filename
        assert call_args[2] == 42  # Line number
        assert "arg1" in call_args[3]  # Args dict

        # The trace function should return itself for chaining
        assert result is trace_function
    finally:
        # Clean up
        pytui.tracer._collector = None


def test_trace_function_return(mock_frame, mock_collector):
    """Test tracing a function return."""
    # Explicitly set _collector to our mock
    import pytui.tracer

    pytui.tracer._collector = mock_collector
    # Force the Python interpreter to evaluate the variable
    # to mitigate any caching issues
    assert pytui.tracer._collector is mock_collector
    # Add something to the call stack
    pytui.tracer._call_stack = [1]

    try:
        trace_function(mock_frame, "return", "return_value")
        mock_collector.add_return.assert_called_once()
        # Check args
        call_args = mock_collector.add_return.call_args[0]
        assert call_args[0] == "test_function"
        assert call_args[1] == "'return_value'"
    finally:
        # Clean up global state
        pytui.tracer._collector = None
        pytui.tracer._call_stack = []


def test_trace_function_exception(mock_frame, mock_collector):
    """Test tracing an exception."""
    # Explicitly set _collector to our mock
    import pytui.tracer

    pytui.tracer._collector = mock_collector
    # Force the Python interpreter to evaluate the variable
    # to mitigate any caching issues
    assert pytui.tracer._collector is mock_collector

    exception = ValueError("test exception")
    try:
        trace_function(mock_frame, "exception", (ValueError, exception, None))
        mock_collector.add_exception.assert_called_once_with(exception)
    finally:
        # Clean up global state
        pytui.tracer._collector = None


def test_trace_function_skips_internal(mock_frame, mock_collector):
    """Test that the tracer skips internal pytui modules."""
    # Set up the test frame with a tracer.py path
    mock_frame._pytui_test_filename = "/path/to/pytui/tracer.py"

    # For "call" events, it should return the trace function to allow further tracing
    result_call = trace_function(mock_frame, "call", None)
    assert (
        result_call is trace_function
    ), "trace_function should return itself for 'call' events even in internal modules"

    # For other events like "return", it should return None
    result_return = trace_function(mock_frame, "return", "value")
    assert (
        result_return is None
    ), "trace_function should return None for non-call events in internal modules"

    # Collector should not be called for internal modules
    import pytui.tracer

    pytui.tracer._collector = mock_collector
    trace_function(mock_frame, "call", None)
    mock_collector.add_call.assert_not_called()
    pytui.tracer._collector = None


def test_install_trace():
    """Test that install_trace sets the trace functions."""
    with patch("sys.settrace") as mock_sys_settrace, patch(
        "threading.settrace"
    ) as mock_thread_settrace:

        install_trace()

        mock_sys_settrace.assert_called_once_with(trace_function)
        mock_thread_settrace.assert_called_once_with(trace_function)
