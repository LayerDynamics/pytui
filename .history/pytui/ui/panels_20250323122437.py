"""UI panel components for the TUI."""

# pylint: disable=trailing-whitespace, too-few-public-methods

# Standard library imports
import time
from typing import List, Dict, Any, Optional

# Third-party imports
try:
    from rich.text import Text
    from rich.syntax import Syntax
    from rich.panel import Panel
    from rich.table import Table
    from rich.layout import Layout
    from rich.console import RenderableType
    from rich.box import ROUNDED
    from rich.columns import Columns
except ImportError:
    # Fallback for when rich isn't available
    Text = Panel = Syntax = Table = Layout = RenderableType = ROUNDED = Columns = object

# Local imports
from .compat import Tree, ScrollView, Container, USING_FALLBACKS
from .widgets import (
    SearchableText,
    ActiveFunctionHighlighter,
    AnimatedSpinnerWidget,
    VariableInspectorWidget,
)
from ..collector import OutputLine, CallEvent, ReturnEvent, ExceptionEvent
from ..utils import format_time

# Use a warning if we're in fallback mode
if USING_FALLBACKS:
    import warnings
    warnings.warn(
        "Running in compatibility mode: Textual is not available. "
        "UI functionality will be limited."
    )


class BasePanel(Container):
    """Base class for all panels with common functionality."""

    def __init__(self, title: str = "Panel"):
        """Initialize the base panel.

        Args:
            title: Panel title
        """
        super().__init__()
        self.title = title
        self.collapsed = False
        self.has_focus = False
        self.filter_text = ""
        self._spinner = None
        self._prev_height = 20  # Default height before collapsing

    async def setup_spinner(self):
        """Set up a spinner for loading state."""
        self._spinner = AnimatedSpinnerWidget(f"Loading {self.title}...", "dots")
        await self.mount(self._spinner)
        await self._spinner.start()

    async def show_spinner(self, show: bool = True):
        """Show or hide the spinner."""
        if self._spinner:
            if show:
                self._spinner.visible = True
                await self._spinner.start()
            else:
                await self._spinner.stop()
                self._spinner.visible = False

    async def toggle_collapse(self):
        """Toggle collapsed state of the panel."""
        self.collapsed = not self.collapsed
        if self.collapsed:
            # Store current height before collapsing
            self._prev_height = self.styles.get("height", 20)
            await self.styles.animate("height", 3)
        else:
            # Restore previous height
            await self.styles.animate("height", getattr(self, "_prev_height", 20))

    async def set_filter(self, filter_text: str):
        """Set a filter for the panel content."""
        self.filter_text = filter_text
        await self.refresh_content()

    async def clear_filter(self):
        """Clear the current filter."""
        if self.filter_text:
            self.filter_text = ""
            await self.refresh_content()

    async def on_focus(self):
        """Handle focus event."""
        self.has_focus = True
        await self.refresh_content()

    async def on_blur(self):
        """Handle blur event."""
        self.has_focus = False
        await self.refresh_content()

    async def refresh_content(self):
        """Refresh the panel content. Override in subclasses."""
        # Implement in subclasses


class OutputLine:
    """Output line for internal use when Rich is not available."""
    def __init__(self, content="", stream="stdout"):
        self.content = content
        self.stream = stream
        self.timestamp = time.time()


class OutputPanel(BasePanel, ScrollView):
    """Panel for displaying script output."""

    def __init__(self):
        """Initialize the output panel."""
        super().__init__(title="Output")
        self.outputs = []
        self.search = SearchableText()
        self.search_mode = False
        self.search_input = ""
        self.auto_scroll = True
        self.show_timestamps = False
        self.group_by_stream = False
        # Create a class-level slots to safely add original_output
        self.__dict__["_original_outputs"] = {}

    def _store_original_output(self, text_obj, output_obj):
        """Store original output safely."""
        self._original_outputs[id(text_obj)] = output_obj
        
    def _get_original_output(self, text_obj):
        """Get original output safely."""
        return self._original_outputs.get(id(text_obj))

    async def add_output(self, output):
        """Add an output line to the panel."""
        # Fix: Check if output is a string or OutputLine object
        if isinstance(output, str):
            # Handle string input (for tests)
            content = output
            stream = "stdout"  # Default stream
            output = OutputLine(content=content, stream=stream)

        # Now proceed with OutputLine object
        if output.stream == "stderr":
            text = Text(output.content, style="red")
        elif output.stream == "system":
            text = Text(output.content, style="yellow")
        else:
            text = Text(output.content)

        # Store the original OutputLine safely
        self._store_original_output(text, output)
        self.outputs.append(text)
        await self.update_content()

        # Auto-scroll to bottom if enabled
        if self.auto_scroll:
            await self.scroll_to_bottom()

    async def add_message(self, message: str):
        """Add a system message to the panel."""
        text = Text(f"[SYSTEM] {message}", style="bold blue")
        output = OutputLine(content=message, stream="system")
        self._store_original_output(text, output)
        self.outputs.append(text)
        await self.update_content()

        # Auto-scroll to bottom if enabled
        if self.auto_scroll:
            await self.scroll_to_bottom()

    async def add_exception(self, exc: ExceptionEvent):
        """Add an exception to the output."""
        message = f"Exception: {exc.exception_type}: {exc.message}" 
        text = Text(message, style="bold red")
        output = OutputLine(content=message, stream="exception")
        self._store_original_output(text, output)
        self.outputs.append(text)
        await self.update_content()

        # Auto-scroll to bottom if enabled
        if self.auto_scroll:
            await self.scroll_to_bottom()

    async def clear(self):
        """Clear the output panel."""
        self.outputs.clear()
        self._original_outputs.clear()
        await self.update_content()

    async def action_search(self):
        """Activate search mode."""
        self.search_mode = True
        self.search_input = ""
        await self.update_content()

    async def action_toggle_timestamps(self):
        """Toggle timestamp display."""
        self.show_timestamps = not self.show_timestamps
        await self.update_content()

    async def action_toggle_grouping(self):
        """Toggle grouping by stream type."""
        self.group_by_stream = not self.group_by_stream
        await self.update_content()

    async def action_toggle_autoscroll(self):
        """Toggle auto-scrolling."""
        self.auto_scroll = not self.auto_scroll
        if self.auto_scroll:
            await self.scroll_to_bottom()

    async def on_key(self, event):
        """Handle key events in search mode."""
        if not self.search_mode:
            return await super().on_key(event)

        # Handle key events for search mode
        key = event.key
        
        # Exit search mode
        if key == "escape":
            self.search_mode = False
            await self.update_content()
            return

        # Perform search
        if key == "enter":
            self.search.search([str(o) for o in self.outputs], self.search_input)
            await self.update_content()
            return

        # Next match
        if key == "n":
            self.search.next_match()
            await self.update_content()
            return

        # Previous match
        if key == "p":
            self.search.prev_match()
            await self.update_content()
            return

        # Backspace
        if key == "backspace" and self.search_input:
            self.search_input = self.search_input[:-1]
            await self.update_content()
            return

        # Add character to search input
        if len(key) == 1:
            self.search_input += key
            await self.update_content()
            return

        # Default handling
        await super().on_key(event)

    async def scroll_to_bottom(self):
        """Scroll to the bottom of the output."""
        if hasattr(self, "scrollarea") and hasattr(self.scrollarea, "scroll_to"):
            await self.scrollarea.scroll_to(y=1.0, animate=False)

    async def refresh_content(self):
        """Refresh content based on current state."""
        await self.update_content()

    async def update_content(self):
        """Update the panel content."""
        # Apply filter if set
        filtered_outputs = self._filter_outputs()

        if self.search_mode and self.search.match_indices:
            # Show highlighted search results
            highlighted = self.search.highlight_matches([str(o) for o in filtered_outputs])
            renderables = highlighted
        else:
            renderables = filtered_outputs.copy()

        # Add search input bar if in search mode
        if self.search_mode:
            search_text = Text(f"Search: {self.search_input}█")
            if self.search.match_indices:
                current = (
                    self.search.current_match + 1 if self.search.current_match >= 0 else 0
                )
                search_text.append(f" ({current}/{len(self.search.match_indices)} matches)")
            renderables.append(Text(""))  # Empty line
            renderables.append(search_text)

        # Add timestamps if enabled
        if self.show_timestamps:
            for i, renderable in enumerate(renderables):
                original = self._get_original_output(renderable)
                if original and hasattr(original, "timestamp"):
                    timestamp = format_time(original.timestamp)
                    renderables[i] = Text(f"[{timestamp}] ") + renderable

        # Handle group by stream if enabled
        if self.group_by_stream:
            grouped = {"stdout": [], "stderr": [], "system": [], "exception": []}
            for renderable in renderables:
                original = self._get_original_output(renderable)
                if original and hasattr(original, "stream"):
                    stream = original.stream
                    if stream in grouped:
                        grouped[stream].append(renderable)
                    else:
                        grouped["stdout"].append(renderable)
                else:
                    grouped["stdout"].append(renderable)

            # Create grouped display
            group_displays = []
            for stream, items in grouped.items():
                if items:
                    stream_title = stream.upper()
                    stream_content = "\n".join([str(r) for r in items])
                    group_displays.append(Panel(stream_content, title=stream_title))

            # Create columns layout if we have groups
            if group_displays:
                content = Columns(group_displays)
            else:
                content = Panel("No output", title="Output")
        else:
            # Regular display
            content = Panel("\n".join([str(r) for r in renderables]), title="Output")

        # Add focus/filter indicators to title
        title = self.title
        if self.has_focus:
            title += " [FOCUSED]"
        if self.filter_text:
            title += f" [FILTER: {self.filter_text}]"

        # Update content based on environment
        if hasattr(self, "_test_display"):
            await self._test_display(Panel(content, title=title))
        else:
            await self.update(Panel(content, title=title))

    def _filter_outputs(self):
        """Filter outputs based on filter_text."""
        if not self.filter_text:
            return self.outputs

        filter_text = self.filter_text.lower()
        filtered = []
        
        for out in self.outputs:
            original = self._get_original_output(out)
            if original and hasattr(original, "content"):
                if filter_text in original.content.lower():
                    filtered.append(out)
                    continue
                    
            if filter_text in str(out).lower():
                filtered.append(out)
                
        return filtered


class CallGraphPanel(BasePanel):
    """Panel for displaying the call graph."""

    def __init__(self):
        """Initialize the call graph panel."""
        super().__init__(title="Call Graph")
        self._tree = None
        self.call_nodes = {}
        self.highlighter = ActiveFunctionHighlighter()
        self.display_var_values = True
        self.show_return_values = True
        self.show_timestamps = False
        self.view_mode = "tree"  # "tree" or "timeline"
        self.variable_inspector = None  # Will be initialized in on_mount

    async def on_mount(self):
        """Set up the initial tree."""
        self._tree = Tree("Execution")
        self.highlighter.set_tree(self._tree)
        try:
            await self.mount(self._tree)
            # Create variable inspector
            self.variable_inspector = VariableInspectorWidget()
            await self.mount(self.variable_inspector)
            self.variable_inspector.visible = False
        except (ImportError, RuntimeError) as e:
            # Log error and continue - allows tests to run without full textual
            print(f"Tree mount failed (testing mode): {e}")

    def _set_tree_for_test(self, mock_tree):
        """Set tree for testing purposes only."""
        self._tree = mock_tree

    async def add_call(self, call: CallEvent):
        """Add a function call to the graph."""
        if self._tree is None:
            self._tree = Tree("Execution")
            self.highlighter.set_tree(self._tree)
            try:
                await self.mount(self._tree)
            except (ImportError, RuntimeError) as e:
                print(f"Tree mount failed: {e}")
                return

        # Format function name and location
        label = f"{call.function_name}()"
        if self.show_timestamps:
            timestamp = format_time(call.timestamp)
            label = f"[{timestamp}] {label}"

        label += f" at {call.filename}:{call.line_no}"

        # Format arguments with enhanced variable display
        if call.args and self.display_var_values:
            args_table = Table(show_header=False, box=None)
            args_table.add_column("Name")
            args_table.add_column("Value")

            for k, v in call.args.items():
                # Skip internal/special variables
                if k.startswith("_") or k == "self":
                    continue

                # Truncate very long values
                v_str = str(v)
                if len(v_str) > 50:
                    v_str = v_str[:47] + "..."

                args_table.add_row(k, v_str)

            if getattr(args_table, "row_count", 0) > 0:
                label += f"\nArgs: {args_table}"

        # Update the variable inspector if it exists
        if self.variable_inspector and call.args:
            self.variable_inspector.set_variables(call.function_name, call.args)

        # Different styling based on view mode
        if self.view_mode == "timeline":
            # For timeline view, we always add at root level with indentation to show depth
            indent = "  " * (len(self.call_nodes) % 10)  # Simple visualization
            node = self._tree.add(f"{indent}{label}")
        else:
            # For tree view, maintain parent/child relationships
            if call.parent_id and call.parent_id in self.call_nodes:
                parent_node = self.call_nodes[call.parent_id]
                node = self._tree.add(label, parent=parent_node.id)
            else:
                node = self._tree.add(label)

        self.call_nodes[call.call_id] = node

        # Store call data for reference
        node.call_data = call

        # Highlight current function call
        self.highlighter.highlight_function(call.call_id)

    async def add_return(self, ret: ReturnEvent):
        """Update the call graph with a return value."""
        if ret.call_id not in self.call_nodes:
            return

        node = self.call_nodes[ret.call_id]

        # Only show return values if enabled
        if not self.show_return_values:
            return

        # Update node label with return value
        current_label = node.label

        # Format return value
        return_text = f"→ {ret.return_value}"
        if len(return_text) > 50:
            return_text = return_text[:47] + "..."

        node.label = f"{current_label} {return_text}"

        # Add timestamp if enabled
        if self.show_timestamps:
            timestamp = format_time(ret.timestamp)
            node.label = f"{node.label} [{timestamp}]"

        # Apply special styling for return values
        if hasattr(node, "set_style"):
            node.set_style("dim blue")

        await self.refresh_tree()

    async def clear(self):
        """Clear the call graph."""
        self.call_nodes.clear()
        if self.variable_inspector:
            self.variable_inspector.clear()
            
        if self._tree is not None:
            try:
                self.remove_widget(self._tree)
                self._tree = Tree("Execution")
                await self.mount(self._tree)
            except (ImportError, RuntimeError) as e:
                print(f"Tree reset failed: {e}")
                self._tree = Tree("Execution")  # At least reset the tree

    async def toggle_var_display(self):
        """Toggle variable value display."""
        self.display_var_values = not self.display_var_values
        if self.variable_inspector:
            self.variable_inspector.visible = self.display_var_values
        await self.refresh_tree()

    async def toggle_view_mode(self):
        """Toggle between tree and timeline view."""
        # Save call data to rebuild view
        calls = [
            node.call_data
            for node in self.call_nodes.values()
            if hasattr(node, "call_data")
        ]

        # Toggle mode
        self.view_mode = "timeline" if self.view_mode == "tree" else "tree"

        # Clear and rebuild
        await self.clear()

        # Sort calls by timestamp if in timeline mode
        if self.view_mode == "timeline":
            calls.sort(key=lambda c: c.timestamp)

        # Re-add calls
        for call in calls:
            await self.add_call(call)

    async def toggle_timestamp_display(self):
        """Toggle timestamp display."""
        self.show_timestamps = not self.show_timestamps
        await self.refresh_tree()

    async def toggle_return_values(self):
        """Toggle return value display."""
        self.show_return_values = not self.show_return_values
        await self.refresh_tree()

    async def refresh_content(self):
        """Refresh content based on current settings."""
        await self.refresh_tree()

    async def refresh_tree(self):
        """Refresh the tree widget."""
        if self._tree and hasattr(self._tree, "refresh"):
            self._tree.refresh()

    @property
    def tree(self):
        """Get the tree widget. Used for testing."""
        return self._tree


class ExceptionPanel(BasePanel):
    """Panel for displaying exceptions."""

    def __init__(self):
        """Initialize the exceptions panel."""
        super().__init__(title="Exceptions")
        self.exceptions = []
        self.show_all = False
        self.detailed_view = True

    async def add_exception(self, exc: ExceptionEvent):
        """Add an exception to the panel."""
        self.exceptions.append(exc)
        await self.update_content()

    async def clear(self):
        """Clear the exceptions panel."""
        self.exceptions.clear()
        await self.update_content()

    async def toggle_view_mode(self):
        """Toggle between showing only the latest exception or all exceptions."""
        self.show_all = not self.show_all
        await self.update_content()

    async def toggle_detail_level(self):
        """Toggle between detailed and summary exception view."""
        self.detailed_view = not self.detailed_view
        await self.update_content()

    async def refresh_content(self):
        """Refresh content based on current settings."""
        await self.update_content()

    async def update_content(self):
        """Update the panel content."""
        if not self.exceptions:
            # Check if we're in a test environment
            if hasattr(self, "update_render_str"):
                await self.update_render_str(Panel("No exceptions", title="Exceptions"))
            else:
                # Use the standard update method
                await self.update(Panel("No exceptions", title=self.title))
            return

        # Determine which exceptions to show
        exceptions_to_show = self.exceptions if self.show_all else [self.exceptions[-1]]

        # Create content based on view type
        if len(exceptions_to_show) == 1 and self.detailed_view:
            # Detailed view for single exception
            exc = exceptions_to_show[0]
            tb_text = "\n".join(exc.traceback)
            content = Panel(
                Syntax(
                    tb_text,
                    "python",
                    theme="monokai",
                    line_numbers=True,
                    word_wrap=True,
                ),
                title=f"Exception: {exc.exception_type}",
            )
        else:
            # Summary view for multiple exceptions
            table = Table(box=ROUNDED)
            table.add_column("Time")
            table.add_column("Type")
            table.add_column("Message")

            for exc in exceptions_to_show:
                timestamp = format_time(exc.timestamp)
                table.add_row(
                    timestamp, Text(exc.exception_type, style="red bold"), exc.message
                )

            view_type = "Detailed" if self.detailed_view else "Summary"
            mode = "All Exceptions" if self.show_all else "Latest Exception"
            content = Panel(table, title=f"{self.title} [{view_type}] [{mode}]")

        # Check if we're in a test environment
        if hasattr(self, "update_render_str"):
            await self.update_render_str(content)
        else:
            await self.update(content)


class LogPanel(BasePanel, ScrollView):
    """Panel specifically for log messages."""

    def __init__(self):
        """Initialize the log panel."""
        super().__init__(title="Logs")
        self.logs = []
        self.log_levels = {
            "DEBUG": "dim blue",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red bold",
        }
        self.visible_levels = set(self.log_levels.keys())
        self.search = SearchableText()

    async def add_log(self, level: str, message: str, source: str = ""):
        """Add a log message.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message content
            source: Source of the log message
        """
        # Normalize log level
        level = level.upper()
        if level not in self.log_levels:
            level = "INFO"

        timestamp = time.time()
        log_entry = {
            "level": level,
            "message": message,
            "source": source,
            "timestamp": timestamp,
        }
        self.logs.append(log_entry)

        # Only update if this log level is visible
        if level in self.visible_levels:
            await self.update_content()

    async def toggle_log_level(self, level: str):
        """Toggle visibility of a log level.

        Args:
            level: Log level to toggle
        """
        level = level.upper()
        if level in self.visible_levels:
            self.visible_levels.remove(level)
        else:
            self.visible_levels.add(level)
        await self.update_content()

    async def clear(self):
        """Clear all logs."""
        self.logs.clear()
        await self.update_content()

    async def update_content(self):
        """Update the panel content."""
        # Filter logs based on visible levels and filter text
        filtered_logs = [log for log in self.logs if log["level"] in self.visible_levels]

        if self.filter_text:
            filter_text = self.filter_text.lower()
            filtered_logs = [
                log
                for log in filtered_logs
                if filter_text in log["message"].lower() or filter_text in log["source"].lower()
            ]

        if not filtered_logs:
            if hasattr(self, "_test_display"):
                await self._test_display(Panel("No logs", title=self.title))
            else:
                await self.update(Panel("No logs", title=self.title))
            return

        # Format logs as text with appropriate styling
        renderables = []
        for log in filtered_logs:
            timestamp = format_time(log["timestamp"])
            level_style = self.log_levels.get(log["level"], "")

            text = Text()
            text.append(f"[{timestamp}] ", style="dim")
            text.append(f"[{log['level']}] ", style=level_style)

            if log["source"]:
                text.append(f"({log['source']}) ", style="italic")

            text.append(log["message"])
            renderables.append(text)

        # Create the panel
        title = self.title
        if len(self.visible_levels) < len(self.log_levels):
            visible = ", ".join(sorted(self.visible_levels))
            title += f" [Showing: {visible}]"

        if self.filter_text:
            title += f" [Filter: {self.filter_text}]"

        # Update the panel
        if hasattr(self, "_test_display"):
            await self._test_display(
                Panel("\n".join([str(r) for r in renderables]), title=title)
            )
        else:
            await self.update(
                Panel("\n".join([str(r) for r in renderables]), title=title)
            )
