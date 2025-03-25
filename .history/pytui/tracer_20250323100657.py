"""Function tracing and debugging tools."""

import sys
import os
import threading
import inspect
import json
import traceback
from functools import wraps
from typing import Any, Dict, Optional, Callable, Tuple, List, Union

from .collector import DataCollector, get_collector
from .utils import safe_repr, truncate_string

# Global state
_collector = None
_call_stack = []
_next_call_id = 1
_call_levels = {}
_trace_file = None

# Track the current collector for use by tests
_current_collector = None

def _should_skip_file(filename: str) -> bool:
    """Check if tracing should be skipped for a file."""
    # Skip tracing for the tracer module itself (avoid infinite recursion)
    return (
        'pytui/tracer.py' in filename or 
        'pytui/collector.py' in filename
    )

def _is_valid_frame(frame):
    """Check if a frame should be traced."""
    if frame is None:
        return False
    
    filename = frame.f_code.co_filename
    return not _should_skip_file(filename)

def _get_args_dict(frame) -> Dict[str, str]:
    """Extract function arguments from a frame."""
    args = {}
    try:
        if frame and frame.f_locals:
            for name, value in frame.f_locals.items():
                # Skip 'self' references and internal vars
                if name == 'self' or name.startswith('__'):
                    continue
                try:
                    # Try to create a string representation, truncated for large values
                    args[name] = truncate_string(safe_repr(value))
                except Exception:
                    args[name] = "<unable to represent>"
    except Exception as e:
        args["__error__"] = f"Error capturing args: {str(e)}"
    return args

def _get_event_handler(event: str) -> Optional[Callable]:
    """Get the appropriate event handler for a trace event."""
    handlers = {
        'call': _handle_call_event,
        'return': _handle_return_event,
        'exception': _handle_exception_event,
        'line': None  # We don't trace lines
    }
    return handlers.get(event)

def _handle_call_event(frame, arg, filename=None, collector=None):
    """Handle a 'call' trace event."""
    global _collector, _call_stack, _next_call_id
    
    # Use provided collector or global collector
    collector = collector or _collector
    if not collector:
        return None
    
    if not filename:
        filename = frame.f_code.co_filename
        
    if _should_skip_file(filename):
        return None
    
    func_name = frame.f_code.co_name
    line_no = frame.f_lineno
    args = _get_args_dict(frame)
    
    # Assign a unique ID to this call
    call_id = _next_call_id
    _next_call_id += 1
    
    # Determine parent call ID if there is one
    parent_id = _call_stack[-1] if _call_stack else None
    
    # Add to call stack
    _call_stack.append(call_id)
    
    # Record the call
    collector.add_call(func_name, filename, line_no, args, call_id=call_id, parent_id=parent_id)
    
    # Return trace_function to continue tracing
    return trace_function

def _handle_return_event(frame, arg, collector=None):
    """Handle a 'return' trace event."""
    global _collector, _call_stack
    
    # Use provided collector or global collector
    collector = collector or _collector
    if not collector or not _call_stack:
        return None
    
    func_name = frame.f_code.co_name
    
    # Get the return value as a string, safely
    try:
        return_str = safe_repr(arg)
    except Exception:
        return_str = "<unable to represent return value>"
    
    # Pop the last call from the stack
    call_id = _call_stack.pop() if _call_stack else None
    
    # Record the return
    collector.add_return(func_name, return_str, call_id=call_id)
    
    # Return trace_function to continue tracing
    return trace_function

def _handle_exception_event(frame, arg, collector=None):
    """Handle an 'exception' trace event."""
    global _collector
    
    # Use provided collector or global collector
    collector = collector or _collector
    if not collector:
        return None
    
    try:
        exception_type, exception_value, _ = arg
        # Add the exception to the collector
        collector.add_exception(exception_value)
    except Exception:
        # If anything goes wrong, we shouldn't disturb program execution
        pass
    
    # Return trace_function to continue tracing
    return trace_function

def trace_function(frame, event, arg):
    """Trace function for sys.settrace."""
    if not _is_valid_frame(frame):
        return trace_function

    handler = _get_event_handler(event)
    if handler:
        return handler(frame, arg, collector=_collector)
    
    return trace_function

def install_trace(collector=None, trace_path=None) -> DataCollector:
    """
    Install function tracing.
    
    Args:
        collector: Optional collector to use, or create a new one.
        trace_path: Optional path to write trace data to (for IPC).
        
    Returns:
        The collector being used.
    """
    global _collector, _call_stack, _next_call_id, _trace_file, _current_collector
    
    # Use the provided collector or get the default one
    _collector = collector or get_collector()
    _current_collector = _collector  # Track for tests
    
    # Reset trace state
    _call_stack = []
    _next_call_id = 1
    
    # Set up trace file for IPC if path was provided
    if trace_path:
        try:
            _trace_file = open(trace_path, 'a', encoding='utf-8')
            # Write a test message to verify the file is working
            _trace_file.write('{"test": "write"}\n')
            _trace_file.flush()
        except Exception as e:
            print(f"Error setting up trace file: {e}")
    
    # Install trace function
    sys.settrace(trace_function)
    threading.settrace(trace_function)
    
    return _collector
