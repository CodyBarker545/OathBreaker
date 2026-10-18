# Oathbreakers

Godot 4.7.2 .NET / C# tactical-game prototype. **This repository root is the game project.** Open this folder in VS Code, `Oathbreakers.sln` in Visual Studio, or `project.godot` in Godot .NET. There is one active Godot project and no Python dependency.

## Project layout

```text
Game/
  project.godot             Godot project; main scene is Battlefield
  Oathbreakers.sln          Visual Studio solution
  Oathbreakers.csproj       C# game assembly
  Scripts/                 Gameplay, units, camera and pathfinding
  Scenes/                  Godot scenes and level layouts
  Assets/
    Characters/            Animated character models used by the game
    Levels/                Trees, rocks and other environment models
  SourceAssets/            Editable Blender files, downloads and licences
  Properties/              Visual Studio run/check profiles
  .vscode/                 VS Code build/run/check profiles
  tools/                   Asset export synchronization
  Docs/                    Editor and gameplay guides
  References/Terrain3D/    Preserved third-party demo, excluded from game imports
  artifacts/               Historical previews and verification logs
```

`SourceAssets`, `References`, tooling and documentation have `.gdignore` files so Godot imports only game resources. Editable sources are preserved alongside the game, without importing duplicate Blender files and old previews. Generated `.godot`, `.vs` and package caches are excluded from Git.

## Work in VS Code

1. Open **D:\SoftwareEng\Game** using File → Open Folder.
2. Install the recommended Microsoft **C#** extension.
3. Open files under `Scripts/` and press **Ctrl+Shift+B** to build. Compiler diagnostics appear in Problems.
4. Choose **Oathbreakers Game** in Run and Debug and press **F5**. Set breakpoints with **F9**, step over with **F10**, and stop with **Shift+F5**.
5. Choose **Oathbreakers Checks** to build and run the headless gameplay checks.

The executable path in `.vscode/launch.json` points to Godot .NET installed on this computer. Update it if Godot moves. See [the VS Code guide](Docs/VS_CODE.md).

## Work in Visual Studio

Open `Oathbreakers.sln`, select **Debug → Oathbreakers Game**, then press **F5**. **Ctrl+Shift+B** builds. See [the Visual Studio guide](Docs/VISUAL_STUDIO.md).

## Build levels

Import **D:\SoftwareEng\Game\project.godot** in Godot .NET. Remove stale `godot/` or `oath-breaker/` entries from the Project Manager list if they remain there; those are the old locations.

Open `Scenes/Battlefield.tscn`. Drag models from `Assets/Levels/` onto `LevelProps`, position and scale them, then save with Ctrl+S. Press F5 to play. Godot is the level editor; VS Code and Visual Studio edit/debug C#.

Props currently affect appearance only. Tactical terrain blocking and elevation require gameplay integration. The Terrain3D add-on and its demo remain preserved under `References/Terrain3D`; they are not enabled in this game. See [level editing](Docs/LEVEL_EDITING.md).

## Assets

Edit models under `SourceAssets/`, export their GLBs there, then run this from the repository root:

```powershell
.\tools\Sync-GodotAssets.ps1
```

This refreshes two character models and the environment GLBs in `Assets/`. Original licences remain with the source assets.

## Build and verify

From this root folder:

```powershell
dotnet build Oathbreakers.sln
& 'D:\Downloads\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64_console.exe' --headless --path . -- --smoke-test
```

Checks cover character imports, idle/walk clips, colliders, independent movement, occupancy and pathfinding. A failure exits with code 1.

Click a character, then an empty tile to move. WASD pans, the wheel zooms and right-click deselects. Combat, turns, fog, scoring and online play remain future work. See [the game overview](Docs/GAME.md).
