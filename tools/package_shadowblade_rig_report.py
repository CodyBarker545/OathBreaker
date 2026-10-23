import json,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin');OUT=ROOT/'inspection_rigged_shadowblade'
def read(n):return json.loads((OUT/n).read_text())
inv=read('rig_inventory.json');m=next(m for m in inv['meshes'] if m['name']=='Mesh0');rig=inv['rigs'][0];tests=read('articulation_measurements.json');export=read('export_verification_timing_fixed.json')
before=read('source_integrity_before.json');after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before};assert before==after
(OUT/'source_integrity_verified.json').write_text(json.dumps({'all_protected_files_unchanged':before==after,'files_checked':len(before),'before':before,'after':after},indent=2))
for view in ['front','side']:
    base=Image.open(OUT/f'rest_{view}.png').convert('RGB');skel=np.array(Image.open(OUT/f'skeleton_color_{view}.png').convert('RGB'))
    mask=(skel[:,:,0]>skel[:,:,1]*1.35)&(skel[:,:,0]>skel[:,:,2]*1.35)&(skel[:,:,0]>75)
    out=np.array(base);out[mask]=(255,80,35);Image.fromarray(out).save(OUT/f'skeleton_overlay_{view}.png')
for name in ['Walking','Running','Arise']:
    frames=[Image.open(OUT/f'clip_{name}_{i:02}_three_quarter.png').convert('RGB') for i in range(13)]
    a=next(a for a in inv['actions'] if a['name']==name);duration=max(40,round((a['frames'][1]-a['frames'][0])/24/12*1000))
    frames[0].save(OUT/f'{name}_sampled_preview.gif',save_all=True,append_images=frames[1:],duration=duration,loop=0)
notes={
 'rest':'Near T stance; arms slope downward and elbows are slightly bent; not a strict horizontal T-pose.',
 'arms_raised':'Both arms rise; shoulder plates deform and shoulder/chest seams open visibly.',
 'arms_lowered':'Both arms lower; underarm/plate compression needs tuning.',
 'elbows_bent':'Both elbows articulate; sleeve and bracer transition pinch; no whole-limb detachment.',
 'wrists_flex':'Hands flex; no large edge stretch measured; sculpted gloves remain coarse.',
 'wrists_twist':'Hands twist; small local compression, no gross global collapse in evidence.',
 'terminal_hand_bend':'Weighted Middle4 controls move the distal hand subtly; no independent fingers/thumb or usable authored grip.',
 'head_left':'Head rotates; hood follows, neck/scarf transition stretches and exposes gaps.',
 'head_right':'Head rotates; asymmetric scarf/hood strain; refine neck weights and clearance.',
 'torso_left':'Torso turns; waist plates and scarf distort rather than remain fully rigid.',
 'torso_right':'Torso turns; waist and chest seams show distortion.',
 'left_leg_forward':'Leg lifts; thigh drags waist panels and stretches the groin/panel transition.',
 'left_leg_backward':'Backward extension works; panels remain linked to leg motion.',
 'right_leg_forward':'Leg lifts; stronger waist/panel stretching than left in this stress pose.',
 'right_leg_backward':'Leg extends; asymmetric strain remains in clothing.',
 'knees_bent':'Both knees bend; kneecap/greave transition compresses and silhouette loses rigid armor shape.',
 'ankles':'Both feet rotate; modest strain, boot transition needs normal animation QA.',
 'crouch':'Crouch is achievable, but skirt overlaps/compresses around thighs and knees; large waist-panel strain.'}
rows=[]
for name,v in tests['static_tests'].items():rows.append(f"| {name.replace('_',' ')} | {v['edge_length_ratio_max']:.2f}× | {v['edge_stretch_gt_1_5']} | {notes[name]} |")
hierarchy='\n'.join(f"- `{b['name']}` ← `{b['parent'] or '(root)'}`" for b in rig['bones'])
exportrows='\n'.join(f"| {name} | {(c['source_frame_range'][1]-c['source_frame_range'][0])/24:.4f} s | {(c['reimport_frame_range'][1]-c['reimport_frame_range'][0])/30:.4f} s | {c['five_normalized_phase_samples_max_vertex_error']:.8f} |" for name,c in export['clips'].items())
report=f'''# Crimson Rogue Knight / Shadowblade — rigging and animation inspection

**Final verdict: Major rigging corrections required for the full requested movement set.** Meshy's generated rig is usable and worth retaining. It has eliminated the need to build a basic humanoid skeleton and body skinning from scratch. Existing walking and running provide a credible starting point. It has not eliminated targeted weight painting, clothing/armor cleanup, or the need to solve dagger grips. A walking prototype needs considerably less work than polished attacks and deep crouching.

Date: October 21, 2026, America/St_Johns. Blender 5.2.2 LTS. MCP returned “Not connected to Blender”; authorized separate background processes performed all inspection and tests. No game code, source Meshy files, existing MPFB rig, or source weights were modified. SHA-256 checks confirm all {len(before)} protected files unchanged; see `source_integrity_verified.json`.

## A. Model specifications

Only one GLB/GLTF/FBX candidate exists recursively under `Full_model`: **`Meshy_AI_Crimson_Rogue_Knight_All_Animations(1).glb`**, 6,426,860 bytes (6.13 MiB). Its contents confirm a skinned mesh and three animations. The filename differs from the previous high-poly Crimson Shadowblade. No matched pre-remesh version of this precise design was provided; differences from the earlier character cannot all be attributed to remeshing.

| Property | Result |
| --- | --- |
| Character mesh / material | `Mesh0` / `BPY_PBRSource` |
| Vertices / edges / triangles | {m['vertices']:,} / {m['edges']:,} / {m['triangles']:,} |
| Faces / quads | {m['faces']:,}, all triangles / 0 |
| Raw indexed connected components | {len(m['island_sizes']):,} |
| Boundary / non-manifold edges | {m['boundary_edges']:,} / {m['nonmanifold_edges']:,} |
| Exact duplicate positions / index-duplicate faces | {m['exact_duplicate_vertices']:,} / {m['duplicate_index_faces']} |
| Inconsistent winding across manifold edges | {m['inconsistent_winding_edges']} |
| UV maps / material slots | 1 (`UVMap`) / 1 |
| Textures | One embedded 2048×2048 normal map, no external image dependencies |
| Base color / metallic / roughness | Constant gray (0.8), 0, 0.5; no color or roughness texture |
| Rest geometry height | {tests['static_tests']['rest']['bounds_max'][2]-tests['static_tests']['rest']['bounds_min'][2]:.4f} source units |

The imported `Icosphere` (42 vertices, 80 triangles) is a Blender custom bone-display shape used by the rig, not a source GLB character primitive. It is excluded from the character geometry count, weight failure count and export selection. See `helper_objects.json`.

The large component and duplicate counts are substantially influenced by GLB splits at UV/normal seams. An **analytical BMesh only**, discarded without modifying the character, merged coincident positions within 1e-6 units: 32,755 vertices, 52 components, 1,737 boundary edges, 1,803 non-manifold edges remained. This is a connectivity diagnostic, not a repaired mesh. Welding touching layers can itself create overconnected edges. The remaining boundaries and separated clothing shapes require local interpretation, not a blanket “broken mesh” verdict. Never globally weld UV/hard-normal seams as a cleanup shortcut.

There are 12,684 exact-position clusters with multiple indexed vertices. All have identical influence names and weights at 1e-6 comparison precision. They should not pull apart merely because their skin weights differ. This does not certify all clothing seams, normals or contacts.

**Visual quality:** hood, scarf folds, shoulders, bracers, waist strips and boots remain recognizable. Bare-geometry Workbench views look much smoother than the actual material; the embedded normal map restores face and armor detail. [Material face close-up](face_material_detail.png) and [material full body](rest_material_three_quarter.png) show this distinction. The face is coarse and glove/finger geometry is simplified, with hard edges and compressed finger forms. Torn hems and clothing transitions are visibly rough. It looks plausible at a small isometric character size, but no actual gameplay-camera or engine performance test was performed. It is still **3.20–5.34×** the earlier 12k–20k complete-character triangle target; no decimation or retopology was performed.

The rest stance is approximately T-like with spread legs and extended arms, but upper arms slope downward about 24° and elbows are not perfectly straight. It is not a strict horizontal T-pose. The bind pose and skeleton are mutually usable; do not forcibly change the bind pose just to make it look like an exact T.

## B. Skeleton assessment

Armature: **`target_character`, 28 bones**. `mixamorig:Hips` is the parentless root/pelvis. There is no separate ground/root-motion bone. There are three spine segments, neck/head, bilateral clavicle/arm/forearm/hand chains and thigh/knee/foot/toe chains. `HeadTop_End`, `headfront`, hand `Middle4` and toe endpoints complete the hierarchy. There are **no dedicated cape, scarf, skirt, armor or weapon bones**, and no full finger/thumb chains.

Joint centers broadly follow the body in front and side evidence: shoulders at upper arms, elbows at sleeve bends, wrists at gloves, hips/knees/ankles along the legs. This is supported by actual articulation rather than by bone names alone. Bone local orientations are varied; tests converted intended world axes into each bone's rest-local axes instead of assuming every joint bends around local X. Numerical head/tail positions and rest matrices are retained in `rig_inventory.json`. [Front skeleton overlay](skeleton_overlay_front.png), [side overlay](skeleton_overlay_side.png) are explicitly composited x-ray views of rest bone segments over the model, not extra rig controls.

Existing actions: `Walking` (about 1.0333 s), `Running` (0.6333 s), `Arise` (1.8333 s). Imported NLA tracks refer to those actions. No idle, attack, damage, defeat or dedicated crouch clip is present. `Arise` is a getting-up motion; it does not establish a finished defeat animation.

### Complete hierarchy (bone ← parent)

{hierarchy}

## C. Skinning assessment

`Mesh0` is parented to `target_character` and its Armature modifier targets that armature. All 50,323 character vertices have deform-bone weights. Influence histogram: 780 vertices with one influence; 16,758 with two; 12,570 with three; 20,215 with four. No vertex exceeds four influences. Deform weight totals range approximately 0.99999986–1.00000013; none differs from one by more than 1e-4. The unweighted custom display shape is not a character skinning failure.

These are good numerical fundamentals, but normalized weights do not establish correct semantic assignments. Direct tests reveal shoulder plates stretching with arms, scarf/neck strain during head turns, and waist strips following thigh motion. Kneecap/greave transitions soften during deep flexion. The cape has no independent control and is carried by existing body weights; the crouch side view shows it pulled into an angular silhouette. Correct body association and moving limbs are confirmed; perfect anatomical assignments are not.

Both `HandMiddle4` bones have nonzero weights (720 left-hand vertices and 788 right-hand vertices), but they are a single distal control per hand. The 40° test produces only a modest shared deformation: [rest hand](hand_rest_detail.png), [terminal bend](hand_terminal_bend_detail.png). It does not independently close four fingers or oppose a thumb. Dagger grips need a deliberate fixed-grip hand shape or additional finger controls and weights. A low-detail fixed grip may be enough at the tactical camera; a full finger rig is not automatically necessary.

No weight changes were applied. Required painting should focus on shoulder/upper-arm armor transitions, scarf/hood/neck, waist/thigh panels, kneecaps and hand controls. Rigid armor needs deliberate weighting or separate rigid sections if stretching is unacceptable. Dedicated clothing bones are an option, not an automatic requirement to replace the humanoid rig.

## D. Animation testing

All static poses were reset independently. Rotations: upper arms 70° upward / 65° downward; elbows 90°; wrist flex 40° and twist 60°; terminal hand 40°; head ±45°; upper torso ±35°; each hip 50° forward / 30° backward; knees 90°; ankles 25°. The crouch combined hips −55°, knees +100°, ankles −45°, lowered arms and a temporary pelvis drop of 0.32 units. It is a stress pose, not an authored foot-planted crouch with IK or ground constraints. Floating feet in isolated knee tests are expected because the hips were held fixed.

Front, side and three-quarter renders were captured for all 18 states. The strain metric below compares evaluated mesh edge lengths with rest lengths; it measures stretching, **not collision or anatomical correctness**. Large ratios flag review regions but are not alone a failure criterion. Workbench evidence does not display the normal map.

| Static test | Maximum edge ratio | Edges stretched >1.5× | Actual observation |
| --- | --- | --- | --- |
{chr(10).join(rows)}

The cloak and skirt have visible overlap/compression in the crouch views; no exact triangle collision certification was performed. Shoulder and neck gaps are visible in close-ups, although some gaps already belong to separated armor/cloth layers. The tests do not show a globally broken rig or detached limbs.

**Existing clips were separately evaluated at 13 evenly spaced times each**, with NLA disabled and the original action assigned directly. Walking and running move the body and limbs coherently with a stable overall silhouette at inspection scale. Waist panels track the legs, with local pinching/stretching around hips and knees. Arise genuinely moves from a lying position through a kneel to standing; its larger bends expose more cloth compression. No idle or attack clip exists to test. These are sampled clip tests, not continuous engine playback, blend-transition validation, foot-slip measurements or collision-free certification. Animated GIFs are sampled previews of the supplied clips, not a new animation library.

### Gameplay readiness

| Capability | Rating | Evidence / remaining requirement |
| --- | --- | --- |
| Idle | Minor corrections needed | Basic body articulation works; no idle clip supplied, breathing and loop untested. |
| Walking | Minor corrections needed | Existing clip sampled successfully; refine panels, foot contact/root-motion convention and loop in engine. |
| Running | Minor corrections needed | Existing clip sampled successfully; tune stronger hip/knee cloth deformation and contacts. |
| Dual-dagger attacks | Major corrections needed | Arm joints work, but shoulder strain and missing grips require correction; no attack clip or weapon attachments tested. |
| Taking damage | Minor corrections needed | Torso/head motion demonstrated; no damage clip, timing or extreme recoil validation. |
| Defeat | Major corrections needed | Arise shows ground-to-standing motion only; reverse/defeat behavior not tested, ground contacts and cloth folds need authoring. |
| Crouching | Major corrections needed | Actual compound stress pose shows waist/skirt distortion and overlap; authored foot placement remains untested. |
| Head movement | Minor corrections needed | Both ±45° turns work; scarf/hood transition needs weights/clearance refinement. |

Ratings describe the path to usable gameplay motions, not whether an absent clip can play today. Independent multi-finger articulation is **not supported by the supplied skeleton**. Fixed hand poses remain possible without a full rebuild.

## E. Export verification

Selected only the character mesh and existing armature, exported GLB to this inspection directory, then imported into a fresh background scene. No source file was overwritten. Both the first failed-timing test and corrected test are retained for review.

The initial default 24 fps sampled export preserved geometry and rig data but truncated fractional endpoints (Arise to frame 43, Running to 15, Walking to 24). Normalized-phase pose errors reached approximately 0.0637–0.1363 source units. **That default export is not a verified animation deliverable.** See `export_verification.json` and `roundtrip_rigged.glb`.

In a separate disposable export test, rescaled key times from the import's 24 fps frame coordinates to a 30 fps timeline and snapped only near-integer floating-point frame coordinates. This preserves original seconds and matches the source key cadence. No original actions or source files were changed. `roundtrip_rigged_timing_fixed.glb` is the corrected test artifact.

| Preserved property | Corrected round-trip result |
| --- | --- |
| Triangles | 64,091 before and after |
| Exported/imported vertices | 50,323 → 50,422; exporter splits attributes, so counts alone are not topology loss |
| Rest surface nearest-position error | ≤0.00000674 source units |
| UV map | `UVMap`; loop-order UV comparison difference 0 |
| Material | `BPY_PBRSource` retained; gray PBR and normal map retained |
| Embedded normal image | 2048²; decoded float-pixel SHA-256 identical |
| Hierarchy / bone names | All 28 names and parent relationships preserved |
| Joint heads / rest matrices | Maximum head error 0.00000302 units; matrix element difference <0.000014 |
| Weights | Maximum compared influence difference <0.00000018 |
| Actions | Arise, Running, Walking all retained |

Weight and deformed-surface comparison maps nearest rest positions because exported vertex order changes. Coincident source seam vertices have matching weights, making those ambiguities benign for skinning comparison. This is sampled numerical preservation, not a game-engine import test.

| Clip | Source duration | Corrected duration | Maximum vertex error at five normalized time samples |
| --- | --- | --- | --- |
{exportrows}

The corrected reimport passes the measured preservation checks, with sampled deformed-vertex errors below 0.000017 source units. No engine scene, code or character registration was modified.

## F. Required corrections, in priority order

1. **Before any production export:** use a timeline/export setup that preserves full clip endpoints; the 30 fps disposable test demonstrates a working path. Exclude Blender display helpers from export.
2. **Before dagger attacks:** choose fixed-grip hands or add necessary finger/thumb controls; test both actual daggers and wrist attachments. Correct shoulder plate weighting and arm clearance at intended attack angles.
3. **Before deep crouch / exaggerated leg motion:** clean up waist-panel and cape weights/clearance; consider minimal clothing controls or simplified moving panels. Refine kneecap rigidity and knee transitions. This is the largest demonstrated deformation task.
4. **Before polished head/torso motion:** refine scarf/hood and waist weighting; inspect gaps under final normal-mapped shading.
5. **Before game integration:** author/choose missing idle, attack, hit, defeat and crouch clips; define in-place versus root-motion behavior; validate foot contacts and transitions. Address the missing separate ground root only if the pipeline needs one.
6. **Before performance approval:** evaluate the 64k-triangle mesh at actual tactical zoom and expected unit counts. Optimize on a future approved derivative if needed. Add dark-fantasy color/roughness treatment; only the normal map is supplied.
7. **Optional after gameplay review:** cosmetic face/glove cleanup, better cloth secondary motion and additional LODs. Rebuild topology only in proven problem regions if weight edits cannot solve them.

Do not replace Meshy's skeleton with the MPFB skeleton as a first step. Do not globally weld every coincident vertex or regenerate the entire rig just because the imported mesh has many seam components.

## G. Final verdict

**Major rigging corrections required** for the entire requested gameplay set, chiefly independent gripping hands and reliable moving cloth/armor under large joint angles. **The basic rig should be reused.** Walking/running need targeted correction and engine validation rather than a new skeleton. The data does not justify blanket rig regeneration, and it does not support claiming that all manual rigging work is finished.

## H. Smallest practical next step

On a new derivative, retain `target_character` and the existing walk/run clips. Establish the verified 30 fps export path, make one fixed dual-dagger grip per hand, then correct shoulder and waist-panel weights only where the intended walk and first attack reveal problems. Add simple wrist weapon attachments and test a single walk-to-attack transition at the real tactical camera. Defer elaborate fingers and cloth simulation unless that test demonstrates they are needed. Complete crouching and ground animations as a separate deformation pass.

Inspection stops here. No production corrections, new gameplay animation library, optimization, or game changes were performed.

## Evidence and reusable inspection files

- [Static test overview](static_overview.jpg), [clip sample overview](clips_overview.jpg).
- [Rest front](rest_front.png), [side](rest_side.png), [three-quarter](rest_three_quarter.png).
- [Skeleton front overlay](skeleton_overlay_front.png), [side overlay](skeleton_overlay_side.png).
- [Arms raised detail](arms_raised_detail_three_quarter.png), [elbows bent](elbows_bent_three_quarter.png), [knees bent](knees_bent_three_quarter.png), [crouch detail](crouch_detail_three_quarter.png), [crouch side](crouch_side.png), [head-turn detail](head_left_detail_three_quarter.png).
- [Walking preview](Walking_sampled_preview.gif), [Running preview](Running_sampled_preview.gif), [Arise preview](Arise_sampled_preview.gif).
- `imported_working_copy.blend` retains the imported rig/actions. `static_test_scene.blend` is disposable evidence infrastructure with the posed tests reset. Temporary test rotations did not become a permanent animation library.
- `roundtrip_rigged_timing_fixed.glb` and `roundtrip_reimported_timing_fixed.blend` contain the successful export test, not a production-ready game character.
- Raw inventories and diagnostics: `glb_source_inventory.json`, `rig_inventory.json`, `articulation_measurements.json`, `clip_measurements.json`, both `export_verification*.json`, `helper_objects.json`, `source_integrity_verified.json`.
'''
(OUT/'rigging_inspection_report.md').write_text(report,encoding='utf-8')
print('REPORT_COMPLETE',len(before),'protected files unchanged; report, overlays and sampled previews saved.')
