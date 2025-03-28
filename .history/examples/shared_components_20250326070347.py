"""Shared UI components for pytui examples."""

from pytui.rich_text_ui.application import Application
from pytui.rich_text_ui.widget import Widget
from pytui.rich_text_ui.static import Static
from pytui.rich_text_ui.container import Container


class App(Application):
    """Application wrapper component."""
    
    def set_root(self, element):
        """Set the root element of the application."""
        self.view = element


class Button(Widget):
    """Button component for user interaction."""
    
    def __init__(self, label="Button", on_click=None):
        """Initialize button with label and click handler."""
        super().__init__()
        self.label = label
        self.on_click = on_click
    
    def render(self):
        """Render the button."""
        return f"[{self.label}]"


class Label(Static):
    """Label component for displaying text."""
    
    def __init__(self, text="", color=None):
        """Initialize label with text and color."""
        super().__init__(text)
        self.color = color
        self.style = color if color else ""
    
    def set_text(self, text):
        """Update the label's text."""
        self.update(text)
    
    def set_align(self, align):
        """Set text alignment."""
        self.justify = align
    
    def set_color(self, color):
        """Set text color."""
        self.style = f"{color}"


class TextInput(Widget):
    """Text input component for user input."""
    
    def __init__(self, value="", width=20, placeholder=""):
        """Initialize text input with value and properties."""
        super().__init__()
        self.value = value
        self.width = width
        self.placeholder = placeholder
    
    def get_value(self):
        """Get current input value."""
        return self.value
    
    def set_value(self, value):
        """Set input value."""
        self.value = value
    
    def render(self):
        """Render the text input."""
        display_value = self.value if self.value else self.placeholder
        return f"[{display_value}]"


class VBox(Container):
    """Vertical box container."""
    
    def __init__(self):
        """Initialize vertical box."""
        super().__init__()
        self.layout = "vertical"
    
    def add(self, widget):
        """Add a widget to the container."""
        return self.mount(widget)
    
    def set_align(self, align):
        """Set alignment for all children."""
        for child in self.children:
            if hasattr(child, 'set_align'):
                child.set_align(align)


class HBox(Container):
    """Horizontal box container."""
    
    def __init__(self):
        """Initialize horizontal box."""
        super().__init__()
        self.layout = "horizontal"
    
    def add(self, widget):
        """Add a widget to the container."""
        return self.mount(widget)


class Table(Widget):
    """Table component for displaying tabular data."""
    
    def __init__(self, headers=None):
        """Initialize table with headers."""
        super().__init__()
        self.headers = headers or []
        self.rows = []
    
    def add_row(self, row):
        """Add a row to the table."""
        self.rows.append(row)
    
    def render(self):
        """Render the table."""
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
    """Modal dialog component."""
    
    def __init__(self, title="Modal"):
        """Initialize modal with title."""
        super().__init__()
        self.title = title
        self.visible = False
    
    def show(self):
        """Show the modal."""
        self.visible = True
    
    def hide(self):
        """Hide the modal."""
        self.visible = False
    
    def render(self):
        """Render the modal."""
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
    """Tab view component for multiple panels."""
    
    def __init__(self):
        """Initialize tab view."""
        super().__init__()
        self.tabs = []
        self.active_tab = 0
    
    def add_tab(self, title, content):
        """Add a new tab."""
        self.tabs.append({"title": title, "content": content})
    
    def next_tab(self):
        """Switch to next tab."""
        self.active_tab = (self.active_tab + 1) % len(self.tabs)
    
    def prev_tab(self):
        """Switch to previous tab."""
        self.active_tab = (self.active_tab - 1) % len(self.tabs)
    
    def render(self):
        """Render the tab view."""
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
