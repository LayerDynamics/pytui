"""Compatibility layer for UI components.

This module provides access to UI components whether the real packages
are installed or the fallback implementations are being used.
"""

# Track if we're using fallback implementations
USING_FALLBACKS = False

try:
    # Attempt to import from textual
    from textual.widgets import Static, Tree
    from textual.scroll_view import ScrollView
    from textual.containers import Container
    from textual.app import App
except ImportError:
    USING_FALLBACKS = True
    # Import from our rich_text_ui implementation instead
    from .rich_text_ui import Static, Container, App, Widget, ScrollView
    
    # Tree is a special case in the alternative implementation
    class Tree(Widget):
        """Tree widget for hierarchical data."""
        # Implementation details are in rich_text_ui.py

# Export classes with consistent naming regardless of backend
__all__ = ["USING_FALLBACKS", "App", "Container", "ScrollView", "Static", "Tree"]
