from ursina import Entity, color


class TileView(Entity):
    def __init__(self, grid_x, grid_z, position, on_select):
        # Normalized RGB values: each component is between 0 and 1.
        if (grid_x + grid_z) % 2 == 0:
            base_color = color.rgba(0.41, 0.45, 0.41, 1)
        else:
            base_color = color.rgba(0.33, 0.37, 0.33, 1)

        super().__init__(
            model="cube",
            position=position,
            scale=(0.96, 0.15, 0.96),
            color=base_color,
            collider="box",
        )

        self.grid_position = (grid_x, grid_z)
        self.base_color = base_color
        self.on_select = on_select

    def on_mouse_enter(self):
        self.color = color.azure

    def on_mouse_exit(self):
        self.color = self.base_color

    def input(self, key):
        if self.hovered and key == "left mouse down":
            self.on_select(self.grid_position)