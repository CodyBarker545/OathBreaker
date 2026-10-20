# Character source assets

Editable Blender files, original downloads, licences and previews are preserved here. Runtime Godot models are in `Assets/Characters/`.

- `ashveil/`: Ashveil Blender source, GLB, textures and render.
- `hooded_assassin/`: assassin sources, earlier iterations, textures and previews.
- `_base/`: Eliber base-body download, licence and inspection metadata.
- `komodo_axe_warrior/`: reference-inspired Komodo warrior, editable Blender source, packed materials, GLB and studio previews.

- `forsaken_sister/`: ivory robes, burgundy hood, sun charms and removable lantern staff.
- `masked_ninja/`: cloth mask and headwrap, layered slate tunic and segmented armor.
- `broken_oath_knight/`: closed helm, blue heraldic cloth, plate armor and removable shield.
- `ash_scholar/`: charcoal robes, ember details, grimoire and copper back apparatus.

The four reference characters are editable rigged prototypes built on the shared fitted Eliber anatomy. Each folder contains its Blender source, GLB, packed materials, copied reference, studio previews and validation report. Cloth collision, final animation cleanup and game LODs still require a production pass.

Edit models in Blender and export GLB. `tools/build_reference_characters.py` and `tools/character_asset_builder.py` reproduce the four reference builds; rerunning replaces their generated files. Use `tools/Sync-GodotAssets.ps1` from the project root to refresh the Godot copies. `tools/validate_reference_characters.py` checks exports and renders sample poses.

`tools/refresh_reference_exports.py` refreshes exports from the saved Blender files, writes texture PNG copies and updates the runtime GLBs. Blender-only height bump and sheen are omitted during GLB export to preserve the intended cloth shading; the editable source retains them. Tangent-space normal maps can be baked in a later detail pass.
