"""Style classes for text formatting."""

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

    SUPPORTS_COLOR: bool = bool(hasattr(sys.stdout, 'isatty') and sys.stdout.isatty())

    def __init__(self, style_string: str = "") -> None:
        """Initialize style from string."""
        self.components: set[str] = set(style_string.split() if style_string else [])

    def __add__(self, other: 'Style') -> 'Style':
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

    def __str__(self) -> str:
        """Return the string representation."""
        return " ".join(self.components)

    def apply(self, text: str) -> str:
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
