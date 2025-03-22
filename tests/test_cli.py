"""Tests for CLI functionality."""

import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from pytui.cli import cli

@pytest.fixture
def sample_script():
    """Create a temporary Python script for testing."""
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
        f.write('print("Hello from test script")')
    yield f.name
    # Clean up
    os.unlink(f.name)

def test_cli_help():
    """Test that CLI help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "Python Terminal UI" in result.output

def test_run_command_help():
    """Test the run command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ['run', '--help'])
    assert result.exit_code == 0
    assert "Run a Python script through the TUI" in result.output

def test_run_missing_script():
    """Test handling of missing script file."""
    runner = CliRunner()
    result = runner.invoke(cli, ['run', 'nonexistent.py'])
    assert result.exit_code != 0
    assert "Error" in result.output

@patch('pytui.cli.ScriptExecutor')
@patch('pytui.cli.PyTUIApp')
def test_run_script(mock_app_class, mock_executor_class, sample_script):
    """Test running a script through the CLI."""
    # Set up mocks
    mock_app = MagicMock()
    mock_app_class.return_value = mock_app
    mock_executor = MagicMock()
    mock_executor_class.return_value = mock_executor
    
    # Run the command
    runner = CliRunner()
    result = runner.invoke(cli, ['run', sample_script, 'arg1', 'arg2'])
    
    # Check result
    assert result.exit_code == 0
    
    # Verify executor was created with correct args
    mock_executor_class.assert_called_once_with(sample_script, ['arg1', 'arg2'])
    
    # Verify app was set up and run
    mock_app.set_executor.assert_called_once_with(mock_executor)
    mock_app.run.assert_called_once()
