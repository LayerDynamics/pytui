"""Tests for the tracer module."""

import os
import sys
import inspect
import types
import pytest
from unittest.mock import patch, MagicMock

from pytui.tracer import trace_function, get_collector, install_trace

@pytest.fixture
def mock_collector():
    """Create a mock collector for testing."""
    mock = MagicMock()
    return mock

@pytest.fixture
def mock_frame():
    """Create a mock frame object for testing."""
    # Create a proper code object that satisfies inspect.iscode()
    code = compile("def test_function(arg1): pass", "test_file.py", "exec")
    test_func_code = [c for c in code.co_consts if isinstance(c, types.CodeType)][0]
    
    class MockFrame:
        f_code = test_func_code
        f_lineno = 42
        f_locals = {"arg1": "value1", "self": object()}
        
        # Add a custom attribute for the internal test
        _pytui_test_filename = None
        
        @property
        def f_code(self):
            if self._pytui_test_filename:
                # Create a custom code object for the internal test
                modified_code = types.CodeType(
                    test_func_code.co_argcount,
                    test_func_code.co_posonlyargcount,
                    test_func_code.co_kwonlyargcount,
                    test_func_code.co_nlocals,
                    test_func_code.co_stacksize,
                    test_func_code.co_flags,
                    test_func_code.co_code,
                    test_func_code.co_consts,
                    test_func_code.co_names,
                    test_func_code.co_varnames,
                    self._pytui_test_filename,  # Modified filename
                    test_func_code.co_name,
                    test_func_code.co_firstlineno,
                    test_func_code.co_lnotab,
                    test_func_code.co_freevars,
                    test_func_code.co_cellvars
                )
                return modified_code
            return test_func_code
        
    return MockFrame()

def test_get_collector():
    """Test that get_collector returns a singleton collector."""
    collector1 = get_collector()
    collector2 = get_collector()
    assert collector1 is collector2

def test_trace_function_call(mock_frame, mock_collector):
    """Test tracing a function call."""
    with patch('pytui.tracer.get_collector', return_value=mock_collector):
        result = trace_function(mock_frame, 'call', None)
        
        mock_collector.add_call.assert_called_once()
        call_args = mock_collector.add_call.call_args[0]
        assert call_args[0] == "test_function"
        assert call_args[1] == "test_file.py"  # This should now pass
        assert call_args[2] == 42
        assert "arg1" in call_args[3]
        assert call_args[3]["arg1"] == "'value1'"
        
        # The trace function should return itself for chaining
        assert result is trace_function

def test_trace_function_return(mock_frame, mock_collector):
    """Test tracing a function return."""
    with patch('pytui.tracer.get_collector', return_value=mock_collector):
        trace_function(mock_frame, 'return', "return_value")
        
        mock_collector.add_return.assert_called_once_with(
            "test_function", 
            "'return_value'"
        )

def test_trace_function_exception(mock_frame, mock_collector):
    """Test tracing an exception."""
    exception = ValueError("test exception")
    with patch('pytui.tracer.get_collector', return_value=mock_collector):
        trace_function(mock_frame, 'exception', (ValueError, exception, None))
        
        mock_collector.add_exception.assert_called_once_with(exception)

def test_trace_function_skips_internal(mock_frame, mock_collector):
    """Test that the tracer skips internal pytui modules."""
    # Use the custom property setter we added
    mock_frame._pytui_test_filename = "/path/to/pytui/tracer.py"
    
    with patch('pytui.tracer.get_collector', return_value=mock_collector):
        result = trace_function(mock_frame, 'call', None)
        
        # Should not add call for internal modules
        mock_collector.add_call.assert_not_called()
        # Should return None to stop tracing this branch
        assert result is None

def test_install_trace():
    """Test that install_trace sets the trace functions."""
    with patch('sys.settrace') as mock_sys_settrace, \
         patch('threading.settrace') as mock_thread_settrace:
        
        install_trace()
        
        mock_sys_settrace.assert_called_once_with(trace_function)
        mock_thread_settrace.assert_called_once_with(trace_function)
