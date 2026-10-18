# Level editing

The level editor is Godot's native 3D editor in the same project as the game.

1. Import `D:\SoftwareEng\Game\project.godot` using Godot .NET.
2. Open `Scenes/Battlefield.tscn`.
3. Select `LevelProps` in the Scene tree.
4. Drag a GLB from `Assets/Levels/` into the 3D scene and parent it under `LevelProps`.
5. Use W to move, E to rotate and R to scale it. Save with Ctrl+S.
6. Press F5 to play the main scene.

`GroundPreview` is the editor ground guide. The C# controller replaces it with a clickable grid during play. Character models are in `Assets/Characters/`; the current units are spawned by `Scripts/Battlefield.cs`.

Environment placement currently dresses the scene visually. Adding a prop does not yet mark its grid cells as blocked or give them elevation.

The downloaded Terrain3D add-on and demo are preserved in `References/Terrain3D/` with their original paths and licences. `.gdignore` keeps this reference out of active imports. Its original project settings are kept as `project.godot.reference`, so the root project is the only active Godot project. Terrain3D is not enabled or integrated with tactical movement.
