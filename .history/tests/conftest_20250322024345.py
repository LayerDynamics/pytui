"""Test fixtures and configuration for pytui tests."""

import pytest
import asyncio

# Configure pytest to run async tests
@pytest.fixture
def event_loop():
    """Create an event loop for each test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Define pytest markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (skipped by default)"
    )
    # Add asyncio marker
    config.addinivalue_line(
        "markers", "asyncio: mark test to run using asyncio"
    )

# Skip slow tests by default
def pytest_addoption(parser):
    """Add command-line options."""
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="run slow tests"
    )

def pytest_collection_modifyitems(config, items):
    """Skip slow tests unless specifically requested."""
    if config.getoption("--run-slow"):
        # If --run-slow is specified, don't skip slow tests
        return
        
    skip_slow = pytest.mark.skip(reason="use --run-slow to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
