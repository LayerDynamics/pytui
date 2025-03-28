import asyncio
from typing import Dict, Any

class StyleManager:
    """Manages widget styles."""

    def __init__(self, widget):
        """Initialize style manager.

        Args:
            widget: Widget to manage styles for
        """
        self.widget = widget
        self._styles = {}

    def __getitem__(self, key):
        """Get a style property.

        Args:
            key: Property name

        Returns:
            Property value
        """
        return self._styles.get(key)

    def __setitem__(self, key, value):
        """Set a style property.

        Args:
            key: Property name
            value: Property value
        """
        self._styles[key] = value

    def get(self, key, default=None):
        """Get a style property with default.

        Args:
            key: Property name
            default: Default value

        Returns:
            Property value or default
        """
        return self._styles.get(key, default)

    @staticmethod
    def _linear(t):
        return t

    @staticmethod
    def _ease_in(t):
        return t * t

    @staticmethod
    def _ease_out(t):
        return 1 - (1 - t) * (1 - t)

    async def animate(self, property_name, target_value, duration=0.3, easing="linear"):
        """Animate a style property change.

        Args:
            property_name: Property to animate
            target_value: Target value
            duration: Animation duration in seconds (must be positive)
            easing: Easing function ('linear', 'ease-in', 'ease-out')

        Examples:
            await widget.styles.animate('opacity', 0.5, duration=1.0)
            await widget.styles.animate('width', 100, easing='ease-in')
        """
        duration = max(0.0, float(duration))
        if easing not in {"linear", "ease-in", "ease-out"}:
            easing = "linear"

        try:
            start = float(self._styles.get(property_name, 0))
            target = float(target_value)
            frame_count = int(duration * 60)

            if frame_count < 1:
                self._styles[property_name] = target
                await self.widget.refresh()
                return

            easing_map = {
                "linear": self._linear,
                "ease-in": self._ease_in,
                "ease-out": self._ease_out,
            }
            ease_func = easing_map[easing]
            frame_time = duration / frame_count

            async def update_frame(step):
                progress = step / frame_count
                current = start + (target - start) * ease_func(progress)
                self._styles[property_name] = current
                await self.widget.refresh()
                await asyncio.sleep(frame_time)

            for step in range(frame_count + 1):
                await update_frame(step)

            self._styles[property_name] = target
            await self.widget.refresh()

        except (ValueError, AttributeError):
            self._styles[property_name] = target_value
            await self.widget.refresh()

    async def animate_multiple(
        self, properties: Dict[str, Any], duration=0.3, easing="linear"
    ):
        """Animate multiple style properties simultaneously.
        
        Args:
            properties: Dict of property names and target values
            duration: Animation duration in seconds
            easing: Easing function name
        """
        tasks = [
            self.animate(prop, value, duration, easing)
            for prop, value in properties.items()
        ]
        await asyncio.gather(*tasks)

    def get_computed_style(self) -> Dict[str, Any]:
        """Get computed style including inherited properties."""
        computed = self._styles.copy()
        if self.widget.parent:
            parent_style = self.widget.parent.styles.get_computed_style()
            for key, value in parent_style.items():
                if key not in computed:
                    computed[key] = value
        return computed