# Oathbreakers battlefield prototype

Run from the project directory:

```powershell
.\.venv\Scripts\python.exe main.py
```

The refined assassin and Ashveil ninja appear near the centre of the 24×24 map.

- Click either character to select him; a cyan or gold marker appears under his feet.
- Click a tile to walk there. The route is cyan and the destination is gold.
- Wait for arrival before selecting another destination. He idles when he stops. You can switch which character is selected; only one moves at a time.
- Other characters block movement paths; you cannot move onto an occupied tile.
- Right-click or Escape deselects the character.
- WASD pans the camera. The mouse wheel zooms in and out.

This is a free-movement prototype: no turn limit, movement allowance, combat or obstacles yet. Paths use orthogonal neighbouring tiles; illegal destinations are rejected by renderer-independent rules in `core/movement.py`.

The character is loaded from `assets/characters/hooded_assassin/blendswap_assassin/assassin_refined.glb`. It retains the fitted Blend Swap body, outfit, textures and animations. Its source and credits are documented beside the asset. `panda3d-gltf` imports the model and `panda3d-simplepbr` renders its material maps; both are listed in `requirements.txt`.

Ashveil is loaded from `assets/characters/ashveil/ashveil.glb`, with a new outfit built around the same fitted body and skeleton. His editable Blender scene and source notes are in that folder.

Validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe main.py --smoke-test
```

The smoke check runs offscreen, independently selects and moves both units, rejects occupied destinations, verifies orientation, animation states, colliders and cleared paths, then saves `artifacts/characters_on_map.png`.
