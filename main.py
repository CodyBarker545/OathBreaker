import sys
from pathlib import Path

import simplepbr
from panda3d.core import Filename
from ursina import Ursina, Entity, Text, AmbientLight, DirectionalLight, Vec3, camera, color, raycast, window

from engine.battlefield_view import BattlefieldView
from engine.camera import setup_battlefield_camera
from engine.assassin_view import AssassinView


BOARD_SIZE = 24


def main():
    smoke_test = '--smoke-test' in sys.argv
    app = Ursina(window_type='offscreen' if smoke_test else 'onscreen')

    window.title = "Oathbreakers — Battlefield Prototype"
    window.color = color.rgb32(25, 28, 34)
    # Offscreen buffers do not emit the window-resize event that sizes the HUD.
    camera.ui_lens.setFilmSize(20 * window.aspect_ratio, 20)

    Text(
        text="OATHBREAKERS | Battlefield Prototype",
        position=(-0.85, 0.46),
        scale=1.2,
    )

    coordinate_text = Text(
        text="Click either character, then a tile. WASD: camera | Wheel: zoom",
        position=(-0.85, 0.40),
        scale=1,
    )

    selected_unit = None
    units = []

    def handle_tile_selected(grid_position):
        if selected_unit is None:
            coordinate_text.text = "Click a character to select him first."
        elif any(unit.moving for unit in units):
            coordinate_text.text = "Walking... choose another destination after arrival."
        elif selected_unit.move_to(grid_position, blocked={u.grid_position for u in units if u is not selected_unit}):
            coordinate_text.text = f"{selected_unit.display_name}: walking to {grid_position}"
        else:
            coordinate_text.text = "Choose a different, unoccupied tile on the board."

    def select_unit(unit):
        nonlocal selected_unit
        selected_unit = unit
        for candidate in units:
            candidate.set_selected(candidate is unit)
        coordinate_text.text = f"{unit.display_name} selected. Click a destination tile. Right-click: deselect"

    def handle_arrival(unit, grid_position):
        coordinate_text.text = (
            f"{unit.display_name} at {grid_position}. Click a destination for the selected character."
            if selected_unit is not None else "Click a character to select him."
        )

    battlefield = BattlefieldView(
        board_size=BOARD_SIZE,
        on_tile_selected=handle_tile_selected,
    )

    camera_controller = setup_battlefield_camera()

    AmbientLight(color=color.rgba(.45, .45, .5, 1))
    sunlight = DirectionalLight(color=color.rgba(.95, .9, .8, 1))
    sunlight.look_at((1, -2, 1))
    # The GLB includes PBR colour, roughness and normal maps.
    pipeline = simplepbr.init(enable_shadows=False, use_normal_maps=True)
    assassin = AssassinView(
        battlefield, (BOARD_SIZE // 2, BOARD_SIZE // 2),
        on_selected=select_unit, on_arrived=handle_arrival,
    )
    assassin.rotation_y = 135
    ashveil = AssassinView(
        battlefield, (BOARD_SIZE // 2 + 2, BOARD_SIZE // 2),
        on_selected=select_unit, on_arrived=handle_arrival,
        model_path=Path(__file__).resolve().parent / 'assets' / 'characters' / 'ashveil' / 'ashveil.glb',
        display_name='Ashveil', marker_color=color.rgba(.9, .65, .22, .5),
    )
    ashveil.rotation_y = 135
    units.extend([assassin, ashveil])

    class SelectionControls(Entity):
        def input(self, key):
            nonlocal selected_unit
            if key in ('right mouse down', 'escape'):
                for unit in units:
                    unit.set_selected(False)
                selected_unit = None
                coordinate_text.text = "Click a character to select him."

    selection_controls = SelectionControls()

    if smoke_test:
        # Exercise the same selection and destination handlers as mouse input.
        handle_tile_selected((10, 10))
        assert not any(u.moving for u in units), 'Unselected unit moved'
        for unit in units:
            start = unit.grid_position
            lower, upper = unit.actor.getTightBounds()
            assert upper.y - lower.y > 1, 'Character is not standing upright'
            select_unit(unit)
            assert sum(u.selected for u in units) == 1
            other = next(u for u in units if u is not unit)
            other_start = other.grid_position
            handle_tile_selected(other_start)
            assert not unit.moving, 'Occupied destination accepted'
            destination = (start[0], start[1] + 2)
            handle_tile_selected(destination)
            assert unit.moving and unit.animation == 'Walk'
            assert other_start not in unit.path
            for _ in range(240):
                unit.advance(1 / 60)
            assert unit.grid_position == destination and not unit.moving
            assert unit.animation == 'Idle'
            assert other.grid_position == other_start, 'Unselected character moved'
        assert all(t.path_state is None for t in battlefield.tiles.values())
        for _ in range(8):
            app.taskMgr.step()
        for unit in units:
            hit = raycast(unit.position + Vec3(0, 3, 0), Vec3(0, -1, 0), distance=4)
            assert hit.entity == unit, 'Character cannot be picked through its collider'
        screenshot = Path(__file__).resolve().parent / 'artifacts' / 'characters_on_map.png'
        screenshot.parent.mkdir(exist_ok=True)
        assert app.win.getScreenshot().write(Filename.fromOsSpecific(str(screenshot)))
        print(f'TWO-CHARACTER SMOKE TEST PASSED: independent selection, movement, occupancy, colliders; screenshot: {screenshot}')
        app.destroy()
        return

    app.run()


if __name__ == "__main__":
    main()
