"""Test fixtures and configuration for pytui tests."""

import pytest
import asyncio

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

# Configure default event loop scope
def pytest_configure(config):
    """Configure pytest markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (skipped by default)"
    )
    # Set default event loop scope to function
    config.addinivalue_line(
        "asyncio_default_fixture_loop_scope", "function"
    )
    # Add asyncio marker
    config.addinivalue_line(
        "markers", "asyncio: mark test to run using asyncio"
    )

@pytest.fixture(scope="function")
async def event_loop():
    """Create an event loop for each test case."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

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
