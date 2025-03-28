"""Advanced example demonstrating tabs, modals, and async updates."""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from examples.shared_components import (
    App, Button, Label, TextInput, VBox, HBox,
    Modal, TabView, Table
)
from pytui.rich_text_ui.colors import Color

def main():
    """Create a tabbed interface with modals."""
    app = App(title="PyTUI Advanced Demo")
    main_container = VBox()
    
    # Create tab view
    tab_view = TabView()
    
    # Data Entry Tab
    data_tab = VBox()
    data_form = HBox()
    data_input = TextInput(placeholder="Enter data")
    data_form.add(Label("Data: "))
    data_form.add(data_input)
    data_tab.add(data_form)
    
    # Create modal for confirmations
    confirm_modal = Modal("Confirm Action")
    confirm_label = Label("Are you sure?")
    confirm_modal.add(confirm_label)
    
    modal_buttons = HBox()
    modal_buttons.add(Button("Yes", lambda: confirm_modal.hide()))
    modal_buttons.add(Button("No", lambda: confirm_modal.hide()))
    confirm_modal.add(modal_buttons)
    
    # Add tabs
    tab_view.add_tab("Data Entry", data_tab)
    tab_view.add_tab("Analytics", Table(headers=["Metric", "Value"]))
    tab_view.add_tab("Settings", Label("Settings Panel"))
    
    # Add controls
    controls = HBox()
    controls.add(Button("Next Tab", lambda: tab_view.next_tab()))
    controls.add(Button("Show Modal", lambda: confirm_modal.show()))
    controls.add(Button("Exit", lambda: app.exit()))
    
    main_container.add(tab_view)
    main_container.add(controls)
    main_container.add(confirm_modal)
    
    app.set_root(main_container)
    app.run()

if __name__ == "__main__":
    asyncio.run(main())
