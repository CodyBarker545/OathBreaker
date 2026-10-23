import bpy,bmesh,json,math,collections
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
ROOT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin');OUT=ROOT/'inspection_rigged_shadowblade'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'imported_working_copy.blend'))
scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');obj=next(o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
for o in scene.objects:
    if o.type=='MESH' and o!=obj:o.hide_render=True
rig.animation_data_clear()
def reset():
    for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
def rotate(name,axis,degrees):
    p=rig.pose.bones[name];p.rotation_mode='QUATERNION'
    world_rest=rig.matrix_world.to_quaternion()@p.bone.matrix_local.to_quaternion()
    p.rotation_quaternion=Quaternion(world_rest.inverted()@Vector(axis),math.radians(degrees))
def pose(name):
    reset()
    for side,sign in [('Left',1),('Right',-1)]:
        if name in ['arms_raised','arms_lowered']:rotate('mixamorig:'+side+'Arm',(0,1,0),sign*(-70 if name=='arms_raised' else 65))
        if name=='elbows_bent':rotate('mixamorig:'+side+'ForeArm',(0,0,1),-sign*90)
        if name=='wrists_flex':rotate('mixamorig:'+side+'Hand',(0,0,1),-sign*40)
        if name=='wrists_twist':rotate('mixamorig:'+side+'Hand',(1,0,0),sign*60)
        if name=='terminal_hand_bend':rotate('mixamorig:'+side+'HandMiddle4',(0,0,1),-sign*40)
        if name=='knees_bent':rotate('mixamorig:'+side+'Leg',(1,0,0),90)
        if name=='ankles':rotate('mixamorig:'+side+'Foot',(1,0,0),25)
        if name=='crouch':
            rotate('mixamorig:'+side+'UpLeg',(1,0,0),-55)
            rotate('mixamorig:'+side+'Leg',(1,0,0),100)
            rotate('mixamorig:'+side+'Foot',(1,0,0),-45)
            rotate('mixamorig:'+side+'Arm',(0,1,0),sign*60)
        if name==side.lower()+'_leg_forward':rotate('mixamorig:'+side+'UpLeg',(1,0,0),-50)
        if name==side.lower()+'_leg_backward':rotate('mixamorig:'+side+'UpLeg',(1,0,0),30)
    if name.startswith('head_'):rotate('mixamorig:Head',(0,0,1),45 if name.endswith('left') else -45)
    if name.startswith('torso_'):rotate('mixamorig:Spine2',(0,0,1),35 if name.endswith('left') else -35)
    if name=='crouch':rig.pose.bones['mixamorig:Hips'].location=rig.data.bones['mixamorig:Hips'].matrix_local.to_quaternion().inverted()@Vector((0,0,-.32))
    bpy.context.view_layer.update()
def coords():
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.array([list(ev.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return a
reset();rest=coords();edges=np.array([list(e.vertices) for e in obj.data.edges]);lengths=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);valid=lengths>1e-7
def measurements():
    a=coords();lens=np.linalg.norm(a[edges[:,0]]-a[edges[:,1]],axis=1);ratios=lens[valid]/lengths[valid]
    return {'bounds_min':a.min(axis=0).tolist(),'bounds_max':a.max(axis=0).tolist(),'max_vertex_displacement':float(np.linalg.norm(a-rest,axis=1).max()),'edge_length_ratio_max':float(ratios.max()),'edge_stretch_gt_1_5':int((ratios>1.5).sum()),'edge_compression_lt_0_5':int((ratios<.5).sum()),'edge_ratio_p99':float(np.quantile(ratios,.99))}
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=600;scene.render.resolution_y=700;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.63,.66,.69);scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD'
if not scene.world:scene.world=bpy.data.worlds.new('TestWorld')
scene.world.color=(.045,.045,.045)
cam_data=bpy.data.cameras.new('TestCamera');camera=bpy.data.objects.new('TestCamera',cam_data);scene.collection.objects.link(camera);scene.camera=camera;cam_data.type='ORTHO';cam_data.ortho_scale=2.45;cam_data.clip_end=100
def render(label,view='three_quarter',center=None,scale=None):
    a=coords();target=Vector(center) if center else Vector((0,0,.9));direction={'front':(0,-1,0),'side':(1,0,0),'three_quarter':(3,-6,2)}[view]
    camera.location=target+Vector(direction).normalized()*7;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();cam_data.ortho_scale=scale or 2.45;scene.render.filepath=str(OUT/f'{label}_{view}.png');bpy.ops.render.render(write_still=True)
# Analytical weld only in disposable BMesh; this is not applied to any mesh object.
bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
weld={'vertices':len(bm.verts),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)}
unseen=set(bm.verts);islands=[]
while unseen:
    todo=[unseen.pop()];c=0
    while todo:
        v=todo.pop();c+=1
        for e in v.link_edges:
            w=e.other_vert(v)
            if w in unseen:unseen.remove(w);todo.append(w)
    islands.append(c)
weld['island_sizes']=sorted(islands,reverse=True);bm.free()
# Check whether split vertices at identical positions retain matching skin weights.
groups={g.index:g.name for g in obj.vertex_groups};seams=collections.defaultdict(list)
for v in obj.data.vertices:seams[tuple(v.co)].append(tuple(sorted((groups[w.group],round(w.weight,6)) for w in v.groups if w.weight>1e-6)))
weld['duplicate_position_clusters']=sum(len(v)>1 for v in seams.values());weld['clusters_with_weight_differences_at_1e_6']=sum(len(set(v))>1 for v in seams.values())
tests={}
states=['rest','arms_raised','arms_lowered','elbows_bent','wrists_flex','wrists_twist','terminal_hand_bend','head_left','head_right','torso_left','torso_right','left_leg_forward','left_leg_backward','right_leg_forward','right_leg_backward','knees_bent','ankles','crouch']
for state in states:
    pose(state);tests[state]=measurements()
    for view in ['front','side','three_quarter']:render(state,view)
    if state in ['rest','arms_raised','elbows_bent','terminal_hand_bend','head_left','knees_bent','crouch']:
        center=(0,0,1.35) if state not in ['knees_bent','crouch'] else (0,0,.6)
        render(state+'_detail','three_quarter',center,1.35)
    print('POSE_DONE',state,flush=True)
(OUT/'articulation_measurements.json').write_text(json.dumps({'method':'world-axis rotations converted to bone rest-local axes; independent reset per pose; edge ratios are strain indicators, not collision certification','weld_diagnostic':weld,'static_tests':tests},indent=2))
# Skeleton overlay as renderable line segments in a disposable collection.
pose('rest');overlay=bpy.data.collections.new('EvidenceSkeleton');scene.collection.children.link(overlay)
for b in rig.data.bones:
    curve=bpy.data.curves.new('bone_'+b.name,'CURVE');curve.dimensions='3D';curve.bevel_depth=.004;poly=curve.splines.new('POLY');poly.points.add(1)
    for p,v in zip(poly.points,[b.head_local,b.tail_local]):p.co=tuple(rig.matrix_world@v)+ (1,)
    ob=bpy.data.objects.new(curve.name,curve);overlay.objects.link(ob);ob.color=(1,.12,.04,1);ob.show_in_front=True
obj.hide_render=True
render('skeleton','front');render('skeleton','side');obj.hide_render=False
overlay.hide_render=True
# Full-range clip sampling independent of NLA, preserving each original action.
clip_results={};rig.animation_data_create()
for action in list(bpy.data.actions):
    reset();rig.animation_data.action=action
    rig.animation_data.action_slot=action.slots[0]
    lo,hi=action.frame_range;results=[]
    for i,frame in enumerate(np.linspace(lo,hi,13)):
        scene.frame_set(int(frame),subframe=float(frame-int(frame)));bpy.context.view_layer.update();results.append({'frame':float(frame),**measurements()})
        render('clip_'+action.name+'_'+str(i).zfill(2),'three_quarter')
    clip_results[action.name]=results
    print('CLIP_DONE',action.name,flush=True)
(OUT/'clip_measurements.json').write_text(json.dumps(clip_results,indent=2))
rig.animation_data_clear();reset()
# Save only an explicitly disposable, unposed test scene. Original imported copy retains source animations/NLA.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'static_test_scene.blend'))
print('ALL_TESTS_COMPLETE',flush=True)
