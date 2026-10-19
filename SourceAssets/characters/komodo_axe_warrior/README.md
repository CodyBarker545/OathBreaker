# Komodo axe warrior — the Broken Crown

Reference: https://chatgpt.com/s/m_6ad64e5848088191bce75c6247986cd3 (Komodo Axe Warrior Sprite Sheet).

Created in Blender with a dimensional, rounded pre-rendered game aesthetic and dark fantasy equipment. The character retains the reference's golden reptilian skin, long muzzle and tail, red cloth, layered metal shoulders and an unarmed loadout for separate weapons later. Distinguishing features include three healed muzzle scars, slit amber eyes, an ivory trophy pauldron, a broken-crown chest medallion, tooth trophies, worn bronze trim, belly plates and dorsal scutes.

- `komodo_axe_warrior.blend`: editable parts, packed albedo textures, deformation rig, draft idle animation and lit studio camera. The saved camera is the front three-quarter view. Studio objects are excluded from the GLB.
- `komodo_axe_warrior.glb`: textured and rigged character, metres, Z-up in Blender / Y-up in glTF. Godot runtime copy: `Assets/Characters/Komodo/Komodo.glb`.
- `komodo_preview.png`, `komodo_rear.png`: Blender studio renders.
- `build_report.json`: mesh and rig counts.

The core torso and legs adapt Eliber's CC0 Rigged Base Mesh, preserved under `../_base/Eliber_Rigged_Base_Mesh/` with its original licence and creator clarification. Head, arms, tail, costume, rig and materials were created for this asset. Other characters and gameplay scenes are unchanged.

The rig has 48 bones and a gentle `Komodo_Idle` cycle. Both hands have humanlike palms, four individually jointed fingers, an opposing three-joint thumb and long curved claws. Select the deformation rig and adjust its custom properties `Grip.L` / `Grip.R` from 0 (relaxed) toward 1 (curled). Adjust the value to fit the held object; the long claws need clearance. The Blender driver controls do not transfer to GLB, but the finger bones and skin weights do. Author and bake object-specific grip poses for the game. `WeaponGrip.L` / `WeaponGrip.R` empties are Blender attachment guides. `hand_detail.png` and `hand_grip.png` show the relaxed and curled hand.

Locomotion/combat clips, cloth simulation, retopology/LOD optimisation and a polished deformation pass remain future production work. Rounded armour and details are separate editable meshes, so this is a detailed character prototype rather than an optimised final crowd asset. Procedural bump shading is Blender-only; packed albedo textures and explicit geometric details export to GLB.

Rebuild with Blender's background mode and `tools/build_komodo.py`, or edit the Blender source and export the selected character meshes plus rig. Run `tools/Sync-GodotAssets.ps1` after a source GLB update.
