"""Tests for UI components."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from pytui.ui.widgets import StatusBar
from pytui.ui.panels import OutputPanel, CallGraphPanel, ExceptionPanel
from pytui.collector import OutputLine, CallEvent, ReturnEvent, ExceptionEvent

@pytest.fixture
def status_bar():
    """Create a status bar for testing."""
    return StatusBar()

def test_status_bar_init(status_bar):
    """Test status bar initialization."""
    assert status_bar.is_running is False
    assert status_bar.is_paused is False
    
def test_status_bar_render(status_bar):
    """Test status bar rendering."""
    # Test initial state (stopped)
    rendered = status_bar.render()
    assert "STOPPED" in str(rendered)
    
    # Test running state
    status_bar.set_running(True)
    rendered = status_bar.render()
    assert "RUNNING" in str(rendered)
    
    # Test paused state
    status_bar.set_paused(True)
    rendered = status_bar.render()
    assert "PAUSED" in str(rendered)
    
    # Test elapsed time formatting
    assert "00:" in str(rendered)  # Should show minutes:seconds

@pytest.mark.asyncio
async def test_output_panel():
    """Test the output panel."""
    panel = OutputPanel()
    
    # Test adding stdout output
    await panel.add_output(OutputLine("Test stdout", "stdout"))
    assert len(panel.outputs) == 1
    
    # Test adding stderr output
    await panel.add_output(OutputLine("Test stderr", "stderr"))
    assert len(panel.outputs) == 2
    assert "red" in str(panel.outputs[1].style)
    
    # Test adding a system message
    await panel.add_message("System message")
    assert len(panel.outputs) == 3
    assert "SYSTEM" in str(panel.outputs[2])
    
    # Test adding an exception
    exc = ExceptionEvent("ValueError", "Test exception", ["Traceback line 1"], 0)
    await panel.add_exception(exc)
    assert len(panel.outputs) == 4
    assert "Exception" in str(panel.outputs[3])
    
    # Test clearing
    await panel.clear()
    assert len(panel.outputs) == 0

@pytest.mark.asyncio
async def test_call_graph_panel():
    """Test the call graph panel."""
    panel = CallGraphPanel()
    
    # We need to mock the tree control since we can't test it directly
    panel.tree = AsyncMock()
    panel.tree.root = MagicMock()
    
    # Test adding a call
    call = CallEvent("test_func", "test.py", 10, {"arg1": "value1"}, call_id=1)
    await panel.add_call(call)
    
    # Should have created a tree node
    assert 1 in panel.call_nodes
    
    # Test adding a return
    ret = ReturnEvent("test_func", "42", call_id=1)
    await panel.add_return(ret)
    
    # Should have updated the node
    node = panel.call_nodes[1]
    assert "42" in node.label

@pytest.mark.asyncio
async def test_exception_panel():
    """Test the exception panel."""
    panel = ExceptionPanel()
    
    # Test initial state
    assert len(panel.exceptions) == 0
    
    # Create a mock update method to avoid rendering issues in tests
    panel.update = AsyncMock()
    
    # Test adding an exception
    exc = ExceptionEvent("ValueError", "Test exception", ["Traceback line 1"], 0)
    await panel.add_exception(exc)
    
    assert len(panel.exceptions) == 1
    panel.update.assert_called_once()
    
    # Test clearing
    await panel.clear()
    assert len(panel.exceptions) == 0
