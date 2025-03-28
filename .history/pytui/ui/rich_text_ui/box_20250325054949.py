class Box:
    """Box drawing characters for borders."""

    _STYLES = {
        "ascii": {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|"},
        "rounded": {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"},
        "square": {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"},
        "double": {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"},
    }

    _STYLES.update({
        "heavy": {
            "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛",
            "h": "━", "v": "┃"
        },
        "dashed": {
            "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
            "h": "┄", "v": "┆"
        },
        "dotted": {
            "tl": ".", "tr": ".", "bl": ".", "br": ".",
            "h": ".", "v": "."
        }
    })

    @staticmethod
    def get_box_style(name="rounded") -> dict:
        """Get a box style by name.

        Args:
            name: Style name (ascii, rounded, square, double)

        Returns:
            Box style dictionary
        """
        return Box._STYLES.get(name.lower(), Box._STYLES["rounded"])

    @staticmethod
    def create_box(width: int, height: int, style="rounded") -> str:
        """Create a box with given dimensions and style.

        Args:
            width: Width of the box
            height: Height of the box
            style: Box style name

        Returns:
            String representation of the box
        """
        box_chars = Box.get_box_style(style)
        lines = []
        lines.append(box_chars["tl"] + box_chars["h"] * (width - 2) + box_chars["tr"])
        for _ in range(height - 2):
            lines.append(box_chars["v"] + " " * (width - 2) + box_chars["v"])
        lines.append(box_chars["bl"] + box_chars["h"] * (width - 2) + box_chars["br"])
        return "\n".join(lines)

    @staticmethod
    def create_header(width: int, style="rounded", text="") -> str:
        """Create a header line with optional text.

        Args:
            width: Width of the header
            style: Box style name
            text: Optional text to include in header

        Returns:
            String representation of the header
        """
        box_chars = Box.get_box_style(style)
        if text:
            text_space = width - 4
            text = text[:text_space] if len(text) > text_space else text
            padding = width - len(text) - 4
            left_pad = padding // 2
            right_pad = padding - left_pad
            return (
                box_chars["tl"]
                + box_chars["h"] * left_pad
                + " "
                + text
                + " "
                + box_chars["h"] * right_pad
                + box_chars["tr"]
            )
        return box_chars["tl"] + box_chars["h"] * (width - 2) + box_chars["tr"]

    @staticmethod
    def create_grid(rows: int, cols: int, style="rounded") -> str:
        """Create a grid with given dimensions.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            style: Box style name
        
        Returns:
            String representation of the grid
        """
        box_chars = Box.get_box_style(style)
        lines = []
        
        # Create top border
        top = box_chars["tl"] + (box_chars["h"] * 3 + box_chars["v"]) * (cols - 1) + box_chars["h"] * 3 + box_chars["tr"]
        lines.append(top)
        
        # Create rows
        for row in range(rows):
            if row > 0:
                # Add horizontal separator
                sep = box_chars["v"] + (box_chars["h"] * 3 + box_chars["v"]) * (cols - 1) + box_chars["h"] * 3 + box_chars["v"]
                lines.append(sep)
            
            # Add content row
            content = box_chars["v"] + ((" " * 3 + box_chars["v"]) * cols)
            lines.append(content)
        
        # Create bottom border
        bottom = box_chars["bl"] + (box_chars["h"] * 3 + box_chars["v"]) * (cols - 1) + box_chars["h"] * 3 + box_chars["br"]
        lines.append(bottom)
        
        return "\n".join(lines)

