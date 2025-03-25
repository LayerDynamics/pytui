"""Tests for utility functions."""

import pytest
from pathlib import Path
from pytui.utils import (
    get_module_path, 
    format_time, 
    truncate_string, 
    safe_repr
)

def test_get_module_path():
    """Test getting module paths."""
    # Test with a built-in module
    os_path = get_module_path("os")
    assert os_path is not None
    assert os_path.exists()
    
    # Test with a non-existent module
    nonexistent = get_module_path("nonexistent_module_xyz")
    assert nonexistent is None

def test_format_time():
    """Test time formatting."""
    # Test zero
    assert format_time(0) == "00:00.000"
    
    # Test minutes and seconds
    assert format_time(65.123) == "01:05.123"
    
    # Test hours (converted to minutes)
    assert format_time(3600) == "60:00.000"

def test_truncate_string():
    """Test string truncation."""
    # Short string, no truncation
    assert truncate_string("hello", 10) == "hello"
    
    # Exact length, no truncation
    assert truncate_string("1234567890", 10) == "1234567890"
    
    # Longer string, truncated with ellipsis
    assert truncate_string("1234567890123", 10) == "1234567..."
    
    # Default max_length
    long_string = "x" * 200
    assert len(truncate_string(long_string)) == 100
    assert truncate_string(long_string).endswith("...")

def test_safe_repr():
    """Test safe representation of objects."""
    # Simple objects
    assert safe_repr(123) == "123"
    assert safe_repr("hello") == "'hello'"
    
    # List
    assert safe_repr([1, 2, 3]) == "[1, 2, 3]"
    
    # Custom object with problematic __repr__
    class BadRepr:
        def __repr__(self):
            raise RuntimeError("Cannot represent")
    
    bad = BadRepr()
    assert safe_repr(bad) == "<representation failed>"
    
    # Long representation
    long_obj = "x" * 200
    assert len(safe_repr(long_obj)) <= 100
    assert safe_repr(long_obj).endswith("...'")
