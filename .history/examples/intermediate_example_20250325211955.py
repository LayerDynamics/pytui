"""Intermediate example demonstrating table and data grid features."""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from examples.shared_components import App, Button, Label, TextInput, VBox, HBox, Table
from pytui.rich_text_ui.colors import Color

def main():
    """Table-based data management example."""
    app = App(title="PyTUI Table Demo")
    main_container = VBox()
    
    # Add header
    title = Label("Data Grid Example", Color.CYAN)
    title.set_align("center")
    main_container.add(title)
    
    # Create data table
    data_table = Table(headers=["ID", "Name", "Value", "Timestamp"])
    
    # Add data entry form
    form = HBox()
    name_input = TextInput(placeholder="Enter name")
    value_input = TextInput(placeholder="Enter value")
    form.add(Label("Name: "))
    form.add(name_input)
    form.add(Label("Value: "))
    form.add(value_input)
    
    main_container.add(form)
    
    # Add controls
    def add_row():
        timestamp = datetime.now().strftime("%H:%M:%S")
        row_id = len(data_table.rows) + 1
        data_table.add_row([row_id, name_input.get_value(), value_input.get_value(), timestamp])
        name_input.set_value("")
        value_input.set_value("")
    
    controls = HBox()
    controls.add(Button("Add Row", add_row))
    controls.add(Button("Exit", lambda: app.exit()))
    main_container.add(controls)
    
    # Add table to container
    main_container.add(data_table)
    
    app.set_root(main_container)
    app.run()

if __name__ == "__main__":
    main()
