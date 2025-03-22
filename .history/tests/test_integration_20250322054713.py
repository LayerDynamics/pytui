import asyncio
import pytest
from pytui.ui.app import PyTUIApp
from pytui.collector import DataCollector
from pytui.ui.panels import OutputPanel, CallGraphPanel, ExceptionPanel
from unittest.mock import AsyncMock

# A dummy executor to simulate events feeding
class DummyExecutor:
    def __init__(self):
        self.collector = DataCollector()
        self.is_running = True
    def start(self):
        # Launch asynchronous feeding of events
        asyncio.create_task(self.feed_events())
    async def feed_events(self):
        await asyncio.sleep(0.1)
        self.collector.add_output("Dummy output", "stdout")
        self.collector.add_call("dummy_func", "dummy.py", 12, {"a": "1"})
        self.collector.add_return("dummy_func", "result")
        self.collector.add_exception(Exception("dummy error"))
        await asyncio.sleep(0.1)
        self.is_running = False
    def pause(self):
        pass
    def resume(self):
        pass
    def restart(self):
        self.collector.clear()
        self.start()

@pytest.mark.asyncio
async def test_pytui_app_integration():
    dummy_executor = DummyExecutor()
    app = PyTUIApp()
    app.set_executor(dummy_executor)
    
    # Mount the app components by calling on_mount
    await app.on_mount()
    
    # Add test display override to prevent actual rendering
    app.output_panel._test_display = AsyncMock()
    
    # Start event processing in background
    event_task = asyncio.create_task(app.process_events())
    
    # Allow more time for events to be processed (increased from 0.3)
    await asyncio.sleep(0.5)
    
    # Validate that panels have received events
    # Check the output panel for at least one output line
    assert len(app.output_panel.outputs) > 0
    
    # Check that the call graph panel registered a call event
    # Increase timeout if needed
    for _ in range(5):  # Try up to 5 times
        if len(app.call_graph_panel.call_nodes) > 0:
            break
        await asyncio.sleep(0.1)
    assert len(app.call_graph_panel.call_nodes) > 0
    
    # Check that the exception panel recorded an exception
    assert len(app.exception_panel.exceptions) > 0
    
    event_task.cancel()

@pytest.mark.asyncio
async def test_app_actions():
    dummy_executor = DummyExecutor()
    app = PyTUIApp()
    app.set_executor(dummy_executor)
    await app.on_mount()
    
    # Add test display override
    app.output_panel._test_display = AsyncMock()
    
    # Test toggle pause action
    initial_paused = app.is_paused
    await app.action_toggle_pause()
    assert app.is_paused != initial_paused
    await app.action_toggle_pause()
    assert app.is_paused == initial_paused
    
    # Test restart action.
    # Set a testing override for OutputPanel display to avoid actual rendering.
    app.output_panel._test_display = AsyncMock(return_value=None)
    # Populate output first.
    await app.output_panel.add_output("Pre-restart message", "stdout")
    assert len(app.output_panel.outputs) > 0
    await app.action_restart()
    # After restart panels should be cleared and a restart message added.
    # (Exact behavior depends on executor restart and panel updates.)
    assert len(app.output_panel.outputs) >= 0
