# pylint: disable=import-error, attribute-defined-outside-init, trailing-whitespace, broad-exception-caught, missing-module-docstring, missing-class-docstring, missing-function-docstring

import asyncio
import traceback
import time
from typing import Dict, Any, Optional

# Third-party imports
from textual.widgets import Header, Footer  # type: ignore
from textual.binding import Binding  # type: ignore

# Local imports
from .compat import App, USING_FALLBACKS
from ..executor import ScriptExecutor
from .panels import OutputPanel, CallGraphPanel, ExceptionPanel
from .widgets import (
    StatusBar,
    AnimatedSpinnerWidget,
    ProgressBarWidget,
    MetricsWidget,
    TimelineWidget,
    SearchBar,
    VariableInspectorWidget,
    KeyBindingsWidget,
)


class PyTUIApp(App):
    """PyTUI Application for visualizing Python execution."""

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("p", "toggle_pause", "Pause/Resume", show=True),
        Binding("r", "restart", "Restart", show=USING_FALLBACKS),
        Binding("/", "search", "Search", show=True),
        Binding("c", "toggle_collapse", "Collapse/Expand", show=True),
        Binding("v", "toggle_vars", "Toggle Variables", show=True),
        Binding("m", "toggle_metrics", "Show/Hide Metrics", show=True),
        Binding("t", "toggle_timeline", "Show/Hide Timeline", show=True),
        Binding("h", "toggle_help", "Show/Hide Help", show=True),
    ]

    def __init__(self, *args, **kwargs):
        """Initialize the application."""
        super().__init__(*args, **kwargs)
        # Group related attributes into a dict to reduce instance attribute count
        self._components = {
            "executor": None,
            "output_panel": None,
            "call_graph_panel": None,
            "exception_panel": None,
            "view": None,
        }
        self.is_paused = False
        self.event_task = None
        self._metrics_visible = False
        self._timeline_visible = False
        self._help_visible = False
        self._setup_error_handling()
        self._stats = {"calls": 0, "returns": 0, "exceptions": 0, "output_lines": 0}
        self._last_stat_update = time.time()

    @property
    def executor(self):
        """Get the executor component."""
        return self._components["executor"]

    @executor.setter
    def executor(self, value):
        """Set the executor component."""
        self._components["executor"] = value

    def _setup_error_handling(self):
        """Set up error handling with traceback."""
        try:
            # Use traceback immediately to satisfy import
            self.error_handler = lambda e: self.show_error(
                f"Error: {str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}"
            )
        except Exception as e:
            print(f"Error setting up error handling: {e}")

    def set_executor(self, executor: ScriptExecutor):
        """Set the script executor."""
        self.executor = executor

    async def on_mount(self):
        """Set up the UI layout."""
        # Use self.view if available; otherwise, create a DummyContainer for tests.
        if not hasattr(self, "view") or self.view is None:

            class DummyContainer:
                async def dock(self, *args, **kwargs):
                    pass

                async def mount(self, *args, **kwargs):
                    pass

            self.view = DummyContainer()
        container = self.view
        await container.dock(Header(), edge="top")
        await container.dock(Footer(), edge="bottom")

        # Create status bar and spinner
        self.status_bar = StatusBar()
        self.spinner = AnimatedSpinnerWidget(
            "Running script...", "dots3", show_elapsed=True
        )
        self.progress_bar = ProgressBarWidget(description="Execution Progress")
        self.search_bar = SearchBar()

        # Create optional widgets
        self.metrics_widget = MetricsWidget()
        self.timeline_widget = TimelineWidget()
        self.variable_inspector = VariableInspectorWidget()
        self.key_bindings_widget = KeyBindingsWidget()

        # Set up key bindings display
        self.key_bindings_widget.set_bindings(
            {
                "Q": "Quit",
                "P": "Pause/Resume",
                "R": "Restart",
                "/": "Search",
                "C": "Collapse/Expand",
                "V": "Toggle Variables",
                "M": "Toggle Metrics",
                "T": "Toggle Timeline",
                "H": "Toggle Help",
            }
        )

        # Add bottom widgets
        await container.dock(self.status_bar, edge="bottom", size=1, z=1)
        await container.dock(self.spinner, edge="bottom", size=1, z=2)
        await container.dock(self.search_bar, edge="bottom", size=3, z=3)
        await container.dock(self.key_bindings_widget, edge="bottom", size=3, z=0)

        # Create panels and assign to instance attributes
        self.output_panel = OutputPanel()
        self.call_graph_panel = CallGraphPanel()
        self.exception_panel = ExceptionPanel()

        # Initialize collapsible state
        self.collapsed_panels = {
            "call_graph": False,
            "output": False,
            "exception": False,
        }

        # Dock main panels
        await container.dock(
            self.call_graph_panel, self.output_panel, self.exception_panel, edge="top"
        )

        # Optional panels start hidden
        if self._metrics_visible:
            await container.dock(self.metrics_widget, edge="right", size=30)

        if self._timeline_visible:
            await container.dock(self.timeline_widget, edge="bottom", size=10)

        if self._help_visible:
            await container.dock(self.key_bindings_widget, edge="bottom", size=3)

        # Start the executor if available
        if self.executor:
            self.executor.start()
            # Start the spinner
            await self.spinner.start()
            # Start progress tracking
            await self.progress_bar.auto_pulse()
            # Start and save the event processing task
            self.event_task = asyncio.create_task(self.process_events())
            # Start metrics collection
            self.stats_task = asyncio.create_task(self._collect_stats())

    async def on_unmount(self):
        # Cancel the event processing task, if it exists
        if hasattr(self, "event_task"):
            self.event_task.cancel()
            try:
                await self.event_task
            except asyncio.CancelledError:
                pass

    async def _collect_stats(self):
        """Periodically collect and update statistics."""
        try:
            while self.executor and self.executor.is_running:
                # Update statistics
                self._stats["output_lines"] = len(self.output_panel.outputs)

                # Update status bar with stats
                self.status_bar.update_stats(self._stats)

                # Add to metrics (track rate of events)
                now = time.time()
                elapsed = now - self._last_stat_update

                if elapsed >= 1.0:  # Update metrics every second
                    # Calculate rates
                    calls_rate = self._stats["calls"] / elapsed
                    output_rate = self._stats["output_lines"] / elapsed

                    # Add to metrics widget
                    self.metrics_widget.add_metric("calls/sec", calls_rate)
                    self.metrics_widget.add_metric("output/sec", output_rate)

                    # Reset for next update
                    self._last_stat_update = now

                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error collecting stats: {e}")

    async def process_events(self):
        """Process events from the executor."""
        if not self.executor:
            return
        collector = self.executor.collector

        while self.executor.is_running:
            try:
                # Get events from the collector
                event_type, event = await collector.get_event()

                # Update statistics regardless of pause state
                self._stats[event_type + "s"] = self._stats.get(event_type + "s", 0) + 1

                # Skip processing if paused
                if self.is_paused:
                    continue

                # Process the event
                if event_type == "output":
                    await self.output_panel.add_output(event)
                    self.timeline_widget.add_event("output", event.content[:50])
                elif event_type == "call":
                    await self.call_graph_panel.add_call(event)
                    # Track function calls in the variable inspector
                    if event.args:
                        self.variable_inspector.set_variables(
                            event.function_name, event.args
                        )
                    self.timeline_widget.add_event(
                        "call",
                        f"{event.function_name}() at {event.filename}:{event.line_no}",
                    )
                    # Update spinner text
                    self.spinner.set_text(f"Executing {event.function_name}()")
                elif event_type == "return":
                    await self.call_graph_panel.add_return(event)
                    self.timeline_widget.add_event(
                        "return", f"{event.function_name}() → {event.return_value}"
                    )
                elif event_type == "exception":
                    await self.exception_panel.add_exception(event)
                    await self.output_panel.add_exception(event)
                    self.timeline_widget.add_event(
                        "exception", f"{event.exception_type}: {event.message}"
                    )
                    # Update status for exception
                    self.status_bar.set_status_message(
                        f"Exception: {event.exception_type}"
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                # More detailed error reporting
                error_details = traceback.format_exc()
                print(f"Error processing event: {str(e)}\n{error_details}")
                # Add a delay to prevent tight loop on errors
                await asyncio.sleep(0.1)

        # Stop animations when execution finishes
        await self.spinner.stop()
        await self.progress_bar.stop_pulse()

        # Update status
        self.status_bar.set_running(False)
        self.status_bar.set_status_message("Execution complete")

    async def action_toggle_pause(self):
        """Toggle pause/resume execution updates."""
        if not self.executor:
            return
        self.is_paused = not self.is_paused
        # Changed from "if self is_paused:" to "if self.is_paused:"
        if self.is_paused:
            self.executor.pause()
            await self.output_panel.add_message("Execution updates paused")
        else:
            self.executor.resume()
            await self.output_panel.add_message("Execution updates resumed")

    async def action_restart(self):
        """Restart the script execution."""
        if not self.executor:
            return
        await self.output_panel.clear()
        await self.call_graph_panel.clear()
        await self.exception_panel.clear()
        self.executor.restart()
        await self.output_panel.add_message("Restarting execution...")

    async def action_search(self):
        """Activate search in the output panel."""
        # Focus the output panel and start search
        await self.output_panel.focus()
        await self.output_panel.action_search()

    async def action_toggle_collapse(self):
        """Toggle collapse state of the focused panel."""
        # Get the currently focused widget
        focused = self.focused

        if focused == self.call_graph_panel:
            self.collapsed_panels["call_graph"] = not self.collapsed_panels[
                "call_graph"
            ]
            if self.collapsed_panels["call_graph"]:
                await self.call_graph_panel.styles.animate("height", 3)
            else:
                await self.call_graph_panel.styles.animate("height", 20)
        elif focused == self.output_panel:
            self.collapsed_panels["output"] = not self.collapsed_panels["output"]
            if self.collapsed_panels["output"]:
                await self.output_panel.styles.animate("height", 3)
            else:
                await self.output_panel.styles.animate("height", 20)
        elif focused == self.exception_panel:
            self.collapsed_panels["exception"] = not self.collapsed_panels["exception"]
            if self.collapsed_panels["exception"]:
                await self.exception_panel.styles.animate("height", 3)
            else:
                await self.exception_panel.styles.animate("height", 10)

    async def action_toggle_vars(self):
        """Toggle variable display in call graph."""
        if hasattr(self.call_graph_panel, "toggle_var_display"):
            await self.call_graph_panel.toggle_var_display()

    async def action_toggle_metrics(self):
        """Toggle metrics panel visibility."""
        self._metrics_visible = not self._metrics_visible

        if self._metrics_visible:
            # Remove first if it exists to avoid duplicates
            try:
                self.view.remove_widget(self.metrics_widget)
            except (ValueError, AttributeError):
                pass

            await self.view.dock(self.metrics_widget, edge="right", size=30)
        else:
            try:
                self.view.remove_widget(self.metrics_widget)
            except (ValueError, AttributeError):
                pass

    async def action_toggle_timeline(self):
        """Toggle timeline panel visibility."""
        self._timeline_visible = not self._timeline_visible

        if self._timeline_visible:
            # Remove first if it exists to avoid duplicates
            try:
                self.view.remove_widget(self.timeline_widget)
            except (ValueError, AttributeError):
                pass

            await self.view.dock(self.timeline_widget, edge="bottom", size=10)
        else:
            try:
                self.view.remove_widget(self.timeline_widget)
            except (ValueError, AttributeError):
                pass

    async def action_toggle_help(self):
        """Toggle help panel visibility."""
        self._help_visible = not self._help_visible

        if self._help_visible:
            # Remove first if it exists to avoid duplicates
            try:
                self.view.remove_widget(self.key_bindings_widget)
            except (ValueError, AttributeError):
                pass

            await self.view.dock(self.key_bindings_widget, edge="bottom", size=3)
        else:
            try:
                self.view.remove_widget(self.key_bindings_widget)
            except (ValueError, AttributeError):
                pass
