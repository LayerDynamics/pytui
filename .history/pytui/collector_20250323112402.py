"""Runtime data collector for aggregating execution events."""

import threading
import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import traceback

@dataclass
class CallEvent:
    """Function call event data."""
    function_name: strvent data."""
    filename: str
    line_no: inte: str
    args: Dict[str, str]
    timestamp: float = field(default_factory=time.time)
    call_id: int = 0str]
    parent_id: Optional[int] = Nonet_factory=time.time)
    call_id: int = 0
@dataclass_id: Optional[int] = None
class ReturnEvent:
    """Function return event data."""
    function_name: str
    return_value: str
    timestamp: float = field(default_factory=time.time)
    call_id: int = 0
    function_name: str
@dataclass_value: str
class ExceptionEvent:= field(default_factory=time.time)
    """Exception event data."""
    exception_type: str
    message: str
    traceback: List[str]
    timestamp: float = field(default_factory=time.time)
    """Exception event data."""
@dataclass
class OutputLine:e: str
    """Output line data."""
    content: strist[str]
    stream: str  # 'stdout', 'stderr', or 'system'time)
    timestamp: float = field(default_factory=time.time)

# Singleton collector instance - use a private name but not global
_COLLECTOR = None
    """Output line data."""
def get_collector():
    """Get or create the singleton collector instance."""
    # Using function-level state instead of global statementtdout', 'stderr', or 'system'
    if get_collector._instance is None:ld(default_factory=time.time)
        get_collector._instance = DataCollector()
    return get_collector._instance
# Singleton collector instance
# Initialize the static variable
get_collector._instance = None


class DataCollector: instance."""
    """Collects runtime data from execution."""

    def __init__(self):ector()
        """Initialize the data collector."""    return _collector
        self.lock = threading.RLock()
        
        # Consolidate event storage into one dictionary to reduce instance attributes
        self.events: Dict[str, List] = {ta from execution."""
            "calls": [],
            "returns": [],
            "exceptions": [],""Initialize the data collector."""
            "output": []        self.lock = threading.RLock()
        }
        self.call_stack = []
        self.next_call_id = 1
        orage into one dictionary.
        # Event processing attributes
        self.loop = None
        self.event_queues = {}            "returns": [],
        self.events_list = []
        self.event_ready = threading.Event()output": [],

    # Added for backward compatibility with tests
    @property    # Instead of event_queues, use a Queue object that's not bound to any loop
    def output(self): a thread-safe mechanism to notify waiting coroutines
        """Return output events list."""None
        return self.events["output"]
        self.events_list = []  # Store events in a thread-safe list
    @propertyevent_ready = threading.Event()  # Signal when new events are available
    def calls(self):
        """Return call events list."""y with tests
        return self.events["calls"]@property
    t(self):
    @propertys["output"]
    def returns(self):
        """Return return events list."""    @property
        return self.events["returns"]
    
    @property
    def exceptions(self):
        """Return exception events list."""
        return self.events["exceptions"]["returns"]

    def _get_loop(self):
        """Return the currently running loop and update stored loop if available."""
        try:ptions"]
            current = asyncio.get_running_loop()
            self.loop = current  # refresh stored loop
            return currenttly running loop and update stored loop if available."""
        except RuntimeError:        try:
            # No running loop - this is probably called from a non-async context
            if self.loop and not self.loop.is_closed():sh stored loop
                return self.loopent
            # Create a new loop if we don't have one
            self.loop = asyncio.new_event_loop() this is probably called from a non-async context
            return self.loopis_closed():

    def add_call(self, function_name, filename, line_no, args, ate a new loop if we don't have one
                 call_id=None, parent_id=None, timestamp=None):)
        """Add a function call event.
        
        Args:
            function_name: Name of the called function call_id=None, parent_id=None
            filename: Source file containing the function
            line_no: Line number of the function calldd a function call event."""
            args: Function arguments
            call_id: Optional ID for the call (auto-generated if None)ble
            parent_id: Optional parent call ID for nested calls
            timestamp: Optional timestamp (current time used if None)ext_call_id
        """call_id += 1
        with self.lock:
            # Use provided call_id if availableid if needed
            if call_id is None:   self.next_call_id = max(self.next_call_id, call_id + 1)
                call_id = self.next_call_id
                self.next_call_id += 1able
            else:all_stack:
                # Update next_call_id if needed                parent_id = self.call_stack[-1]
                self.next_call_id = max(self.next_call_id, call_id + 1)
            
            # Use provided parent_id if available            function_name=function_name,
            if parent_id is None and self.call_stack:
                parent_id = self.call_stack[-1]
            gs,
            call = CallEvent(
                function_name=function_name,t_id,
                filename=filename,
                line_no=line_no,
                args=args,
                call_id=call_id,call_stack.append(call_id)
                parent_id=parent_id,
                timestamp=timestamp or time.time()all))
            )

            self.events["calls"].append(call)ion_name, return_value, call_id=None):
            self.call_stack.append(call_id)

            self.events_list.append(('call', call))stack if not provided
            self.event_ready.set()f call_id is None:
                    if not self.call_stack:
    def add_return(self, function_name, return_value, call_id=None, timestamp=None):
        """Add a function return event.
        
        Args:    # Remove matching call_id from stack if it exists
            function_name: Name of the returning function_stack:
            return_value: Function return valueemove(call_id)
            call_id: Optional ID for the call (taken from stack if None)
            timestamp: Optional timestamp (current time used if None)
        """on_name, return_value=return_value, call_id=call_id
        with self.lock:
            # Get call_id from stack if not provided
            if call_id is None:].append(ret)
                if not self.call_stack:turn", ret))
                    return()
                call_id = self.call_stack.pop()
            else:xception(self, exception):
                # Remove matching call_id from stack if it exists        """Add an exception event."""
                if call_id in self.call_stack:
                    self.call_stack.remove(call_id)            exc_type = type(exception).__name__
tion)
            ret = ReturnEvent(
                function_name=function_name,xception, exception.__traceback__
                return_value=return_value,            )
                call_id=call_id,
                timestamp=timestamp or time.time()
            )on_type=exc_type, message=message, traceback=tb_lines

            self.events["returns"].append(ret)
            self.events_list.append(('return', ret))            self.events["exceptions"].append(exc)
            self.event_ready.set()
            
    def add_exception(self, exception):d(("exception", exc))
        """Add an exception event.            self.event_ready.set()
        
        Args:stream: str):
            exception: The exception object that was raisedt line."""
        """
        with self.lock:ent, stream=stream)
            exc_type = type(exception).__name__)
            message = str(exception)
            tb_lines = traceback.format_exception(
                type(exception), exception, exception.__traceback__nd(("output", line))
            )

            exc = ExceptionEvent(    def clear(self):
                exception_type=exc_type, data."""
                message=message,
                traceback=tb_linesents["calls"].clear()
            )
ceptions"].clear()
            self.events["exceptions"].append(exc)ear()

            # Add to event listself.next_call_id = 1
            self.events_list.append(('exception', exc))
            self.event_ready.set()

    def add_output(self, content: str, stream: str):
        """Add an output line.""
        e:
        Args:
            content: Text content of the output            with self.lock:
            stream: Stream identifier ('stdout', 'stderr', or 'system')elf.events_list:
        """list.pop(0)
        with self.lock:
            line = OutputLine(content=content, stream=stream) be set
            self.events["output"].append(line)# Use asyncio.sleep for cooperative multitasking
            self.event_ready.wait(0.1)  # Short timeout to allow checking again












































        # No-op implementation, but has docstring now        """        to flush events in the child process if needed        This is a no-op in the parent process but can be used                """Flush any pending events.    def flush(self):                self.event_ready.clear()  # Reset for next wait            else:                await asyncio.sleep(0.1)  # Yield to event loop            if not self.event_ready.is_set():            self.event_ready.wait(0.1)  # Short timeout to allow checking again            # Use asyncio.sleep for cooperative multitasking            # No events available, wait for the event to be set                                return self.events_list.pop(0)                if self.events_list:            with self.lock:            # Check if there are events in the list        while True:        """            Tuple of (event_type, event_data)        Returns:                """Get next event from the queue for the current loop.    async def get_event(self):            self.event_ready.clear()            self.events_list.clear()            self.next_call_id = 1            self.call_stack.clear()            self.events["output"].clear()            self.events["exceptions"].clear()            self.events["returns"].clear()            self.events["calls"].clear()        with self.lock:        """Clear all collected data."""    def clear(self):            self.event_ready.set()            self.events_list.append(('output', line))            # Add to event list            if not self.event_ready.is_set():
                await asyncio.sleep(0.1)  # Yield to event loop
            else:
                self.event_ready.clear()  # Reset for next wait

    def flush(self):
        """Flush any pending events."""
        # This is a no-op in the parent process but can be used
        # to flush events in the child process if needed
        pass
