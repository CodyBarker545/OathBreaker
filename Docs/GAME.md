# Oathbreakers Godot and C sharp game

This is the active game project. Open **Oathbreakers.sln** in Visual Studio for code and debugging, or import **project.godot** in the Godot 4.7.2 .NET editor for scene and level editing.

[Visual Studio setup and controls](VISUAL_STUDIO.md)

## Game

The C# prototype contains a 24x24 grid, Assassin and Ashveil, imported materials and animations, click-to-move, occupied-tile blocking and a tactical camera angled down about 37 degrees. Click a character and then an empty tile. WASD pans, the wheel zooms and right-click deselects.

## Files

- `Scripts/Battlefield.cs`: grid, click input, selection, camera and runtime checks.
- `Scripts/TacticalUnit.cs`: character imports, animation and movement.
- `Scripts/GridPathfinder.cs`: shortest grid paths.
- `Scenes/Battlefield.tscn`: the native Godot level scene.
- `Assets/Characters/`: the two animated runtime GLBs.
- `Assets/Levels/`: foliage and stone GLBs.
- `Properties/launchSettings.json`: Visual Studio game and headless-check profiles.

Editable Blender sources and original licences live in `SourceAssets/` at the project root. Refresh runtime exports using `tools/Sync-GodotAssets.ps1` from the root. Godot's generated `.godot/` cache and Visual Studio's `.vs/` files are ignored by Git.

## Levels

Open `Scenes/Battlefield.tscn` in Godot. `GroundPreview` is an editor guide; C# replaces it with clickable tiles during play. Drag environment GLBs into `LevelProps`, position and scale them, then save. Props currently affect appearance only; grid blocking and elevations require explicit gameplay data.

## Build and checks

Use the Godot .NET editor and a .NET 8 SDK. `global.json` selects .NET 8, and the project uses Godot.NET.Sdk 4.7.2. `NuGet.Config` supports official NuGet and the ignored local package directory used for Godot-bundled packages.

```powershell
dotnet build Oathbreakers.sln
```

In Visual Studio, choose **Oathbreakers Checks** and press F5 to run the headless checks. Choose **Oathbreakers Game** to run the game. The earlier Python/Ursina implementation has been removed.
