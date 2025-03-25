"""Tracer module for capturing function calls and execution flow."""

import os
import sys
import inspect
import threading
import json
import atexit
from typing import Dict, Any

from .collector import get_collector

class TraceState:
    """Class to manage tracing state."""
    def __init__(self):
        # File handling
        self._trace_file = None
        self._current_trace_file = None
        
        # Collector references
        self._collector = None
        self._current_collector = None
        
        # Call tracking
        self._call_stack = []
        self._current_call_id = 1
        
    def get_collector(self):
        """Get current collector instance."""
        return self._collector or self._current_collector
    
    def set_collector(self, collector):
        """Set collector instances."""
        self._collector = collector
        self._current_collector = collector

# Global state instance
_state = TraceState()


def trace_function(frame, event, arg):
    """Trace function for sys.settrace."""
    if not _is_valid_frame(frame):
        return trace_function
    
    handler = _get_event_handler(event)
    if handler:
        return handler(frame, arg)
    return trace_function

def _is_valid_frame(frame):
    """Check if frame is valid for tracing."""
    return (frame and frame.f_code and 
            _should_trace_line(frame) and 
            not _should_skip_file(frame.f_code.co_filename))

def _get_event_handler(event):
    """Get appropriate handler for event type."""
    handlers = {
        "call": _handle_call_event,
        "return": _handle_return_event,
        "exception": _handle_exception_event
    }
    return handlers.get(event)


def _handle_call_event(frame, func_name, filename, collector):
    """Handle function call events."""
    if func_name.startswith("__") or func_name == "<module>":
        return

    line_no = frame.f_lineno
    args_dict = _get_function_args(frame)

    call_id = _state.current_call_id
    _state.current_call_id += 1
    parent_id = _state.current_call_stack[-1] if _state.current_call_stack else None
    _state.current_call_stack.append(call_id)

    collector.add_call(
        func_name,
        filename,
        line_no,
        args_dict,
        call_id=call_id,
        parent_id=parent_id,
    )

    _send_trace_event(
        "call",
        {
            "function_name": func_name,
            "filename": filename,
            "line_no": line_no,
            "args": args_dict,
            "call_id": call_id,
            "parent_id": parent_id,
        },
    )


def _handle_return_event(frame, arg, func_name, collector):
    """Handle function return events."""
    if _state.current_call_stack:
        call_id = _state.current_call_stack.pop()
        return_value_str = repr(arg)

        collector.add_return(func_name, return_value_str, call_id=call_id)
        _send_trace_event(
            "return",
            {
                "function_name": func_name,
                "return_value": return_value_str,
                "call_id": call_id,
            },
        )


def _handle_exception_event(arg, collector):
    """Handle exception events."""
    _, exc_value, _ = arg
    collector.add_exception(exc_value)
    _send_trace_event("exception", {"exception": repr(exc_value)})


def _get_collector():
    """Get the current collector instance."""
    if _state.collector is not None:
        return _state.collector

    if _state.current_collector is None:
        _state.current_collector = get_collector()
        _state.collector = _state.current_collector
    return _state.current_collector


def _should_skip_file(filename: str) -> bool:
    """Check if file should be skipped for tracing."""
    return "pytui" in str(filename) and (
        "tracer.py" in str(filename) or "collector.py" in str(filename)
    )


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
        pass
    return args_dict


def _send_trace_event(event_type: str, func_data: Dict[str, Any]):
    """Send an event via IPC if trace file is available."""
    if not _state.current_trace_file:
        return

    try:
        event_data = {"type": event_type, **func_data}
        if event_type == "call" and func_data.get("function_name") == "function1":
            print("Debug: Traced function1 call, writing to trace file")
            print("DEBUG_TRACE: function1 called", file=sys.stderr)

        with open(_state.current_trace_file.name, "a", encoding="utf-8") as f:
            json_data = json.dumps(event_data)
            f.write(json_data + "\n")
            f.flush()
            if event_type == "call" and func_data.get("function_name") == "function1":
                os.fsync(f.fileno())
    except (IOError, TypeError, ValueError) as exc:
        print(f"Error writing trace data: {exc}")


def flush_trace():
    """Flush the trace file before exiting."""
    if _state.current_trace_file is not None:
        try:
            _state.current_trace_file.flush()
        except IOError:
            pass


def install_trace(collector=None, trace_path=None):
    """Install the trace function with optional IPC.

    Args:
        collector: DataCollector instance to use
        trace_path: Path to file for IPC with parent process
    """
    _state.current_collector = collector or get_collector()
    _state.collector = _state.current_collector
    _state.current_call_stack = []
    _state.call_stack = []
    _state.current_call_id = 1

    if trace_path:
        try:
            with open(trace_path, "w", encoding="utf-8") as trace_file:
                trace_file.write('{"test": "write"}\n')
                trace_file.flush()
                _state.current_trace_file = trace_file
                _state.trace_file = trace_file
                
            def cleanup_trace():
                if _state.trace_file and not _state.trace_file.closed:
                    _state.trace_file.close()
            
            atexit.register(flush_trace)
            atexit.register(cleanup_trace)
        except (IOError, OSError, PermissionError) as exc:
            print(f"Failed to open trace file: {exc}")

    sys.settrace(trace_function)
    threading.settrace(trace_function)

    return _state.current_collector


def _should_trace_line(frame) -> bool:
    """Determine if a line should be traced."""
    return frame.f_code.co_filename.endswith(".py")


def _get_call_id() -> int:
    """Generate unique call ID."""
    _state.last_call_id += 1
    return _state.last_call_id


def _get_parent_id() -> int:
    """Get parent call ID from stack."""
    return _state.current_call_stack[-1] if _state.current_call_stack else None


def _trace_call(frame, event, arg) -> None:
    """Handle function call events."""
    if not _should_trace_line(frame):
        return None

    try:
        if event == "call":
            _handle_call_trace(frame)
            return _trace_call
        if event == "return":
            _handle_return_trace(frame, arg)
        return None
    except (ValueError, AttributeError, TypeError) as e:
        print(f"Error in trace call: {e}")
        return None


def _record_trace_event(event: Dict[str, Any]) -> None:
    """Record a trace event."""
    try:
        event_json = json.dumps(event)
        if _state.trace_file and not _state.trace_file.closed:
            with open(_state.trace_file.name, "a", encoding="utf-8") as f:
                f.write(event_json + "\n")
                f.flush()
    except (IOError, ValueError, TypeError) as e:
        print(f"Error recording trace event: {e}")


def _filter_frame(frame):
    """Filter frames to exclude system files."""
    if not frame:
        return None
    return frame


def _get_function_name(frame):
    """Get function name from frame."""
    return frame.f_code.co_name


def _format_value(value):
    """Format value for trace output."""
    return str(value)


def _cleanup_trace():
    """Clean up tracing resources."""
    sys.settrace(None)
    threading.settrace(None)
    if _state.trace_file and not _state.trace_file.closed:
        _state.trace_file.close()
