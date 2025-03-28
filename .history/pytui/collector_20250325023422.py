"""Runtime data collector for aggregating execution events."""

import threading
import time
import asyncio
import traceback
from typing import Dict, List, Optional  # Removed "Any"


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
        self._queue = asyncio.Queue()

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
            self._queue.put_nowait(("call", call))

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
            self._queue.put_nowait(("return", ret))

    def add_exception(self, exception, message=None, tb=None):
        """Add an exception event."""
        with self.lock:
            exc_type = type(exception).__name__
            exc_message = message or str(exception)

            # Fix traceback handling
            if tb is None:
                if hasattr(exception, "__traceback__") and exception.__traceback__:
                    tb_lines = traceback.format_tb(exception.__traceback__)
                else:
                    tb_lines = []
            else:
                tb_lines = tb if isinstance(tb, list) else [str(tb)]

            exc = ExceptionEvent(
                exception_type=exc_type, message=exc_message, traceback=tb_lines
            )

            self.events["exceptions"].append(exc)
            self.events_list.append(("exception", exc))
            self.event_ready.set()
            self._queue.put_nowait(("exception", exc))

    def add_output(self, content: str, stream: str):
        """Add an output line."""
        with self.lock:
            line = OutputLine(content=content, stream=stream)
            self.events["output"].append(line)

            # Add to event list
            self.events_list.append(("output", line))
            self.event_ready.set()
            self._queue.put_nowait(("output", line))

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
        return await self._queue.get()

    def flush(self):
        """Flush any pending events.

        In child processes where events are forwarded through asyncio queues,
        this method transfers all buffered events into their corresponding queues.
        In the parent process (or when no async loop/queues are set up), it simply
        drains the internal event list.

        This implementation ensures that any event producers are not blocked by
        pending events and that listeners attached to the async queues receive
        all buffered events in a thread-safe manner.
        """
        # Acquire lock to safely extract and clear pending events
        with self.lock:
            pending_events = self.events_list[:]
            self.events_list.clear()
            self.event_ready.clear()

        # If an asyncio loop and event queues are available, flush events to them.
        # This is typically done in a child process that forwards events for further processing.
        if self.loop is not None and not self.loop.is_closed():
            for evt_type, evt in pending_events:
                # If there's an asyncio.Queue registered for this event type, put the event in it.
                queue = self.event_queues.get(evt_type)
                if queue is not None:
                    # Schedule the queue put in a thread-safe manner to prevent blocking.
                    asyncio.run_coroutine_threadsafe(queue.put(evt), self.loop)
        # In case there's no active event loop or event queues defined,
        # the flush operation simply drains the pending events.
