import bpy,bmesh,json,math
from pathlib import Path
OUT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\outfit')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'assassin_concept_v005.blend'))
rig=bpy.data.objects['Assassin_Skeleton']
parts=[o for o in bpy.data.collections['Outfit_Head'].objects if o.type=='MESH' and o.name.startswith(('Hair_','Hood_'))]
def sample(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=[ev.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return p
bpy.context.view_layer.update();before={o.name:sample(o) for o in parts}
bone=rig.pose.bones['head'];original=bone.matrix_basis.copy()
bone.rotation_mode='XYZ';bone.rotation_euler=(math.radians(12),math.radians(20),math.radians(17));bpy.context.view_layer.update()
transform=rig.matrix_world@bone.matrix@bone.bone.matrix_local.inverted()@rig.matrix_world.inverted()
errors={o.name:max((p-transform@q).length for p,q in zip(sample(o),before[o.name])) for o in parts}
bone.matrix_basis=original;bpy.context.view_layer.update()
assert max(errors.values())<.00001,errors
meshes=[o for c in bpy.data.collections['Character_Assassin'].children if c.name.startswith('Outfit_') for o in c.objects if o.type=='MESH']
zero={};unweighted={}
for obj in meshes:
    bm=bmesh.new();bm.from_mesh(obj.data);n=sum(f.calc_area()<1e-12 for f in bm.faces);bm.free()
    if n:zero[obj.name]=n
    ids={g.index for g in obj.vertex_groups if g.name in rig.data.bones}
    n=sum(not any(w.group in ids and w.weight>0 for w in v.groups) for v in obj.data.vertices)
    if n:unweighted[obj.name]=n
assert not zero and not unweighted
assert all(o.data.uv_layers for o in meshes)
report=json.loads((OUT/'assassin_concept_v005_validation.json').read_text())
report.update(outfit_source_triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),degenerate_outfit_faces=zero,unweighted_outfit_vertices=unweighted,head_turn_relative_fit_max_error_m=max(errors.values()),head_turn_attachment_objects_checked=len(parts),all_outfit_meshes_have_uvs=True)
(OUT/'assassin_concept_v005_validation.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=report['file'])
result={k:report[k] for k in ['file','hood_hair_edge_intersections','hood_hair_minimum_measured_clearance_m','head_turn_relative_fit_max_error_m','head_turn_attachment_objects_checked','original_bones','t_pose_unchanged']}
