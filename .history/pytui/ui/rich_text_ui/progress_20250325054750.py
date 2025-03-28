from .widget import Widget
from .style import Style

class ProgressBar(Widget):
    """Progress bar widget."""
    
    def __init__(self, total=100, completed=0, width=40):
        """Initialize progress bar."""
        super().__init__()
        self.total = total
        self.completed = completed
        self.width = width
        self.style = Style("green")
        self.background_style = Style("dim")
        
    def update(self, completed):
        """Update progress value."""
        self.completed = min(max(0, completed), self.total)
        
    def render(self):
        """Render progress bar."""
        ratio = self.completed / self.total
        filled = int(self.width * ratio)
        empty = self.width - filled
        
        bar = "█" * filled + "░" * empty
        percentage = f"{int(ratio * 100)}%"
        
        # Center percentage in bar
        pos = (self.width - len(percentage)) // 2
        bar = (
            self.style.apply(bar[:pos]) +
            Style("bold white").apply(percentage) +
            self.style.apply(bar[pos + len(percentage):])
        )
        
        return bar
