# Ashveil ninja prototype

An editable stylized interpretation of the user-supplied **Oathbreakers Ashveil ninja portfolio sheet.png**. The model uses the same fitted continuous Eliber base body and skeleton as the first assassin. Source: https://blendswap.com/blend/14675, by Eliber, CC0 (including the creator's licensing clarification on that listing). The original download remains under the project's `characters/` folder.

## Deliverables

- `ashveil.blend`: editable body, outfit, skeleton, materials, lights and camera.
- `ashveil.glb`: character-only game export with embedded textures and Idle, Walk and Arm_Motion_Test clips.
- `ashveil_preview.png`: actual Blender render.
- `../build_ashveil.py`: reproducible Blender build script.

Ashveil has layered cloth headwraps, an engraved mask, grey cowl and tunic, a single shoulder pauldron, bracers, baggy trousers, skirt panels, crossed leg cords, leather harnesses and belt ornaments. Existing boots and gloves are reused and recoloured. New cloth materials have packed weave textures. This is a stylized prototype rather than a detailed sculpt or exact reproduction. Weapons and smoke/teleport abilities have not been added.

## In the game

Run `main.py` from the project root using the project Python environment. Both characters spawn near the map centre. Click either character to select only that character, then click an empty tile. He walks there and idles on arrival. The other character blocks pathfinding and occupied destination tiles are rejected. One character moves at a time. Selection may switch while a character is moving, but another movement command waits until arrival.

WASD pans the camera; the wheel zooms. Right-click or Escape deselects both. The `main.py --smoke-test` check exercises both characters, independent selection and movement, occupied-tile rejection, upright models and colliders, then captures `artifacts/characters_on_map.png`.

The original blocking animations are reused; detailed cloth deformation, intersection cleanup and polished animation remain production tasks.
