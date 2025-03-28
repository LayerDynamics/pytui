from .widget import Widget
from .style import Style
from .box import Box
from .panel import Panel
from .table_data import TableData

class Table(Widget):
    """Table widget for displaying tabular data."""

    def __init__(self, title=None, box=None, show_header=True, show_footer=False):
        """Initialize table.

        Args:
            title: Table title
            box: Box style
            show_header: Whether to show column headers
            show_footer: Whether to show footer
        """
        super().__init__()
        self.title = title
        self.box = box or Box.get_box_style("rounded")
        self.show_header = show_header
        self.show_footer = show_footer
        self._data = TableData()

    def add_column(self, title, **kwargs):
        """Add a column to the table."""
        self._data.columns.append(title)
        self._data.column_styles.append(kwargs.get("style"))
        width = kwargs.get("width", 0) or len(title)
        self._data.column_widths.append(width)
        return self

    def add_row(self, *values, style=None):
        """Add a row to the table."""
        row = []
        for i, value in enumerate(values):
            value_str = str(value)
            if i < len(self._data.column_widths):
                self._data.column_widths[i] = max(
                    self._data.column_widths[i], len(value_str)
                )
            row.append(value_str)

        self._data.rows.append(row)
        self._data.row_styles.append(style)
        return self

    def _render_header(self, box_chars, separator):
        """Render table header."""
        lines = []
        if self.show_header:
            header = box_chars["v"] + "  "
            for i, col in enumerate(self._data.columns):
                width = self._data.column_widths[i]
                header += f" {col:<{width}} " + box_chars["v"]
            lines.extend(
                [
                    box_chars["tl"] + separator + box_chars["tr"],
                    header,
                    box_chars["v"] + box_chars["h"] * len(separator) + box_chars["v"],
                ]
            )
        return lines

    def _render_rows(self, box_chars, num_columns):
        """Render table rows."""
        lines = []
        for i, row in enumerate(self._data.rows):
            row_text = box_chars["v"] + "  "
            for j, cell in enumerate(row[:num_columns]):
                width = self._data.column_widths[j]
                row_text += f" {str(cell):<{width}} " + box_chars["v"]

            if self._data.row_styles[i]:
                row_text = Style(self._data.row_styles[i]).apply(row_text)
            lines.append(row_text)
        return lines

    def render(self):
        """Render the table."""
        if not self._data.columns or not self._data.rows:
            return Panel(
                f"Table: {self.title or 'No data'} (no data)", border_style="dim"
            ).render()

        # Normalize data
        num_columns = len(self._data.columns)
        for i, row in enumerate(self._data.rows):
            if len(row) < num_columns:
                self._data.rows[i] = row + [""] * (num_columns - len(row))

        # Setup box characters and separator
        box_chars = {
            k: self.box.get(k, v)
            for k, v in {
                "tl": "┌",
                "tr": "┐",
                "bl": "└",
                "br": "┘",
                "h": "─",
                "v": "│",
            }.items()
        }

        separator = box_chars["h"] * 3
        for width in self._data.column_widths:
            separator += box_chars["h"] * (width + 2) + box_chars["h"] * 3

        # Build table
        lines = []
        if self.title:
            lines.extend([f" {self.title} ", ""])

        lines.extend(self._render_header(box_chars, separator))
        lines.extend(self._render_rows(box_chars, num_columns))

        if self.show_footer:
            lines.extend(self._render_footer(box_chars, separator))

        # Add bottom border
        lines.append(
            box_chars["bl"] + box_chars["h"] * len(separator) + box_chars["br"]
        )

        return "\n".join(lines)

    def _render_footer(self, box_chars, separator):
        """Render table footer."""
        lines = [box_chars["v"] + box_chars["h"] * len(separator) + box_chars["v"]]
        footer = box_chars["v"] + "  "
        for i, width in enumerate(self._data.column_widths):
            text = "Total" if i == 0 else ""
            footer += f" {text:<{width}} " + box_chars["v"]
        lines.append(footer)
        return lines