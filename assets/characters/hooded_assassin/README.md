# Hooded assassin prototype

The newer version using the downloaded Eliber body, with no weapons and three animation clips, is in [blendswap_assassin](blendswap_assassin/README.md). The files described below are the earlier procedural prototype.

An original geometric interpretation of the supplied character sheet:
https://chatgpt.com/s/m_6ad51238f2e48191a466b2054db3ca65

## Files

- `hooded_assassin.blend`: editable Blender scene, character rig, lighting and presentation plinth.
- `hooded_assassin.glb`: character and skeleton only, with material colours and UV coordinates.
- `preview_front.png` and `preview_back.png`: actual Blender renders.
- `build_assassin.py`: commented Blender Python source that rebuilds the scene and exports the model.

## Open and learn

1. Open `hooded_assassin.blend` in Blender 4.5 or later.
2. The Outliner collection `ASSASSIN | editable character parts` contains the model.
3. Select an armour or cloth object in Object Mode to edit that individual piece. Press Tab to edit its mesh vertices. Use Z then M for Material Preview if you want to see its colours.
4. Select `Assassin_Rig | rigid prototype weights`, enter Pose Mode using the mode menu, select a bone and press R to rotate it. Alt+R clears the selected bone's rotation.
5. Press Numpad 0 to see the prepared front camera; F12 renders it. The STUDIO collection contains only presentation objects and is excluded from the supplied GLB.
6. Save changes under a new filename before experimenting. Running `build_assassin.py` regenerates the deliverables and overwrites them.

The source creates parts in this sequence: materials, body, armour, face, hood and hair, scarf, weapons, rig, UVs, export and presentation lighting. Change the material RGB values near the top for colour variants. The model faces -Y with Z up and stands approximately two metres high.

## Scope

This is a stylized segmented prototype, not a detailed reproduction or final production asset. It uses material colours instead of painted textures and has automatically projected UVs. Its 16-bone skeleton uses rigid weights per part, suitable for simple posing; cloth, shoulders and body joints need deformation work for convincing animation. There are no animation clips, facial rig, finger bones, cloth simulation or baked texture maps. The parts have not been merged or optimized for draw calls, and the GLB has not been tested in Ursina/Panda3D.

Next production steps are anatomy and silhouette refinement, joint topology and smooth weight painting, texture baking and painting, animation, mesh/material consolidation, and validation inside the game renderer.

## Rebuild

From the project root in PowerShell, using the portable Blender downloaded for this task:

```powershell
& '.\tools\blender-portable\blender-4.5.3-windows-x64\blender.exe' --background --python '.\assets\characters\hooded_assassin\build_assassin.py'
```

The portable Blender download is stored under `tools/blender-portable` and excluded from Git. No system installation is required.
