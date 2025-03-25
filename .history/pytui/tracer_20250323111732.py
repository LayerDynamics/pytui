"""Tracer module for capturing function calls and execution flow."""

import os
import sys
import inspect
import threading
import json
import atexit
from typing import Dict, Any, Optional

from .collector import get_collector


class FileState:
    """Manages trace file state."""

    def __init__(self):
        self.trace_file: Optional[Any] = None
        self.current_trace_file: Optional[Any] = None

    def close_files(self):
        """Close any open trace files."""
        if self.trace_file and not self.trace_file.closed:
            self.trace_file.close()
        if self.current_trace_file and not self.current_trace_file.closed:
            self.current_trace_file.close()

    def is_active(self) -> bool:
        """Check if any trace files are active."""
        return bool(self.trace_file or self.current_trace_file)


class CollectorState:
    """Manages collector state."""

    def __init__(self):
        self.collector: Optional[Any] = None
        self.current_collector: Optional[Any] = None

    def get_collector(self):
        """Get current collector instance."""
        return self.collector or self.current_collector

    def set_collector(self, collector):
        """Set collector instances."""
        self.collector = collector
        self.current_collector = collector

    def clear(self):
        """Clear all collector references."""
        self.collector = None
        self.current_collector = None


class CallState:
    """Manages call tracking state."""

    def __init__(self):
        self.call_stack: list = []
        self.current_call_stack: list = []
        self.current_call_id: int = 1
        self.last_call_id: int = 0

    def reset(self):
        """Reset call tracking state."""
        self.current_call_stack = []
        self.call_stack = []
        self.current_call_id = 1
        self.last_call_id = 0

    def get_current_call_info(self) -> dict:
        """Get current call stack information."""
        return {
            "current_id": self.current_call_id,
            "stack_depth": len(self.current_call_stack),
            "last_call": self.last_call_id,
        }


class TraceState:
    """Class to manage tracing state."""

    def __init__(self):
        self.files = FileState()
        self.collectors = CollectorState()
        self.calls = CallState()

    @property
    def trace_file(self):
        """Get the trace file."""
        return self.files.trace_file

    @trace_file.setter
    def trace_file(self, value):
        """Set the trace file."""
        self.files.trace_file = value

    @property
    def current_trace_file(self):
        """Get the current trace file."""
        return self.files.current_trace_file

    @current_trace_file.setter
    def current_trace_file(self, value):
        """Set the current trace file."""
        self.files.current_trace_file = value

    @property
    def collector(self):
        """Get the collector."""
        return self.collectors.collector

    @collector.setter
    def collector(self, value):
        """Set the collector."""
        self.collectors.collector = value

    @property
    def current_collector(self):
        """Get the current collector."""
        return self.collectors.current_collector

    @current_collector.setter
    def current_collector(self, value):
        """Set the current collector."""
        self.collectors.current_collector = value

    @property
    def current_call_stack(self):
        """Get the current call stack."""
        return self.calls.current_call_stack

    @current_call_stack.setter
    def current_call_stack(self, value):
        """Set the current call stack."""
        self.calls.current_call_stack = value

    def get_collector(self):
        """Get current collector instance."""
        return self.collectors.get_collector()

    def set_collector(self, collector):
        """Set collector instances."""
        self.collectors.set_collector(collector)

    def reset(self):
        """Reset state for new trace session."""
        self.calls.reset()
        self.files.close_files()


# Global state instance
_state = TraceState()


def trace_function(frame, event, arg):
    """Trace function for sys.settrace."""
    if not _is_valid_frame(frame):
        return trace_function

    handler = _get_event_handler(event)
    if handler:
        # Get the collector and any other needed arguments
        collector = _state.get_collector()
        if event == "call":
            func_name = frame.f_code.co_name
            filename = frame.f_code.co_filename
            return handler(frame, arg, func_name, filename, collector)
        if event == "return":
            func_name = frame.f_code.co_name
            return handler(arg, func_name, collector)
        if event == "exception":
            # Pass arg directly as it's the exception info tuple
            return handler(arg, collector)
    return trace_function


def _is_valid_frame(frame):
    """Check if frame is valid for tracing."""
    return (
        frame
        and frame.f_code
        and _should_trace_line(frame)
        and not _should_skip_file(frame.f_code.co_filename)
    )


def _get_event_handler(event):
    """Get appropriate handler for event type."""
    handlers = {
        "call": _handle_call_event,
        "return": _handle_return_event,
        "exception": _handle_exception_event,
    }
    return handlers.get(event)


def _handle_call_event(frame, arg, func_name, filename, collector):
    """Handle function call events.

    Args:
        frame: The execution frame
        arg: An argument that will be used if callable; otherwise, its representation will be recorded.
        func_name: Name of the function being called
        filename: File in which the function is defined
        collector: Data collector instance
    """
    try:
        if func_name.startswith("__") or func_name == "<module>":
            return trace_function

        line_no = frame.f_lineno
        args_dict = _get_function_args(frame)

        # Use arg: call it if it's callable, otherwise record its repr.
        if callable(arg):
            try:
                arg_result = arg()
                args_dict["arg_result"] = repr(arg_result)
            except (TypeError, ValueError) as e:
                args_dict["arg_result"] = f"<error calling arg: {e}>"
        else:
            args_dict["arg_value"] = repr(arg)

        call_id = _state.calls.current_call_id
        _state.calls.current_call_id += 1
        parent_id = (
            _state.calls.current_call_stack[-1]
            if _state.calls.current_call_stack
            else None
        )
        _state.calls.current_call_stack.append(call_id)

        # Record both locally and via IPC
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
        return trace_function
    except (AttributeError, TypeError, ValueError) as e:
        print(f"Error in call event handler: {e}")
        return trace_function


def _handle_return_event(arg, func_name, collector):
    """Handle function return events."""
    if _state.calls.current_call_stack:
        call_id = _state.calls.current_call_stack.pop()
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
    # Return the trace function to continue handling further events.
    return trace_function


def _handle_exception_event(exc_info, collector):
    """Handle exception events."""
    # Use exc_info directly now that we're passing it correctly
    _, exc_value, _ = exc_info
    collector.add_exception(exc_value)
    _send_trace_event("exception", {"exception": repr(exc_value)})
    return trace_function


def _get_collector():
    """Get the current collector instance."""
    collector = _state.collectors.get_collector()
    if collector is not None:
        return collector
    
    # Create a new collector if none exists
    from .collector import get_collector
    new_collector = get_collector()
    _state.collectors.set_collector(new_collector)
    return new_collector


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
    if not _state.files.current_trace_file:
        return

    try:
        event_data = {"type": event_type, **func_data}
        if event_type == "call" and func_data.get("function_name") == "function1":
            print("Debug: Traced function1 call, writing to trace file")
            print("DEBUG_TRACE: function1 called", file=sys.stderr)

        with open(_state.files.current_trace_file.name, "a", encoding="utf-8") as f:
            json_data = json.dumps(event_data)
            f.write(json_data + "\n")
            f.flush()
            if event_type == "call" and func_data.get("function_name") == "function1":
                os.fsync(f.fileno())
    except (IOError, TypeError, ValueError) as exc:
        print(f"Error writing trace data: {exc}")


def flush_trace():
    """Flush the trace file before exiting."""
    if _state.files.current_trace_file is not None:
        try:
            _state.files.current_trace_file.flush()
        except IOError:
            pass


def install_trace(collector=None, trace_path=None):
    """Install the trace function with optional IPC.

    Args:
        collector: DataCollector instance to use
        trace_path: Path to file for IPC with parent process
    """
    # Reset state before setting the collector, not after
    _state.reset()
    # Set the collector
    _state.set_collector(collector or get_collector())

    if trace_path:
        try:
            with open(trace_path, "w", encoding="utf-8") as trace_file:
                trace_file.write('{"test": "write"}\n')
                trace_file.flush()
                _state.files.current_trace_file = trace_file
                _state.files.trace_file = trace_file

            def cleanup_trace():
                if _state.files.trace_file and not _state.files.trace_file.closed:
                    _state.files.trace_file.close()

            atexit.register(flush_trace)
            atexit.register(cleanup_trace)
        except (IOError, OSError, PermissionError) as exc:
            print(f"Failed to open trace file: {exc}")

    sys.settrace(trace_function)
    threading.settrace(trace_function)
    return _state.collectors.current_collector


def _should_trace_line(frame) -> bool:
    """Determine if a line should be traced."""
    return frame.f_code.co_filename.endswith(".py")


def _get_call_id() -> int:
    """Generate unique call ID."""
    _state.calls.last_call_id += 1
    return _state.calls.last_call_id


def _get_parent_id() -> int:
    """Get parent call ID from stack."""
    return (
        _state.calls.current_call_stack[-1] if _state.calls.current_call_stack else None
    )


def _trace_call(frame, event, arg) -> None:
    """Handle function call events."""
    if not _should_trace_line(frame):
        return None

    try:
        if event == "call":
            _handle_call_event(
                frame,
                arg,
                frame.f_code.co_name,
                frame.f_code.co_filename,
                _state.get_collector(),  # Add the missing collector argument
            )
            return _trace_call
        if event == "return":
            _handle_return_event(arg, frame.f_code.co_name, _state.get_collector())
        return None
    except (ValueError, AttributeError, TypeError) as e:
        print(f"Error in trace call: {e}")
        return None


def _record_trace_event(event: Dict[str, Any]) -> None:
    """Record a trace event."""
    try:
        event_json = json.dumps(event)
        if _state.files.trace_file and not _state.files.trace_file.closed:
            with open(_state.files.trace_file.name, "a", encoding="utf-8") as f:
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
    if _state.files.trace_file and not _state.files.trace_file.closed:
        _state.files.trace_file.close()


# For compatibility with tests that import _current_collector
_current_collector = _state.get_collector()
