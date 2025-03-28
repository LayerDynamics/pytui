"""Rich and textual UI components implementation.

This module provides a collection of terminal UI components for building
rich text-based user interfaces in Python applications.

Key Components:
- Widget: Base class for all UI components
- Container: Widget for organizing other widgets
- Panel: Bordered container with optional title
- Text: Styled text display widget
- Table: Display tabular data
- Layout: Organize widgets in layouts
- Application: Main application class for terminal UIs
- Console: Terminal output management with logging features

Usage Examples:
    # Simple text display
    from pytui.rich_text_ui import Text, Panel
    text = Text("Hello World", style="bold green")
    panel = Panel(text, title="Greeting", border_style="cyan")
    print(panel.render())

    # Creating an application
    from pytui.rich_text_ui import Application, Container, Text
    
    app = Application(title="My App")
    
    async def on_mount():
        container = Container()
        text = Text("Hello from PyTUI!", style="bold green")
        await container.mount(text)
        await app.view.mount(container)
    
    app.on_mount = on_mount
    app.run()
"""

from .widget import Widget
from .container import Container
from .scroll_view import ScrollView
from .style_manager import StyleManager
from .style import Style
from .text import Text
from .static import Static
from .panel import Panel
from .table import Table
from .table_data import TableData
from .layout import Layout
from .box import Box
from .app_config import AppConfig
from .console import Console, ConsoleConfig, LogLevel
from .application import Application
from .events import Event, KeyEvent, MouseEvent, ResizeEvent
from .progress import ProgressBarWidget, SpinnerWidget, AnimatedSpinnerWidget
from .util import get_terminal_size, strip_ansi, truncate
from .colors import Color
from .metrics import MetricsWidget, TimelineWidget

__all__ = [
    # Base components
    "Widget",
    "Container",
    "ScrollView",
    
    # Styling
    "StyleManager",
    "Style",
    "Color",
    
    # Text display
    "Text",
    "Static",
    
    # Containers
    "Panel",
    "Layout",
    "Box",
    
    # Data display
    "Table",
    "TableData",
    
    # Application framework
    "AppConfig",
    "Console",
    "ConsoleConfig",
    "LogLevel",
    "Application",
    
    # Events
    "Event",
    "KeyEvent",
    "MouseEvent",
    "ResizeEvent",
    
    # Progress indicators
    "ProgressBarWidget",
    "SpinnerWidget",
    "AnimatedSpinnerWidget",
    
    # Metrics and monitoring
    "MetricsWidget",
    "TimelineWidget",
    
    # Utilities
    "get_terminal_size",
    "strip_ansi",
    "truncate",
]

# Component documentation
Widget.__doc__ = """Base class for all UI widgets.

Attributes:
    name (str): Widget name for identification
    id: Unique identifier for the widget
    parent (Widget): Parent widget that contains this widget
    children (list): Child widgets contained by this widget
    styles (StyleManager): Style manager for widget appearance
    visible (bool): Whether the widget is visible
    focused (bool): Whether the widget has focus
    hover (bool): Whether the widget is being hovered
    width (int, optional): Widget width
    height (int, optional): Widget height
    classes (set): CSS-like classes applied to the widget

Methods:
    render(): Render the widget to a string representation
    mount(*widgets): Mount child widgets to this widget
    update(content): Update widget content
    refresh(): Refresh the widget display
    focus(): Focus this widget
    on(event_name, callback): Register an event handler
    emit(event_name, *args, **kwargs): Emit an event to registered handlers
"""

Application.__doc__ = """Main application class for terminal UI.

Create an Application instance and override on_mount() to initialize your UI.

Attributes:
    config (AppConfig): Application configuration
    view (Container): Root container for all widgets
    bindings (dict): Key bindings for application
    is_running (bool): Whether the application is running

Methods:
    on_mount(): Called when application is mounted (override this)
    on_unmount(): Called when application is unmounted (override this)
    mount(): Mount the application
    exit(): Exit the application
    refresh(): Refresh the application display
    run(): Run the application synchronously
    run_async(): Run the application asynchronously
    bind(key, handler): Bind a key to a handler function
"""

Panel.__doc__ = """Panel with a border and optional title.

A Panel is used to draw a border around content, optionally with a title.

Attributes:
    content: Panel content (string or renderable)
    title (str): Panel title
    border_style (Style): Style for the border
    box (dict): Box drawing characters
    padding (tuple): Padding as (horizontal, vertical) tuple

Methods:
    render(): Render panel with border and content
"""

Table.__doc__ = """Table widget for displaying tabular data.

Attributes:
    title (str): Table title
    box (dict): Box style for table borders
    show_header (bool): Whether to show column headers
    show_footer (bool): Whether to show footer

Methods:
    add_column(title, **kwargs): Add a column to the table
    add_row(*values, style=None): Add a row to the table
    render(): Render the table
"""

Text.__doc__ = """Text content with styling.

Attributes:
    content (str): Text content
    style (Style): Text style
    justify (str): Text justification ('left', 'center', 'right')

Methods:
    render(): Render text with styling
    append(text, style=None): Append text with optional style
    clear(): Clear text content
"""

Console.__doc__ = """Console output widget with advanced features.

Attributes:
    file: Output file (defaults to stdout)
    max_lines (int): Maximum number of lines to store
    show_timestamp (bool): Whether to show timestamps
    default_style (Style): Default text style
    auto_scroll (bool): Whether to auto-scroll to bottom

Methods:
    write(text, style=None, timestamp=None, level=None): Write content to console
    log(*messages, sep=" ", style=None, level="INFO"): Log a message
    debug(*messages): Log debug messages
    info(*messages): Log info messages
    warning(*messages): Log messages at WARNING level
    error(*messages): Log messages at ERROR level
    critical(*messages): Log messages at CRITICAL level
    success(*messages): Log success message with green styling
    clear(): Clear the console buffer
    export(filename, output_format="text"): Export console contents to a file
"""

Container.__doc__ = """Container for organizing widgets.

A Container holds and organizes multiple widgets in either vertical or
horizontal layouts.

Attributes:
    layout (str): Layout mode ('vertical' or 'horizontal')
    children (list): Child widgets contained by this container

Methods:
    render(): Render the container with children
    dock(*widgets, edge="left", size=None): Dock widgets to an edge
"""

Layout.__doc__ = """Layout manager for arranging widgets.

Attributes:
    content: Initial content
    size: Layout size
    children: Child layouts
    layout_type (str): Layout type ('vertical', 'horizontal', 'grid')

Methods:
    render(): Render the layout with content
    split(*layouts): Split the layout into multiple sections
    split_column(*layouts): Split into vertical columns
    split_row(*layouts): Split into horizontal rows
"""

Box.__doc__ = """Box drawing characters for borders.

Static methods:
    get_box_style(name="rounded"): Get a box style by name
    create_box(width, height, style="rounded"): Create a box with given dimensions
    create_header(width, style="rounded", text=""): Create a header line
    create_grid(rows, cols, style="rounded"): Create a grid with given dimensions

Available box styles:
    - ascii: ASCII characters (+, -, |)
    - rounded: Rounded corners (╭, ╮, ╯, ╰, ─, │)
    - square: Square corners (┌, ┐, └, ┘, ─, │)
    - double: Double lines (╔, ╗, ╚, ╝, ═, ║)
    - heavy: Heavy lines (┏, ┓, ┗, ┛, ━, ┃)
    - dashed: Dashed lines with rounded corners
    - dotted: Dotted lines
"""

ProgressBarWidget.__doc__ = """Progress bar widget for showing execution progress.

Attributes:
    total (int): Total steps for completion
    description (str): Description of the progress
    show_percentage (bool): Whether to show percentage
    show_time (bool): Whether to show elapsed time
    completed (int): Number of completed steps

Methods:
    update(completed, description=None): Update progress completion
    increment(amount=1): Increment progress by an amount
    reset(total=None, description=None): Reset the progress bar
    auto_pulse(interval=0.2, pulse_size=1): Auto-pulse for indeterminate progress
    stop_pulse(): Stop the auto-pulse animation
"""

SpinnerWidget.__doc__ = """A spinner widget for showing progress.

Attributes:
    text (str): Text to display alongside the spinner
    spinner_type (str): Type of spinner animation to use

Methods:
    start(): Start the spinner animation
    stop(): Stop the spinner animation
"""

StyleManager.__doc__ = """Manages widget styles.

Attributes:
    widget: Widget to manage styles for

Methods:
    animate(property_name, target_value, duration=0.3, easing="linear"):
        Animate a style property change
    animate_multiple(properties, duration=0.3, easing="linear"):
        Animate multiple style properties simultaneously
    get_computed_style(): Get computed style including inherited properties
"""

ScrollView.__doc__ = """Container that supports scrolling.

Attributes:
    scroll_x (float): Horizontal scroll position (0-1)
    scroll_y (float): Vertical scroll position (0-1)
    content_width (int): Content width
    content_height (int): Content height
    viewport_width (int): Viewport width
    viewport_height (int): Viewport height

Methods:
    scroll_to(x=None, y=None, animate=False): Scroll to a position
"""

Style.__doc__ = """Style representation for text formatting.

Attributes:
    components (set): Set of style components

Methods:
    apply(text): Apply this style to text

Available style components:
    - Colors: black, red, green, yellow, blue, magenta, cyan, white
    - Bright colors: bright_black, bright_red, bright_green, bright_yellow,
      bright_blue, bright_magenta, bright_cyan, bright_white
    - Attributes: bold, dim, italic, underline, blink, reverse
"""
