import bpy,bmesh,json,hashlib,collections,struct,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin')
OUT=ROOT/'inspection_rigged_shadowblade'
OUT.mkdir(exist_ok=True)
SOURCE=next((ROOT/'Full_model').glob('*.glb'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[p for p in (ROOT/'Full_model').rglob('*') if p.is_file()]
protected+=list((ROOT/'orignal_models').glob('*.glb'))+[ROOT/'base/assassin_base.blend']
manifest={str(p):digest(p) for p in protected}
(OUT/'source_integrity_before.json').write_text(json.dumps(manifest,indent=2))
with SOURCE.open('rb') as f:
    f.read(12);n,k=struct.unpack('<II',f.read(8));g=json.loads(f.read(n))
(OUT/'glb_source_inventory.json').write_text(json.dumps({k:g.get(k,[]) for k in ['asset','meshes','materials','textures','images','skins','nodes','animations']},indent=2))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
scene=bpy.context.scene
rigs=[o for o in scene.objects if o.type=='ARMATURE']
meshes=[o for o in scene.objects if o.type=='MESH']
def box(o):
    pts=[o.matrix_world@Vector(p) for p in o.bound_box]
    return {'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]}
inventory={'source':str(SOURCE),'meshes':[],'rigs':[],'actions':[]}
for o in meshes:
    m=o.data;bm=bmesh.new();bm.from_mesh(m)
    unseen=set(bm.verts);islands=[]
    while unseen:
        todo=[unseen.pop()];count=0
        while todo:
            v=todo.pop();count+=1
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in unseen:unseen.remove(w);todo.append(w)
        islands.append(count)
    deform={b.name for r in rigs for b in r.data.bones if b.use_deform}
    groups={vg.index:vg.name for vg in o.vertex_groups}
    weights=[];totals=[];unweighted=[];influences=collections.Counter();group_stats=collections.defaultdict(list)
    for v in m.vertices:
        ws=[w for w in v.groups if groups[w.group] in deform and w.weight>1e-6]
        influences[len(ws)]+=1;totals.append(sum(w.weight for w in ws))
        if not ws:unweighted.append(v.index)
        for w in ws:group_stats[groups[w.group]].append((v.index,w.weight))
    inventory['meshes'].append({'name':o.name,'vertices':len(m.vertices),'edges':len(m.edges),'faces':len(m.polygons),'triangles':sum(len(p.vertices)-2 for p in m.polygons),'polygon_sides':dict(collections.Counter(len(p.vertices) for p in m.polygons)),'island_sizes':sorted(islands,reverse=True),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'inconsistent_winding_edges':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),'exact_duplicate_vertices':sum(c-1 for c in collections.Counter(tuple(v.co) for v in m.vertices).values()),'duplicate_index_faces':sum(c-1 for c in collections.Counter(tuple(sorted(p.vertices)) for p in m.polygons).values()),'uvs':[{'name':u.name,'loops':len(u.data)} for u in m.uv_layers],'materials':[m.name if m else None for m in m.materials],'material_faces':dict(collections.Counter(p.material_index for p in m.polygons)),'parent':o.parent.name if o.parent else None,'modifiers':[{'name':x.name,'type':x.type,'target':x.object.name if x.type=='ARMATURE' and x.object else None} for x in o.modifiers],'vertex_groups':groups,'unweighted_count':len(unweighted),'influence_histogram':dict(influences),'weight_sum_min':min(totals),'weight_sum_max':max(totals),'unnormalized_gt_1e_4':sum(abs(t-1)>1e-4 for t in totals),'group_stats':{k:{'vertices':len(v),'maximum_weight':max(w for i,w in v)} for k,v in group_stats.items()},'bounds':box(o)})
    bm.free()
for r in rigs:
    inventory['rigs'].append({'name':r.name,'matrix_world':[list(row) for row in r.matrix_world],'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'head_world':list(r.matrix_world@b.head_local),'tail_world':list(r.matrix_world@b.tail_local),'matrix_local':[list(row) for row in b.matrix_local],'deform':b.use_deform} for b in r.data.bones],'active_action':r.animation_data.action.name if r.animation_data and r.animation_data.action else None,'nla_tracks':[{'name':t.name,'strips':[{'name':s.name,'action':s.action.name if s.action else None,'start':s.frame_start,'end':s.frame_end} for s in t.strips]} for t in r.animation_data.nla_tracks] if r.animation_data else []})
inventory['actions']=[{'name':a.name,'frames':list(a.frame_range),'slots':[s.identifier for s in a.slots]} for a in bpy.data.actions]
inventory['images']=[{'name':im.name,'size':list(im.size),'packed':bool(im.packed_file),'source':im.source,'filepath':im.filepath} for im in bpy.data.images if im.source!='VIEWER' and im.type!='RENDER_RESULT']
inventory['materials']=[{'name':m.name,'nodes':[{'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes] if m.use_nodes else []} for m in bpy.data.materials]
(OUT/'rig_inventory.json').write_text(json.dumps(inventory,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'imported_working_copy.blend'))
print('INVENTORY_COMPLETE',[(m['name'],m['vertices'],m['triangles']) for m in inventory['meshes']],[(r['name'],len(r['bones'])) for r in inventory['rigs']],len(inventory['actions']),flush=True)
