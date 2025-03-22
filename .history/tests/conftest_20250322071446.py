"""Test fixtures and configuration for pytui tests."""

import pytest
import asyncio
from typing import Generator

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

# Configure markers and options
def pytest_configure(config):
    """Configure pytest markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (skipped by default)"
    )
    # Add asyncio marker
    config.addinivalue_line(
        "markers", "asyncio: mark test to run using asyncio"
    )

# Set the default fixture loop scope via pytestmark
pytestmark = pytest.mark.asyncio(scope="function")

@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create and provide a fresh event loop for each test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop  # Return the loop as a regular value, not an async generator
    loop.close()
    asyncio.set_event_loop(None)

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
