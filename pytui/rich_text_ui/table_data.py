class TableData:
    """Data container for table content."""

    def __init__(self):
        self.columns = []
        self.column_styles = []
        self.column_widths = []
        self.rows = []
        self.row_styles = []

    def clear(self):
        """Clear all table data."""
        self.columns.clear()
        self.column_styles.clear()
        self.column_widths.clear()
        self.rows.clear()
        self.row_styles.clear()

    def get_column_count(self) -> int:
        """Get the number of columns in the table.

        Returns:
            int: Number of columns
        """
        return len(self.columns)
