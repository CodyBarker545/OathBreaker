import bpy,json,math,hashlib,collections,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
ROOT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin');OUT=ROOT/'inspection_rigged_shadowblade'
timing_fix='--timing-fix' in sys.argv
suffix='_timing_fixed' if timing_fix else ''
bpy.ops.wm.open_mainfile(filepath=str(OUT/'imported_working_copy.blend'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');obj=next(o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
rig.animation_data_clear()
def neutral(r):
    r.animation_data_clear()
    for b in r.pose.bones:b.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
def snapshot(r,o):
    neutral(r);m=o.data
    return {'vertices':len(m.vertices),'triangles':sum(len(p.vertices)-2 for p in m.polygons),'uv_layers':[u.name for u in m.uv_layers],'materials':[m.name for m in m.materials],'bones':{b.name:{'parent':b.parent.name if b.parent else None,'head_world':list(r.matrix_world@b.head_local),'matrix_world':[list(row) for row in r.matrix_world@b.matrix_local]} for b in r.data.bones},'uv_values':np.array([list(l.uv) for l in m.uv_layers[0].data]),'coords':np.array([list(o.matrix_world@v.co) for v in m.vertices]),'weights':[{o.vertex_groups[w.group].name:w.weight for w in v.groups if w.weight>1e-7} for v in m.vertices],'images':{im.name:{'size':list(im.size),'pixel_sha256':hashlib.sha256(np.array(im.pixels[:],dtype=np.float32).tobytes()).hexdigest()} for im in bpy.data.images if im.source!='VIEWER' and im.type!='RENDER_RESULT'}}
def evaluated(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.array([list(ev.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return a
def clips(r,o):
    result={}
    for act in list(bpy.data.actions):
        neutral(r);r.animation_data_create();r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
        lo,hi=act.frame_range;frames=[]
        for f in np.linspace(lo,hi,5):
            bpy.context.scene.frame_set(int(f),subframe=float(f-int(f)));bpy.context.view_layer.update();frames.append(evaluated(o))
        result[act.name]={'range':list(act.frame_range),'samples':frames}
    neutral(r);return result
before=snapshot(rig,obj);before_clips=clips(rig,obj)
source_fps=bpy.context.scene.render.fps
if timing_fix:
    # Meshy's original keys are at 30 Hz. Imported into the default 24 Hz scene,
    # these become fractional frame endpoints that Blender's sampler truncates.
    # Rescale keys in this disposable export test only, retaining seconds.
    factor=30/source_fps
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for key in fc.keyframe_points:
                            for co in [key.co,key.handle_left,key.handle_right]:
                                x=co.x*factor;co.x=round(x) if abs(x-round(x))<.001 else x
    bpy.context.scene.render.fps=30
rig.animation_data_create();rig.animation_data.action=bpy.data.actions.get('Walking');rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
props=bpy.ops.export_scene.gltf.get_rna_type().properties
settings={'filepath':str(OUT/('roundtrip_rigged'+suffix+'.glb')),'export_format':'GLB','use_selection':True,'export_animations':True,'export_animation_mode':'ACTIONS','export_frame_range':False,'export_force_sampling':True,'export_optimize_animation_size':False,'export_rest_position_armature':True}
settings={k:v for k,v in settings.items() if k in props}
print('EXPORT_SETTINGS',settings,flush=True);bpy.ops.export_scene.gltf(**settings)
bpy.ops.wm.read_factory_settings(use_empty=True)
if timing_fix:bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(OUT/('roundtrip_rigged'+suffix+'.glb')))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');obj=next(o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
after=snapshot(rig,obj);after_clips=clips(rig,obj)
kd=KDTree(len(after['coords']))
for i,v in enumerate(after['coords']):kd.insert(Vector(v),i)
kd.balance();mapping=[];distances=[]
for v in before['coords']:
    co,i,d=kd.find(Vector(v));mapping.append(i);distances.append(d)
# Prefer identical vertex order when preserved, so UV seams do not make nearest-point mappings ambiguous.
same_order=len(before['coords'])==len(after['coords']) and np.max(np.abs(before['coords']-after['coords']))<1e-5
if same_order:mapping=list(range(len(before['coords'])))
weight_delta=max(abs(w-after['weights'][mapping[i]].get(name,0)) for i,weights in enumerate(before['weights']) for name,w in weights.items())
results={'export_settings':settings,'before':{k:v for k,v in before.items() if k not in ['uv_values','coords','weights']},'after':{k:v for k,v in after.items() if k not in ['uv_values','coords','weights']},'same_vertex_order':bool(same_order),'max_nearest_rest_vertex_distance':max(distances),'max_weight_difference':weight_delta,'bone_hierarchy_equal':{k:v['parent'] for k,v in before['bones'].items()}=={k:v['parent'] for k,v in after['bones'].items()},'max_joint_head_world_difference':max((Vector(b['head_world'])-Vector(after['bones'][n]['head_world'])).length for n,b in before['bones'].items()),'max_rest_bone_matrix_difference':max(abs(float(b['matrix_world'][i][j])-float(after['bones'][n]['matrix_world'][i][j])) for n,b in before['bones'].items() for i in range(4) for j in range(4)),'uv_max_difference_in_loop_order':float(np.max(np.abs(before['uv_values']-after['uv_values']))) if before['uv_values'].shape==after['uv_values'].shape else None,'clips':{}}
for n,c in before_clips.items():
    other=after_clips.get(n)
    results['clips'][n]={'source_frame_range':c['range'],'reimport_frame_range':other['range'] if other else None,'five_normalized_phase_samples_max_vertex_error':max(float(np.linalg.norm(a-b[mapping],axis=1).max()) for a,b in zip(c['samples'],other['samples'])) if other else None}
results['source_fps']=source_fps;results['reimport_fps']=bpy.context.scene.render.fps
(OUT/('export_verification'+suffix+'.json')).write_text(json.dumps(results,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/('roundtrip_reimported'+suffix+'.blend')))
print('ROUNDTRIP_COMPLETE',json.dumps({k:v for k,v in results.items() if k not in ['before','after']}),flush=True)
