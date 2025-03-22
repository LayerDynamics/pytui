"""Utility functions for pytui."""

import os
import sys
from typing import List, Dict, Any, Optional
import importlib.util
from pathlib import Path

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
        if hasattr(module, '__file__') and module.__file__:
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
    return s[:max_length-3] + "..."
    
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
            # Fix the truncation to ensure total length is exactly 100
            if repr_str.startswith("'") and len(repr_str) > 3:
                return repr_str[:96] + "...'"
            elif repr_str.startswith('"') and len(repr_str) > 3:
                return repr_str[:96] + '..."'
            else:
                return repr_str[:97] + "..."
        return repr_str
    except Exception:
        return "<representation failed>"
