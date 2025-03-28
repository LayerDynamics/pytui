import sys

class Style:
    """Style representation for text formatting."""

    COLORS = {
        # Basic colors
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        # Bright colors
        "bright_black": "\033[90m",
        "bright_red": "\033[91m",
        "bright_green": "\033[92m",
        "bright_yellow": "\033[93m",
        "bright_blue": "\033[94m",
        "bright_magenta": "\033[95m",
        "bright_cyan": "\033[96m",
        "bright_white": "\033[97m",
        # Others
        "reset": "\033[0m",
        "dim": "\033[2m",
        "bold": "\033[1m",
        "italic": "\033[3m",
        "underline": "\033[4m",
        "blink": "\033[5m",
        "reverse": "\033[7m",
    }

    # Check if terminal supports color
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        SUPPORTS_COLOR = True
    else:
        SUPPORTS_COLOR = False

    def __init__(self, style_string=""):
        """Initialize style from string.

        Args:
            style_string: Space-separated style components (e.g., "bold red")
        """
        self.components = set()
        if style_string:
            for component in style_string.split():
                self.components.add(component)

    def __add__(self, other):
        """Combine two styles."""
        if not other:
            return self
        result = Style()
        result.components = self.components.copy()
        if isinstance(other, Style):
            result.components.update(other.components)
        elif isinstance(other, str):
            result.components.update(Style(other).components)
        return result

    def __str__(self):
        """Return the string representation."""
        return " ".join(self.components)

    def apply(self, text):
        """Apply this style to text."""
        if not self.SUPPORTS_COLOR or not self.components:
            return text

        codes = []
        for comp in self.components:
            if comp in self.COLORS:
                codes.append(self.COLORS[comp])

        if not codes:
            return text

        return f"{''.join(codes)}{text}{self.COLORS['reset']}"