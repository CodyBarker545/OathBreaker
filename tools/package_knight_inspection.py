import json,hashlib,struct,re
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\broken_oath_knight');BASE=ROOT/'inspection';OUT=BASE/'knight'
def read(n):return json.loads((OUT/n).read_text())
j=read('inventory.json');m=j['meshes'][0];t=read('test_results.json');e=read('export_verification.json');h=read('central_helmet_supplement.json')
before=next(iter(json.loads((BASE/'original_integrity_before.json').read_text()).values()));after=hashlib.sha256((ROOT/'knight.blend').read_bytes()).hexdigest();assert before==after
(BASE/'original_integrity_verified.json').write_text(json.dumps({'source':str(ROOT/'knight.blend'),'sha256_before':before,'sha256_after':after,'original_unchanged':True},indent=2))
f=(OUT/'roundtrip.glb').open('rb');f.read(12);n,k=struct.unpack('<II',f.read(8));glb=json.loads(f.read(n));f.close();container={k:len(glb.get(k,[])) for k in ['scenes','meshes','skins','animations','materials','images']};container['joint_counts']=[len(s['joints']) for s in glb.get('skins',[])];container['clip_names']=[a['name'] for a in glb.get('animations',[])];assert container['meshes']==1 and container['skins']==1 and container['animations']==2 and container['joint_counts']==[28]
(OUT/'export_container_inventory.json').write_text(json.dumps(container,indent=2))
for view in ['front','side']:
    a=np.array(Image.open(OUT/f'rest_{view}.png').convert('RGB'));b=np.array(Image.open(OUT/f'skeleton_lines_{view}.png').convert('RGB'));mask=(b[:,:,0]>b[:,:,1]*1.35)&(b[:,:,0]>b[:,:,2]*1.35)&(b[:,:,0]>75);a[mask]=(255,80,35);Image.fromarray(a).save(OUT/f'skeleton_overlay_{view}.png')
canvas=Image.new('RGB',(1200,1440),(25,25,25));draw=ImageDraw.Draw(canvas)
for i,v in enumerate(['front','back','side','three_quarter']):
    canvas.paste(Image.open(OUT/f'rest_{v}.png').convert('RGB'),((i%2)*600,(i//2)*720+20));draw.text(((i%2)*600+10,(i//2)*720+3),v.replace('_',' '),fill='white')
canvas.save(OUT/'views_overview.jpg',quality=93)
for clip,info in t['clips'].items():
    frames=[Image.open(OUT/f'clip_{clip}_{i:02}_three_quarter.png').convert('RGB') for i in range(13)];name=re.sub(r'(\.\d{3})+$','',clip);frames[0].save(OUT/f'{name}_sampled_preview.gif',save_all=True,append_images=frames[1:],duration=max(40,round(info['duration']/12*1000)),loop=0)
notes={
'arms_overhead':'Arms raise and skin follows; large pauldrons/shoulder transitions distort and approach the cathedral section.',
'arms_forward':'Forward reach works; shoulder plates and hanging chains move with the arms rather than independently.',
'elbows_90':'Elbows articulate; armor/bracer transitions compress and pinch.',
'wrists':'Hands twist; gauntlet/hand junction strains locally. Independent finger/grip motion remains untested.',
'head_left':'Cathedral upper section turns and visibly changes shape near its lower/side transitions.',
'head_right':'Opposite turn works, with asymmetric architectural-shell strain.',
'torso_forward':'Torso bends; breastplate/waist layers stretch instead of remaining fully rigid.',
'torso_side_left':'Side bend works; torso armor and waist transitions distort.',
'torso_side_right':'Opposite side bend works with asymmetric armor compression.',
'thigh_left':'Leg rises; tabard/skirt panels follow and pull across the waist/thigh.',
'thigh_right':'Opposite leg rise shows similar panel dragging.',
'knees_90':'Knees bend; greave/kneecap and cloth transitions compress.',
'ankles':'Feet rotate; local boot/greave movement requires authored foot-roll validation.',
'crouch':'Compound pose works; waist cloth and knee/armor layers bunch and overlap in the evidence.'}
rows='\n'.join(f"| {n.replace('_',' ')} | {v['vertices_moved_over_1e_5']:,} | {v['edge_ratio_max']:.2f}× | {notes[n]} |" for n,v in t['static'].items() if n!='rest')
clips='\n'.join(f"| {n} | {c['frames'][0]:.1f}–{c['frames'][1]:.4f} | {c['duration']:.4f} s | {c['first_last_max_vertex_distance']:.8f} | {c['root_horizontal_net_distance']:.8f} |" for n,c in t['clips'].items())
bones='\n'.join(f"- `{b['name']}` ← `{b['parent'] or '(root)'}`" for b in j['rigs'][0]['bones'])
report=f'''# Broken Oath Knight — rigging and animation inspection

**Verdict: usable for locomotion prototyping; armor-weight corrections required for finished gameplay.** The bound skeleton, skin weights and supplied walk/run clips work and survive GLB export. Retain the rig. Its auto weights do not preserve the cathedral-shaped upper armor, pauldrons and other plated regions as fully rigid forms under larger poses.

Source: `D:/SoftwareEng/Game/SourceAssets/characters/broken_oath_knight/knight.blend`, {j['bytes']:,} bytes (about 14.86 MiB). Tested October 21, 2026 through Blender MCP, Blender 5.2.2 LTS. Initial addon-status handshake returned WinError 10053, but scene-info, code execution and visual tools succeeded; tests used MCP. Read a fresh byte-for-byte copy into a disposable scene because the source was open. Original SHA-256 unchanged after testing. No original geometry, rig, weights, actions or game code was altered.

## Model specifications

| Property | Measured result |
| --- | --- |
| Character mesh objects | 1 |
| Vertices / edges | {m['vertices']:,} / {m['edges']:,} |
| Faces / triangles / quads | {m['faces']:,} / {m['triangles']:,} / {m['quads']} |
| Raw indexed islands | {m['island_count']:,} |
| Exact duplicate positions | {m['exact_duplicate_vertices']:,} |
| Raw boundary / non-manifold edges | {m['boundary_edges']:,} / {m['non_manifold_edges']:,} |
| Very small/degenerate faces (<1e-12 local area) | {m['degenerate_faces']} |
| Inconsistent winding at manifold adjacencies | {m['inconsistent_winding_edges']} |
| UV maps / materials / texture images | 1 / 1 / 1 |
| Texture | Packed 2048×2048 normal map; no external dependency |
| Material | Gray PBR, metallic 0, roughness 0.5; no color/roughness texture |
| Neutral height / unit scale | {t['rest_bounds_max'][2]-t['rest_bounds_min'][2]:.4f} source units / {j['unit_scale']} |

All faces are triangles. This is approximately **195.6K triangles**, not a 100K-triangle mesh. Tall spires contribute substantially to the overall height and silhouette. Check gameplay camera framing/selection bounds against this height rather than forcing it to match ordinary human head height.

Many raw duplicate/island/boundary counts reflect split UV/normal attributes. An analytical coincidence merge within 1e-6 units, discarded without modifying the mesh, yields {m['analytical_weld']['vertices']:,} positions, {len(m['analytical_weld']['island_sizes'])} components and {m['analytical_weld']['boundary_edges']:,} boundary edges. Coincident position vertices have matching weights at 1e-6 precision. Do not globally weld clothing and hard-normal seams indiscriminately. Remaining openings/tiny faces deserve local review; no exact intersection or universal outward-normal proof was performed.

The supplied file has one source scene, rather than the many saved inspection scenes seen in some earlier assets. Its `Icosphere` is a bone-display helper, excluded from character counts, weight failures and export. The cathedral facade, large pauldrons, hanging chains, tabard and pointed greaves read clearly in inspection views. They add collision and rigidity requirements. No final isometric camera or engine benchmark was performed.

## Skeleton and skinning

One **28-bone armature** drives the mesh. Mesh parent and Armature modifier agree on the correct target. All **168,974 vertices** have weights; none is unweighted or uses more than four influences. Distribution: 3,142 vertices with one influence, 23,412 with two, 36,899 with three, 105,521 with four. Totals are approximately 0.99999985–1.00000013; none outside 1±0.0001. All vertex-group names match deform bones.

Hips is the parentless root/pelvis. Spine, neck/head, clavicle/arm/hand and leg/foot/toe chains exist. There is no separate ground root, independent finger/thumb chains, or dedicated plate, tabard, chain or pendant bones. The single terminal `HandMiddle4` controls are not a full finger rig. No weapon/grip or attack interaction was tested.

Bone positions broadly match humanoid joint regions and actual skin movement is confirmed. Local axes vary; tests converted intended world axes into each bone's rest-local axes. Numerical normalization is good, but rigidity assignments are not solved simply by normalized weights.

### Specific cathedral-shell check

Head turns visibly alter the upper architectural form. A supplementary **approximate central-upper region**, within 0.25 units of head-joint X and at least 0.20 units above head-joint Z, contains **16,170 vertices**, all predominantly weighted to Head. During ±45° head turns, internal edge ratios range roughly **0.63–1.31**, with 173–206 edges stretching by over 10%. Thus this region does not move as a perfectly rigid shell, even though its dominant bone is Head.

This selection is a geometric envelope, not a manually separated helmet component. A broader upper-height selection includes shoulder/arm parts and cannot be treated as one rigid object. The measurements nevertheless support local rigid-weight cleanup in architecture intended to behave as metal/stone armor. Do not automatically make all upper-body geometry rigid or assign every spire and pauldron to Head: decide which pieces should follow head, torso or shoulders.

## Actual articulation tests

Reset independently between poses. Rest-relative rotations: arms upward 80° / forward 90°, elbows 90°, wrists 50° twist, head ±45°, torso forward 30° / sideways ±25°, each thigh 50°, knees 90°, ankles 25°, plus compound crouch. Upward arm testing is a range stress test, not certification of a fully vertical weapon attack. Crouch uses hips −50°, knees +95°, ankles −45° and a temporary 0.30-unit pelvis drop; it is not a finished foot-planted IK pose. Isolated knee tests keep the pelvis fixed.

| Test | Vertices moved >1e-5 | Maximum edge ratio | Observed mesh behavior |
| --- | --- | --- | --- |
{rows}

Every non-rest test visibly deforms the associated skin. No whole-limb detachment or global binding failure was found. Edge ratios indicate strain, not exact clipping or an automatic quality score. Some armor/panel overlaps are visible; no exact posed collision certification was performed. Workbench evidence emphasizes geometry rather than normal-map detail. [Movement overview](knight/movement_overview.jpg), [raised-arm detail](knight/arms_overhead_detail_three_quarter.png), [head-turn detail](knight/head_left_detail_three_quarter.png), [crouch detail](knight/crouch_detail_three_quarter.png).

## Existing clips

Walking and Running target this bound rig. Each was evaluated separately at **13 evenly spaced times**, with NLA disabled on the disposable test rig. Whole-body motion is coherent at inspection size; plates and cloth still follow auto weights and need review for rigid behavior. No idle, weapon attack, damage, defeat or dedicated crouch clip is supplied.

| Appended action name | Source frames, 24 fps | Duration | Max first/last vertex mismatch | Net horizontal pelvis travel |
| --- | --- | --- | --- | --- |
{clips}

Endpoint positions match within about 0.0000017 units and net horizontal travel is essentially zero: these are loop-compatible **in-place** clips. Endpoint velocity continuity, foot lock, actual game transitions and shadow/weapon interaction remain untested. [Animation samples](knight/animation_overview.jpg), [Walking preview](knight/Walking_sampled_preview.gif), [Running preview](knight/Running_sampled_preview.gif).

## GLB round-trip verification

Exported only the character mesh and bound armature, then reimported into an empty scene. Verified container: **one mesh, one skin with 28 joints, two clips, one material and one image**. Display helpers/camera/light excluded.

- Triangles unchanged at 195,629; exported vertices may split further for attributes.
- Rest surface nearest-position error ≤0.00000250 units; UV loop comparison difference zero.
- Bone names/parents retained; joint-head error <0.00000109 and rest-matrix element difference <0.00000465.
- Maximum weight difference <0.000000179; decoded normal-map pixel checksum identical.
- Walking/Running durations preserved. Five normalized phase samples match the source deformed surface within **0.00000317 units**.

Used a disposable 30 fps export timeline preserving original seconds to avoid fractional 24 fps endpoint truncation, then restored test-source key coordinates. No permanent animation library was authored. [Verified test GLB](knight/roundtrip.glb) is a prototype artifact; clip names retain inspection suffixes. This is Blender round-trip validation, not game-engine integration.

## Required corrections and fastest next step

1. **Major for polished armor:** decide the cathedral/head/torso/shoulder attachment scheme and give intended rigid components consistent weights. Refine lower architectural transitions and pauldron clearance before large attacks/head turns. Keep the basic humanoid skeleton.
2. **Movement cleanup:** correct tabard, waist, knee and greave behavior for the actual first gameplay attack/crouch. Hanging chains have no independent controls; their current arm-following behavior may need a simple control or revised attachment if visually distracting.
3. **Missing gameplay content:** create/choose idle, attack, hit and defeat clips; establish grips/weapon attachments and validate transitions. Independent finger articulation is not supplied by this rig.
4. **Art and engine check:** add the desired color/roughness style, check spire height/camera framing and selection bounds, and benchmark the intended tactical camera/unit count. At 195.6K triangles, ten instances represent about 1.96 million character triangles per geometry pass before shadows/weapons. No FPS claim or polygon reduction was made.

**Conclusion:** locomotion prototype-ready with a reusable rig; not yet a finished combat character because automatic weights deform intended rigid armor. No rig regeneration or source edits were performed.

## Evidence and preservation

[Four views](knight/views_overview.jpg), [front skeleton overlay](knight/skeleton_overlay_front.png), [side overlay](knight/skeleton_overlay_side.png), [wireframe](knight/wire_front.png), [wire detail](knight/wire_detail.png). Skeleton overlays are composited x-ray evidence from actual rest bone segments.

Exact diagnostics: `knight/inventory.json`, `knight/test_results.json`, `knight/helmet_rigidity_supplement.json`, `knight/central_helmet_supplement.json`, `knight/export_verification.json`, `knight/export_container_inventory.json`. Disposable Blend/GLB projects are in `knight/`. `original_integrity_verified.json` confirms the original source unchanged. Inspection stops here.
'''
(BASE/'inspection_report.md').write_text(report,encoding='utf-8')
missing=[v for v in re.findall(r'\]\(([^)]+)\)',report) if not (BASE/v).exists()];assert not missing,missing
print('KNIGHT_REPORT_COMPLETE: source unchanged; 28-joint GLB / 2 clips verified; architectural rigidity findings documented.')
