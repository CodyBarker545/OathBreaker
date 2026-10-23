import json,hashlib,struct,re,shutil
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\ash_scholar');BASE=ROOT/'inspection/retest_20261021_0132';OUT=BASE/'mage'
def read(n):return json.loads((OUT/n).read_text())
j=read('inventory.json');m=j['meshes'][0];t=read('test_results.json');e=read('export_verification.json')
baseline=next(iter(json.loads((BASE/'original_integrity_before.json').read_text()).values()));digest=hashlib.sha256((ROOT/'mage.blend').read_bytes()).hexdigest();assert baseline==digest
(BASE/'original_integrity_verified.json').write_text(json.dumps({'source':str(ROOT/'mage.blend'),'before_sha256':baseline,'after_sha256':digest,'original_unchanged_during_retest':True},indent=2))
f=(OUT/'roundtrip.glb').open('rb');f.read(12);n,k=struct.unpack('<II',f.read(8));glb=json.loads(f.read(n));f.close();container={k:len(glb.get(k,[])) for k in ['scenes','meshes','skins','animations','materials','images']};container['joint_counts']=[len(s['joints']) for s in glb.get('skins',[])];container['clip_names']=[a['name'] for a in glb.get('animations',[])];assert container['meshes']==1 and container['skins']==1 and container['animations']==2 and container['joint_counts']==[28]
(OUT/'export_container_inventory.json').write_text(json.dumps(container,indent=2))
for view in ['front','side']:
    a=np.array(Image.open(OUT/f'rest_{view}.png').convert('RGB'));b=np.array(Image.open(OUT/f'skeleton_lines_{view}.png').convert('RGB'));mask=(b[:,:,0]>b[:,:,1]*1.35)&(b[:,:,0]>b[:,:,2]*1.35)&(b[:,:,0]>75);a[mask]=(255,80,35);Image.fromarray(a).save(OUT/f'skeleton_overlay_{view}.png')
for clip,info in t['clips'].items():
    frames=[Image.open(OUT/f'clip_{clip}_{i:02}_three_quarter.png').convert('RGB') for i in range(13)];name=re.sub(r'(\.\d{3})+$','',clip);frames[0].save(OUT/f'{name}_sampled_preview.gif',save_all=True,append_images=frames[1:],duration=max(40,round(info['duration']/12*1000)),loop=0)
observations={
'arms_overhead':'Arms and mesh rise; shoulder plates/upper sleeve distort. Relative to lowered rest arms, this is an upward range stress test, not full vertical overhead certification.',
'arms_forward':'Forward reach works; shoulder/chest transition stretches.',
'elbows_90':'Both elbows bend with local sleeve/bracer compression.',
'wrists':'Hands twist; minor local bracer/hand strain; finger poses untested.',
'head_left':'Head turns; hood/scarf crowd the neck and shoulder transition.',
'head_right':'Opposite turn works with asymmetric hood/scarf strain.',
'torso_forward':'Body bends; belt, medallion/robe and upper cloth compress.',
'torso_side_left':'Side bend works; waist and robe folds distort.',
'torso_side_right':'Opposite bend works; asymmetric waist/drape strain.',
'thigh_left':'Leg rises; a broad robe panel follows the leg and stretches at the waist.',
'thigh_right':'Opposite leg rises, also dragging robe panels.',
'knees_90':'Knees bend; robe and lower sleeve/boot regions compress around legs.',
'ankles':'Feet rotate; no whole-foot detachment seen.',
'crouch':'Crouch works; long robe bunches and overlaps around the thighs/knees.'}
rows='\n'.join(f"| {name.replace('_',' ')} | {v['vertices_moved_over_1e_5']:,} | {v['edge_ratio_max']:.2f}× | {observations[name]} |" for name,v in t['static'].items() if name!='rest')
report=f'''# Mage retest — skeleton connection repaired

**The previous blocking issue is fixed. Mage is now usable for walk/run prototyping.** The saved main scene has a connected 28-bone rig, and both the mesh and supplied locomotion clips work. Final combat/casting use still needs robe/shoulder cleanup, missing gameplay clips and engine validation.

Retested October 21, 2026 through Blender MCP, Blender 5.2.2 LTS. Source: `D:/SoftwareEng/Game/SourceAssets/characters/ash_scholar/mage.blend`, 340,274,323 bytes. Inspected a fresh byte-for-byte copy of the revised saved file in a disposable scene. The revised source checksum matches before/after this retest. No repairs, reweighting, optimization, new gameplay animations or game changes were made by this retest.

## What changed from the first check

| Check | Previous file | Revised file |
| --- | --- | --- |
| Armature in main character scene | None | One, 28 bones |
| Armature modifier target | None | Correctly targets the character rig |
| Mesh parent | None | Same rig |
| Existing weights | Retained but undriven | All 135,337 vertices driven by deform groups |
| Walk/run attached to this character | Unavailable | Both present and tested |
| Exported GLB skin / clips | 0 / 0 | 1 skin, 28 joints / 2 clips |
| Skin weights after GLB reimport | Lost in static export | Preserved within numerical precision |

The source rig is `target_character.019`; the appended working copy receives a numeric suffix. The mesh has one Armature modifier, and parent/modifier agree. All 28 group names match deform bones. No unweighted vertices; totals span approximately 0.99999985–1.00000013, with none outside 1±0.0001. Influence counts are 1,005 vertices with one influence; 25,893 two; 30,848 three; 77,591 four. None exceeds four.

Geometry remains **135,337 vertices and 191,325 triangles**. UV map, gray PBR material and embedded 2048² normal map are present. No painted color texture is supplied. Counts and sparse static topology diagnostics remain as in the previous inspection; no cleanup or polygon changes were performed.

## Actual articulation tests

Independently reset between poses. Tested rest-relative upward arm rotation 80°, forward reach 90°, elbows 90°, wrist twist 50°, head ±45°, torso forward 30° and sideways ±25°, each thigh forward 50°, knees 90°, ankles 25°, and compound crouch. Crouch includes a temporary 0.30-unit pelvis drop and is not an authored foot-planted IK animation. Isolated knee tests keep the pelvis fixed.

| Test | Vertices moved >1e-5 | Maximum edge ratio | Observed mesh behavior |
| --- | --- | --- | --- |
{rows}

All non-rest tests visibly move the associated skin. No global detachment or failed binding was observed. Large hip/shoulder movements and crouching show robe dragging, compression and local stretching. Edge ratios flag strain, not exact clipping or automatic failure. Exact posed intersections and continuous engine playback were not certified. Workbench evidence emphasizes geometry and does not display the normal map. [Movement overview](mage/movement_overview.jpg), [shoulder detail](mage/arms_overhead_detail_three_quarter.png), [crouch detail](mage/crouch_detail_three_quarter.png), [front skeleton overlay](mage/skeleton_overlay_front.png).

The 28-bone rig has standard body chains, a Hips root and terminal hand controls. It has no separate ground root, dedicated robe chains or independent finger/thumb chains. No staff/weapon grip or casting interaction was tested.

## Walking and running

Tested only the clips attached to this character's bound rig, each at 13 evenly spaced times. Walking is approximately **1.0333 seconds**, Running **0.6333 seconds**. Source scene is 24 fps with fractional clip endpoints. Whole-body motion is coherent at the sampled times, with visible robe motion/pulling around the legs.

Both return to matching endpoint poses within about **0.0000011 units**, with essentially zero net horizontal Hips travel: they are loop-compatible **in-place** clips. Endpoint velocity continuity, foot slip, transitions and actual gameplay camera suitability are untested. No idle, spell/attack, hit, defeat or dedicated crouch action attached to this rig was found.

[Animation samples](mage/animation_overview.jpg), [Walking sampled preview](mage/Walking_sampled_preview.gif), [Running sampled preview](mage/Running_sampled_preview.gif).

## GLB round-trip result: passed measured skinning checks

Exported only this mesh and its bound armature, then reimported into a clean temporary scene. Container inspection confirms **one mesh, one skin with 28 joints, two animations, one material and one image**. Unrelated scenes/rigs/actions are excluded.

- Triangles unchanged at 191,325; extra indexed vertices may result from exporter attribute splits.
- Rest-surface nearest-position discrepancy ≤0.00000179 units; UV loop comparison difference zero.
- Bone names and hierarchy preserved. Joint-head difference <0.00000112 units; rest matrix element difference <0.0000186.
- Maximum weight difference <0.000000179; coincident position seams have matching weights at 1e-6 precision.
- Material and packed normal map retained; decoded texture pixel hash unchanged.
- Walking/Running durations preserved. Five normalized time samples per reimported clip differ from the source deformed mesh by at most **0.0000044 units**.

The disposable export uses a 30 fps timeline with original seconds preserved, avoiding fractional endpoint truncation. Test source key coordinates were restored afterward. No permanent clip library was authored. [Verified rigged test GLB](mage/roundtrip.glb) is an inspection/prototype artifact; names retain appended numeric suffixes. This is Blender export validation, not a game-engine benchmark.

## Remaining work and verdict

**Keep the repaired rig.** It is sufficient to start locomotion integration on a future approved derivative. Rig regeneration is not indicated by these tests.

Before finished gameplay, refine shoulder/hood/robe weighting and clearance for the actual first spell/cast and required crouch; validate hand poses and any staff; add idle, attack/cast, damage and defeat clips and transitions; author final colors/roughness; and test grounded movement and the actual tactical camera. The ~191K-triangle count remains far above the earlier 12K–20K target and needs profiling with the intended unit count. No FPS or finished combat-readiness claim is made.

Raw evidence: `mage/inventory.json`, `mage/test_results.json`, `mage/export_verification.json`, `mage/export_container_inventory.json`. Disposable Blend projects and GLB are in `mage/`; `original_integrity_verified.json` confirms the revised original unchanged during testing. This report supersedes the earlier missing-skeleton verdict for the older saved version.
'''
(BASE/'inspection_report.md').write_text(report,encoding='utf-8')
index=ROOT/'inspection/inspection_report.md';archive=ROOT/'inspection/initial_unbound_inspection_report.md'
if index.exists() and not archive.exists():shutil.copy2(index,archive)
index.write_text('''# Mage — latest inspection

**Retest passed the previous blocking check:** the revised mage now has a bound 28-bone rig, working walk/run clips, and a successful rigged GLB round trip. Usable for locomotion prototyping; robe/shoulder cleanup and finished gameplay testing remain.

[Latest detailed retest and evidence](retest_20261021_0132/inspection_report.md)

[Historical first inspection of the older, unbound version](initial_unbound_inspection_report.md)

The revised original was preserved unchanged during the retest.
''',encoding='utf-8')
print('MAGE_RETEST_REPORT_COMPLETE: repaired binding and rigged roundtrip verified; previous report archived; source unchanged.')
