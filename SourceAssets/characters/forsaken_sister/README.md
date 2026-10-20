# Forsaken Sister

Editable Blender prototype built from the existing fitted Eliber base and shared anatomical refinements.

Ivory layered robes, burgundy hood, mail sleeves, sun charms and a removable glowing lantern staff.

- Open `forsaken_sister.blend` in Blender. Materials and generated color textures are packed.
- `forsaken_sister.glb` is also copied to `Assets/Characters/ForsakenSister/ForsakenSister.glb`.
- Reference: `Forsaken Sister Lantern Sprite Atlas.png`, preserved here as `reference.png`.
- `preview.png` and `rear.png` show the neutral model. `walk_check.png` and `arm_check.png` show sample poses.
- The shared 96-bone rig retains Idle, Walk and Arm_Motion_Test draft clips. Finger bones and Blender HandGrip.L/R controls are retained; bake driver-based grip poses before export.
- Equipment is in its own collection and can be hidden or removed. Studio objects are excluded from GLB. Combat weapons are omitted.
- `validation_report.json` records clean GLB import, bounds, mesh binding, animation and export checks.

These are first-pass assets, with simplified forms and materials. Cloth collision, hand/equipment contact poses, animation cleanup, closer reference detailing and LOD/draw-call optimization remain. The shared clips do not imply animation-ready cloth or equipment grips.

Base license: Eliber Rigged Base Mesh, CC0. Original download and license are preserved in `../_base/Eliber_Rigged_Base_Mesh/`. Reference image rights are separate from the base license.

Rebuild from the project root with Blender using `tools/build_reference_characters.py`; this replaces generated source and export files. Shared authoring helpers are in `tools/character_asset_builder.py`.

