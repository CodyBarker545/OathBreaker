import bpy,json,math,hashlib,re
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
BASE=Path(OUTPUT_BASE) if globals().get('OUTPUT_BASE') else Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\Full_model\inspection');out=BASE/CHARACTER
scene=bpy.data.scenes[json.loads((out/'inventory.json').read_text())['scene']];bpy.context.window.scene=scene
rig=next((m.object for o in scene.objects if o.type=='MESH' for m in o.modifiers if m.type=='ARMATURE' and m.object),None)
obj=next(o for o in scene.objects if o.type=='MESH' and (not rig or any(m.type=='ARMATURE' for m in o.modifiers)))
actions=[bpy.data.actions[n] for n in json.loads((out/'test_results.json').read_text())['clips']]
def reset(r):
    if r:
        r.animation_data_clear()
        for b in r.pose.bones:b.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
def coords(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.array([list(ev.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return a
def snapshot(r,o):
    reset(r);m=o.data
    images={n.image for mat in m.materials if mat and mat.use_nodes for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
    return {'vertices':len(m.vertices),'triangles':sum(len(p.vertices)-2 for p in m.polygons),'uv_names':[u.name for u in m.uv_layers],'uvs':np.array([list(l.uv) for l in m.uv_layers[0].data]) if m.uv_layers else np.empty((0,2)),'materials':[mat.name for mat in m.materials if mat],'coords':np.array([list(o.matrix_world@v.co) for v in m.vertices]),'weights':[{o.vertex_groups[w.group].name:w.weight for w in v.groups if w.weight>1e-7} for v in m.vertices],'bones':{b.name:{'parent':b.parent.name if b.parent else None,'head':list(r.matrix_world@b.head_local),'matrix':[list(row) for row in r.matrix_world@b.matrix_local]} for b in r.data.bones} if r else {},'images':[{'name':im.name,'size':list(im.size),'pixels_sha256':hashlib.sha256(np.array(im.pixels[:],dtype=np.float32).tobytes()).hexdigest()} for im in images]}
def sample(r,o,acts):
    result={}
    for a in acts:
        reset(r);r.animation_data_create();r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];lo,hi=a.frame_range;samples=[]
        for frame in np.linspace(lo,hi,5):
            bpy.context.scene.frame_set(int(frame),subframe=float(frame-int(frame)));bpy.context.view_layer.update();samples.append(coords(o))
        result[re.sub(r'(\.\d{3})+$','',a.name)]={'range':list(a.frame_range),'duration':float(hi-lo)/(scene.render.fps/scene.render.fps_base),'samples':samples}
    reset(r);return result
before=snapshot(rig,obj);source_fps=scene.render.fps/scene.render.fps_base;before_clips=sample(rig,obj,actions) if rig else {}
key_backup=[];old_fps=scene.render.fps;old_base=scene.render.fps_base
if rig and actions:
    for a in actions:
        for layer in a.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for key in fc.keyframe_points:
                            key_backup.append((key,tuple(key.co),tuple(key.handle_left),tuple(key.handle_right)))
                            for co in [key.co,key.handle_left,key.handle_right]:
                                x=co.x*30/source_fps;co.x=round(x) if abs(x-round(x))<.001 else x
    scene.render.fps=30;scene.render.fps_base=1
    rig.animation_data_create();rig.animation_data.action=actions[0];rig.animation_data.action_slot=actions[0].slots[0]
    for a in actions:
        track=rig.animation_data.nla_tracks.new();track.name=a.name
        strip=track.strips.new(a.name,0,a);strip.frame_start=a.frame_range[0];strip.frame_end=a.frame_range[1]
for o in scene.objects:o.select_set(False)
obj.select_set(True)
if rig:rig.select_set(True)
bpy.context.view_layer.objects.active=rig or obj
settings={'filepath':str(out/'roundtrip.glb'),'export_format':'GLB','use_selection':True,'use_active_scene':True,'export_animations':bool(rig and actions),'export_animation_mode':'ACTIONS','export_anim_single_armature':False,'export_frame_range':False,'export_force_sampling':True,'export_optimize_animation_size':False,'export_rest_position_armature':True}
props=bpy.ops.export_scene.gltf.get_rna_type().properties;settings={k:v for k,v in settings.items() if k in props}
try:bpy.ops.export_scene.gltf(**settings)
finally:
    for key,co,hl,hr in key_backup:key.co=co;key.handle_left=hl;key.handle_right=hr
    scene.render.fps=old_fps;scene.render.fps_base=old_base;reset(rig)
target=bpy.data.scenes.new('Reimport_'+CHARACTER);target.render.fps=30 if actions else old_fps;bpy.context.window.scene=target
old_actions=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(out/'roundtrip.glb'))
after_actions=[a for a in bpy.data.actions if a not in old_actions]
r2=next((o for o in target.objects if o.type=='ARMATURE'),None);o2=next(o for o in target.objects if o.type=='MESH' and (not r2 or any(m.type=='ARMATURE' for m in o.modifiers)))
after=snapshot(r2,o2);after_clips=sample(r2,o2,after_actions) if r2 else {}
kd=KDTree(len(after['coords']))
for i,v in enumerate(after['coords']):kd.insert(Vector(v),i)
kd.balance();mapping=[];dist=[]
for v in before['coords']:
    co,i,d=kd.find(Vector(v));mapping.append(i);dist.append(d)
same_order=len(before['coords'])==len(after['coords']) and np.max(np.abs(before['coords']-after['coords']))<1e-5
if same_order:mapping=list(range(len(before['coords'])))
weight_error=max((abs(w-after['weights'][mapping[i]].get(n,0)) for i,ws in enumerate(before['weights']) for n,w in ws.items()),default=0)
seams={}
for i,v in enumerate(before['coords']):seams.setdefault(tuple(v),set()).add(tuple(sorted((n,round(w,6)) for n,w in before['weights'][i].items())))
results={'source_fps':source_fps,'export_fps':30 if actions else old_fps,'export_settings':settings,'before':{k:v for k,v in before.items() if k not in ['uvs','coords','weights']},'after':{k:v for k,v in after.items() if k not in ['uvs','coords','weights']},'same_vertex_order':bool(same_order),'max_nearest_rest_position_error':max(dist),'max_weight_error':weight_error,'split_position_clusters_with_weight_disagreement_at_1e_6':sum(len(v)>1 for v in seams.values()),'uv_max_loop_order_difference':float(np.max(np.abs(before['uvs']-after['uvs']))) if before['uvs'].shape==after['uvs'].shape else None,'hierarchy_equal':{n:b['parent'] for n,b in before['bones'].items()}=={n:b['parent'] for n,b in after['bones'].items()},'max_joint_head_error':max(((Vector(b['head'])-Vector(after['bones'][n]['head'])).length for n,b in before['bones'].items()),default=0),'max_rest_matrix_element_error':max((abs(float(b['matrix'][i][j])-float(after['bones'][n]['matrix'][i][j])) for n,b in before['bones'].items() for i in range(4) for j in range(4)),default=0),'clips':{}}
for n,c in before_clips.items():
    other=after_clips.get(n)
    results['clips'][n]={'source_frames':c['range'],'reimport_frames':other['range'] if other else None,'source_duration':c['duration'],'reimport_duration':(other['range'][1]-other['range'][0])/target.render.fps if other else None,'five_phase_samples_max_deformed_vertex_error':max(float(np.linalg.norm(a-b[mapping],axis=1).max()) for a,b in zip(c['samples'],other['samples'])) if other else None}
(out/'export_verification.json').write_text(json.dumps(results,indent=2))
bpy.data.libraries.write(str(out/'reimported_roundtrip.blend'),{target},fake_user=True,compress=True)
bpy.context.window.scene=scene
print('EXPORT_COMPLETE',CHARACTER,json.dumps({k:v for k,v in results.items() if k not in ['before','after']}),flush=True)
