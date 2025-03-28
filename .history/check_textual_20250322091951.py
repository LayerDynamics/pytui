"""Script to check Textual package compatibility and class/widget availability."""

import sys
import importlib
from typing import List, Set


def check_textual_version() -> str:
    """Check installed Textual version."""
    try:
        import textual

        return textual.__version__
    except ImportError:
        return "Not installed"


def find_widget_classes(modules: List[str], target_classes: Set[str]) -> dict:
    """Search for widget classes in Textual modules.

    Args:
        modules: List of module paths to check
        target_classes: Set of class names to look for

    Returns:
        Dict mapping found classes to their module paths
    """
    found_classes = {}

    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            for name in dir(module):
                if name in target_classes:
                    found_classes[name] = f"{module_name}.{name}"
                    print(f"✓ Found {name} in {module_name}")
        except ImportError as e:
            print(f"✗ Failed to import {module_name}: {e}")

    return found_classes


def main():
    """Main entry point."""
    print("=== Checking Textual Installation ===")
    version = check_textual_version()
    print(f"Textual version: {version}")

    modules = [
        "textual",
        "textual.app",
        "textual.widgets",
        "textual.containers",
        "textual.widget",
        "textual.widgets.tree",
        "textual.widgets.tree_control",
        "textual.tree",
    ]

    target_classes = {
        "Tree",
        "TreeControl",
        "TreeView",
        "ScrollView",
        "Static",
        "Container",
        "App",
    }

    print("\n=== Searching for Required Widgets ===")
    found = find_widget_classes(modules, target_classes)

    print("\n=== Summary ===")
    missing = target_classes - set(found.keys())
    if missing:
        print(f"Missing classes: {', '.join(missing)}")
    else:
        print("All required classes found!")

    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
