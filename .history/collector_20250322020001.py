"""Runtime data collector for aggregating execution events."""

import threading
import time
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


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


class DataCollector:
    """Collects runtime data from execution."""

    def __init__(self):
        """Initialize the data collector."""
        self.lock = threading.RLock()
        self.call_stack = []
        self.next_call_id = 1

        # Events storage
        self.calls: List[CallEvent] = []
        self.returns: List[ReturnEvent] = []
        self.exceptions: List[ExceptionEvent] = []
        self.output: List[OutputLine] = []

        # Create asyncio queue for live updates
        self.event_queue = asyncio.Queue()

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

            self.calls.append(call)
            self.call_stack.append(call_id)

            # Add to async queue for live updates
            asyncio.run_coroutine_threadsafe(
                self.event_queue.put(("call", call)), asyncio.get_event_loop()
            )

    def add_return(self, function_name: str, return_value: str):
        """Add a function return event."""
        with self.lock:
            if not self.call_stack:
                return

            call_id = self.call_stack.pop()

            ret = ReturnEvent(
                function_name=function_name, return_value=return_value, call_id=call_id
            )

            self.returns.append(ret)

            # Add to async queue for live updates
            asyncio.run_coroutine_threadsafe(
                self.event_queue.put(("return", ret)), asyncio.get_event_loop()
            )

    def add_exception(self, exception):
        """Add an exception event."""
        with self.lock:
            import traceback

            exc_type = type(exception).__name__
            message = str(exception)
            tb_lines = traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )

            exc = ExceptionEvent(
                exception_type=exc_type, message=message, traceback=tb_lines
            )

            self.exceptions.append(exc)

            # Add to async queue for live updates
            asyncio.run_coroutine_threadsafe(
                self.event_queue.put(("exception", exc)), asyncio.get_event_loop()
            )

    def add_output(self, content: str, stream: str):
        """Add an output line."""
        with self.lock:
            line = OutputLine(content=content, stream=stream)
            self.output.append(line)

            # Add to async queue for live updates
            asyncio.run_coroutine_threadsafe(
                self.event_queue.put(("output", line)), asyncio.get_event_loop()
            )

    def clear(self):
        """Clear all collected data."""
        with self.lock:
            self.calls.clear()
            self.returns.clear()
            self.exceptions.clear()
            self.output.clear()
            self.call_stack.clear()
            self.next_call_id = 1

    async def get_event(self):
        """Get next event from the queue."""
        return await self.event_queue.get()
