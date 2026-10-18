# Assassin source assets

The current source is `blendswap_assassin/assassin_refined.blend`; its export is `blendswap_assassin/assassin_refined.glb`. Godot uses the copy under `Assets/Characters/Assassin/Assassin.glb`.

Earlier Blender files, animation renders and texture iterations are retained as historical source assets. The character was inspired by https://chatgpt.com/s/m_6ad51238f2e48191a466b2054db3ca65.

The fitted body is based on Eliber's CC0 Rigged Base Mesh: https://blendswap.com/blend/14675. Its original download and licence are under `SourceAssets/characters/_base/`.

Python generation and validation scripts have been removed. Use Blender to edit the source and export GLB, then refresh the Godot runtime copy using `tools/Sync-GodotAssets.ps1`.
