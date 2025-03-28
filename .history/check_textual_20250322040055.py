import textual
import inspect

# Check what's in textual.widgets
print("=== textual.widgets contents ===")
import textual.widgets as widgets

for name in dir(widgets):
    if not name.startswith("_"):
        print(f"textual.widgets.{name}")

# Check available submodules
print("\n=== textual widget modules ===")
for name in dir(textual):
    if not name.startswith("_") and name != "widgets":
        try:
            module = getattr(textual, name)
            if hasattr(module, "Tree"):
                print(f"Found Tree in textual.{name}")
        except (ImportError, AttributeError):
            pass
