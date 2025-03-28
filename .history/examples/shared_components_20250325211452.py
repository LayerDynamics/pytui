"""Shared UI components for pytui examples."""

from pytui.rich_text_ui.application import Application
from pytui.rich_text_ui.widget import Widget
from pytui.rich_text_ui.text import Text
from pytui.rich_text_ui.static import Static
from pytui.rich_text_ui.container import Container
from pytui.rich_text_ui.colors import Color
from pytui.rich_text_ui.list import List as UIList
from pytui.rich_text_ui.progress import Progress

class App(Application):
    def set_root(self, element):
        self.view = element

class Button(Widget):
    def __init__(self, label="Button", on_click=None):
        super().__init__()
        self.label = label
        self.on_click = on_click
    
    def render(self):
        return f"[{self.label}]"

class Label(Static):
    def __init__(self, text="", color=None):
        super().__init__(text)
        self.color = color
        self.style = color if color else ""
    
    def set_text(self, text):
        self.update(text)
        
    def set_align(self, align):
        self.justify = align
        
    def set_color(self, color):
        self.style = f"{color}"

class TextInput(Widget):
    def __init__(self, value="", width=20, placeholder=""):
        super().__init__()
        self.value = value
        self.width = width
        self.placeholder = placeholder
        
    def get_value(self):
        return self.value
        
    def set_value(self, value):
        self.value = value
        
    def render(self):
        display_value = self.value if self.value else self.placeholder
        return f"[{display_value}]"

class VBox(Container):
    def __init__(self):
        super().__init__()
        self.layout = "vertical"
        
    def add(self, widget):
        return self.mount(widget)
        
    def set_align(self, align):
        for child in self.children:
            if hasattr(child, 'set_align'):
                child.set_align(align)

class HBox(Container):
    def __init__(self):
        super().__init__()
        self.layout = "horizontal"
        
    def add(self, widget):
        return self.mount(widget)
