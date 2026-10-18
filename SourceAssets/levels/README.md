# Environment source assets

The active level builder is Godot's native 3D scene editor. Open `Scenes/Battlefield.tscn` and place models from `Assets/Levels/` under `LevelProps`.

This source directory preserves:

- `source_packs/`: original foliage and stone ZIP archives.
- `sources/`: extracted Blender files and their original licences.
- `models/`: the previously prepared GLB and BAM props plus source manifest.
- `textures/`: environment texture sources.
- `scenes/` and `prefabs/`: legacy Ursina asset folders, not read by Godot.

The supplied packs are CC0 according to their bundled licences. Those original licence files are retained unchanged. GLB works directly in Godot; BAM belongs to the former Panda3D/Ursina workflow. Converted props are centred near ground level and normalized to a starting size; adjust scale in Godot.

The Python exporter and Ursina editor have been removed. For future asset changes, edit the source in Blender, export GLB to `models/`, and run `tools/Sync-GodotAssets.ps1` to refresh the Godot copies. Existing Ursina CSV scenes are not imported automatically.
