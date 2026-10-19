# Level editing

The starting map is **Oathstone Crossing**, authored with Terrain3D and the existing tree, fern and rock assets. It has elevations, a creek, two bridges, opposing character spawns and a claimable central shrine.

1. Open `D:\SoftwareEng\Game\project.godot` using Godot .NET.
2. Open `Scenes/StartingLevel.tscn` to edit terrain and props.
3. Select `Terrain3D` to sculpt hills, smooth banks or paint the configured meadow, stone and earth textures. Its Data Directory is already set.
4. Expand `LevelProps` to move existing trees and rocks. Drag additional GLBs from `Assets/Levels/` under `LevelProps`.
5. Use W to move, E to rotate and R to scale. Save with Ctrl+S.
6. Press F5 to run the main `Battlefield.tscn`, which loads this level and spawns the characters.

When adding an obstacle, select its top-level node under `LevelProps` and add Boolean metadata `blocks_movement = true` in the Inspector. Optional Float metadata `blocking_radius` sets its footprint radius in metres (default 0.58). Props without this metadata are decorative. Existing blocker props already have it. Trees and rocks in this level also have saved surface materials that can be edited on their mesh children; the source GLBs remain unchanged.

`Bridges` holds the flank crossings, `SpawnPoints` holds the two start markers, and `Objective` contains the shrine's ring and beacon. Keep the level and Terrain3D nodes at their authored transforms. Terrain movement samples the real Terrain3D heightmap, uses bridge decks and rejects water, steep edges, occupied cells and obstacle footprints.

See [the starting-level guide](STARTING_LEVEL.md) for map dimensions, metadata, gameplay rules and the optional baseline generator. Terrain3D is installed under `addons/terrain_3d` and enabled in the main project. `References/Terrain3D` is the preserved reference copy.
