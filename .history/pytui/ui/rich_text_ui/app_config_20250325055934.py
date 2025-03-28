"""Configuration module for TUI applications.

This module provides configuration management for terminal user interface applications.
"""

import sys
import signal
import asyncio
from .container import Container
from .panel import Panel
from .text import Text


class AppConfig:
    """Configuration class for App."""

    def __init__(self, title="TUI Application"):
        """Initialize app configuration.

        Args:
            title: Application title
        """
        self.title = title
        self._config = {
            'mounted': False,
            'error': None,
            'is_running': False,
            'bindings': {},
            'loop': None,
            'refresh_task': None,
            'view': Container()
        }

    @property
    def mounted(self):
        """Get mounted state."""
        return self._config['mounted']

    @mounted.setter
    def mounted(self, value):
        """Set mounted state."""
        self._config['mounted'] = value

    @property
    def error(self):
        """Get error state."""
        return self._config['error']

    @error.setter
    def error(self, value):
        """Set error state."""
        self._config['error'] = value

    @property
    def is_running(self):
        """Get running state."""
        return self._config['is_running']

    @is_running.setter
    def is_running(self, value):
        """Set running state."""
        self._config['is_running'] = value

    @property
    def view(self):
        """Get view container."""
        return self._config['view']

    @view.setter
    def view(self, value):
        """Set view container."""
        self._config['view'] = value

    def set_event_loop(self, loop):
        """Set the event loop.

        Args:
            loop: Asyncio event loop
        """
        self._config['loop'] = loop

    async def on_mount(self):
        """Called when the app is mounted. Initializes the application state and UI.

        This method should be overridden by subclasses to:
        - Set up initial application state
        - Create and mount widgets
        - Register event handlers
        - Initialize resources
        - Set up background tasks

        Returns:
            None

        Examples:
            class MyApp(App):
                async def on_mount(self):
                    await super().on_mount() # Call parent implementation first

                    # Set up app state
                    self.counter = 0

                    # Create widgets
                    self.header = Panel("My App")
                    self.content = Container()
                    self.status = Text("Ready")

                    # Mount widgets
                    await self.view.mount(
                        self.header,
                        self.content,
                        self.status
                    )

                    # Register handlers
                    self.view.on("key", self.handle_key)

                    # Start background tasks
                    asyncio.create_task(self.update_loop())
        """
        try:
            # Initialize base application state
            self.mounted = True
            self.error = None

            # Set up default key bindings
            self._config['bindings'].update(
                {
                    "q": self.exit,
                    "ctrl+c": self.exit,
                    "r": self.refresh,
                }
            )

            # Create default layout if view is empty
            if not self.view.children:
                header = Panel(self.title, border_style="bold")
                content = Container(name="main")
                footer = Text("Press 'q' to quit", style="dim")
                await self.view.mount(header, content, footer)

            # Initial render
            await self.view.refresh()

            # Set up signal handlers
            self._setup_signal_handlers()

            # Create background task for periodic refresh
            async def refresh_loop():
                while self.is_running:
                    await asyncio.sleep(0.1)
                    if self.view.children:
                        await self.view.refresh()

            self._config['refresh_task'] = asyncio.create_task(refresh_loop())
        except (RuntimeError, IOError, asyncio.CancelledError) as e:
            self.error = str(e)
            print(f"Error during mount: {e}", file=sys.stderr)

        except (ValueError, AttributeError, TypeError) as e:
            # Catch specific exceptions that could occur during widget operations
            self.error = str(e)
            print(f"Error during mount: {e}", file=sys.stderr)
            # Ensure cleanup on error
            self.mounted = False
            if self._config['refresh_task']:
                self._config['refresh_task'].cancel()
            await self.on_unmount()

    async def refresh(self):
        """Force a refresh of the display."""
        if self.view:
            await self.view.refresh()
        self.mounted = False
        self.error = None

    async def on_unmount(self):
        """Called when the app is unmounted. Performs cleanup and disposal.

        This method handles:
        - Canceling background tasks
        - Cleaning up widget tree
        - Closing connections/files
        - Resetting terminal state
        - Stopping running processes"""
        try:
            # Cancel refresh task if running
            if hasattr(self, "_config['refresh_task']"):
                self._config['refresh_task'].cancel()
                try:
                    await self._config['refresh_task']
                except asyncio.CancelledError:
                    pass

            # Remove signal handlers
            if self._config['loop']:
                try:
                    self._config['loop'].remove_signal_handler(signal.SIGINT)
                    self._config['loop'].remove_signal_handler(signal.SIGTERM)
                except (NotImplementedError, ValueError):
                    pass

            # Clear widget tree
            if self.view:
                await self._unmount_widget_tree(self.view)
                self.view.children.clear()

            # Reset terminal state
            self._reset_terminal()

            # Clear application state
            self.mounted = False
            self._config['bindings'].clear()
            self.error = None

        except (RuntimeError, IOError) as err:
            # Log specific cleanup errors but don't raise
            print(f"Error during unmount: {err}", file=sys.stderr)

    async def _unmount_widget_tree(self, widget):
        """Recursively unmount all widgets in the tree."""
        if hasattr(widget, "children"):
            # Make a copy of children list to avoid modification
            # during iteration
            children = widget.children[:]
            for child in children:
                await self._unmount_widget_tree(child)
                widget.remove_widget(child)

        # Clear widget state
        widget.parent = None
        widget.focused = False
        if hasattr(widget, "event_handlers"):
            widget.event_handlers.clear()

    def _reset_terminal(self):
        """Reset terminal to initial state."""
        sys.stdout.write("\033[?25h")  # Show cursor
        sys.stdout.write("\033[0m")    # Reset colors
        sys.stdout.write("\033[2J")    # Clear screen
        sys.stdout.write("\033[H")     # Move to home position
        sys.stdout.flush()

    def exit(self):
        """Exit the application."""
        self._config['is_running'] = False

    def action(self, action_name):
        """Handle an action.

        Args:
            action_name: Action to perform

        Returns:
            The result of the action method if found, None otherwise
        """
        method_name = f"action_{action_name}"
        if hasattr(self, method_name):
            return getattr(self, method_name)()
        print(f"Action not found: {action_name}")
        return None

    def run(self):
        """Run the application."""
        self.is_running = True

        # Create and set event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self.set_event_loop(loop)

        # Run the application
        try:
            # Mount the application
            loop.run_until_complete(self.on_mount())

            # In fallback mode, render the initial state and exit
            print(f"\n{self.title}\n{'=' * len(self.title)}\n")
            print(self.view.render())
            print("\nPress Ctrl+C to exit\n")

            # Keep the app running until exit() is called
            while self.is_running:
                try:
                    loop.run_until_complete(asyncio.sleep(0.1))
                except KeyboardInterrupt:
                    print("\nExiting...")
                    self.is_running = False

        finally:
            # Unmount the application
            loop.run_until_complete(self.on_unmount())
            if not loop.is_closed():
                loop.close()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            self._config['loop'].add_signal_handler(sig, self.exit)
