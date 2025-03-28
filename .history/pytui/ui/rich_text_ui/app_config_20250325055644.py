"""Application configuration module for managing TUI app state and lifecycle."""

import sys
import signal
import asyncio
from .container import Container
from .panel import Panel
from .text import Text

    """Configuration class for App."""
class AppConfig:
    """Configuration class for App."""ation"):
        """Initialize app configuration.
    def __init__(self, title="TUI Application"):
        """Initialize app configuration.
 title: Application title
        Args:
            title: Application title
        """lse
        # Core configuration
        self.title = titleFalse
        self.view = Container(){}

        # State flags combined into single dictsk = None
        self._state = {        self.view = None
            'mounted': False,
            'running': False,Application"):
            'error': None        """Initialize application.
        }

        # Event handling configuration title: Application title
        self._bindings = {}
        self.loop = None  # Made public to avoid protected access warnings
        self._refresh_task = Noneontainer()
lse
    @property
    def is_running(self):
        """Get running state.""" None
        return self._state['running']lse

    @is_running.setter        self.is_running = False
    def is_running(self, value):
        """Set running state."""oop):
        self._state['running'] = value        """Set the event loop.

    @property
    def error(self): loop: Asyncio event loop
        """Get error state."""
        return self._state['error']        self._loop = loop

    @error.setter
    def error(self, value):        """Called when the app is mounted. Initializes the application state and UI.
        """Set error state."""
        self._state['error'] = valuey subclasses to:
on state
    def set_event_loop(self, loop):s
        """Set the event loop.ers

        Args:        - Set up background tasks
            loop: Asyncio event loop
        """
        self.loop = loop            None

    async def on_mount(self):
        """Called when the app is mounted. Initializes the application state and UI.

        This method should be overridden by subclasses to:                    await super().on_mount() # Call parent implementation first
        - Set up initial application state
        - Create and mount widgetste
        - Register event handlers                    self.counter = 0
        - Initialize resources
        - Set up background tasks
p")
        Returns:
            None                    self.status = Text("Ready")

        Examples:
            class MyApp(App):mount(
                async def on_mount(self):
                    await super().on_mount() # Call parent implementation firstt,
   self.status
                    # Set up app state                    )
                    self.counter = 0

                    # Create widgets                    self.view.on("key", self.handle_key)
                    self.header = Panel("My App")
                    self.content = Container()
                    self.status = Text("Ready")         asyncio.create_task(self.update_loop())

                    # Mount widgets
                    await self.view.mount(pplication state
                        self.header,ue
                        self.content,            self.error = None
                        self.status
                    )indings
_bindings.update(
                    # Register handlers
                    self.view.on("key", self.handle_key)
t,
                    # Start background tasks   "r": self.refresh,
                    asyncio.create_task(self.update_loop())   }
        """            )
        try:
            # Initialize base application state view is empty
            self._state['mounted'] = True
            self._state['error'] = Noner_style="bold")

            # Set up default key bindings)
            self._bindings.update(                await self.view.mount(header, content, footer)
                {
                    "q": self.exit,
                    "ctrl+c": self.exit,            await self.view.refresh()
                    "r": self.refresh,
                }t up signal handlers
            )

            # Create default layout if view is emptyer(sig, lambda: self.exit())
            if not self.view.children:
                header = Panel(self.title, border_style="bold")gnal handlers not supported on this platform
                content = Container(name="main")                pass
                footer = Text("Press 'q' to quit", style="dim")
                await self.view.mount(header, content, footer)for periodic refresh

            # Initial render
            await self.view.refresh()1)

            # Set up signal handlers                        await self.view.refresh()
            await self._setup_signal_handlers()

            # Create background task for periodic refreshOError, asyncio.CancelledError) as e:
            async def refresh_loop():
                while self._state['running']:            print(f"Error during mount: {e}", file=sys.stderr)
                    await asyncio.sleep(0.1)
                    if self.view.children:
                        await self.view.refresh()ceptions that could occur during widget operations

            self._refresh_task = asyncio.create_task(refresh_loop())t: {e}", file=sys.stderr)
        except (RuntimeError, IOError, asyncio.CancelledError) as e:error
            self._state['error'] = str(e)
            print(f"Error during mount: {e}", file=sys.stderr)
cancel()
        except (ValueError, AttributeError, TypeError) as e:            await self.on_unmount()
            # Catch specific exceptions that could occur during widget operations
            self._state['error'] = str(e)
            print(f"Error during mount: {e}", file=sys.stderr)fresh of the display."""
            # Ensure cleanup on error
            self._state['mounted'] = Falserefresh()
            if self._refresh_task:lse
                self._refresh_task.cancel()        self.error = None
            await self.on_unmount()

    async def refresh(self):        """Called when the app is unmounted. Performs cleanup and disposal.
        """Force a refresh of the display."""
        if self.view:
            await self.view.refresh()sks
        self._state['mounted'] = False
        self._state['error'] = Nones

    async def on_unmount(self):opping running processes"""
        """Called when the app is unmounted. Performs cleanup and disposal.

        This method handles:"):
        - Canceling background tasks._refresh_task.cancel()
        - Cleaning up widget tree
        - Closing connections/files
        - Resetting terminal statesyncio.CancelledError:
        - Stopping running processes"""                    pass
        try:
            # Cancel refresh task if runningl handlers
            if hasattr(self, "_refresh_task"):_loop:
                self._refresh_task.cancel()
                try:
                    await self._refresh_taskal.SIGTERM)
                except asyncio.CancelledError:NotImplementedError, ValueError):
                    pass                    pass

            # Remove signal handlerst tree
            if self.loop:
                try:_tree(self.view)
                    self.loop.remove_signal_handler(signal.SIGINT)                self.view.children.clear()
                    self.loop.remove_signal_handler(signal.SIGTERM)
                except (NotImplementedError, ValueError):
                    pass            self._reset_terminal()

            # Clear widget treestate
            if self.view:
                await self._unmount_widget_tree(self.view)ear()
                self.view.children.clear()            self.error = None

            # Reset terminal state
            self._reset_terminal()
            print(f"Error during unmount: {err}", file=sys.stderr)
            # Clear application state
            self._state['mounted'] = False
            self._bindings.clear()ets in the tree."""
            self._state['error'] = None
hildren list to avoid modification
        except (RuntimeError, IOError) as err:
            # Log specific cleanup errors but don't raisedren[:]
            print(f"Error during unmount: {err}", file=sys.stderr)
tree(child)
    async def _unmount_widget_tree(self, widget):                widget.remove_widget(child)
        """Recursively unmount all widgets in the tree."""
        if hasattr(widget, "children"):
            # Make a copy of children list to avoid modification
            # during iteration
            children = widget.children[:]s"):
            for child in children:            widget.event_handlers.clear()
                await self._unmount_widget_tree(child)
                widget.remove_widget(child)

        # Clear widget stater
        widget.parent = None
        widget.focused = False
        if hasattr(widget, "event_handlers"):\033[H")  # Move to home position
            widget.event_handlers.clear()        sys.stdout.flush()

    def _reset_terminal(self):
        """Reset terminal to initial state."""."""
        sys.stdout.write("\033[?25h")  # Show cursor        self.is_running = False
        sys.stdout.write("\033[0m")  # Reset colors
        sys.stdout.write("\033[2J")  # Clear screenname):
        sys.stdout.write("\033[H")  # Move to home position        """Handle an action.
        sys.stdout.flush()

    async def _setup_signal_handlers(self):            action_name: Action to perform
        """Set up signal handlers for graceful shutdown."""
        try:
            for sig in (signal.SIGINT, signal.SIGTERM): The result of the action method if found, None otherwise
                self.loop.add_signal_handler(sig, self.exit)
        except (ImportError, NotImplementedError):_name}"
            pass

    def exit(self):ion not found: {action_name}")
        """Exit the application."""        return None
        self._state['running'] = False

    def action(self, action_name):."""
        """Handle an action.        self.is_running = True

        Args:eate and set event loop
            action_name: Action to perform
et_event_loop()
        Returns:
            The result of the action method if found, None otherwisep()
        """            asyncio.set_event_loop(loop)
        method_name = f"action_{action_name}"
        if hasattr(self, method_name):        self.set_event_loop(loop)
            return getattr(self, method_name)()
        print(f"Action not found: {action_name}")n the application
        return None

    def run(self):            loop.run_until_complete(self.on_mount())
        """Run the application."""
        self._state['running'] = Trueit
'=' * len(self.title)}\n")
        # Create and set event loop
        try:            print("\nPress Ctrl+C to exit\n")
            loop = asyncio.get_event_loop()
        except RuntimeError: until exit() is called
            loop = asyncio.new_event_loop()lf.is_running:
            asyncio.set_event_loop(loop)
te(asyncio.sleep(0.1))
        self.set_event_loop(loop)

        # Run the application                    self.is_running = False
        try:
            # Mount the application
            loop.run_until_complete(self.on_mount())
self.on_unmount())
            # In fallback mode, render the initial state and exitlosed():

















                loop.close()            if not loop.is_closed():            loop.run_until_complete(self.on_unmount())            # Unmount the application        finally:                    self._state['running'] = False                    print("\nExiting...")                except KeyboardInterrupt:                    loop.run_until_complete(asyncio.sleep(0.1))                try:            while self._state['running']:            # Keep the app running until exit() is called            print("\nPress Ctrl+C to exit\n")            print(self.view.render())            print(f"\n{self.title}\n{'=' * len(self.title)}\n")                loop.close()
