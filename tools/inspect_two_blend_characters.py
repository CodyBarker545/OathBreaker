import bpy,bmesh,json,math,hashlib,collections
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters')
BASE=Path(OUTPUT_BASE) if globals().get('OUTPUT_BASE') else ROOT/'hooded_assassin/Full_model/inspection'
BASE.mkdir(exist_ok=True)
sources={'assassin':ROOT/'hooded_assassin/orignal_models/assassin.blend','guardian':ROOT/'gental_guardian/orignal_models/guardian.blend'}
if not (BASE/'original_integrity_before.json').exists():
    protected_sources=[Path(SOURCE_PATH)] if globals().get('SOURCE_PATH') else sources.values()
    (BASE/'original_integrity_before.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected_sources},indent=2))
out=BASE/CHARACTER;out.mkdir(exist_ok=True)
source=Path(SOURCE_PATH) if globals().get('SOURCE_PATH') else sources[CHARACTER]
old_scene=bpy.context.scene
with bpy.data.libraries.load(str(source),link=False) as (src,dst):
    dst.scenes=[SCENE_NAME] if globals().get('SCENE_NAME') else src.scenes;dst.actions=src.actions
scene=dst.scenes[0];scene.name='Inspection_'+CHARACTER
scene['inspection_source']=str(source);scene['inspection_original_scene']=old_scene.name
bpy.context.window.scene=scene
objects=list(scene.objects);rigs=[o for o in objects if o.type=='ARMATURE']
custom_shapes={b.custom_shape for r in rigs for b in r.pose.bones if b.custom_shape}
meshes=[o for o in objects if o.type=='MESH' and o not in custom_shapes]
helper=Path(r'D:\SoftwareEng\Game\tools\inspect_assassin_originals.py').read_text()
exec(helper[helper.index('def bounds('):helper.index('def render_views(')])
inventory={'source':str(source),'bytes':source.stat().st_size,'scene':scene.name,'fps':scene.render.fps/scene.render.fps_base,'unit_scale':scene.unit_settings.scale_length,'original_frame':scene.frame_current,'meshes':[],'rigs':[],'actions':[],'helpers':[{'name':o.name,'type':o.type} for o in objects if o not in meshes and o not in rigs]}
for o in meshes:
    d=inspect_mesh(o);m=o.data;bm=bmesh.new();bm.from_mesh(m)
    d['edges']=len(m.edges);d['non_manifold_edges']=sum(not e.is_manifold for e in bm.edges);bm.free()
    d['parent']=o.parent.name if o.parent else None
    d['armature_targets']=[mod.object.name if mod.object else None for mod in o.modifiers if mod.type=='ARMATURE']
    names={vg.index:vg.name for vg in o.vertex_groups};deform={b.name for r in rigs for b in r.data.bones if b.use_deform}
    totals=[];hist=collections.Counter();unused=[];groups=collections.defaultdict(list)
    for v in m.vertices:
        ws=[w for w in v.groups if names[w.group] in deform and w.weight>1e-6]
        total=sum(w.weight for w in ws);totals.append(total);hist[len(ws)]+=1
        for w in ws:groups[names[w.group]].append((v.index,w.weight))
    d['weights']={'unweighted_vertices':hist[0],'influence_histogram':dict(hist),'min_total':min(totals),'max_total':max(totals),'unnormalized_gt_1e_4':sum(abs(t-1)>1e-4 for t in totals),'groups':{n:{'vertices':len(v),'max_weight':max(w for i,w in v)} for n,v in groups.items()},'group_names_without_matching_deform_bones':[n for n in names.values() if n not in deform]}
    # Analysis-only coincidence merge, never applied to the model.
    bm=bmesh.new();bm.from_mesh(m);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    unseen=set(bm.verts);sizes=[]
    while unseen:
        todo=[unseen.pop()];count=0
        while todo:
            v=todo.pop();count+=1
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in unseen:unseen.remove(w);todo.append(w)
        sizes.append(count)
    d['analytical_weld']={'vertices':len(bm.verts),'island_sizes':sorted(sizes,reverse=True),'boundary_edges':sum(e.is_boundary for e in bm.edges),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges)};bm.free()
    inventory['meshes'].append(d)
for r in rigs:
    inventory['rigs'].append({'name':r.name,'scale':list(r.scale),'matrix_world':[list(row) for row in r.matrix_world],'pose_position':r.data.pose_position,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head_world':list(r.matrix_world@b.head_local),'tail_world':list(r.matrix_world@b.tail_local),'matrix_local':[list(row) for row in b.matrix_local],'deform':b.use_deform} for b in r.data.bones],'active_action':r.animation_data.action.name if r.animation_data and r.animation_data.action else None,'nla':[{'name':t.name,'strips':[{'name':s.name,'action':s.action.name if s.action else None} for s in t.strips]} for t in r.animation_data.nla_tracks] if r.animation_data else []})
for a in dst.actions:
    inventory['actions'].append({'name':a.name,'frames':list(a.frame_range),'duration':(a.frame_range[1]-a.frame_range[0])/inventory['fps'],'slots':[s.identifier for s in a.slots]})
materials={mat for o in meshes for mat in o.data.materials if mat};images=set()
inventory['materials']=[]
for mat in materials:
    item={'name':mat.name,'images':[],'principled':[]}
    if mat.use_nodes:
        for n in mat.node_tree.nodes:
            if n.type=='TEX_IMAGE' and n.image:images.add(n.image);item['images'].append(n.image.name)
            if n.type=='BSDF_PRINCIPLED':item['principled'].append({k:list(n.inputs[k].default_value) if k=='Base Color' else float(n.inputs[k].default_value) for k in ['Base Color','Metallic','Roughness']})
    inventory['materials'].append(item)
inventory['images']=[{'name':im.name,'size':list(im.size),'channels':im.channels,'packed':bool(im.packed_file),'source':im.source,'filepath':im.filepath,'resolved_path':bpy.path.abspath(im.filepath,library=im.library),'has_data':im.has_data} for im in images]
(out/'inventory.json').write_text(json.dumps(inventory,indent=2))
print('INVENTORY',CHARACTER,[(d['name'],d['vertices'],d['faces'],d['triangles'],d['quads'],d['island_count']) for d in inventory['meshes']],[(r['name'],len(r['bones'])) for r in inventory['rigs']],inventory['actions'],flush=True)
