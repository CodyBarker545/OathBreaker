# Assassin with fitted Blend Swap body

## Refined boots and surfaces

The latest version is **assassin_refined.blend**, with **assassin_refined.glb** as its game export. The earlier animated files are preserved.

This revision replaces the oval foot placeholders with shaped leather boots, a defined outsole, a raised instep, ankle cuffs and straps, bronze buckles and curved steel toe guards. Cuffs blend between foot and shin weights. Curved surfaces use smooth shading and additional geometry; armour edges have small bevels.

Six materials now have 1024×1024 colour, packed roughness/metallic and tangent normal maps. Images are packed into the Blender scene and embedded in the GLB, with PNG sources under `textures/`. `refined_preview.png`, `refined_boots.png` and `refined_walk.gif` show this revision.

The same Idle, Walk and Arm_Motion_Test clips remain available. The lower sections describe those animation controls. Run `refine_assassin.py` using portable Blender to reproduce this refinement from the earlier `assassin_animated.blend`; the source script sits one folder above this README.

This version uses the user-downloaded **Rigged Base Mesh by Eliber**:
https://blendswap.com/blend/14675

The listing is CC0. In its comments, the creator explicitly clarified that the model was originally CC-BY and later changed to CC0. The original download and its bundled license HTML remain unchanged under `characters/Eliber_Rigged_Base_Mesh/` in the project. Credit is retained here for provenance.

## Open the character

Open `assassin_animated.blend` in Blender 4.5 or later. It contains the fitted character, editable outfit, skeleton, animation actions, studio lights and camera. Press Space over the timeline to play the default Idle action.

To change the animation, select `Assassin_Animation_Rig`, change a lower editor to **Dope Sheet**, select **Action Editor** in its mode dropdown and choose the desired action in the action selector:

| Action | Frames at 24 fps | Purpose |
| --- | --- | --- |
| Idle | 1–49 | Breathing and cloth sway; loop |
| Walk | 1–25 | Walk in place; loop |
| Arm_Motion_Test | 1–37 | Alternating arm movement to inspect equipment attachment |

Set the timeline end to the selected action's last frame before playing it. The repeated last frame closes each loop.

## What was made

- The downloaded continuous body was rescaled and refitted to the outfit. Its legacy IK controls were replaced with a clean FK setup; the original bone hierarchy was adapted and finger bones retained.
- Hidden head and hand surfaces were removed from the fitted copy and replaced with the authored masked face, hair and gloves. The original downloaded file is untouched.
- The assassin has a hood, mask, blond hair, layered dark armour with bronze edges, crimson scarf and tabards, belt, pouches, gloves and boots.
- Armour is rigidly weighted to the corresponding body bones. Cloth tails have their own smoothly weighted chains with authored secondary motion.
- Weapons are omitted, as requested. The arm test is a movement study, not a weapon attack animation.

`assassin_animated.glb` contains the character, skin and three animation clips. It excludes studio objects. `fitted_rest.png` is the rest-pose render; GIFs show the actual rendered animations. The `.blend` retains all editable components.

## Validation and limits

The build checks that the bracer remains fixed relative to the forearm through all three actions. `validation.json` records this check and the source model. `verify_runtime.py` also loads the GLB using the installed Panda3D glTF loader, finds all three clips and poses each at its beginning, middle and end without opening a window. `runtime_validation.json` records the result. This is an import and pose check, not a visual test inside the game.

This remains a stylized prototype with blocking animations and material colours. The walk is in place, without root travel or foot-lock IK; some sliding or intersections may remain. Cloth motion is keyed rather than simulated. The original source body's topology and weights are retained where possible, while equipment has rigid weights. Final deformation cleanup, texture painting, material consolidation and game-renderer validation are future production work.

## Rebuild

From the project root in PowerShell:

```powershell
& '.\tools\blender-portable\blender-4.5.3-windows-x64\blender.exe' --background --python-exit-code 1 --python '.\assets\characters\hooded_assassin\fit_blendswap_base.py'
$env:ASSASSIN_INPUT = (Resolve-Path '.\assets\characters\hooded_assassin\blendswap_assassin\assassin_fitted.blend').Path
$env:ASSASSIN_OUT = (Resolve-Path '.\assets\characters\hooded_assassin\blendswap_assassin').Path
& '.\tools\blender-portable\blender-4.5.3-windows-x64\blender.exe' --background --python-exit-code 1 --python '.\assets\characters\hooded_assassin\animate_assassin.py'
```

The rebuild overwrites the generated model and preview frames in this folder. Keep hand edits in a separate `.blend` file.
