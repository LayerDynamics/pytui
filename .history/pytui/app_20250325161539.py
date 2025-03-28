"""Application module for PyTUI."""

class App:
    """Main application class for PyTUI."""
    
    def __init__(self, title="PyTUI Application"):
        """Initialize the application.
        
        Args:
            title: The title of the application
        """
        self.title = title
        self.root = None
    
    def set_root(self, element):
        """Set the root element of the application.
        
        Args:
            element: The root UI element
        """
        self.root = element
    
    def run(self):
        """Run the application main loop."""
        print(f"Running application: {self.title}")
        if self.root:
            self.root.render()
    
    def exit(self):
        """Exit the application."""
        print("Exiting application")
        # In a real implementation, this would break the main loop
