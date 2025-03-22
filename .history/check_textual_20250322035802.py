import textual
import inspect
for name in dir(textual):
    print(f"textual.{name}")

# And to find ScrollView specifically
import textual
for module_name in dir(textual):
    module = getattr(textual, module_name)
    if hasattr(module, "ScrollView"):
        print(f"Found ScrollView in textual.{module_name}")