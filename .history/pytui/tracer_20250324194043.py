"""Script execution tracer."""
import os
import sys
import time
import threading
import traceback
from typing import Optional, Dict, Any, Tuple, Union
from pathlib import Path

from .collector import get_collector

# Internal state tracking
_call_stack = []
_collector = None

def _should_skip_file(filename: str) -> bool:
    """Check if we should skip tracing a file."""
    # Convert to string if it's a Path object
    if isinstance(filename, Path):
        filename = str(filename)
    
    return (
        "pytui" in filename 
        and any(x in filename for x in ["tracer.py", "collector.py"])
    )

def _format_value(value: Any) -> str:
    """Safely format a value for display."""
    try:
        # Handle Path objects specially
        if isinstance(value, Path):
            return f"Path('{str(value)}')"
            
        # For other objects, use normal repr with length limit
        result = repr(value)
        if len(result) > 1000:
            result = result[:997] + "..."
        return result
    except Exception:  # pylint: disable=broad-except
        return "<unrepresentable>"

def trace_function(frame: Any, event: str, arg: Any) -> Optional[Any]:
    """Trace function for sys.settrace."""
    # Exit early if no collector or skipped file
    if _collector is None or _should_skip_file(frame.f_code.co_filename):
        return None
    
    # Get function name and determine handler
    func_name = frame.f_code.co_name
    handler = _EVENT_HANDLERS.get(event)
    
    if handler:
        return handler(arg, func_name, _collector)
        
    return trace_function

def _handle_call_event(arg: Any, func_name: str, collector: Any) -> Any:
    """Handle call events."""
    frame = sys._getframe(1)  # Get caller's frame
    filename = frame.f_code.co_filename
    lineno = frame.f_lineno
    
    # Format arguments
    local_vars = frame.f_locals
    args = {
        name: _format_value(value)
        for name, value in local_vars.items()
        if not name.startswith('_') and name != 'self'
    }
    
    # Get parent call ID if we have a call stack
    parent_id = _call_stack[-1] if _call_stack else None
    
    # Add the call event
    collector.add_call(func_name, filename, lineno, args, parent_id=parent_id)
    
    return trace_function

def _handle_return_event(arg: Any, func_name: str, collector: Any) -> None:
    """Handle return events."""
    # Format return value safely
    return_value = _format_value(arg)
    
    # Add return event
    if _call_stack:
        collector.add_return(func_name, return_value)
    
    return None

def _handle_exception_event(arg: Any, func_name: str, collector: Any) -> Any:
    """Handle exception events."""
    exc_type, exc_value, _ = arg
    
    if exc_value is not None:
        collector.add_exception(exc_value)
    
    return trace_function

# Map event types to handlers
_EVENT_HANDLERS = {
    'call': _handle_call_event,
    'return': _handle_return_event,
    'exception': _handle_exception_event
}

def install_trace(collector: Optional[Any] = None) -> Any:
    """Install tracing for the current thread."""
    global _collector  # pylint: disable=global-statement
    
    if collector is None:
        collector = get_collector()
        
    _collector = collector
    
    # Install trace functions
    sys.settrace(trace_function)
    threading.settrace(trace_function)
    
    return collector
