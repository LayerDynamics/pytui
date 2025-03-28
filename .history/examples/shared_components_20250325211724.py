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

class Table(Widget):
    def __init__(self, headers=None):
        super().__init__()
        self.headers = headers or []
        self.rows = []
        
    def add_row(self, row):
        self.rows.append(row)
        
    def render(self):
        if not self.rows:
            return "[Empty Table]"
        
        # Calculate column widths
        col_widths = [len(h) for h in self.headers]
        for row in self.rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
                
        # Render table
        lines = []
        # Headers
        header = "│ " + " │ ".join(h.ljust(w) for h, w in zip(self.headers, col_widths)) + " │"
        lines.append("┌" + "─" * (len(header)-2) + "┐")
        lines.append(header)
        lines.append("├" + "─" * (len(header)-2) + "┤")
        
        # Rows
        for row in self.rows:
            line = "│ " + " │ ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths)) + " │"
            lines.append(line)
        lines.append("└" + "─" * (len(header)-2) + "┘")
        
        return "\n".join(lines)

class Modal(Container):
    def __init__(self, title="Modal"):
        super().__init__()
        self.title = title
        self.visible = False
        
    def show(self):
        self.visible = True
        
    def hide(self):
        self.visible = False
        
    def render(self):
        if not self.visible:
            return ""
            
        width = 50
        content = super().render()
        lines = [
            "┌" + "─" * (width-2) + "┐",
            "│" + self.title.center(width-2) + "│",
            "├" + "─" * (width-2) + "┤",
            content,
            "└" + "─" * (width-2) + "┘"
        ]
        return "\n".join(lines)

class TabView(Container):
    def __init__(self):
        super().__init__()
        self.tabs = []
        self.active_tab = 0
        
    def add_tab(self, title, content):
        self.tabs.append({"title": title, "content": content})
        
    def next_tab(self):
        self.active_tab = (self.active_tab + 1) % len(self.tabs)
        
    def prev_tab(self):
        self.active_tab = (self.active_tab - 1) % len(self.tabs)
        
    def render(self):
        if not self.tabs:
            return "[No Tabs]"
            
        # Render tab headers
        headers = []
        for i, tab in enumerate(self.tabs):
            if i == self.active_tab:
                headers.append(f"[{tab['title']}]")
            else:
                headers.append(f" {tab['title']} ")
        
        header = " ".join(headers)
        content = self.tabs[self.active_tab]['content'].render()
        
        return f"{header}\n{'─' * len(header)}\n{content}"
