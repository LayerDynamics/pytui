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
    
    # Add debug output for the first few calls
    static_counter = getattr(trace_function, '_counter', 0)
    trace_function._counter = static_counter + 1
    
    if static_counter < 5:
        print(f"TRACE DEBUG [{static_counter}]: event={event}, func={frame.f_code.co_name if frame else 'None'}")
    
    # First try to get the collector from the global reference
    collector = _collector
    
    # If not available, try to get from function
    if collector is None:
        collector = get_collector()
        _collector = collector
        if static_counter < 5:
            print(f"TRACE DEBUG: Initialized collector, id={id(collector)}")
    
    if collector is None:
        # Cannot trace without a collector
        print("Warning: No collector available for tracing")
        return None
    
    # Skip internal calls and empty frames
    if frame is None or frame.f_code is None:
        return trace_function
    
    # Get basic frame info regardless of event type
    func_name = frame.f_code.co_name
    filename = frame.f_code.co_filename
    
    # Handle different event types
    if event == 'call':
        line_no = frame.f_lineno
        
        # Skip tracing for internal modules if we're tracing a full path file
        if filename and ('pytui' in filename) and ('tracer.py' in filename):
            return None
        
        # Skip special functions but continue tracing inside them
        if func_name.startswith('__') or func_name == '<module>':
            return trace_function
        
        # Add debug output for captured functions
        if not ('pytui' in filename):
            print(f"TRACE CAPTURE: {func_name} at {filename}:{line_no}")
            
        # Get function arguments - only needed for call events
        args = inspect.getargvalues(frame)
        args_dict = {}
        for arg_name in args.args:
            if arg_name in args.locals:
                try:
                    value = repr(args.locals[arg_name])
                    if len(value) > 100:
                        value = value[:97] + "..."
                    args_dict[arg_name] = value
                except:
                    args_dict[arg_name] = "<unable to represent>"
        
        # Add call event to collector
        collector.add_call(func_name, filename, line_no, args_dict)
        
        return trace_function
        
    elif event == 'return':
        # Handle return events unconditionally for any function
        try:
            # Always use repr to safely convert any return value to string
            return_value = repr(arg)
            collector.add_return(func_name, return_value)
        except Exception as e:
            print(f"Error capturing return for {func_name}: {e}")
        return trace_function
        
    elif event == 'exception':
        # Handle exception events unconditionally
        try:
            exc_type, exc_value, exc_traceback = arg
            collector.add_exception(exc_value)
        except Exception as e:
            print(f"Error capturing exception: {e}")
        return trace_function
    
    # Default: continue tracing
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
