"""Type definitions for UI components."""

from typing import TypeVar, Union, Any

# Rich renderable type
RenderableType = Union[str, Any]

# Generic widget type
WidgetType = TypeVar("WidgetType")

# Callback type
CallbackType = Callable[..., Any]
