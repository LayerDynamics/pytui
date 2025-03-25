"""Function tracing implementation."""

import sys
import os
import threading
import json
import traceback
from typing import Optional, Dict, Any, Callable

_current_collector = None
_call_stack = []
_next_call_id = 1
_trace_file = None

def _is_valid_frame(frame) -> bool:
    """Check if a frame should be traced."""
    if not frame or not frame.f_code:
        return False
    
    filename = frame.f_code.co_filename
    # Skip internal Python files and pytui internals except test files
    if (filename.startswith('<') or 
        ('pytui' in filename and 
         not filename.endswith('test.py') and
         not 'tests' in filename)):
        return False
    return True

def _get_event_handler(event: str) -> Optional[Callable]:
    """Get the appropriate handler for an event type."""
    handlers = {
        'call': _handle_call_event,
        'return': _handle_return_event,
        'exception': _handle_exception_event
    }
    return handlers.get(event)

def _handle_call_event(frame, arg) -> None:
    """Handle function call events."""
    global _next_call_id, _call_stack
    
    if not _current_collector:
        return None
        
    try:
        func_name = frame.f_code.co_name
        filename = frame.f_code.co_filename
        line_no = frame.f_lineno
        
        # Get arguments while handling potential errors
        args = {}
        for key, value in frame.f_locals.items():
            if key != 'self':  # Skip self reference
                try:
                    args[key] = repr(value)
                except:
                    args[key] = '<repr failed>'
        
        call_id = _next_call_id
        _next_call_id += 1
        
        parent_id = _call_stack[-1] if _call_stack else None
        _call_stack.append(call_id)
        
        _write_trace_event('call', {
            'function_name': func_name,
            'filename': filename,
            'line_no': line_no,
            'args': args,
            'call_id': call_id,
            'parent_id': parent_id
        })
        
    except Exception as e:
        sys.stderr.write(f"Error in call tracer: {e}\n")
    
    return trace_function

def _handle_return_event(frame, arg) -> None:
    """Handle function return events."""
    if not _current_collector or not _call_stack:
        return None
        
    try:
        func_name = frame.f_code.co_name
        return_value = repr(arg) if arg is not None else 'None'
        
        call_id = _call_stack.pop() if _call_stack else None
        
        _write_trace_event('return', {
            'function_name': func_name,
            'return_value': return_value,
            'call_id': call_id
        })
        
    except Exception as e:
        sys.stderr.write(f"Error in return tracer: {e}\n")
    
    return trace_function

def _handle_exception_event(frame, arg) -> None:
    """Handle exception events."""
    if not _current_collector:
        return None
        
    try:
        exc_type, exc_value, _ = arg
        _current_collector.add_exception(exc_value)
        
    except Exception as e:
        sys.stderr.write(f"Error in exception tracer: {e}\n")
    
    return trace_function

def _write_trace_event(event_type: str, data: Dict[str, Any]) -> None:
    """Write a trace event to the trace file."""
    if _trace_file:
        try:
            data['type'] = event_type
            json_str = json.dumps(data)
            with open(_trace_file, 'a', encoding='utf-8') as f:
                f.write(json_str + '\n')
                f.flush()
        except Exception as e:
            sys.stderr.write(f"Error writing trace event: {e}\n")

def trace_function(frame, event, arg):
    """Trace function for sys.settrace."""
    if not _is_valid_frame(frame):
        return trace_function
        
    handler = _get_event_handler(event)
    if handler:
        return handler(frame, arg)
    return trace_function

def install_trace(collector=None, trace_path=None):
    """Install the tracer."""
    global _current_collector, _trace_file
    
    if collector:
        _current_collector = collector
    
    if trace_path:
        _trace_file = trace_path
        
    sys.settrace(trace_function)
    threading.settrace(trace_function)
    
    return _current_collector
