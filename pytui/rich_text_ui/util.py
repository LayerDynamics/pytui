import os
import shutil
from typing import Tuple


def get_terminal_size() -> Tuple[int, int]:
    """Get terminal size."""
    try:
        columns, rows = shutil.get_terminal_size()
        return max(columns, 20), max(rows, 10)
    except:
        return 80, 24


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    import re

    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def truncate(text: str, width: int, suffix="...") -> str:
    """Truncate text to width."""
    if len(text) <= width:
        return text
    return text[: width - len(suffix)] + suffix
