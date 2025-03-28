"""PyTUI - A Python Terminal User Interface library.

PyTUI is a lightweight Terminal User Interface library built on top of the rich_text_ui
components. It provides a simple way to create rich, interactive terminal applications.

Key Components:
--------------
1. Widgets: Basic UI building blocks like Text, Panel, Table, etc.
2. Panels: Specialized components like OutputPanel, CallGraphPanel
3. Application: Main application framework for creating TUIs
4. Executor: Script execution and monitoring utilities

Quick Start:
-----------
```python
import pytui

# Create a simple application
app = pytui.Application(title="My TUI App")

# Add a text panel
panel = pytui.Panel("Hello PyTUI!", title="Welcome")
app.view.mount(panel)

# Run the application
app.run()
```

For script execution visualization:
```python
from pytui.app import PyTUIApp
from pytui.executor import ScriptExecutor

# Create script executor
executor = ScriptExecutor("my_script.py")

# Create and run visualization app
app = PyTUIApp()
app.set_executor(executor)
app.run()
```
"""

__version__ = "0.1.0"

# Import core modules
from .rich_text_ui.widget import Widget
from .rich_text_ui.static import Static
from .rich_text_ui.text import Text
from .rich_text_ui.panel import Panel
from .rich_text_ui.table import Table
from .rich_text_ui.layout import Layout
from .rich_text_ui.container import Container
from .rich_text_ui.scroll_view import ScrollView
from .rich_text_ui.console import Console
from .rich_text_ui.box import Box
from .rich_text_ui.application import Application
from .rich_text_ui.colors import Color

# Import widget utilities
from .widget_utils import (
    ActiveFunctionHighlighter,
    SearchableText,
    CollapsibleMixin,
    ensure_callable,
    format_widget_style,
    get_widget_timestamp,
)

# Import specialized widgets
from .widgets import (
    StatusBar,
    CollapsibleWidget,
    SearchWidget,
    ProgressBarWidget,
    AnimatedSpinnerWidget,
    ROUNDED,
)

# Import panels
from .panels import (
    BasePanel,
    OutputPanel,
    CallGraphPanel,
    ExceptionPanel,
    LogPanel,
    Tree,
)

# Import application and executor
from .app import PyTUIApp
from .executor import ScriptExecutor

# Import collector components
from .collector import (
    DataCollector,
    CallEvent,
    ReturnEvent,
    ExceptionEvent,
    OutputLine,
    get_collector,
)

# Constants and utilities
from .utils import format_time, truncate_string, safe_repr

# Expose all public components
__all__ = [
    # Version
    "__version__",
    
    # Base Components
    "Widget",
    "Static",
    "Text",
    "Panel",
    "Table",
    "Layout",
    "Container",
    "ScrollView",
    "Console",
    "Box",
    "Application",
    "Color",
    
    # Widget Utilities
    "ActiveFunctionHighlighter",
    "SearchableText",
    "CollapsibleMixin",
    "ensure_callable",
    "format_widget_style",
    "get_widget_timestamp",
    
    # Specialized Widgets
    "StatusBar",
    "CollapsibleWidget",
    "SearchWidget",
    "ProgressBarWidget",
    "AnimatedSpinnerWidget",
    "ROUNDED",
    
    # Panels
    "BasePanel",
    "OutputPanel",
    "CallGraphPanel",
    "ExceptionPanel",
    "LogPanel",
    "Tree",
    
    # Application and Executor
    "PyTUIApp",
    "ScriptExecutor",
    
    # Collector Components
    "DataCollector",
    "CallEvent",
    "ReturnEvent",
    "ExceptionEvent",
    "OutputLine",
    "get_collector",
    
    # Utils
    "format_time",
    "truncate_string",
    "safe_repr",
]

# Component Documentation
component_docs = {
    "Widget": "Base widget class for all UI components",
    "Static": "Widget for displaying static content",
    "Text": "Widget for displaying styled text",
    "Panel": "Container with a border and optional title",
    "Table": "Widget for displaying tabular data",
    "Layout": "Manager for arranging widgets in layouts",
    "Container": "Container for organizing multiple widgets",
    "ScrollView": "Container with scrolling capabilities",
    "Console": "Advanced console for rich text output",
    "Box": "Box drawing characters for UI elements",
    "Application": "Main application framework for TUIs",
    "StatusBar": "Widget for displaying status information",
    "CollapsibleWidget": "Widget that can be collapsed/expanded",
    "SearchWidget": "Widget for search functionality",
    "ProgressBarWidget": "Widget for showing progress",
    "AnimatedSpinnerWidget": "Widget for showing loading animations",
    "BasePanel": "Base class for specialized panels",
    "OutputPanel": "Panel for displaying script output",
    "CallGraphPanel": "Panel for displaying function call graphs",
    "ExceptionPanel": "Panel for displaying exceptions",
    "LogPanel": "Panel for log messages with filtering",
    "Tree": "Widget for hierarchical data display",
    "PyTUIApp": "Application for script execution visualization",
    "ScriptExecutor": "Utility for running and tracing Python scripts",
    "DataCollector": "Collector for runtime execution data",
}

# Add examples for core components
examples = {
    "Panel": """
    # Create a simple panel
    panel = pytui.Panel("Hello World", title="My Panel")
    """,
    
    "Text": """
    # Create styled text
    text = pytui.Text("Important message", style="bold red")
    """,
    
    "Container": """
    # Create a container with multiple widgets
    container = pytui.Container()
    container.mount(pytui.Text("First item"))
    container.mount(pytui.Text("Second item"))
    """,
    
    "Application": """
    # Create and run a basic application
    app = pytui.Application(title="My App")
    app.view.mount(pytui.Panel("Content"))
    app.run()
    """,
    
    "ScriptExecutor": """
    # Execute a Python script with tracing
    executor = pytui.ScriptExecutor("script.py")
    executor.start()
    """,
}

def get_component_doc(component_name):
    """Get documentation for a component."""
    doc = component_docs.get(component_name, "No documentation available")
    example = examples.get(component_name, "")
    return f"{doc}\n\n{example}" if example else doc

def list_components():
    """List all available components."""
    return sorted(component_docs.keys())

def get_example(component_name):
    """Get example code for a component."""
    return examples.get(component_name, "No example available")
