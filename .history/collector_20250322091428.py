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


# Singleton collector instance
_collector = None


def get_collector():
    """Get or create the singleton collector instance."""
    global _collector
    if _collector is None:
        _collector = DataCollector()
    return _collector


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

    # Added for backward compatibility with tests
    @property
    def output(self):
        return self.events["output"]

    @property
    def calls(self):
        return self.events["calls"]

    @property
    def returns(self):
        return self.events["returns"]

    @property
    def exceptions(self):
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

    def add_call(
        self, function_name: str, filename: str, line_no: int, args: Dict[str, str]
    ):
        """Add a function call event."""
        with self.lock:
            parent_id = self.call_stack[-1] if self.call_stack else None
            call_id = self.next_call_id
            self.next_call_id += 1

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

            # Instead of directly using run_coroutine_threadsafe, just add to the list
            self.events_list.append(("call", call))
            self.event_ready.set()  # Signal that a new event is available

    def add_return(self, function_name: str, return_value: str):
        """Add a function return event."""

        with self.lock:
            if not self.call_stack:
                return

            call_id = self.call_stack.pop()

            ret = ReturnEvent(
                function_name=function_name, return_value=return_value, call_id=call_id
            )

            self.events["returns"].append(ret)

            # Add to event list instead of using Queue directly
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
