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
    call_id: Optional[int] = None
    timestamp: float = field(default_factory=time.time)


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
        """Initialize collector state."""
        self.output = []
        self.calls = []
        self.returns = []
        self.exceptions = []
        self.next_call_id = 1
        self.call_stack = []
        self._event_queue = asyncio.Queue()
        self._loop = None

    def add_call(self, function_name, filename, line_no, args, parent_id=None):
        """Add a function call event."""
        call_id = self.next_call_id
        self.next_call_id += 1

        # Create call event
        event = CallEvent(
            function_name=function_name,
            filename=str(filename),  # Convert Path to string
            line_no=line_no,
            args=args,
            call_id=call_id,
            parent_id=parent_id,
        )

        # Track call stack
        self.call_stack.append(call_id)
        self.calls.append(event)
        self._queue_event("call", event)

    def add_return(self, function_name, return_value, call_id=None):
        """Add a function return event."""
        if not call_id and self.call_stack:
            call_id = self.call_stack.pop()

        event = ReturnEvent(
            function_name=function_name, return_value=return_value, call_id=call_id
        )
        self.returns.append(event)
        self._queue_event("return", event)

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
