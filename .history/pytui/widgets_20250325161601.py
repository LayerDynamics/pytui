"""Widget classes for PyTUI."""

class Widget:
    """Base class for all widgets."""
    
    def __init__(self):
        self.parent = None
        self.align = "left"
    
    def set_align(self, align):
        """Set the alignment of this widget.
        
        Args:
            align: One of "left", "center", "right"
        """
        self.align = align
    
    def render(self):
        """Render the widget to the screen."""
        pass


class Label(Widget):
    """A simple text label widget."""
    
    def __init__(self, text="", color=None):
        """Initialize a label.
        
        Args:
            text: The text content of the label
            color: The color of the text
        """
        super().__init__()
        self.text = text
        self.color = color
    
    def set_text(self, text):
        """Set the text of this label.
        
        Args:
            text: The new text content
        """
        self.text = text
    
    def set_color(self, color):
        """Set the color of this label.
        
        Args:
            color: The new color
        """
        self.color = color
    
    def render(self):
        """Render the label to the screen."""
        print(f"Label: {self.text} (align: {self.align}, color: {self.color})")


class Button(Widget):
    """A clickable button widget."""
    
    def __init__(self, label="Button", on_click=None):
        """Initialize a button.
        
        Args:
            label: The text on the button
            on_click: Callback function when button is clicked
        """
        super().__init__()
        self.label = label
        self.on_click = on_click
    
    def render(self):
        """Render the button to the screen."""
        print(f"Button: {self.label} (align: {self.align})")


class TextInput(Widget):
    """A text input field widget."""
    
    def __init__(self, value="", width=20):
        """Initialize a text input.
        
        Args:
            value: Initial value
            width: Width in characters
        """
        super().__init__()
        self.value = value
        self.width = width
    
    def get_value(self):
        """Get the current value of the input.
        
        Returns:
            The current text value
        """
        return self.value
    
    def set_value(self, value):
        """Set the value of this input.
        
        Args:
            value: The new text value
        """
        self.value = value
    
    def render(self):
        """Render the text input to the screen."""
        print(f"TextInput: {self.value} (width: {self.width}, align: {self.align})")
