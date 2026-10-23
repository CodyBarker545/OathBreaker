import json,hashlib,struct,re
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
BASE=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\native\inspection');OUT=BASE/'native'
def read(n):return json.loads((OUT/n).read_text())
j=read('inventory.json');m=j['meshes'][0];t=read('test_results.json');e=read('export_verification.json');r=j['rigs'][0]
before=json.loads((BASE/'original_integrity_before.json').read_text());after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before};assert before==after
(BASE/'original_integrity_verified.json').write_text(json.dumps({'original_unchanged':True,'before':before,'after':after},indent=2))
f=(OUT/'roundtrip.glb').open('rb');f.read(12);n,k=struct.unpack('<II',f.read(8));g=json.loads(f.read(n));f.close();summary={k:len(g.get(k,[])) for k in ['scenes','meshes','skins','animations','materials','images']};summary['joint_counts']=[len(s['joints']) for s in g['skins']];summary['clip_names']=[a['name'] for a in g['animations']];assert summary['meshes']==1 and summary['skins']==1 and summary['animations']==2 and summary['joint_counts']==[28]
(OUT/'export_container_inventory.json').write_text(json.dumps(summary,indent=2))
for view in ['front','side']:
    a=np.array(Image.open(OUT/f'rest_{view}.png').convert('RGB'));b=np.array(Image.open(OUT/f'skeleton_lines_{view}.png').convert('RGB'));mask=(b[:,:,0]>b[:,:,1]*1.35)&(b[:,:,0]>b[:,:,2]*1.35)&(b[:,:,0]>75);a[mask]=(255,80,35);Image.fromarray(a).save(OUT/f'skeleton_overlay_{view}.png')
canvas=Image.new('RGB',(1200,1440),(25,25,25));draw=ImageDraw.Draw(canvas)
for i,v in enumerate(['front','back','side','three_quarter']):
    canvas.paste(Image.open(OUT/f'rest_{v}.png').convert('RGB'),((i%2)*600,(i//2)*720+20));draw.text(((i%2)*600+10,(i//2)*720+3),v.replace('_',' '),fill='white')
canvas.save(OUT/'views_overview.jpg',quality=92)
for name,c in t['clips'].items():
    frames=[Image.open(OUT/f'clip_{name}_{i:02}_three_quarter.png').convert('RGB') for i in range(13)];label=re.sub(r'(\.\d{3})+$','',name);frames[0].save(OUT/f'{label}_sampled_preview.gif',save_all=True,append_images=frames[1:],duration=max(40,round(c['duration']/12*1000)),loop=0)
comparisons={}
for name,path in [('assassin_tpose',Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\Full_model\inspection\assassin_tpose\inventory.json')),('guardian',Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\Full_model\inspection\guardian\inventory.json'))]:
    other=json.loads(path.read_text());om=other['meshes'][0];rr=next(x for x in other['rigs'] if x['name'] in om['armature_targets']);aa={b['name']:b for b in r['bones']};bb={b['name']:b for b in rr['bones']};same=set(aa)==set(bb)
    comparisons[name]={'same_names_and_parents':same and {n:b['parent'] for n,b in aa.items()}=={n:b['parent'] for n,b in bb.items()},'max_joint_head_difference':max(float(np.linalg.norm(np.array(b['head_world'])-bb[n]['head_world'])) for n,b in aa.items()) if same else None,'max_rest_matrix_element_difference':max(float(np.max(np.abs(np.array(b['matrix_local'])-bb[n]['matrix_local']))) for n,b in aa.items()) if same else None,'clip_transfer_tested':False}
(OUT/'rig_comparisons.json').write_text(json.dumps(comparisons,indent=2))
observations={
'arms_overhead':'Arms and mesh rise; fur shoulder garment stretches and narrows with the arm/torso transition.',
'arms_forward':'Forward reach works; shoulder fur and upper sleeve follow the arms with visible local distortion.',
'elbows_90':'Elbows bend; sleeve/bracer region compresses and pinches locally.',
'wrists':'Hands twist; generally coherent at this scale, no independent finger or grip validation.',
'head_left':'Head turns; long hair follows and its shoulder/back transition distorts.',
'head_right':'Opposite turn works with some asymmetric hair/neck strain.',
'torso_forward':'Body bends; torso cloth and hanging garment transition stretch/compress.',
'torso_side_left':'Side bend works; waist and shoulder garment compress.',
'torso_side_right':'Opposite bend works, with asymmetric garment strain.',
'thigh_left':'Thigh rises; hanging waist cloth is dragged by the leg.',
'thigh_right':'Opposite thigh rises; similarly broad cloth displacement.',
'knees_90':'Knees bend; trouser/boot and lower garment transitions bunch.',
'ankles':'Feet rotate with modest measured strain; production foot-contact checks remain.',
'crouch':'Compound pose works, but waist cloth, fur and leg layers bunch/overlap in the evidence.'}
rows='\n'.join(f"| {n.replace('_',' ')} | {v['vertices_moved_over_1e_5']:,} | {v['edge_ratio_max']:.2f}× | {observations[n]} |" for n,v in t['static'].items() if n!='rest')
clips='\n'.join(f"| {re.sub(r'(\.\d{{3}})+$','',n)} | {c['frames'][0]:.1f}–{c['frames'][1]:.4f} | {c['duration']:.4f} s | {c['first_last_max_vertex_distance']:.8f} | {c['root_horizontal_net_distance']:.8f} |" for n,c in t['clips'].items())
bones='\n'.join(f"- `{b['name']}` ← `{b['parent'] or '(root)'}`" for b in r['bones'])
report=f'''# Native character — technical and animation inspection

**Verdict: usable for locomotion prototyping; corrections required before finished combat use.** The supplied file has a functional 28-bone rig, complete skinning and working walk/run animations. Reuse its rig. Larger poses reveal shoulder-fur, hair and waist-cloth deformation; this is not yet a fully validated combat asset.

Source: `D:/SoftwareEng/Game/SourceAssets/characters/native/native.blend`, {j['bytes']:,} bytes (about 104.1 MiB). Inspected October 21, 2026 through connected Blender MCP, Blender 5.2.2 LTS. Appended the source's main `Scene` into a disposable inspection scene. The original file and user's live scene were preserved; source SHA-256 matches before/after. No optimization, new permanent gameplay animation, weight edits or game changes were performed.

## Mesh and materials

| Property | Measured result |
| --- | --- |
| Character mesh objects | 1 |
| Vertices / edges | {m['vertices']:,} / {m['edges']:,} |
| Faces / triangles | {m['faces']:,} / {m['triangles']:,} |
| Quads / ngons | 0 / 0 |
| Raw indexed islands | {m['island_count']:,} |
| Exact duplicate positions | {m['exact_duplicate_vertices']:,} |
| Boundary / non-manifold edges | {m['boundary_edges']:,} / {m['non_manifold_edges']:,} |
| Degenerate faces (<1e-12 local area) | {m['degenerate_faces']} |
| Inconsistent winding at manifold adjacencies | {m['inconsistent_winding_edges']} |
| UV maps | 1, `UVMap` |
| Materials | 1 gray PBR; metallic 0, roughness 0.5 |
| Textures | One packed 2048² normal map; no external image dependency |
| Neutral height / scene unit scale | {t['rest_bounds_max'][2]-t['rest_bounds_min'][2]:.4f} source units / {j['unit_scale']} |

The final geometry is approximately **197K triangles**, rather than 100K triangles or 100K quads. On an analytical BMesh only, merging coincident positions within 1e-6 gives **98,341 positions, five components and 601 boundary edges**. The diagnostic was discarded, not applied. Many raw splits are UV/normal seams; global welding could damage those attributes or join touching clothing layers. Coincident vertices have matching weights at 1e-6 comparison precision.

Zero inconsistent winding edges does not certify every face outward: the model has open/split layers, and no exhaustive inward-normal or exact intersection certification was performed. Small degenerate faces and remaining boundaries merit local review on a future derivative. No whole-mesh repair is justified solely by the raw split counts.

The long hair, fur shoulder garment, layered waist panels, belts and boots make a recognizable silhouette. Dense sculpted detail should read well in inspection views, though hair/fur add small-scale noise. No actual isometric gameplay-camera comparison was performed. Only gray material and normal detail are supplied; painted dark-fantasy colors and roughness treatment remain art work. UV existence is verified; packing/overlap quality was not exhaustively certified.

The main scene has one character armature. The saved BLEND also contains 14 scenes and older inspection/reimport data. Its large file size is not the same thing as runtime character memory. Export the intended scene and character selection explicitly.

## Skeleton and skin weights

The character mesh is parented to its armature and its Armature modifier targets the same rig. All **155,173** vertices have deform weights, none with more than four influences. Histogram: 1,714 vertices have one influence; 34,277 two; 39,827 three; 79,355 four. Totals span approximately 0.99999985–1.00000013; none differs from one by more than 1e-4. Group names match deform bones.

There are **28 bones**, with a parentless `mixamorig:Hips` pelvis/root. Spine, neck/head, clavicles, arms/hands and legs/feet/toes are present. There is no separate ground root, no independent finger/thumb chains, and no dedicated hair, fur, cloth or pouch controls. Each hand has one terminal `HandMiddle4`; that does not provide individual finger posing.

Joint centers broadly follow anatomy in skeleton views and actual mesh movement. Bone axes vary; tests converted intended world axes to each bone's rest-local axes. The skeleton moves the skin successfully. Numerical weight normalization does not establish rigid garment behavior: fur and cloth follow body weights, and high leg motion drags hanging panels. Targeted painting and possibly minimal garment controls should be considered for the intended attacks/crouch.

### Complete bone hierarchy (bone ← parent)

{bones}

## Actual articulation tests

Reset independently before each pose. Tested arms overhead 80° and forward 90°, elbows 90°, wrist twist 50°, head ±45°, torso forward 30° and sideways ±25°, each thigh forward 50°, knees 90° and ankles 25°. The crouch combines hips −50°, knees +95°, ankles −45°, lowered arms and a temporary pelvis drop of 0.30 units. It is a stress pose, not authored foot-planted IK animation. Isolated knee tests deliberately hold the pelvis fixed.

All non-rest tests produced evaluated vertex displacement. Front, side and three-quarter images confirm mesh movement rather than only bone rotations. Workbench evidence emphasizes geometry and does not show the normal map. Edge-length ratios flag strain; they are not collision tests or automatic quality scores.

| Test | Vertices moved >1e-5 | Maximum edge ratio | Actual observation |
| --- | --- | --- | --- |
{rows}

No global skin detachment or completely failed joint binding was observed. Shoulder fur visibly stretches during overhead reach; hair/neck and waist cloth need clearance/weight refinement. Large thigh and crouch poses expose the strongest distortion (maximum edge ratios about 6–7× in local regions). Apparent overlaps are visual findings, not exact posed collision certification. See [movement overview](native/movement_overview.jpg), [overhead detail](native/arms_overhead_detail_three_quarter.png), [crouch detail](native/crouch_detail_three_quarter.png) and [crouch side](native/crouch_side.png).

## Existing animations

Only Walking and Running are supplied for the main character. Both were separately evaluated at **13 evenly spaced times** with NLA disabled on the disposable test rig. The body/limbs move coherently; cloth follows leg motion and shows local pulling. These are suitable starting clips for a prototype. No idle, attack, damage, defeat or dedicated crouch clip was identified.

| Action (appended name) | Source frames, 24 fps | Duration | Max endpoint vertex mismatch | Net horizontal pelvis travel |
| --- | --- | --- | --- | --- |
{clips}

Both have matching endpoint poses within approximately 1e-6 units and essentially zero net horizontal pelvis displacement, so they are loop-compatible **in-place** clips. Endpoint velocities, foot sliding, continuous playback and blend transitions were not validated in the engine. [Clip samples](native/animation_overview.jpg), [Walking sampled preview](native/Walking_sampled_preview.gif), [Running sampled preview](native/Running_sampled_preview.gif).

## Export and reimport

Exported only the intended mesh and bound armature from the intended scene, then reimported into a new empty scene. The verified GLB contains **one mesh, one skin with 28 joints, two clips, one material and one image**. It excludes unrelated scenes and display helpers.

Triangles are unchanged at 196,681. Exported vertex counts can increase due to attribute splitting. Rest surface nearest-position error is at most **0.00000195 units**; UV loop-order difference is zero. Bone names/parents match; joint heads differ by less than 0.00000126 units, and rest matrix elements by less than 0.0000056. Weight differences are below 0.000000179. The decoded normal-map pixel checksum is identical. Material/object names receive numeric suffixes in the shared inspection session.

For the export test only, preserved clip seconds on a 30 fps timeline to avoid truncating fractional 24 fps endpoints, then restored test source key coordinates. Walking reimports as frames 0–31 at 30 fps (1.0333 s), Running 0–19 (0.6333 s). Five normalized time samples per clip match the source deformed surface within **0.00000357 units**. This verifies a Blender round trip, not game-engine integration.

[Verified test GLB](native/roundtrip.glb) is an inspection/prototype artifact. Its clip names retain numeric suffixes, not production naming. `native/export_verification.json` and `native/export_container_inventory.json` contain exact results.

## Animation sharing and game readiness

The native, guardian and bound assassin_tpose rigs have matching 28-bone names/hierarchies, but their measured rest transforms differ. A reusable humanoid animation library is a plausible goal; direct clip assignment across characters is not proven safe. No animation transfer was performed. Use rest-aware retargeting or explicitly test a proposed direct-sharing path first. See `native/rig_comparisons.json`.

**Ready now:** technical locomotion prototyping with the existing rig and supplied walk/run clips, followed by engine import testing.

**Corrections before polished combat:** shoulder fur/waist cloth/hair deformation, actual weapon or casting hand poses, missing gameplay clips and transitions, final materials, and ground/root conventions. Independent finger animation is not supported by the current rig. Retain the basic skeleton; wholesale rig regeneration is not recommended by these tests.

**Performance remains unmeasured.** Approximately 196.7K triangles is far above the earlier 12K–20K target. Ten instances would represent 1,966,810 character triangles and about 1.55 million source vertex instances per geometry pass, before weapons/shadows or exporter splits. A 28-bone rig with at most four influences is numerically straightforward, but skinning many vertices, shadows and materials still need profiling. The 2K normal map is about 16 MiB as RGBA8 without mips, 21.3 MiB with a full mip chain; repeated instances can share it, and actual engine compression may reduce memory. No FPS claim or polygon reduction was made.

## Evidence and preservation

- [Front/back/side/three-quarter](native/views_overview.jpg).
- [Front skeleton overlay](native/skeleton_overlay_front.png), [side overlay](native/skeleton_overlay_side.png); composited x-ray evidence from actual rest-bone segments.
- [Wireframe](native/wire_front.png), [wire detail](native/wire_detail.png), [movement overview](native/movement_overview.jpg), [animation overview](native/animation_overview.jpg).
- `native/inventory.json`, `native/test_results.json`, `native/export_verification.json`, `native/export_container_inventory.json`, and `native/rig_comparisons.json` hold measurements.
- `native/inspection_working_copy.blend`, `native/reimported_roundtrip.blend`, and `native/roundtrip.glb` are disposable working artifacts.
- `original_integrity_verified.json` confirms the original source unchanged. No game integration or production correction was performed.
'''
(BASE/'inspection_report.md').write_text(report,encoding='utf-8')
print('NATIVE_REPORT_COMPLETE: source unchanged; GLB container and clips verified.')
