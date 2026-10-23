import bpy, bmesh, json, math, hashlib, collections, time
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin')
out=root/'inspection_full_shadowblade'
out.mkdir(exist_ok=True)
source=root/'orignal_models/Meshy_AI_crimson_shadowblade_1021021027_generate.glb'
protected=list((root/'orignal_models').glob('*'))+[root/'base/assassin_base.blend']
manifest={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.is_file()}
# Reuse the established read-only geometry diagnostics, without its batch driver.
helper=(Path(r'D:\SoftwareEng\Game\tools\inspect_assassin_originals.py').read_text())
exec(helper[helper.index('def bounds('):helper.index('def render_views(')])
objects=list(bpy.context.scene.objects)
result={'source':str(source),'sha256':manifest[str(source)],'bounds':bounds(objects),'unit_scale':bpy.context.scene.unit_settings.scale_length,'meshes':[]}
for o in objects:
    if o.type!='MESH':continue
    d=inspect_mesh(o)
    bm=bmesh.new();bm.from_mesh(o.data)
    d['edges']=len(bm.edges)
    d['non_manifold_edges']=sum(not e.is_manifold for e in bm.edges)
    bm.free()
    d['smooth_faces']=sum(p.use_smooth for p in o.data.polygons)
    result['meshes'].append(d)
result['armatures']=[{'name':o.name,'bones':len(o.data.bones)} for o in objects if o.type=='ARMATURE']
result['actions']=[a.name for a in bpy.data.actions]
result['materials']=[{'name':m.name,'nodes':[{'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes] if m.use_nodes else [],'blend':str(getattr(m,'surface_render_method',None))} for m in set(mat for o in objects if o.type=='MESH' for mat in o.data.materials if mat)]
result['images']=[{'name':im.name,'size':list(im.size),'channels':im.channels,'packed':bool(im.packed_file),'source':im.source,'filepath':im.filepath} for im in bpy.data.images if im.type!='RENDER_RESULT']
(out/'geometry.json').write_text(json.dumps(result,indent=2))
(out/'integrity_before.json').write_text(json.dumps(manifest,indent=2))
print('INSPECTION_COMPLETE',[(d['vertices'],d['edges'],d['faces'],d['triangles'],d['island_count'],d['self_intersection_pairs']) for d in result['meshes']])
