import json,hashlib,struct,re
from pathlib import Path
from PIL import Image
import numpy as np
BASE=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\Full_model\inspection');OUT=BASE/'assassin_tpose';source=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\orignal_models\assassin_tpose.blend')
def read(n):return json.loads((OUT/n).read_text())
j=read('inventory.json');m=j['meshes'][0];t=read('test_results.json');e=read('export_verification.json');r=next(r for r in j['rigs'] if r['name'] in m['armature_targets']);g=json.loads((BASE/'guardian/inventory.json').read_text())['rigs'][0]
aa={b['name']:b for b in r['bones']};gg={b['name']:b for b in g['bones']}
comparison={'bone_names_and_hierarchy_equal':{n:b['parent'] for n,b in aa.items()}=={n:b['parent'] for n,b in gg.items()},'maximum_world_joint_head_difference':max(float(np.linalg.norm(np.array(b['head_world'])-gg[n]['head_world'])) for n,b in aa.items()),'maximum_rest_matrix_element_difference':max(float(np.max(np.abs(np.array(b['matrix_local'])-gg[n]['matrix_local']))) for n,b in aa.items()),'animation_transfer_performed':False}
(OUT/'guardian_rig_comparison.json').write_text(json.dumps(comparison,indent=2))
before=hashlib.sha256((OUT/'source_working_copy.blend').read_bytes()).hexdigest();after=hashlib.sha256(source.read_bytes()).hexdigest();assert before==after
(OUT/'source_integrity_verified.json').write_text(json.dumps({'source':str(source),'working_copy_initial_sha256':before,'original_after_sha256':after,'original_unchanged':before==after},indent=2))
f=(OUT/'roundtrip.glb').open('rb');f.read(12);n,k=struct.unpack('<II',f.read(8));glb=json.loads(f.read(n));f.close()
summary={k:len(glb.get(k,[])) for k in ['scenes','meshes','skins','animations','materials','images']};summary['joints_per_skin']=[len(s['joints']) for s in glb.get('skins',[])];summary['clip_names']=[a['name'] for a in glb.get('animations',[])];assert summary['meshes']==1 and summary['skins']==1 and summary['animations']==2 and summary['joints_per_skin']==[28]
(OUT/'export_container_inventory.json').write_text(json.dumps(summary,indent=2))
for view in ['front','side']:
    body=np.array(Image.open(OUT/f'rest_{view}.png').convert('RGB'));bones=np.array(Image.open(OUT/f'skeleton_lines_{view}.png').convert('RGB'));mask=(bones[:,:,0]>1.35*bones[:,:,1])&(bones[:,:,0]>1.35*bones[:,:,2])&(bones[:,:,0]>75);body[mask]=(255,80,35);Image.fromarray(body).save(OUT/f'skeleton_overlay_{view}.png')
for name,clip in t['clips'].items():
    frames=[Image.open(OUT/f'clip_{name}_{i:02}_three_quarter.png').convert('RGB') for i in range(13)];duration=max(40,round(clip['duration']/12*1000));label=re.sub(r'(\.\d{3})+$','',name);frames[0].save(OUT/f'{label}_sampled_preview.gif',save_all=True,append_images=frames[1:],duration=duration,loop=0)
rows='\n'.join(f"| {n.replace('_',' ')} | {v['vertices_moved_over_1e_5']:,} | {v['edge_ratio_max']:.2f}× | {v['stretch_edges_gt_1_5']:,} |" for n,v in t['static'].items() if n!='rest')
report=f'''# assassin_tpose.blend — readiness check

**Usable for a walking/running prototype. Not yet approved as a finished combat character.** This file supplies the working skeleton and skinning absent from the earlier `assassin.blend`. Keep the bound rig; the current evidence does not justify rig regeneration.

Checked October 21, 2026 through Blender MCP, Blender 5.2.2 LTS. Source: `{source}`. To preserve the live project and original file, copied the file into this inspection directory, appended only its main `Scene` for tests, and saved evidence separately. The source checksum still matches the copy made before testing. No original bones, mesh, weights, actions or game code were changed.

## Confirmed contents

- One character mesh: **140,240 vertices, 195,786 triangles**, all triangular faces. One UV map, one gray PBR material, one packed 2048² normal map. No painted color texture.
- Two 28-bone armature objects in the source main scene: `target_character.005` and `target_character.006`. The mesh is parented to and its Armature modifier targets **`target_character.006`**. The other rig does not deform this mesh through that modifier.
- All vertices weighted; totals approximately 0.99999986–1.00000013. Zero unweighted vertices or totals outside 1±0.0001. Maximum four influences per vertex: 2,557 have one, 40,787 two, 35,548 three, 61,348 four.
- The bound rig has a Hips root, torso/head, arms/hands, legs/feet/toes. One terminal `HandMiddle4` per hand; no independent finger/thumb chains or clothing bones.
- Main-scene saved actions include walk/run pairs for each rig. Tested only the pair attached to the mesh's bound rig. Inspector-appended action/object names receive numeric suffixes.
- The saved file contains **14 scenes**, including earlier inspection/reimport scenes, which contributes to its approximately 107 MiB size. It is not a clean single-character delivery project. Export the intended scene/mesh/bound armature explicitly; do not export the entire file indiscriminately.

Raw split topology has 3,924 indexed islands, {m['boundary_edges']:,} boundary edges and {m['non_manifold_edges']:,} non-manifold edges, with {m['degenerate_faces']} very small/degenerate face. Many splits are attribute seams; coincident-position vertices have matching skin weights. These raw counts alone do not demonstrate broken skinning. Local openings/overlaps still need production review. No cleanup was applied.

## Actual movement tests

Every pose was independently reset and actual evaluated mesh displacement was measured and rendered. Tested both arms overhead/forward, elbows at 90°, wrist twist, head left/right, torso forward/sideways, each thigh forward, both knees at 90°, ankles, and a compound crouch. The crouch is an articulation stress test rather than an authored foot-planted IK animation. Isolated knee poses intentionally keep the pelvis fixed.

The mesh follows the bound rig in every tested movement. There is no global detachment or failed skin binding. Elbows and wrists remain broadly usable at inspection size. Larger shoulder rotations visibly distort plate/sleeve transitions; head turns strain scarf/hood transitions. High thigh lifts drag waist cloth, while deep knee/crouch poses compress and stretch cloth and armor transitions. These need targeted weights/clearance work for polished action poses. Direct triangle collision certification and in-engine testing were not performed.

| Test | Vertices moved >1e-5 units | Maximum edge-length ratio | Edges stretched >1.5× |
| --- | --- | --- | --- |
{rows}

Ratios indicate local strain, not an automatic pass/fail or proof of clipping. Workbench evidence shows geometry; it does not render the normal-map detail. See [movement overview](movement_overview.jpg), [raised-arm detail](arms_overhead_detail_three_quarter.png), [crouch detail](crouch_detail_three_quarter.png), and [skeleton overlay](skeleton_overlay_front.png).

## Existing animation tests

The bound rig's **Walking and Running** clips were each evaluated at 13 evenly spaced times. They visibly animate the whole character coherently and look usable for a prototype at the inspection scale. End poses match within about 0.0000013 units, and net horizontal Hips motion is essentially zero: they are in-place, loop-compatible clips. Smooth endpoint velocities, foot slip and game transitions remain untested.

Walking is approximately 1.0333 seconds; Running 0.6333 seconds. Source scene is 24 fps with fractional clip frame endpoints. No idle, dagger-attack, hit, defeat or dedicated crouch clip on the bound rig was identified. Finger articulation and weapon grips remain untested beyond the supplied hand controls; independent finger posing is not supported by this skeleton.

Evidence: [animation samples](animation_overview.jpg), [Walking sampled preview](Walking_sampled_preview.gif), [Running sampled preview](Running_sampled_preview.gif).

## Export validation

Exported only this character mesh and bound skeleton from the intended scene. The verified test GLB contains **one mesh, one skin with 28 joints, two clips, one material and one image**, excluding the spare rig and unrelated scenes.

Triangle count is preserved. Maximum nearest rest-surface error is {e['max_nearest_rest_position_error']:.9f} units; maximum weight difference is {e['max_weight_error']:.9f}; hierarchy matches, UV loop comparison is exact, and the normal image's decoded pixel checksum is unchanged. Additional output vertices are exporter attribute splits, not extra triangles. Material/object names receive import suffixes.

For the disposable export only, preserved original seconds on a 30 fps timeline and restored test source key coordinates afterward. This avoids fractional-endpoint truncation. Reimported Walking/Running durations match the originals; the maximum evaluated vertex discrepancy over five normalized time samples is below **0.0000041 units**. This is a Blender round trip, not an engine import benchmark.

[Verified test GLB](roundtrip.glb) is suitable as an inspection/prototype artifact; it is not a final production character. Its clip names retain inspection numeric suffixes: `{summary['clip_names']}`. See `export_verification.json` and `export_container_inventory.json` for exact measurements.

## Compatibility with guardian

The bound assassin rig and previously inspected guardian have identical bone names and parent relationships, both 28 bones. Their rest transforms differ: maximum joint-head separation is approximately **{comparison['maximum_world_joint_head_difference']:.4f} units**, and rest matrix elements are not identical. A shared humanoid animation system is plausible, but identical names do not establish safe direct action assignment. No clip was transferred between the two in this check. Use rest-pose-aware retargeting or separately fitted clips unless a future direct-sharing test proves acceptable deformation.

## What remains before final use

1. Create a clean delivery derivative containing only the intended mesh, bound rig and intended clips; preserve this original. Use scene/selection export and restrict exported actions. The test GLB demonstrates that isolation works.
2. Correct shoulder plate, scarf/hood, waist cloth and knee deformation for the actual first attack and crouch, rather than rebuilding the skeleton.
3. Establish a dagger grip, either a fixed hand pose/shape or the required extra finger controls. Add/validate the missing gameplay clips and weapon attachments.
4. Author the desired dark-fantasy colors/roughness; only gray material plus normal detail is currently supplied.
5. Benchmark in the game: approximately 196K triangles is far above the earlier 12K–20K target. No decimation was performed and no FPS or ten-unit engine performance claim is made.

**Verdict:** basic rigging is solved sufficiently for locomotion prototyping. Keep this rig. Targeted corrections, clean export configuration, missing gameplay clips and an actual engine test are still needed for final combat use. Original file unchanged; inspection stops here.
'''
(OUT/'readiness_report.md').write_text(report,encoding='utf-8')
print('READY_REPORT_COMPLETE; source unchanged; 1 mesh / 1 skin / 28 joints / 2 clips verified.')
