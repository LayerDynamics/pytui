"""Tracer module for capturing function calls and execution flow."""

import sys
import os
import inspect
import threading
import json
import atexit

from .collector import get_collector

# Global collector reference for direct access in trace functions
_collector = None
# IPC file for sending trace data to parent process
_trace_file = None
# Call stack for managing parent IDs
_call_stack = []
# Next call ID
_next_call_id = 1

def trace_function(frame, event, arg):
    """Trace function for sys.settrace."""
    global _collector, _trace_file, _call_stack, _next_call_id
    
    # Skip if no trace file is available for IPC
    if _trace_file is None:
        return trace_function
    
    # Get collector if needed
    if _collector is None:
        _collector = get_collector()
    
    # Skip empty frames
    if frame is None or frame.f_code is None:
        return trace_function
    
    # Get basic frame info
    func_name = frame.f_code.co_name
    filename = frame.f_code.co_filename
    
    # Handle different event types
    if event == 'call':
        line_no = frame.f_lineno
        
        # Skip internal calls
        if ('pytui' in filename) or func_name.startswith('__') or func_name == '<module>':
            return trace_function
        
        # Generate a unique call ID
        call_id = _next_call_id
        _next_call_id += 1
        
        # Get parent ID from call stack
        parent_id = _call_stack[-1] if _call_stack else None
        
        # Save call ID on stack
        _call_stack.append(call_id)
        
        # Get arguments
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
        
        # Create JSON event for IPC
        event_data = {
            'type': 'call',
            'function_name': func_name,
            'filename': filename,
            'line_no': line_no,
            'args': args_dict,
            'call_id': call_id,
            'parent_id': parent_id
        }
        
        # Send to parent process via IPC
        try:
            _trace_file.write(json.dumps(event_data) + '\n')
            _trace_file.flush()
        except:
            # Ignore errors in IPC
            pass
            
        # Add locally to collector too
        if _collector:
            _collector.add_call(func_name, filename, line_no, args_dict, 
                               call_id=call_id, parent_id=parent_id)
        
        return trace_function
        
    elif event == 'return':
        # Pop from call stack
        if _call_stack:
            call_id = _call_stack.pop()
            
            # Create return event
            return_value = repr(arg)
            event_data = {
                'type': 'return',
                'function_name': func_name,
                'return_value': return_value,
                'call_id': call_id
            }
            
            # Send via IPC
            try:
                _trace_file.write(json.dumps(event_data) + '\n')
                _trace_file.flush()
            except:
                pass
                
            # Add locally
            if _collector:
                _collector.add_return(func_name, return_value, call_id=call_id)
    
    # Continue tracing
    return trace_function

def flush_trace():
    """Flush the trace file before exiting."""
    global _trace_file
    if _trace_file:
        try:
            _trace_file.flush()
        except:
            pass

def install_trace(collector=None, trace_path=None):
    """Install the trace function with optional IPC.
    
    Args:
        collector: DataCollector instance to use
        trace_path: Path to file for IPC with parent process
    """
    global _collector, _trace_file, _call_stack, _next_call_id
    
    # Set collector
    _collector = collector or get_collector()
    
    # Reset call data
    _call_stack = []
    _next_call_id = 1
    
    # Set up IPC if a path is provided
    if trace_path:
        try:
            _trace_file = open(trace_path, 'w')
            # Register cleanup
            atexit.register(flush_trace)
        except Exception as e:
            print(f"Failed to open trace file: {e}")
    
    # Register trace function
    sys.settrace(trace_function)
    threading.settrace(trace_function)
    
    return _collector
