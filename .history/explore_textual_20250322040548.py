"""Script to explore Textual package structure with better compatibility."""

import sys
import importlib

def check_module_for_classes(module_name, target_classes):
    """Check if a module contains any of the target classes."""
    try:
        module = importlib.import_module(module_name)
        found = []
        
        for name in dir(module):
            if name in target_classes:
                found.append(f"{module_name}.{name}")
                print(f"✓ Found {name} in {module_name}")
        
        return found
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {e}")
        return []

# Define modules to check and target classes
modules = [
    'textual',
    'textual.app',
    'textual.widgets',
    'textual.containers',
    'textual.widget',  # Some versions use singular "widget"
    'textual.widgets.tree',
    'textual.widgets.tree_control',
    'textual.tree'
]

target_classes = ['Tree', 'TreeControl', 'TreeView', 'ScrollView', 'Static', 'Container', 'App']

# Check modules for target classes
print("=== Searching for needed widgets ===")
for module in modules:
    check_module_for_classes(module, target_classes)

# Try some common import patterns for tree widgets
print("\n=== Trying tree widget import patterns ===")
tree_imports = [
    "from textual.widgets import Tree",
    "from textual.tree import Tree",
    "from textual import Tree",
    "from textual.widgets import TreeControl",
    "from textual.widgets import TreeView"
]

for import_stmt in tree_imports:
    try:
        exec(import_stmt)
        print(f"✓ {import_stmt}")
    except ImportError:
        print(f"✗ {import_stmt}")
