"""Tracer module for capturing function calls and execution flow."""

import sys
import inspect
import threading
import json
import atexit
import io
from typing import Optional, Dict, Any, Tuple

from .collector import get_collector

# Module-level variables (renamed to avoid invalid name warnings)
# Using underscores to indicate they're internal, not constants
_current_collector = None
_current_trace_file = None
_current_call_stack = []
_current_call_id = 1


def trace_function(frame, event, arg):
    """Trace function for sys.settrace."""
    if frame is None or frame.f_code is None:
        return trace_function

    # Get collector if needed
    collector = _get_collector()
    if collector is None:
        return None

    # Get basic frame info
    func_name = frame.f_code.co_name
    filename = frame.f_code.co_filename

    # Skip internal modules
    if _should_skip_file(filename):
        return None

    # Handle different event types
    if event == 'call':
        return _handle_call_event(frame, func_name, filename, collector)
    if event == 'return':
        _handle_return_event(func_name, arg, collector)
        return trace_function
    if event == 'exception':
        _handle_exception_event(arg, collector)
        return trace_function

    # Default: continue tracing
    return trace_function


def _get_collector():
    """Get the current collector instance."""
    global _current_collector
    if _current_collector is None:
        _current_collector = get_collector()
    return _current_collector


def _should_skip_file(filename):
    """Check if file should be skipped for tracing."""
    return ('pytui' in str(filename) and 
            ('tracer.py' in str(filename) or 'collector.py' in str(filename)))


def _handle_call_event(frame, func_name, filename, collector):
    """Handle a function call event."""
    global _current_call_stack, _current_call_id
    
    # Skip special functions but continue tracing inside them
    if func_name.startswith('__') or func_name == '<module>':
        return trace_function
    
    # Log debug for important functions
    if func_name == 'function1':
        print(f"Debug: Tracing call to {func_name} in {filename}")
    
    line_no = frame.f_lineno
    
    # Generate a unique call ID
    call_id = _current_call_id
    _current_call_id += 1
    
    # Get parent ID from call stack
    parent_id = _current_call_stack[-1] if _current_call_stack else None
    
    # Save call ID on stack
    _current_call_stack.append(call_id)
    
    # Get function arguments
    args_dict = _get_function_args(frame)
    
    # Add to collector
    collector.add_call(func_name, filename, line_no, args_dict, 
                      call_id=call_id, parent_id=parent_id)
    
    # Send to parent process via IPC if available
    _send_call_event(func_name, filename, line_no, args_dict, call_id, parent_id)
    
    return trace_function


def _get_function_args(frame):
    """Extract function arguments from frame."""
    args_dict = {}
    try:
        args = inspect.getargvalues(frame)
        for arg_name in args.args:
            if arg_name in args.locals:
                try:
                    value = repr(args.locals[arg_name])
                    if len(value) > 100:
                        value = value[:97] + "..."
                    args_dict[arg_name] = value
                except Exception:
                    args_dict[arg_name] = "<unable to represent>"
    except Exception:
        # If any error occurs during argument extraction, return empty dict
        pass
    return args_dict


def _handle_return_event(func_name, return_value, collector):
    """Handle a function return event."""
    global _current_call_stack
    
    if not _current_call_stack:
        return
        
    call_id = _current_call_stack.pop()
    
    # Format return value
    return_value_str = repr(return_value)
    
    # Add to collector
    collector.add_return(func_name, return_value_str, call_id=call_id)
    
    # Send via IPC if available
    _send_return_event(func_name, return_value_str, call_id)


def _handle_exception_event(arg, collector):
    """Handle an exception event."""
    # Unpack exception info, ignoring unused variables
    _, exc_value, _ = arg
    
    # Add to collector
    collector.add_exception(exc_value)
    
    # Send via IPC if available
    _send_exception_event(exc_value)


def _send_call_event(func_name, filename, line_no, args_dict, call_id, parent_id):
    """Send call event via IPC if trace file is available."""
    global _current_trace_file
    
    if _current_trace_file is None:
        return
        
    try:
        event_data = {
            'type': 'call',
            'function_name': func_name,
            'filename': filename,
            'line_no': line_no,
            'args': args_dict,
            'call_id': call_id,
            'parent_id': parent_id
        }
        json_data = json.dumps(event_data)
        _current_trace_file.write(json_data + '\n')
        _current_trace_file.flush()
        
        # Extra debug for function1
        if func_name == 'function1':
            print("Debug: Wrote function1 call to trace file")
    except Exception as exc:
        print(f"Error writing trace data: {exc}")


def _send_return_event(func_name, return_value, call_id):
    """Send return event via IPC if trace file is available."""
    global _current_trace_file
    
    if _current_trace_file is None:
        return
        
    try:
        event_data = {
            'type': 'return',
            'function_name': func_name,
            'return_value': return_value,
            'call_id': call_id
        }
        _current_trace_file.write(json.dumps(event_data) + '\n')
        _current_trace_file.flush()
    except IOError:
        # Silently ignore IO errors on return events
        pass


def _send_exception_event(exc_value):
    """Send exception event via IPC if trace file is available."""
    global _current_trace_file
    
    if _current_trace_file is None:
        return
        
    try:
        event_data = {
            'type': 'exception',
            'exception': repr(exc_value)
        }
        _current_trace_file.write(json.dumps(event_data) + '\n')
        _current_trace_file.flush()
    except IOError:
        # Silently ignore IO errors on exception events
        pass


def flush_trace():
    """Flush the trace file before exiting."""
    if _current_trace_file is not None:
        try:
            _current_trace_file.flush()
        except IOError:
            pass


def install_trace(collector=None, trace_path=None):
    """Install the trace function with optional IPC.
    
    Args:
        collector: DataCollector instance to use
        trace_path: Path to file for IPC with parent process
    """
    global _current_collector, _current_trace_file, _current_call_stack, _current_call_id
    
    # Set collector
    _current_collector = collector or get_collector()
    
    # Reset call data
    _current_call_stack = []
    _current_call_id = 1
    
    # Set up IPC if a path is provided
    if trace_path:
        try:
            # Use with statement and specify encoding
            with open(trace_path, 'w', encoding='utf-8') as f:
                # Just create the file, we'll open it for writing
                pass
                
            # Open file for continuous writing
            _current_trace_file = open(trace_path, 'w', encoding='utf-8')
            
            # Register cleanup
            atexit.register(flush_trace)
        except Exception as exc:
            print(f"Failed to open trace file: {exc}")
    
    # Register trace function
    sys.settrace(trace_function)
    threading.settrace(trace_function)
    
    return _current_collector
