from engine.tile_view import TileView

class BattlefieldView:
    def __init__(self, board_size, on_tile_selected, tile_spacing=1):
        self.tiles = {}

        board_offset = (board_size - 1) / 2

        for grid_x in range(board_size):
            for grid_z in range(board_size):
                position = (
                    (grid_x - board_offset) * tile_spacing,
                    0,
                    (grid_z - board_offset) * tile_spacing,
                )

                self.tiles[(grid_x, grid_z)] = TileView(
                    grid_x=grid_x,
                    grid_z=grid_z,
                    position=position,
                    on_select=on_tile_selected,
                )

    def show_path(self, path):
        for tile in self.tiles.values():
            tile.set_path_state(None)
        for cell in path:
            self.tiles[cell].set_path_state('path')
        if path:
            self.tiles[path[-1]].set_path_state('destination')
