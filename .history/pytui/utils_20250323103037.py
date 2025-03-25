"""Utility functions for pytui."""

import os
import sys
from typing import List, Dict, Any, Optional
import importlib.util
from pathlib import Path
import psutil  # Import psutil at the module level


def get_module_path(module_name: str) -> Optional[Path]:
    """
    Get the file path for a module by name.

    Args:
        module_name: Name of the module to find.

    Returns:
        Path to the module file or None if not found.
    """
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, "__file__") and module.__file__:
            return Path(module.__file__)
        return None
    except (ImportError, AttributeError):
        return None


def format_time(seconds: float) -> str:
    """
    Format seconds into a human-readable time string.

    Args:
        seconds: Time in seconds.

    Returns:
        Formatted time string (MM:SS.ms).
    """
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes):02d}:{int(seconds):02d}.{int((seconds % 1) * 1000):03d}"


def truncate_string(s: str, max_length: int = 100) -> str:
    """
    Truncate a string to a maximum length with ellipsis.

    Args:
        s: String to truncate.
        max_length: Maximum length.

    Returns:
        Truncated string.
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - 3] + "..."


def safe_repr(obj: Any) -> str:
    """
    Safely get the representation of an object.

    Args:
        obj: Object to represent.

    Returns:
        String representation or fallback message.
    """
    try:
        repr_str = repr(obj)
        if len(repr_str) > 100:
            # Adjust slices so the overall length is ≤ 100 characters.
            if repr_str.startswith("'") and len(repr_str) > 3:
                return repr_str[:95] + "...'"
            elif repr_str.startswith('"') and len(repr_str) > 3:
                return repr_str[:95] + '..."'
            else:
                return repr_str[:96] + "..."
        return repr_str
    except Exception:
        return "<representation failed>"


def kill_process_tree(pid):
    """Kill a process and all its children."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # Kill children first
        for child in children:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        
        # Kill parent
        try:
            parent.kill()
        except psutil.NoSuchProcess:
            pass
            
    except psutil.NoSuchProcess:
        pass  # Process already terminated

def terminate_process_tree(pid, timeout=5):
    """Gracefully terminate a process and its children with timeout."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # Terminate children first
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
                
        # Terminate parent
        try:
            parent.terminate()
        except psutil.NoSuchProcess:
            pass
            
        # Wait for processes to terminate
        _, alive = psutil.wait_procs([parent] + children, timeout=timeout)
        
        # Kill any remaining processes
        if alive:
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
                    
    except psutil.NoSuchProcess:
        pass  # Process already terminated
