# Refined assassin source

Open `assassin_refined.blend` in Blender to edit the fitted Eliber body, armour, scarf, boots, materials and skeleton. Export `assassin_refined.glb` after editing. Runtime copy: `Assets/Characters/Assassin/Assassin.glb`.

The body originates from Eliber's Rigged Base Mesh, https://blendswap.com/blend/14675, CC0. The creator clarified the transition from CC-BY to CC0 in the listing comments. Original sources and licence records remain in `SourceAssets/characters/_base/`.

The model includes shaped boots, rigid armour, weighted cloth chains, packed material maps, and Idle, Walk and Arm_Motion_Test animation actions. Earlier exports and previews remain for reference. Draft animation may still contain sliding or intersections.

The Python rebuild and verification scripts have been removed. Blender is the asset-authoring tool; Godot is the game runtime. Use `tools/Sync-GodotAssets.ps1` to copy source GLBs into the Godot asset folders after exporting.
