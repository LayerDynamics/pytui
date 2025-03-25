"""Tracer module for capturing function calls and execution flow."""

import sys
import inspect
import threading
import json
import atexit
from typing import Dict, Any, Optional, List, TextIO

from .collector import get_collector

# Module-level variables - these are not constants, so keeping lowercase with underscores is appropriate
_current_collector = None
_current_trace_file = None
_current_call_stack: List[int] = []
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
    # Use nonlocal instead of global as it's cleaner
    nonlocal_collector = _current_collector
    if nonlocal_collector is None:
        nonlocal_collector = get_collector()
        # Update module-level variable
        globals()['_current_collector'] = nonlocal_collector
    return nonlocal_collector


def _should_skip_file(filename: str) -> bool:
    """Check if file should be skipped for tracing."""
    return ('pytui' in str(filename) and 
            ('tracer.py' in str(filename) or 'collector.py' in str(filename)))


def _handle_call_event(frame, func_name: str, filename: str, collector):
    """Handle a function call event."""
    # Create local copies to avoid repeated global assignments
    call_stack = _current_call_stack
    current_call_id = _current_call_id
    
    # Skip special functions but continue tracing inside them
    if func_name.startswith('__') or func_name == '<module>':
        return trace_function
    
    # Log debug for important functions
    if func_name == 'function1':
        print(f"Debug: Tracing call to {func_name} in {filename}")
    
    line_no = frame.f_lineno
    
    # Generate a unique call ID
    call_id = current_call_id
    # Update module-level counter
    globals()['_current_call_id'] = current_call_id + 1
    
    # Get parent ID from call stack
    parent_id = call_stack[-1] if call_stack else None
    
    # Save call ID on stack
    call_stack.append(call_id)
    
    # Get function arguments
    args_dict = _get_function_args(frame)
    
    # Add to collector
    collector.add_call(func_name, filename, line_no, args_dict,
                      call_id=call_id, parent_id=parent_id)
    
    # Send to parent process via IPC if available
    _send_event('call', func_name, filename, line_no, args_dict, call_id, parent_id)
    
    return trace_function


def _get_function_args(frame) -> Dict[str, str]:
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
                except (ValueError, TypeError):
                    args_dict[arg_name] = "<unable to represent>"
    except (ValueError, TypeError, AttributeError):
        # If any error occurs during argument extraction, return empty dict
        pass
    return args_dict


def _handle_return_event(func_name: str, return_value, collector):
    """Handle a function return event."""
    # Create local copy to avoid global assignment
    call_stack = _current_call_stack
    
    if not call_stack:
        return
        
    call_id = call_stack.pop()
    
    # Format return value
    return_value_str = repr(return_value)
    
    # Add to collector
    collector.add_return(func_name, return_value_str, call_id=call_id)
    
    # Send via IPC if available
    _send_event('return', func_name, return_value=return_value_str, call_id=call_id)


def _handle_exception_event(arg, collector):
    """Handle an exception event."""
    # Unpack exception info, ignoring unused variables
    _, exc_value, _ = arg
    
    # Add to collector
    collector.add_exception(exc_value)
    
    # Send via IPC if available
    _send_event('exception', exception=exc_value)


def _send_event(event_type: str, func_name: str = '', filename: str = '', 
                line_no: int = 0, args: Dict[str, str] = None, 
                call_id: int = 0, parent_id: Optional[int] = None,
                return_value: str = '', exception: Any = None):
    """Send an event via IPC if trace file is available."""
    trace_file = _current_trace_file
    
    if trace_file is None:
        return
        
    try:
        if event_type == 'call':
            event_data = {
                'type': 'call',
                'function_name': func_name,
                'filename': filename,
                'line_no': line_no,
                'args': args or {},
                'call_id': call_id,
                'parent_id': parent_id
            }
            
            json_data = json.dumps(event_data)
            trace_file.write(json_data + '\n')
            trace_file.flush()
            
            # Extra debug for function1
            if func_name == 'function1':
                print("Debug: Wrote function1 call to trace file")
                
        elif event_type == 'return':
            event_data = {
                'type': 'return',
                'function_name': func_name,
                'return_value': return_value,
                'call_id': call_id
            }
            trace_file.write(json.dumps(event_data) + '\n')
            trace_file.flush()
            
        elif event_type == 'exception':
            event_data = {
                'type': 'exception',
                'exception': repr(exception)
            }
            trace_file.write(json.dumps(event_data) + '\n')
            trace_file.flush()
            
    except (IOError, TypeError, ValueError) as exc:
        print(f"Error writing trace data: {exc}")


def flush_trace():
    """Flush the trace file before exiting."""
    trace_file = _current_trace_file
    if trace_file is not None:
        try:
            trace_file.flush()
        except IOError:
            pass


def install_trace(collector=None, trace_path=None):
    """Install the trace function with optional IPC.
    
    Args:
        collector: DataCollector instance to use
        trace_path: Path to file for IPC with parent process
    """
    # Use globals() to update module-level variables
    globals_dict = globals()
    
    # Set collector
    collector_to_use = collector or get_collector()
    globals_dict['_current_collector'] = collector_to_use
    
    # Reset call data
    globals_dict['_current_call_stack'] = []
    globals_dict['_current_call_id'] = 1
    
    # Set up IPC if a path is provided
    if trace_path:
        try:
            # Create the file first with a context manager
            with open(trace_path, 'w', encoding='utf-8'):
                pass
                
            # Then open it for continuous writing
            trace_file = open(trace_path, 'w', encoding='utf-8')
            globals_dict['_current_trace_file'] = trace_file
            
            # Register cleanup
            atexit.register(flush_trace)
        except (IOError, OSError, PermissionError) as exc:
            print(f"Failed to open trace file: {exc}")
    
    # Register trace function
    sys.settrace(trace_function)
    threading.settrace(trace_function)
    
    return collector_to_use
