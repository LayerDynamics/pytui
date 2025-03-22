"""Tracer module for capturing function calls and execution flow."""

import sys
import os
import inspect
import threading

from .collector import get_collector

# Global collector reference for direct access in trace functions
_collector = None

def trace_function(frame, event, arg):
    """Trace function for sys.settrace."""
    global _collector
    
    # First try to get the collector from the global reference
    collector = _collector
    
    # If not available, try to get from function
    if collector is None:
        collector = get_collector()
        _collector = collector
    
    if collector is None:
        # Cannot trace without a collector
        print("Warning: No collector available for tracing")
        return None
    
    # Skip internal calls and empty frames
    if frame is None or frame.f_code is None:
        return trace_function
        
    if event == 'call':
        func_name = frame.f_code.co_name
        filename = frame.f_code.co_filename
        line_no = frame.f_lineno
        
        # Skip tracing for internal modules and special names
        if ('pytui' in filename and 'tracer.py' in filename):
            # Changed: Return None instead of trace_function for internal modules
            return None
        
        if func_name.startswith('__') or func_name == '<module>':
            return trace_function  # Continue tracing but skip this frame
            
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
        
        # Add call event to collector with debugging
        try:
            collector.add_call(func_name, filename, line_no, args_dict)
            # Debug output for first few calls
            if collector and len(collector.calls) < 5:
                print(f"Debug: Traced call to {func_name} at {filename}:{line_no}")
        except Exception as e:
            print(f"Error capturing call: {e}")
            
        return trace_function
        
    elif event == 'return':
        # Fixed: Ensure we call add_return unconditionally
        try:
            collector.add_return(frame.f_code.co_name, repr(arg))
        except Exception as e:
            print(f"Error capturing return: {e}")
        return trace_function
        
    elif event == 'exception':
        # Fixed: Ensure we call add_exception unconditionally
        try:
            exc_type, exc_value, exc_traceback = arg
            collector.add_exception(exc_value)
        except Exception as e:
            print(f"Error capturing exception: {e}")
        return trace_function
        
    return trace_function

def install_trace():
    """Install the trace function."""
    # Get the collector first
    collector = get_collector()
    
    # Ensure the global reference is properly set
    global _collector
    _collector = collector
    
    # Set both trace functions
    sys.settrace(trace_function)
    threading.settrace(trace_function)
    
    # Return the collector for reference
    return collector
