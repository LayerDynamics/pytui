"""Runtime data collector for aggregating execution events."""

import threading
import time
import asyncio
from typing import Dict, List, Optional  # Removed "Any"
from dataclasses import dataclass, field
import traceback  # Moved from inside methods


@dataclass
class CallEvent:
    """Function call event data."""

    function_name: str
    filename: str
    line_no: int
    args: Dict[str, str]
    timestamp: float = field(default_factory=time.time)
    call_id: int = 0
    parent_id: Optional[int] = None


@dataclass
class ReturnEvent:
    """Function return event data."""

    function_name: str
    return_value: str
    timestamp: float = field(default_factory=time.time)
    call_id: int = 0


@dataclass
class ExceptionEvent:
    """Exception event data."""

    exception_type: str
    message: str
    traceback: List[str]
    timestamp: float = field(default_factory=time.time)


@dataclass
class OutputLine:
    """Output line data."""

    content: str
    stream: str  # 'stdout', 'stderr', or 'system'
    timestamp: float = field(default_factory=time.time)


# Singleton collector instance - renamed to follow UPPER_CASE convention
COLLECTOR = None


def get_collector():
    """Get or create the singleton collector instance."""
    # Use module-level function lookup instead of global statement
    if globals().get("COLLECTOR") is None:
        globals()["COLLECTOR"] = DataCollector()
    return globals()["COLLECTOR"]


# pylint: disable=too-many-instance-attributes
class DataCollector:
    """Collects runtime data from execution."""

    def __init__(self):
        """Initialize the data collector."""
        self.lock = threading.RLock()
        self.call_stack = []
        self.next_call_id = 1

        # Consolidate event storage into one dictionary.
        self.events: Dict[str, List] = {
            "calls": [],
            "returns": [],
            "exceptions": [],
            "output": [],
        }

        # Instead of event_queues, use a Queue object that's not bound to any loop
        # and a thread-safe mechanism to notify waiting coroutines
        self.loop = None
        self.event_queues = {}
        self.events_list = []  # Store events in a thread-safe list
        self.event_ready = threading.Event()  # Signal when new events are available

    @property
    def output(self):
        """Get output events list for backward compatibility."""
        return self.events["output"]

    @property
    def calls(self):
        """Get call events list for backward compatibility."""
        return self.events["calls"]

    @property
    def returns(self):
        """Get return events list for backward compatibility."""
        return self.events["returns"]

    @property
    def exceptions(self):
        """Get exception events list for backward compatibility."""
        return self.events["exceptions"]

    def _get_loop(self):
        """Return the currently running loop and update stored loop if available."""
        try:
            current = asyncio.get_running_loop()
            self.loop = current  # refresh stored loop
            return current
        except RuntimeError:
            # No running loop - this is probably called from a non-async context
            if self.loop and not self.loop.is_closed():
                return self.loop
            # Create a new loop if we don't have one
            self.loop = asyncio.new_event_loop()
            return self.loop

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def add_call(
        self, function_name, filename, line_no, args, call_id=None, parent_id=None
    ):
        """Add a function call event."""
        with self.lock:
            # Use provided call_id if available
            if call_id is None:
                call_id = self.next_call_id
                self.next_call_id += 1
            else:
                # Update next_call_id if needed
                self.next_call_id = max(self.next_call_id, call_id + 1)

            # Use provided parent_id if available
            if parent_id is None and self.call_stack:
                parent_id = self.call_stack[-1]

            call = CallEvent(
                function_name=function_name,
                filename=filename,
                line_no=line_no,
                args=args,
                call_id=call_id,
                parent_id=parent_id,
            )

            self.events["calls"].append(call)
            self.call_stack.append(call_id)

            self.events_list.append(("call", call))
            self.event_ready.set()

    def add_return(self, function_name, return_value, call_id=None):
        """Add a function return event."""
        with self.lock:
            # Get call_id from stack if not provided
            if call_id is None:
                if not self.call_stack:
                    return
                call_id = self.call_stack.pop()
            else:
                # Remove matching call_id from stack if it exists
                if call_id in self.call_stack:
                    self.call_stack.remove(call_id)

            ret = ReturnEvent(
                function_name=function_name, return_value=return_value, call_id=call_id
            )

            self.events["returns"].append(ret)
            self.events_list.append(("return", ret))
            self.event_ready.set()

    def add_exception(self, exception):
        """Add an exception event."""
        with self.lock:
            exc_type = type(exception).__name__
            message = str(exception)
            tb_lines = traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )

            exc = ExceptionEvent(
                exception_type=exc_type, message=message, traceback=tb_lines
            )

            self.events["exceptions"].append(exc)

            # Add to event list
            self.events_list.append(("exception", exc))
            self.event_ready.set()

    def add_output(self, content: str, stream: str):
        """Add an output line."""
        with self.lock:
            line = OutputLine(content=content, stream=stream)
            self.events["output"].append(line)

            # Add to event list
            self.events_list.append(("output", line))
            self.event_ready.set()

    def clear(self):
        """Clear all collected data."""
        with self.lock:
            self.events["calls"].clear()
            self.events["returns"].clear()
            self.events["exceptions"].clear()
            self.events["output"].clear()
            self.call_stack.clear()
            self.next_call_id = 1
            self.events_list.clear()
            self.event_ready.clear()

    async def get_event(self):
        """Get next event from the queue for the current loop."""
        while True:
            # Check if there are events in the list
            with self.lock:
                if self.events_list:
                    return self.events_list.pop(0)

            # No events available, wait for the event to be set
            # Use asyncio.sleep for cooperative multitasking
            self.event_ready.wait(0.1)  # Short timeout to allow checking again
            if not self.event_ready.is_set():
                await asyncio.sleep(0.1)  # Yield to event loop
            else:
                self.event_ready.clear()  # Reset for next wait

    def flush(self):
        """Flush any pending events."""
        # This is a no-op in the parent process but can be used
        # to flush events in the child process if needed
        # Removed unnecessary pass statement
