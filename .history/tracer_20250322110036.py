"""Tracer module for capturing function calls and execution flow."""

import sys
import inspect
import threading
import json
import atexit
from typing import Dict, Any, Optional, List

from .collector import get_collector

# Module-level variables - these are not constants despite module level placement
# pylint: disable=invalid-name
_current_collector = None
_current_trace_file = None
_current_call_stack: List[int] = []
_current_call_id = 1


def trace_function(frame, event, arg):
    """Trace function for sys.settrace."""
    # Early exits for invalid frames or missing collector
    if frame is None or frame.f_code is None:
        return trace_function

    collector = _get_collector()
    if collector is None:
        return None

    # Get basic frame info
    func_name = frame.f_code.co_name
    filename = frame.f_code.co_filename

    # Skip internal modules
    if _should_skip_file(filename):
        return None

    # Handle different event types (consolidating returns)
    handlers = {
        "call": lambda: _handle_call_event(frame, func_name, filename, collector),
        "return": lambda: _handle_return_and_continue(func_name, arg, collector),
        "exception": lambda: _handle_exception_and_continue(arg, collector)
    }
    
    # Use handler if available, otherwise return the trace function
    return handlers.get(event, lambda: trace_function)()


def _handle_return_and_continue(func_name, return_value, collector):
    """Process a return event and continue tracing."""
    _handle_return_event(func_name, return_value, collector)
    return trace_function


def _handle_exception_and_continue(arg, collector):
    """Process an exception event and continue tracing."""
    _handle_exception_event(arg, collector)
    return trace_function


def _get_collector():
    """Get the current collector instance."""
    # Use nonlocal instead of global as it's cleaner
    nonlocal_collector = _current_collector
    if nonlocal_collector is None:
        nonlocal_collector = get_collector()
        # Update module-level variable
        globals()["_current_collector"] = nonlocal_collector
    return nonlocal_collector


def _should_skip_file(filename: str) -> bool:
    """Check if file should be skipped for tracing."""
    return "pytui" in str(filename) and (
        "tracer.py" in str(filename) or "collector.py" in str(filename)
    )


def _handle_call_event(frame, func_name: str, filename: str, collector):
    """Handle a function call event."""
    # Create local copies to avoid repeated global assignments
    call_stack = _current_call_stack
    current_call_id = _current_call_id

    # Skip special functions but continue tracing inside them
    if func_name.startswith("__") or func_name == "<module>":
        return trace_function

    # Log debug for important functions
    if func_name == "function1":
        print(f"Debug: Tracing call to {func_name} in {filename}")

    line_no = frame.f_lineno

    # Generate a unique call ID
    call_id = current_call_id
    # Update module-level counter
    globals()["_current_call_id"] = current_call_id + 1

    # Get parent ID from call stack
    parent_id = call_stack[-1] if call_stack else None

    # Save call ID on stack
    call_stack.append(call_id)

    # Get function arguments
    args_dict = _get_function_args(frame)

    # Add to collector
    collector.add_call(
        func_name, filename, line_no, args_dict, call_id=call_id, parent_id=parent_id
    )

    # Send to parent process via IPC if available
    _send_trace_event(
        event_type="call",
        func_data={
            "function_name": func_name,
            "filename": filename,
            "line_no": line_no,
            "args": args_dict,
            "call_id": call_id,
            "parent_id": parent_id
        }
    )

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
    _send_trace_event(
        event_type="return",
        func_data={
            "function_name": func_name,
            "return_value": return_value_str,
            "call_id": call_id
        }
    )


def _handle_exception_event(arg, collector):
    """Handle an exception event."""
    # Unpack exception info, ignoring unused variables
    _, exc_value, _ = arg

    # Add to collector
    collector.add_exception(exc_value)

    # Send via IPC if available
    _send_trace_event(
        event_type="exception",
        func_data={
            "exception": repr(exc_value)
        }
    )


def _send_trace_event(event_type: str, func_data: Dict[str, Any]):
    """Send an event via IPC if trace file is available.
    
    Args:
        event_type: Type of event (call, return, exception)
        func_data: Event data to send
    """
    trace_file = _current_trace_file

    if trace_file is None:
        return

    try:
        event_data = {"type": event_type, **func_data}
        
        # Add extra debug output for function1
        if event_type == "call" and func_data.get("function_name") == "function1":
            print("Debug: Wrote function1 call to trace file")

        json_data = json.dumps(event_data)
        trace_file.write(json_data + "\n")
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
    globals_dict["_current_collector"] = collector_to_use

    # Reset call data
    globals_dict["_current_call_stack"] = []
    globals_dict["_current_call_id"] = 1

    # Set up IPC if a path is provided
    if trace_path:
        try:
            # Create and then open the file for writing
            with open(trace_path, "w", encoding="utf-8"):
                # Just create the file first
                pass
                
            # Now open it for continuous writing using a context manager in a way
            # that works with our flush requirements
            trace_file_obj = open(trace_path, "w", encoding="utf-8")
            globals_dict["_current_trace_file"] = trace_file_obj
            
            # Register cleanup
            atexit.register(flush_trace)
            atexit.register(lambda: trace_file_obj.close())
        except (IOError, OSError, PermissionError) as exc:
            print(f"Failed to open trace file: {exc}")

    # Register trace function
    sys.settrace(trace_function)
    threading.settrace(trace_function)

    return collector_to_use
