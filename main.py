from ursina import Ursina, Text, color, window

from engine.battlefield_view import BattlefieldView
from engine.camera import setup_battlefield_camera


BOARD_SIZE = 24


def main():
    app = Ursina()

    window.title = "Oathbreakers — Battlefield Prototype"
    window.color = color.rgb32(25, 28, 34)

    Text(
        text="OATHBREAKERS | Battlefield Prototype",
        position=(-0.85, 0.46),
        scale=1.2,
    )

    coordinate_text = Text(
        text="Click a tile. Use WASD to move the camera.",
        position=(-0.85, 0.40),
        scale=1,
    )

    def handle_tile_selected(grid_position):
        coordinate_text.text = f"Selected tile: {grid_position}"
        print(f"Selected tile: {grid_position}")

    battlefield = BattlefieldView(
        board_size=BOARD_SIZE,
        on_tile_selected=handle_tile_selected,
    )

    camera_controller = setup_battlefield_camera()

    app.run()


if __name__ == "__main__":
    main()