"""Tracer module for capturing function calls and execution flow."""

import sys
import os
import inspect
import threading

from .collector import DataCollector

# Global collector instance
_collector = None

def get_collector():
    """Get the global collector instance."""
    global _collector
    if _collector is None:
        _collector = DataCollector()
    return _collector

def trace_function(frame, event, arg):
    """Trace function for sys.settrace."""
    # Get collector early to ensure it's ready
    collector = get_collector()
    if collector is None:
        return None
    
    # Skip internal calls and empty frames
    if frame is None or frame.f_code is None:
        return trace_function
        
    if event == 'call':
        func_name = frame.f_code.co_name
        filename = frame.f_code.co_filename
        line_no = frame.f_lineno
        
        # Skip tracing for internal modules and special names
        if ('pytui' in filename and not os.environ.get('PYTUI_TRACE_SELF')) or \
           func_name.startswith('__'):
            return None
            
        # Get function arguments
        args = inspect.getargvalues(frame)
        args_dict = {}
        for arg_name in args.args:
            if arg_name in args.locals:
                # Try to convert value to string safely
                try:
                    value = repr(args.locals[arg_name])
                    # Limit length for display
                    if len(value) > 100:
                        value = value[:97] + "..."
                    args_dict[arg_name] = value
                except:
                    args_dict[arg_name] = "<unable to represent>"
        
        # Add call event to collector
        collector.add_call(func_name, filename, line_no, args_dict)
            
        return trace_function
        
    elif event == 'return':
        collector.add_return(frame.f_code.co_name, repr(arg))
        return trace_function
        
    elif event == 'exception':
        exc_type, exc_value, exc_traceback = arg
        collector.add_exception(exc_value)
        return trace_function
        
    return trace_function

def install_trace():
    """Install the trace function."""
    sys.settrace(trace_function)
    threading.settrace(trace_function)
