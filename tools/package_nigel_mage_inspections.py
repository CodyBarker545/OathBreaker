import json,hashlib,re,struct
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters')
characters=[('axe_warrior','nigel'),('ash_scholar','mage')]
data={}
for folder,name in characters:
    base=ROOT/folder/'inspection';out=base/name
    def read(n):return json.loads((out/n).read_text())
    inv=read('inventory.json');test=read('test_results.json');export=read('export_verification.json');supplement=read('weight_binding_supplement.json');m=inv['meshes'][0]
    source=ROOT/folder/(name+'.blend');manifest=json.loads((base/'original_integrity_before.json').read_text());baseline=next(iter(manifest.values()));digest=hashlib.sha256(source.read_bytes()).hexdigest();assert baseline==digest
    (base/'original_integrity_verified.json').write_text(json.dumps({'source':str(source),'sha256_before':baseline,'sha256_after':digest,'original_unchanged':True},indent=2))
    f=(out/'roundtrip.glb').open('rb');f.read(12);n,k=struct.unpack('<II',f.read(8));g=json.loads(f.read(n));f.close()
    container={k:len(g.get(k,[])) for k in ['scenes','meshes','skins','animations','materials','images']};container['joint_counts']=[len(s['joints']) for s in g.get('skins',[])];container['clip_names']=[a['name'] for a in g.get('animations',[])]
    assert container['meshes']==1 and container['animations']==(2 if name=='nigel' else 0) and container['skins']==(1 if name=='nigel' else 0)
    (out/'export_container_inventory.json').write_text(json.dumps(container,indent=2))
    canvas=Image.new('RGB',(1200,1440),(25,25,25));draw=ImageDraw.Draw(canvas)
    for i,v in enumerate(['front','back','side','three_quarter']):
        canvas.paste(Image.open(out/f'rest_{v}.png').convert('RGB'),((i%2)*600,(i//2)*720+20));draw.text(((i%2)*600+10,(i//2)*720+3),v.replace('_',' '),fill='white')
    canvas.save(out/'views_overview.jpg',quality=92)
    if name=='nigel':
        for v in ['front','side']:
            a=np.array(Image.open(out/f'rest_{v}.png').convert('RGB'));b=np.array(Image.open(out/f'skeleton_lines_{v}.png').convert('RGB'));mask=(b[:,:,0]>b[:,:,1]*1.35)&(b[:,:,0]>b[:,:,2]*1.35)&(b[:,:,0]>75);a[mask]=(255,80,35);Image.fromarray(a).save(out/f'skeleton_overlay_{v}.png')
        clips=list(test['clips']);canvas=Image.new('RGB',(1500,748),(25,25,25));draw=ImageDraw.Draw(canvas)
        for i,(clip,frame) in enumerate((c,f) for c in clips for f in [0,3,6,9,12]):
            im=Image.open(out/f'clip_{clip}_{frame:02}_three_quarter.png').convert('RGB').resize((300,350));canvas.paste(im,((i%5)*300,(i//5)*374+24));draw.text(((i%5)*300+6,(i//5)*374+6),clip+' sample '+str(frame),fill='white')
        canvas.save(out/'animation_overview.jpg',quality=92)
        for clip,details in test['clips'].items():
            frames=[Image.open(out/f'clip_{clip}_{i:02}_three_quarter.png').convert('RGB') for i in range(13)];canonical=re.sub(r'(\.\d{3})+$','',clip);frames[0].save(out/f'{canonical}_sampled_preview.gif',save_all=True,append_images=frames[1:],duration=max(40,round(details['duration']/12*1000)),loop=0)
    data[name]={'folder':folder,'base':base,'out':out,'inv':inv,'test':test,'export':export,'supplement':supplement,'mesh':m,'container':container}

comparison=Image.new('RGB',(1200,760),(25,25,25));draw=ImageDraw.Draw(comparison)
for i,name in enumerate(['nigel','mage']):
    comparison.paste(Image.open(data[name]['out']/'rest_three_quarter.png').convert('RGB'),(i*600,40));draw.text((i*600+12,13),name.title()+(' - working rig' if name=='nigel' else ' - Armature target missing'),fill='white')
comparison.save(data['nigel']['base']/'nigel_mage_comparison.jpg',quality=93)

def common_spec(d):
    m=d['mesh'];s=d['supplement'];t=d['test'];return f'''| Vertices / edges | {m['vertices']:,} / {m['edges']:,} |
| Faces / triangles / quads | {m['faces']:,} / {m['triangles']:,} / {m['quads']} |
| Raw indexed islands | {m['island_count']:,} |
| Raw boundary / non-manifold edges | {m['boundary_edges']:,} / {m['non_manifold_edges']:,} |
| Exact duplicate positions / tiny degenerate faces | {m['exact_duplicate_vertices']:,} / {m['degenerate_faces']} |
| Inconsistent winding at manifold adjacencies | {m['inconsistent_winding_edges']} |
| UV maps / materials / images | 1 / 1 / 1 |
| Normal map | Packed 2048×2048, no external dependency |
| Base color / metallic / roughness | Constant gray (0.8), 0, 0.5 |
| Nonzero weight-group assignments | {s['vertices_with_any_nonzero_group']:,} vertices |
| Weight totals | {s['weight_sum_min']:.9f}–{s['weight_sum_max']:.9f} |
| Weight totals outside 1±0.0001 | {s['weight_totals_outside_1e_4']} |
| Neutral height / scene unit scale | {t['rest_bounds_max'][2]-t['rest_bounds_min'][2]:.4f} source units / {d['inv']['unit_scale']} |'''

nd=data['nigel'];m=nd['mesh'];t=nd['test'];e=nd['export'];r=nd['inv']['rigs'][0]
observations={
'arms_overhead':'Raised-arm stress pose works; shoulder armor/fur and upper-arm shape stretch.',
'arms_forward':'Forward reach works, but broad chest/shoulder attachment distorts.',
'elbows_90':'Elbows bend; local compression and bracer/sleeve pinching remain.',
'wrists':'Hands rotate; bracer/hand transition strains locally, no independent grip validation.',
'head_left':'Head turns; beard/neck/shoulder layers crowd and distort at the transition.',
'head_right':'Opposite turn works with some asymmetric beard/neck compression.',
'torso_forward':'Body bends; belt/armor and hanging cloth compress and stretch.',
'torso_side_left':'Side bend works; waist and shoulder garment distort.',
'torso_side_right':'Opposite side bend works with asymmetric waist strain.',
'thigh_left':'Leg lifts; hanging skirt/waist panels follow and pull across the thigh.',
'thigh_right':'Opposite leg lift produces similar cloth dragging.',
'knees_90':'Knees bend; boot/knee and lower clothing transitions compress.',
'ankles':'Feet rotate; local boot deformation needs foot-roll/contact cleanup.',
'crouch':'Compound crouch works; waist panels and knee/boot layers bunch and overlap visually.'}
movements='\n'.join(f"| {name.replace('_',' ')} | {v['vertices_moved_over_1e_5']:,} | {v['edge_ratio_max']:.2f}× | {observations[name]} |" for name,v in t['static'].items() if name!='rest')
clips='\n'.join(f"| {name} | {c['frames'][0]:.1f}–{c['frames'][1]:.4f} | {c['duration']:.4f} s | {c['first_last_max_vertex_distance']:.8f} | {c['root_horizontal_net_distance']:.8f} |" for name,c in t['clips'].items())
bones='\n'.join(f"- `{b['name']}` ← `{b['parent'] or '(root)'}`" for b in r['bones'])
nr=f'''# Nigel — axe warrior inspection

**Verdict: usable for walking/running prototyping; targeted corrections required before finished axe combat.** The body rig works and survives export. Reuse it. Shoulder/waist/boot deformation, a real axe grip, missing combat clips and an engine test remain.

Source: `D:/SoftwareEng/Game/SourceAssets/characters/axe_warrior/nigel.blend`, {nd['inv']['bytes']:,} bytes. Inspected October 21, 2026 using Blender MCP, Blender 5.2.2 LTS. Appended the source's main `Scene` into a disposable scene; original SHA-256 verified unchanged. No rig, weights, polygon counts, original actions or game code were edited.

## Specifications and geometry

| Property | Measured result |
| --- | --- |
{common_spec(nd)}

All faces are triangles; approximately 197.5K triangles is not a 100K-triangle result. An analysis-only coincidence merge (not applied) yields {m['analytical_weld']['vertices']:,} positions, {len(m['analytical_weld']['island_sizes'])} components and {m['analytical_weld']['boundary_edges']:,} boundary edges. Many raw split vertices/islands are UV or normal seams. Their coincident weights match at 1e-6 precision. Do not globally weld them as a shortcut. Remaining boundaries, tiny faces and overlap candidates require local interpretation; no exact intersection or outward-normal certification was performed.

The muscular silhouette, asymmetric shoulder garment, beard, waist cloth and boots remain recognizable. Rest arms are lowered relative to an exact horizontal T-pose. The material is gray plus normal detail, with no color/roughness texture. No axe is visible in the inspected character views and no weapon/grip attachment was tested. Final isometric readability and performance were not measured in the game.

The BLEND carries many earlier inspection/reimport scenes and unrelated rigs/actions. Its large file size is not a runtime character size. Only the main character's bound rig and clips were used for this assessment.

## Rig and weights

Main character has one **28-bone rig**. Parent and Armature modifier agree on the bound skeleton. All 154,306 vertices have normalized weights, at most four influences, with no group-name mismatch against deform bones. The Hips bone is the root/pelvis; spine, neck/head, clavicles, arms/hands, thighs/calves and feet/toes exist. No separate ground root, clothing bones or full finger/thumb chains are provided. `HandMiddle4` is a single distal hand control, not independent fingers.

Joint positions broadly fit the body and actual mesh movement is confirmed. Bone names alone are not used as proof of animation readiness. Weight normalization is good; garment rigidity/clearance still needs manual attention. Do not replace the whole rig based on these local issues.

### Bone hierarchy (bone ← parent)

{bones}

## Articulation tests

Every test was reset independently. Applied rest-relative rotations: arms 80° upward and 90° forward, elbows 90°, wrists 50° twist, head ±45°, torso forward 30° / sideways ±25°, each thigh 50°, knees 90°, ankles 25°, and a compound crouch. Because the rest arms slope downward, the raised pose is a large upward range test rather than proof of fully vertical, fully extended overhead weapon motion. Crouch includes hips −50°, knees +95°, ankles −45° and a temporary pelvis drop of 0.30 units; it is not an authored foot-planted IK animation.

| Test | Vertices moved >1e-5 | Max edge-length ratio | Observed mesh behavior |
| --- | --- | --- | --- |
{movements}

No global skin detachment or completely failed joint was observed. Large relative poses reveal local distortion, especially the shoulder garment and hanging cloth. Edge ratios indicate strain, not automatic failure or collision certification. Workbench renders emphasize geometry rather than the embedded normal map. [Movement overview](nigel/movement_overview.jpg), [raised-arm detail](nigel/arms_overhead_detail_three_quarter.png), [crouch detail](nigel/crouch_detail_three_quarter.png).

## Existing animations

Only the **Walking and Running pair associated with this bound rig** was tested, each at 13 evenly spaced times. Other saved actions belong to earlier scenes/characters and were not treated as Nigel clips. Both move the character coherently at inspection scale, with clothing pulling/compression still visible. No idle, axe attack, hit, defeat or authored crouch clip is supplied for this rig.

| Appended action name | Source frames at 24 fps | Duration | Max first/last vertex mismatch | Net horizontal pelvis travel |
| --- | --- | --- | --- | --- |
{clips}

Endpoint poses match within about 1.1e-6 units and net horizontal travel is essentially zero: these are loop-compatible in-place clips. Velocity continuity, foot locking, weapon interaction and engine transitions remain untested. [Clip overview](nigel/animation_overview.jpg), [Walking preview](nigel/Walking_sampled_preview.gif), [Running preview](nigel/Running_sampled_preview.gif).

## GLB round trip

The final test export contains exactly one mesh, one skin with 28 joints, two animations, one material and one packed image. Unrelated scenes/actions and display helpers were excluded. Triangle count remains 197,516; additional output vertices are attribute splits. UV loop difference is zero and the decoded normal-map pixel checksum is identical.

Maximum rest position error is {e['max_nearest_rest_position_error']:.9f} units, weight difference {e['max_weight_error']:.9f}, joint-head error {e['max_joint_head_error']:.9f}, and rest-matrix element error below 0.0000049. Hierarchy is preserved. To retain fractional source clip endpoints, exported a disposable 30 fps timeline preserving seconds, then restored test source key coordinates. Five normalized phase samples of reimported clips match within 0.00000272 units.

[Verified test GLB](nigel/roundtrip.glb) is a prototype artifact, not a finished axe-combat character. Clip names contain inspection suffixes. No game-engine import or benchmark was performed.

## Required next work

1. Keep the rig; establish a fixed or articulated axe grip and actual weapon attachment(s), including two-hand coordination if required. Full fingers are absent, so choose the simplest grip method that looks correct at the tactical camera.
2. Correct shoulder, waist-panel, beard/neck and knee/boot deformation for the first real axe attack. Validate a fully extended overhead attack separately.
3. Add/validate missing idle, attack, hit and defeat clips and transitions, then review crouch if required.
4. Author the final color/roughness style, use a clean scene/selection export, and profile the ~197.5K-triangle character with the intended number of units. No FPS claim or optimization was made.

Nigel's names/hierarchy follow the same 28-bone convention as earlier characters; rest-pose/proportion equivalence and shared clip deformation were not tested here. No animation transfer was performed.

## Evidence

[Four views](nigel/views_overview.jpg), [front skeleton overlay](nigel/skeleton_overlay_front.png), [side overlay](nigel/skeleton_overlay_side.png), [wireframe](nigel/wire_front.png), [wire detail](nigel/wire_detail.png). Skeleton overlays are composited x-ray evidence of actual rest bone segments. Raw inventory, movement/clip measurements, binding supplement and export verification are in `nigel/`. `original_integrity_verified.json` confirms the source unchanged. Inspection stops here.
'''
(nd['base']/'inspection_report.md').write_text(nr,encoding='utf-8')

md=data['mage'];m=md['mesh'];s=md['supplement'];e=md['export']
mr=f'''# Mage — ash scholar inspection

**Verdict: not animation-ready as saved. The character has retained weights but no connected skeleton.** Recover the correct matching rig/export before rebuilding anything. Existing normalized groups may allow much of the skinning work to be preserved; that remains to be validated against the correct rest skeleton.

Source: `D:/SoftwareEng/Game/SourceAssets/characters/ash_scholar/mage.blend`, {md['inv']['bytes']:,} bytes. Inspected October 21, 2026 through Blender MCP, Blender 5.2.2 LTS. The file was already open, so a byte-for-byte working copy was read as a library and its main `Scene` appended into a disposable scene. Original SHA-256 matches the copy made before tests. No source rig, weights, geometry or game code was changed.

## Specifications and visual quality

| Property | Measured result |
| --- | --- |
{common_spec(md)}

One complete hooded mage mesh is present in the main scene, in a lowered-arm stance. Shoulder layers, medallion, belt/pouches, long coat panels and boots are recognizable. The material is gray plus a packed 2K normal map, with no painted color or roughness map. The face/hood transition and thin torn coat edges need final visual review. No actual game-camera test was performed.

Every face is triangular. Approximately **191.3K triangles** is above the earlier 12K–20K target; no reduction was performed. An analysis-only coincidence merge (discarded, not applied) yields {m['analytical_weld']['vertices']:,} positions, {len(m['analytical_weld']['island_sizes'])} components and {m['analytical_weld']['boundary_edges']:,} boundary edges. Most large raw split counts are influenced by attribute seams; remaining openings and tiny faces still need local interpretation. Zero inconsistent manifold winding does not certify every normal or prove intersection-free geometry. UV existence is confirmed, not exhaustive overlap/packing quality.

## Critical rig connection failure

The main scene contains **no armature object**. The mesh has no parent, and its existing **Armature modifier has `object=None`**. Thus no skeleton currently drives it. Other rigs and walk/run actions elsewhere in the saved multi-scene file are not evidence that this mage is bound correctly. Arbitrarily assigning one of them could use the wrong proportions, axes or rest transforms.

Crucially, the mesh still has **28 Mixamo-style named vertex groups**, and all **135,337 vertices** have nonzero assignments. Influence histogram: 1,005 vertices have one group; 25,893 two; 30,848 three; 77,591 four. All totals are normalized within 1e-4. Their names cover Hips, spine/head, arms/hands and legs/feet, including single terminal hand controls.

The raw `inventory.json` reports 135,337 vertices without a matching deform-bone influence because there are no connected deform bones to compare against. **That does not mean the vertex group weights are empty.** `weight_binding_supplement.json` records the retained assignments independently. No reweighting or automatic binding was performed.

## Movement and animation tests

Only static front/back/side/three-quarter and wireframe inspection is possible for this character as saved. Arms, elbows, wrists, head, torso, hips, knees, ankles and crouching cannot be tested through its missing skeleton. No deformation success is claimed, and no other character's rig was substituted.

The file contains earlier inspection scenes and unrelated saved Walking/Running actions, but none is associated with a bound mage armature in the main scene. Therefore idle, walk, run, casting/attack, hit, defeat and crouch readiness remain **unverified/not supported in the current configuration**. The retained weights are a useful starting point, not proof that the correct joint placements or deformation are known.

## Export verification — skinning fails as saved

Exported only the mage mesh, then reimported into a clean scene. Geometry remains **191,325 triangles**, nearest rest-position error is zero, UV loop comparison is exact, and gray PBR material plus packed normal-map pixels are retained. Vertex counts can increase due to attribute splits.

However, the exported GLB has **one mesh, zero skins and zero animations**. Bone-named vertex groups are not preserved as usable glTF skinning without a connected skeleton: the reimported mesh has lost those assignments, producing the recorded maximum weight difference of **1.0**. This is a functional skinning failure, not floating-point noise. The unchanged BLEND remains the source containing the retained groups.

`mage/roundtrip.glb` is static export evidence, **not a rigged game deliverable**. `mage/export_verification.json` has empty bone dictionaries; its computed hierarchy-equality boolean merely compares two empty sets and must not be interpreted as successful rig preservation. The verified container inventory explicitly records zero skins/animations.

## Smallest reliable next step

1. Recover/re-export the **matching original mage skeleton** and verify its rest pose, axes, scale and transforms against this mesh. Existing stored weight groups may be reusable; do not automatically overwrite them with new automatic weights.
2. On a future approved derivative, restore the correct parent/modifier target and any required matching bind transforms. Then rerun actual joint tests and walk/run before deciding whether weight corrections or regeneration are needed. This inspection did not make that repair.
3. Test robe/skirt clearance for locomotion, casting, crouch and defeat; full finger controls and garment bones cannot be judged until the actual rig is available.
4. Validate a rigged GLB export, create the missing gameplay clips/material treatment, and benchmark the actual tactical camera and unit count.

No specific FPS is claimed. Both source projects include many prior inspection/reimport scenes, so large BLEND file size does not directly indicate runtime memory. A shared animation system cannot be verified between Nigel and this mage until the mage has its correct connected rig.

## Evidence and preservation

[Front/back/side/three-quarter](mage/views_overview.jpg), [front view](mage/rest_front.png), [side](mage/rest_side.png), [wireframe](mage/wire_front.png), [wire detail](mage/wire_detail.png). No skeleton overlay or skeletal pose evidence is possible for the unbound character. Raw inventory, binding supplement, static test results and export verification are in `mage/`. `original_integrity_verified.json` confirms the source unchanged. Inspection stops here without repairs.
'''
(md['base']/'inspection_report.md').write_text(mr,encoding='utf-8')
for folder,name in characters:
    p=ROOT/folder/'inspection';report=(p/'inspection_report.md').read_text(encoding='utf-8');missing=[x for x in re.findall(r'\]\(([^)]+)\)',report) if not (p/x).exists()];assert not missing,missing
print('REPORTS_COMPLETE: both originals unchanged; Nigel rigged roundtrip verified; Mage missing-binding and static-export weight loss documented.')
