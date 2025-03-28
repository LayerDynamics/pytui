from .widget import Widget
from .style import Style
from .box import Box


class Panel(Widget):
    """Panel with a border and optional title."""

    def __init__(self, content="", *, title="", border_style=None, box=None):
        """Initialize panel.

        Args:
            content: Panel content
            title: Panel title
            border_style: Style for the border
            box: Box drawing characters
        """
        super().__init__()
        self.content = content
        self.title = title
        self.border_style = (
            Style(border_style) if isinstance(border_style, str) else border_style
        )
        self.box = box or Box.get_box_style("rounded")
        self.padding = (1, 1)  # (horizontal, vertical)

    def _create_borders(self, width):
        """Create border lines for the panel."""
        box_chars = {
            "tl": self.box.get("tl", "┌"),
            "tr": self.box.get("tr", "┐"),
            "bl": self.box.get("bl", "└"),
            "br": self.box.get("br", "┘"),
            "h": self.box.get("h", "─"),
            "v": self.box.get("v", "│"),
        }

        title_str = ""
        if self.title:
            max_title_width = width - 4
            title = self.title[:max_title_width]
            title_str = f" {title} "

        # Create borders
        if title_str:
            padding = width - len(title_str) - 2
            left_pad = padding // 2
            right_pad = padding - left_pad
            top = (
                box_chars["tl"]
                + box_chars["h"] * left_pad
                + title_str
                + box_chars["h"] * right_pad
                + box_chars["tr"]
            )
        else:
            top = box_chars["tl"] + box_chars["h"] * (width - 2) + box_chars["tr"]

        bottom = box_chars["bl"] + box_chars["h"] * (width - 2) + box_chars["br"]

        return top, bottom, box_chars["v"]

    def render(self):
        """Render panel with border and content."""
        # Convert content to string
        content_str = (
            self.content.render()
            if hasattr(self.content, "render")
            else str(self.content)
        )
        content_lines = content_str.split("\n")

        # Calculate width
        content_width = max(
            [len(line) for line in content_lines] + [len(self.title)], default=0
        )
        width = content_width + self.padding[0] * 2 + 2

        # Get borders
        top_border, bottom_border, v = self._create_borders(width)
        lines = [top_border]

        # Add padding and content
        empty_line = v + " " * (width - 2) + v
        lines.extend([empty_line] * self.padding[1])

        for line in content_lines:
            padding_width = max(0, width - 2 - len(line) - self.padding[0] * 2)
            padded = line + " " * padding_width
            lines.append(v + " " * self.padding[0] + padded + " " * self.padding[0] + v)

        lines.extend([empty_line] * self.padding[1])
        lines.append(bottom_border)

        # Apply border style
        if self.border_style:
            lines = [
                (
                    self.border_style.apply(line)
                    if i == 0 or i == len(lines) - 1 or line.startswith(v)
                    else line
                )
                for i, line in enumerate(lines)
            ]

        return "\n".join(lines)
