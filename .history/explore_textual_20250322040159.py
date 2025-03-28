"""Script to explore Textual package structure."""

import importlib
import inspect
import textual
import sys


def print_module_contents(module_name, indent=0):
    """Print all contents of a module, recursively exploring submodules."""
    try:
        module = importlib.import_module(module_name)
        print(f"{' ' * indent}{module_name}")

        # Look for widgets we need
        for name in dir(module):
            if name in ["Static", "ScrollView", "Tree", "App", "Container"]:
                obj = getattr(module, name)
                if inspect.isclass(obj):
                    print(f"{' ' * (indent+2)}✓ FOUND: {name}")

        # Explore submodules
        if hasattr(module, "__path__"):
            for _, name, is_pkg in importlib.iter_modules(module.__path__):
                if not name.startswith("_"):  # Skip private modules
                    full_name = f"{module_name}.{name}"
                    print_module_contents(full_name, indent + 2)
    except (ImportError, AttributeError) as e:
        print(f"{' ' * indent}Error importing {module_name}: {e}")


print("=== Exploring Textual Package Structure ===")
print_module_contents("textual")

print("\n=== Direct imports test ===")
# Test direct imports to see what's available
try:
    from textual.app import App

    print("✓ from textual.app import App")
except ImportError:
    print("✗ from textual.app import App")

try:
    from textual.widgets import Static

    print("✓ from textual.widgets import Static")
except ImportError:
    print("✗ from textual.widgets import Static")

try:
    from textual.containers import Container

    print("✓ from textual.containers import Container")
except ImportError:
    print("✗ from textual.containers import Container")

try:
    from textual.scroll_view import ScrollView

    print("✓ from textual.scroll_view import ScrollView")
except ImportError:
    print("✗ from textual.scroll_view import ScrollView")

try:
    from textual.widgets.tree import Tree

    print("✓ from textual.widgets.tree import Tree")
except ImportError:
    print("✗ from textual.widgets.tree import Tree")
