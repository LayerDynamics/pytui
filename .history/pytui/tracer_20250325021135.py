"""Tracer module for capturing function calls and execution flow."""

import os
import sys
import inspect
import threading
import json
import atexit
from typing import Dict, Any, Optional

# First party imports
from pytui.collector import DataCollector, CallEvent, ReturnEvent, ExceptionEvent
from pytui.utils import safe_repr

# Local imports
from .collector import get_collector

# Global collector reference
COLLECTOR = None  # Changed from _collector to UPPER_CASE
# Global call stack (needed for test compatibility)
_call_stack = []


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


def _should_skip_file(filename: str) -> bool:
    """Check if file should be skipped for tracing."""
    # Convert to forward slashes for consistent checking
    normalized_path = filename.replace("\\", "/")
    # Always allow test files
    if "/tests/" in normalized_path:
        return False
    # Skip internal pytui files
    return "/pytui/" in normalized_path


def _handle_call_with_collector(collector, is_internal, call_event):
    """Handle call event with collector."""
    if not is_internal:
        collector.add_call(
            call_event.function_name,
            call_event.filename,
            call_event.line_no,
            call_event.args
        )
    return trace_function


def _handle_return_with_collector(collector, is_internal, return_event):
    """Handle return event with collector."""
    if not is_internal:
        collector.add_return(
            return_event.function_name,
            return_event.return_value,
            call_id=return_event.call_id
        )


def trace_function(frame, event, arg):
    """Trace function for collecting execution data."""
    global COLLECTOR, _call_stack

    if COLLECTOR is None:
        return None

    # Check if this is an internal module
    is_internal = _should_skip_file(frame.f_code.co_filename)

    if is_internal:
        # For internal files, we only want to continue tracing on "call" events
        return trace_function if event == "call" else None

    try:
        if event == "call":
            COLLECTOR.add_call(
                frame.f_code.co_name,
                frame.f_code.co_filename,
                frame.f_lineno,
                frame.f_locals
            )
            _call_stack.append(frame.f_code.co_name)
            return trace_function

        elif event == "return" and _call_stack:
            func_name = _call_stack.pop() if _call_stack else frame.f_code.co_name
            COLLECTOR.add_return(func_name, arg)
            return trace_function

        elif event == "exception":
            exc_type, exc_value, _ = arg
            COLLECTOR.add_exception(exc_value)
            return trace_function

    except Exception as e:
        print(f"Error in trace_function ({event}): {e}")
        
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
        try:
            return_value_str = safe_repr(arg)
        except (ValueError, TypeError, AttributeError):
            return_value_str = "<unrepresentable>"

        collector.add_return(func_name, return_value_str, call_id=call_id)
        _send_trace_event(
            "return",
            {
                "function_name": func_name,
                "return_value": return_value_str,
                "call_id": call_id,
            },
        )
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

    # Create a new collector without reimporting
    new_collector = get_collector()
    _state.collectors.set_collector(new_collector)
    return new_collector


def _get_function_args(frame) -> Dict[str, str]:
    """Extract function arguments from frame."""

    def format_collection(value, max_items=3):
        """Helper to format collection types."""
        length = len(value)
        if length <= max_items:
            return repr(value)
        sample = list(value)[:max_items]
        return f"{type(value).__name__}[{length}] {repr(sample)[:-1]}, ...]"

    args_dict = {}
    try:
        args = inspect.getargvalues(frame)
        for arg_name in args.args:
            if arg_name not in args.locals:
                continue

            try:
                value = args.locals[arg_name]
                if isinstance(value, (int, float, bool, str, type(None))):
                    args_dict[arg_name] = repr(value)
                elif isinstance(value, (list, tuple, set)):
                    args_dict[arg_name] = format_collection(value)
                elif isinstance(value, dict):
                    args_dict[arg_name] = format_collection(value)
                elif hasattr(value, "__class__"):
                    cls_name = value.__class__.__name__
                    module = value.__class__.__module__
                    str_value = str(value)[:50]
                    args_dict[arg_name] = f"{module}.{cls_name}: {str_value}"
                else:
                    args_dict[arg_name] = repr(value)[:100]
            except (ValueError, TypeError) as e:
                args_dict[arg_name] = f"<unable to represent: {e}>"
    except (ValueError, TypeError, AttributeError) as e:
        print(f"Error getting function args: {e}")
    return args_dict


def _send_trace_event(event_type: str, func_data: Dict[str, Any]):
    """Send an event via IPC if trace file is available."""
    if not _state.files.current_trace_file:
        return

    try:
        event_data = {"type": event_type, **func_data}
        should_debug = (
            event_type == "call" and func_data.get("function_name") == "function1"
        )

        if should_debug:
            print("Debug: Traced function1 call, writing to trace file")
            print("DEBUG_TRACE: function1 called", file=sys.stderr)

        with open(_state.files.current_trace_file.name, "a", encoding="utf-8") as f:
            json_data = json.dumps(event_data)
            f.write(json_data + "\n")
            f.flush()
            if should_debug:
                os.fsync(f.fileno())
    except (IOError, TypeError, ValueError) as exc:
        print(f"Error writing trace data: {exc}")


def flush_trace():
    """Flush the trace file before exiting."""
    try:
        if (
            _state.files.current_trace_file is not None
            and not _state.files.current_trace_file.closed
        ):
            _state.files.current_trace_file.flush()
    except (IOError, ValueError):
        # Ignore errors on flush during shutdown
        pass


def install_trace(collector=None, trace_path=None):
    """Install the trace function with optional IPC.

    Args:
        collector: DataCollector instance to use
        trace_path: Path to file for IPC with parent process
    """
    global COLLECTOR
    _call_stack.clear()
    _state.reset()

    if collector is None:
        collector = DataCollector()

    # Set both state and global collector
    _state.set_collector(collector)
    COLLECTOR = collector  # Ensure global collector is set

    if trace_path:
        try:
            with open(trace_path, "w", encoding="utf-8") as trace_file:
                trace_file.write('{"type": "test", "message": "Trace file is working"}\n')
                trace_file.flush()
                os.fsync(trace_file.fileno())

            _state.files.current_trace_file = open(trace_path, "a", encoding="utf-8")
            _state.files.trace_file = _state.files.current_trace_file
            atexit.register(flush_trace)
            atexit.register(_state.files.close_files)
        except (IOError, OSError, PermissionError) as exc:
            print(f"Failed to open trace file: {exc}")

    sys.settrace(trace_function)
    threading.settrace(trace_function)
    return collector


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
pytest --run-slow
========================================================= test session starts ==========================================================
platform darwin -- Python 3.13.2, pytest-8.3.5, pluggy-1.5.0 -- /opt/miniconda3/envs/pytui/bin/python3.13
cachedir: .pytest_cache
rootdir: /Users/ryanoboyle/pytui
configfile: pytest.ini
testpaths: pytui/tests
plugins: asyncio-0.25.3
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=function
collected 61 items                                                                                                                     

pytui/tests/test_cli.py::test_cli_help PASSED                                                                                    [  1%]
pytui/tests/test_cli.py::test_run_command_help PASSED                                                                            [  3%]
pytui/tests/test_cli.py::test_run_missing_script PASSED                                                                          [  4%]
pytui/tests/test_cli.py::test_run_script PASSED                                                                                  [  6%]
pytui/tests/test_collector.py::test_add_output PASSED                                                                            [  8%]
pytui/tests/test_collector.py::test_add_call PASSED                                                                              [  9%]
pytui/tests/test_collector.py::test_add_nested_call PASSED                                                                       [ 11%]
pytui/tests/test_collector.py::test_add_return PASSED                                                                            [ 13%]
pytui/tests/test_collector.py::test_add_exception PASSED                                                                         [ 14%]
pytui/tests/test_collector.py::test_clear PASSED                                                                                 [ 16%]
pytui/tests/test_collector.py::test_event_queue PASSED                                                                           [ 18%]
pytui/tests/test_error_handling.py::test_error_handling SKIPPED (use --run-slow to run)                                          [ 19%]
pytui/tests/test_error_handling.py::test_long_running_script_termination SKIPPED (use --run-slow to run)                         [ 21%]
pytui/tests/test_error_handling.py::test_stdout_flood_handling SKIPPED (use --run-slow to run)                                   [ 22%]
pytui/tests/test_error_handling.py::test_executor_start_stop_restart_stress PASSED                                               [ 24%]
pytui/tests/test_error_handling.py::test_executor_async_operations Debug: Found 1 lines in trace file
Debug: First few trace lines:
  Line 1 : {"type": "test", "message": "Trace file is working"}
Debug: Processed 0 call events and 0 return events with 0 errors
Debug: Attempting alternative parsing method...
Debug: Alternative parsing found 0 calls
PASSED                                                        [ 26%]
pytui/tests/test_executor.py::test_executor_initialization PASSED                                                                [ 27%]
pytui/tests/test_executor.py::test_integration Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
FAILED                                                                            [ 29%]
pytui/tests/test_executor.py::test_pause_resume PASSED                                                                           [ 31%]
pytui/tests/test_executor.py::test_stop_functionality PASSED                                                                     [ 32%]
pytui/tests/test_executor.py::test_restart_functionality PASSED                                                                  [ 34%]
pytui/tests/test_executor.py::test_tracer_integration PASSED                                                                     [ 36%]
pytui/tests/test_executor.py::test_mock_executor PASSED                                                                          [ 37%]
pytui/tests/test_executor_stress.py::test_large_output_handling SKIPPED (Temporary skip due to concurrency issues.)              [ 39%]
pytui/tests/test_executor_stress.py::test_recursive_function_tracing SKIPPED (Temporary skip due to concurrency issues.)         [ 40%]
pytui/tests/test_executor_stress.py::test_multiple_script_execution SKIPPED (Temporary skip due to concurrency issues.)          [ 42%]
pytui/tests/test_executor_stress.py::test_process_cleanup_on_error SKIPPED (Temporary skip due to concurrency issues.)           [ 44%]
pytui/tests/test_integration.py::test_pytui_app_integration PASSED                                                               [ 45%]
pytui/tests/test_integration.py::test_app_actions PASSED                                                                         [ 47%]
pytui/tests/test_integration_complex.py::test_app_initialization PASSED                                                          [ 49%]
pytui/tests/test_integration_complex.py::test_output_processing PASSED                                                           [ 50%]
pytui/tests/test_integration_complex.py::test_call_processing PASSED                                                             [ 52%]
pytui/tests/test_integration_complex.py::test_return_processing PASSED                                                           [ 54%]
pytui/tests/test_integration_complex.py::test_exception_processing PASSED                                                        [ 55%]D
ebug: Trace file exists, size: 0                                                                                                        Debug: Trace file is empty, retrying...

pytui/tests/test_integration_complex.py::test_pause_resume_functionality PASSED                                                  [ 57%]
pytui/tests/test_integration_complex.py::test_restart_functionality PASSED                                                       [ 59%]
pytui/tests/test_integration_complex.py::test_search_functionality PASSED                                                        [ 60%]
pytui/tests/test_integration_complex.py::test_collapse_functionality PASSED                                                      [ 62%]
pytui/tests/test_integration_complex.py::test_variable_display_toggle PASSED                                                     [ 63%]
pytui/tests/test_integration_complex.py::test_metrics_toggle PASSED                                                              [ 65%]
pytui/tests/test_performance.py::test_executor_overhead SKIPPED (Temporary skip due to performance instability.)                 [ 67%]
pytui/tests/test_performance.py::test_tracer_function_performance SKIPPED (async def function and no async plugin installed ...) [ 68%]
pytui/tests/test_performance.py::test_collector_event_throughput PASSED                                                          [ 70%]
pytui/tests/test_tracer.py::test_get_collector PASSED                                                                            [ 72%]
pytui/tests/test_tracer.py::test_trace_function_call Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
FAILED                                                                      [ 73%]
pytui/tests/test_tracer.py::test_trace_function_return FAILED                                                                    [ 75%]
pytui/tests/test_tracer.py::test_trace_function_exception FAILED                                                                 [ 77%]
pytui/tests/test_tracer.py::test_trace_function_skips_internal PASSED                                                            [ 78%]
pytui/tests/test_tracer.py::test_install_trace Debug: Trace file exists, size: 0
PASSED                                                                            [ 80%]Debug: Trace file is empty, retrying...

pytui/tests/test_tracing_debug.py::test_debug_function_tracing SKIPPED (No function calls traced - skipping assertion)           [ 81%]
pytui/tests/test_tracing_debug.py::test_trace_function_direct FAILED                                                             [ 83%]
pytui/tests/test_tracing_debug.py::test_trace_function_output FAILED                                                             [ 85%]
pytui/tests/test_ui_components.py::test_status_bar_init PASSED                                                                   [ 86%]
pytui/tests/test_ui_components.py::test_status_bar_render PASSED                                                                 [ 88%]
pytui/tests/test_ui_components.py::test_output_panel PASSED                                                                      [ 90%]
pytui/tests/test_ui_components.py::test_call_graph_panel PASSED                                                                  [ 91%]
pytui/tests/test_ui_components.py::test_exception_panel PASSED                                                                   [ 93%]
pytui/tests/test_utils.py::test_get_module_path PASSED                                                                           [ 95%]
pytui/tests/test_utils.py::test_format_time PASSED                                                                               [ 96%]
pytui/tests/test_utils.py::test_truncate_string PASSED                                                                           [ 98%]
pytui/tests/test_utils.py::test_safe_repr PASSED                                                                                 [100%]

=============================================================== FAILURES ===============================================================
___________________________________________________________ test_integration ___________________________________________________________

sample_script = '/var/folders/16/w598_8dn2db6kl086m_9wtfm0000gn/T/tmpsg24o4s2.py'

    def test_integration(sample_script):
        """Test the complete integration of ScriptExecutor."""
        # Set up test environment
        test_state = setup_test_environment(sample_script)
    
        # Execute the verification steps
        verify_process_started(test_state)
        verify_collector_setup(test_state)
        verify_data_collection(test_state)
>       verify_call_events(test_state)

pytui/tests/test_executor.py:208: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

test_state = {'executor': <pytui.executor.ScriptExecutor object at 0x106dc83e0>, 'start_time': 1742893863.5708318}

    def verify_call_events(test_state):
        """Verify call events are captured."""
        executor = test_state["executor"]
        # Check for function calls
>       assert len(executor.collector.calls) > 0
E       assert 0 > 0
E        +  where 0 = len([])
E        +    where [] = <pytui.collector.DataCollector object at 0x106ecbf20>.calls
E        +      where <pytui.collector.DataCollector object at 0x106ecbf20> = <pytui.executor.ScriptExecutor object at 0x106dc83e0>.coll
ector                                                                                                                                   
pytui/tests/test_executor.py:168: AssertionError
--------------------------------------------------------- Captured stdout call ---------------------------------------------------------
Debug: Reading trace data from /var/folders/16/w598_8dn2db6kl086m_9wtfm0000gn/T/pytui_trace_grhqocsn.jsonl
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 53
Debug: Found 1 lines in trace file
Debug: First few trace lines:
  Line 1 : {"type": "test", "message": "Trace file is working"}
Debug: Processed 0 call events and 0 return events with 0 errors
Debug: Attempting alternative parsing method...
Debug: Alternative parsing found 0 calls
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
Debug: Trace file exists, size: 0
Debug: Trace file is empty, retrying...
_______________________________________________________ test_trace_function_call _______________________________________________________

mock_frame = <pytui.tests.test_tracer.mock_frame.<locals>.MockFrame object at 0x106fcfe00>, mock_collector = <MagicMock id='4412210016'>

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
    
>           mock_collector.add_call.assert_called_once()

pytui/tests/test_tracer.py:74: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <MagicMock name='mock.add_call' id='4412209344'>

    def assert_called_once(self):
        """assert that the mock was called only once.
        """
        if not self.call_count == 1:
            msg = ("Expected '%s' to have been called once. Called %s times.%s"
                   % (self._mock_name or 'mock',
                      self.call_count,
                      self._calls_repr()))
>           raise AssertionError(msg)
E           AssertionError: Expected 'add_call' to have been called once. Called 0 times.

/opt/miniconda3/envs/pytui/lib/python3.13/unittest/mock.py:956: AssertionError
______________________________________________________ test_trace_function_return ______________________________________________________

mock_frame = <pytui.tests.test_tracer.mock_frame.<locals>.MockFrame object at 0x106fcfa10>, mock_collector = <MagicMock id='4412208336'>

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
>           mock_collector.add_return.assert_called_once()

pytui/tests/test_tracer.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <MagicMock name='mock.add_return' id='4412197920'>

    def assert_called_once(self):
        """assert that the mock was called only once.
        """
        if not self.call_count == 1:
            msg = ("Expected '%s' to have been called once. Called %s times.%s"
                   % (self._mock_name or 'mock',
                      self.call_count,
                      self._calls_repr()))
>           raise AssertionError(msg)
E           AssertionError: Expected 'add_return' to have been called once. Called 0 times.

/opt/miniconda3/envs/pytui/lib/python3.13/unittest/mock.py:956: AssertionError
____________________________________________________ test_trace_function_exception _____________________________________________________

mock_frame = <pytui.tests.test_tracer.mock_frame.<locals>.MockFrame object at 0x106fcc6e0>, mock_collector = <MagicMock id='4412198256'>

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
>           mock_collector.add_exception.assert_called_once_with(exception)

pytui/tests/test_tracer.py:126: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <MagicMock name='mock.add_exception' id='4412203632'>, args = (ValueError('test exception'),), kwargs = {}
msg = "Expected 'add_exception' to be called once. Called 0 times."

    def assert_called_once_with(self, /, *args, **kwargs):
        """assert that the mock was called exactly once and that that call was
        with the specified arguments."""
        if not self.call_count == 1:
            msg = ("Expected '%s' to be called once. Called %s times.%s"
                   % (self._mock_name or 'mock',
                      self.call_count,
                      self._calls_repr()))
>           raise AssertionError(msg)
E           AssertionError: Expected 'add_exception' to be called once. Called 0 times.

/opt/miniconda3/envs/pytui/lib/python3.13/unittest/mock.py:988: AssertionError
______________________________________________________ test_trace_function_direct ______________________________________________________

    def test_trace_function_direct():
        """Test trace_function directly without executor."""
    
        # Create a frame-like object
        class MockFrame:
            """Mock frame for testing trace_function."""
    
            f_code = type(
                "Code",
                (),
                {
                    "co_name": "sample_function",
                    "co_filename": "test_file.py",
                    "co_firstlineno": 1,
                },
            )
            f_lineno = 1
            f_locals = {"x": 42}
    
        frame = MockFrame()
    
        # Test call event
        result = trace_function(frame, "call", None)
        assert (
            result is trace_function
        ), "Trace function should return itself for call events"
    
        # Test return event
        trace_function(frame, "return", 84)  # Return value from sample_function(42)
    
        # Test that trace_function ignores internal files
        frame.f_code.co_filename = "/path/to/pytui/tracer.py"
        result = trace_function(frame, "call", None)
>       assert result is None, "Should ignore internal pytui files"
E       AssertionError: Should ignore internal pytui files
E       assert <function trace_function at 0x106e76b60> is None

pytui/tests/test_tracing_debug.py:135: AssertionError
______________________________________________________ test_trace_function_output ______________________________________________________

    def test_trace_function_output():
        """Test that trace_function properly captures output."""
        import types
    
        # Create a real code object instead of mock
        code = compile("def test(): pass", "test.py", "exec")
        test_code = [c for c in code.co_consts if isinstance(c, types.CodeType)][0]
    
        class FrameInfo:
            f_code = test_code
            f_lineno = 1
            f_locals = {}
    
        frame = FrameInfo()
    
        collector = get_collector()
        trace_result = trace_function(frame, "call", None)
    
        # Verify trace behavior
        assert trace_result is trace_function
>       assert len(collector.calls) > 0
E       assert 0 > 0
E        +  where 0 = len([])
E        +    where [] = <pytui.collector.DataCollector object at 0x1070b0550>.calls

pytui/tests/test_tracing_debug.py:158: AssertionError
=========================================================== warnings summary ===========================================================
pytui/tests/test_integration_complex.py:63
  /Users/ryanoboyle/pytui/pytui/tests/test_integration_complex.py:63: PytestCollectionWarning: cannot collect test class 'TestException'
 because it has a __init__ constructor (from: pytui/tests/test_integration_complex.py)                                                      class TestException(Exception):

pytui/tests/test_performance.py:151
  /Users/ryanoboyle/pytui/pytui/tests/test_performance.py:151: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  
You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html                   @pytest.mark.timeout(10)

pytui/tests/test_error_handling.py::test_executor_async_operations
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/threadexception.py:82: PytestUnhandledThreadExceptionWarning: Exceptio
n in thread Thread-18 (_monitor_process)                                                                                                  
  Traceback (most recent call last):
    File "/opt/miniconda3/envs/pytui/lib/python3.13/threading.py", line 1041, in _bootstrap_inner
      self.run()
      ~~~~~~~~^^
    File "/opt/miniconda3/envs/pytui/lib/python3.13/threading.py", line 992, in run
      self._target(*self._args, **self._kwargs)
      ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/ryanoboyle/pytui/pytui/executor.py", line 510, in _monitor_process
      returncode = self.process.wait()
                   ^^^^^^^^^^^^^^^^^
  AttributeError: 'NoneType' object has no attribute 'wait'
  
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

pytui/tests/test_executor.py::test_integration
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/threadexception.py:82: PytestUnhandledThreadExceptionWarning: Exceptio
n in thread Thread-38 (_monitor_process)                                                                                                  
  Traceback (most recent call last):
    File "/opt/miniconda3/envs/pytui/lib/python3.13/threading.py", line 1041, in _bootstrap_inner
      self.run()
      ~~~~~~~~^^
    File "/opt/miniconda3/envs/pytui/lib/python3.13/threading.py", line 992, in run
      self._target(*self._args, **self._kwargs)
      ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/ryanoboyle/pytui/pytui/executor.py", line 510, in _monitor_process
      returncode = self.process.wait()
                   ^^^^^^^^^^^^^^^^^
  AttributeError: 'NoneType' object has no attribute 'wait'
  
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

pytui/tests/test_integration.py::test_pytui_app_integration
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/threadexception.py:82: PytestUnhandledThreadExceptionWarning: Exceptio
n in thread Thread-58 (_monitor_process)                                                                                                  
  Traceback (most recent call last):
    File "/opt/miniconda3/envs/pytui/lib/python3.13/threading.py", line 1041, in _bootstrap_inner
      self.run()
      ~~~~~~~~^^
    File "/opt/miniconda3/envs/pytui/lib/python3.13/threading.py", line 992, in run
      self._target(*self._args, **self._kwargs)
      ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/ryanoboyle/pytui/pytui/executor.py", line 510, in _monitor_process
      returncode = self.process.wait()
                   ^^^^^^^^^^^^^^^^^
  AttributeError: 'NoneType' object has no attribute 'wait'
  
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

pytui/tests/test_integration_complex.py::test_return_processing
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/threadexception.py:82: PytestUnhandledThreadExceptionWarning: Exceptio
n in thread Thread-63 (_monitor_process)                                                                                                  
  Traceback (most recent call last):
    File "/opt/miniconda3/envs/pytui/lib/python3.13/threading.py", line 1041, in _bootstrap_inner
      self.run()
      ~~~~~~~~^^
    File "/opt/miniconda3/envs/pytui/lib/python3.13/threading.py", line 992, in run
      self._target(*self._args, **self._kwargs)
      ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/ryanoboyle/pytui/pytui/executor.py", line 510, in _monitor_process
      returncode = self.process.wait()
                   ^^^^^^^^^^^^^^^^^
  AttributeError: 'NoneType' object has no attribute 'wait'
  
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

pytui/tests/test_integration_complex.py::test_exception_processing
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/python.py:159: RuntimeWarning: coroutine 'test_exception_processing' w
as never awaited                                                                                                                            result = testfunction(**testargs)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

pytui/tests/test_integration_complex.py::test_pause_resume_functionality
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/python.py:159: RuntimeWarning: coroutine 'test_pause_resume_functional
ity' was never awaited                                                                                                                      result = testfunction(**testargs)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

pytui/tests/test_integration_complex.py::test_restart_functionality
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/python.py:159: RuntimeWarning: coroutine 'test_restart_functionality' 
was never awaited                                                                                                                           result = testfunction(**testargs)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

pytui/tests/test_integration_complex.py::test_search_functionality
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/python.py:159: RuntimeWarning: coroutine 'test_search_functionality' w
as never awaited                                                                                                                            result = testfunction(**testargs)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

pytui/tests/test_integration_complex.py::test_collapse_functionality
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/python.py:159: RuntimeWarning: coroutine 'test_collapse_functionality'
 was never awaited                                                                                                                          result = testfunction(**testargs)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

pytui/tests/test_integration_complex.py::test_variable_display_toggle
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/python.py:159: RuntimeWarning: coroutine 'test_variable_display_toggle
' was never awaited                                                                                                                         result = testfunction(**testargs)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

pytui/tests/test_integration_complex.py::test_metrics_toggle
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/python.py:159: RuntimeWarning: coroutine 'test_metrics_toggle' was nev
er awaited                                                                                                                                  result = testfunction(**testargs)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

pytui/tests/test_performance.py::test_tracer_function_performance
  /opt/miniconda3/envs/pytui/lib/python3.13/site-packages/_pytest/python.py:148: PytestUnhandledCoroutineWarning: async def functions ar
e not natively supported and have been skipped.                                                                                           You need to install a suitable plugin for your async framework, for example:
    - anyio
    - pytest-asyncio
    - pytest-tornasync
    - pytest-trio
    - pytest-twisted
    warnings.warn(PytestUnhandledCoroutineWarning(msg.format(nodeid)))

pytui/tests/test_tracer.py::test_trace_function_skips_internal
pytui/tests/test_tracer.py::test_trace_function_skips_internal
pytui/tests/test_tracer.py::test_trace_function_skips_internal
  /Users/ryanoboyle/pytui/pytui/tests/test_tracer.py:41: DeprecationWarning: co_lnotab is deprecated, use co_lines instead.
    setattr(self, attr, getattr(original_code, attr))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================================================= short test summary info ========================================================
FAILED pytui/tests/test_executor.py::test_integration - assert 0 > 0
FAILED pytui/tests/test_tracer.py::test_trace_function_call - AssertionError: Expected 'add_call' to have been called once. Called 0 tim
es.                                                                                                                                     FAILED pytui/tests/test_tracer.py::test_trace_function_return - AssertionError: Expected 'add_return' to have been called once. Called 0
 times.                                                                                                                                 FAILED pytui/tests/test_tracer.py::test_trace_function_exception - AssertionError: Expected 'add_exception' to be called once. Called 0 
times.                                                                                                                                  FAILED pytui/tests/test_tracing_debug.py::test_trace_function_direct - AssertionError: Should ignore internal pytui files
FAILED pytui/tests/test_tracing_debug.py::test_trace_function_output - assert 0 > 0
======================================== 6 failed, 45 passed, 10 skipped, 17 warnings in 23.91s ========================================
