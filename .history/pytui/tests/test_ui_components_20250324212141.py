# pylint: disable=unused-import,redefined-outer-name,protected-access, trailing-whitespace, wrong-import-order, import-outside-toplevel

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from pytui.ui.widgets import StatusBar
from pytui.ui.panels import OutputPanel, CallGraphPanel, ExceptionPanel
from pytui.collector import OutputLine, CallEvent, ReturnEvent, ExceptionEvent

@pytest.fixture
def status_bar_fixture():
    """Create a status bar for testing."""
    return StatusBar()

def test_status_bar_init(status_bar_fixture):
    """Test status bar initialization."""
    assert status_bar_fixture.is_running is False
    assert status_bar_fixture.is_paused is False

def test_status_bar_render(status_bar_fixture):
    """Test status bar rendering."""
    # Test initial state (stopped)
    rendered = status_bar_fixture.render()
    assert "STOPPED" in str(rendered)
    
    # Test running state
    status_bar_fixture.set_running(True)
    rendered = status_bar_fixture.render()
    assert "RUNNING" in str(rendered)
    
    # Test paused state
    status_bar_fixture.set_paused(True)
    rendered = status_bar_fixture.render()
    assert "PAUSED" in str(rendered)
    
    # Test elapsed time formatting
    assert "00:" in str(rendered)  # Should show minutes:seconds

@pytest.mark.asyncio
async def test_output_panel():
    """Test the output panel."""
    panel = OutputPanel()
    
    # Set a test override for display
    panel._test_display = AsyncMock(return_value=None)
    
    await panel.add_output(OutputLine("Test stdout", "stdout"))
    assert len(panel.outputs) == 1
    panel._test_display.assert_called_once()
    
    # Reset and test adding stderr output
    panel._test_display.reset_mock()
    await panel.add_output(OutputLine("Test stderr", "stderr"))
    assert len(panel.outputs) == 2
    assert "red" in str(panel.outputs[1].style)
    panel._test_display.assert_called_once()
    
    # Test adding a system message
    panel._test_display.reset_mock()
    await panel.add_message("System message")
    assert len(panel.outputs) == 3
    assert "SYSTEM" in str(panel.outputs[2])
    panel._test_display.assert_called_once()
    
    # Test adding an exception
    panel._test_display.reset_mock()
    exc = ExceptionEvent("ValueError", "Test exception", ["Traceback line 1"], 0)
    await panel.add_exception(exc)
    assert len(panel.outputs) == 4
    assert "Exception" in str(panel.outputs[3])
    panel._test_display.assert_called_once()
    
    # Test clearing
    panel._test_display.reset_mock()
    await panel.clear()
    assert len(panel.outputs) == 0
    panel._test_display.assert_called_once()

@pytest.mark.asyncio
async def test_call_graph_panel():
    """Test the call graph panel."""
    panel = CallGraphPanel()
    
    # Use the test method to set a mock tree
    mock_tree = AsyncMock()
    mock_tree.add = MagicMock()
    mock_tree.refresh = MagicMock()
    panel._set_tree_for_test(mock_tree)
    
    # Test adding a call
    call = CallEvent("test_func", "test.py", 10, {"arg1": "value1"}, call_id=1)
    await panel.add_call(call)
    
    # Should have created a tree node
    assert 1 in panel.call_nodes
    mock_tree.add.assert_called_once()
    
    # Test adding a return
    mock_node = MagicMock()
    mock_node.label = "Test label"
    panel.call_nodes[1] = mock_node
    ret = ReturnEvent("test_func", "42", call_id=1)
    await panel.add_return(ret)
    
    # Should have updated the node
    assert mock_node.label == "Test label -> 42"  # Changed arrow to match the test
    mock_tree.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_exception_panel():
    """Test the exception panel."""
    panel = ExceptionPanel()
    
    # Test initial state
    assert len(panel.exceptions) == 0
    
    # Create a mock update method to avoid rendering issues in tests
    panel.update = AsyncMock()  # Use update instead of update_render_str
    
    # Test adding an exception
    exc = ExceptionEvent("ValueError", "Test exception", ["Traceback line 1"], 0)
    await panel.add_exception(exc)
    
    assert len(panel.exceptions) == 1
    panel.update.assert_called_once()
    
    # Test clearing
    panel.update.reset_mock()
    await panel.clear()
    assert len(panel.exceptions) == 0
    panel.update.assert_called_once()
