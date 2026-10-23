import bpy,json,math,collections
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
BASE=Path(OUTPUT_BASE) if globals().get('OUTPUT_BASE') else Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\Full_model\inspection');out=BASE/CHARACTER
scene=bpy.data.scenes[json.loads((out/'inventory.json').read_text())['scene']];bpy.context.window.scene=scene
rig=next((m.object for o in scene.objects if o.type=='MESH' for m in o.modifiers if m.type=='ARMATURE' and m.object),None)
custom_shapes={b.custom_shape for b in rig.pose.bones if b.custom_shape} if rig else set()
meshes=[o for o in scene.objects if o.type=='MESH' and o not in custom_shapes];obj=meshes[0]
for shape in custom_shapes:
    shape.hide_render=True
    if shape.name in bpy.context.view_layer.objects:shape.hide_set(True)
actions=[]
if rig:
    if rig.animation_data:
        if rig.animation_data.action:actions.append(rig.animation_data.action)
        for track in rig.animation_data.nla_tracks:
            for strip in track.strips:
                if strip.action and strip.action not in actions:actions.append(strip.action)
    # Include source actions even if not assigned to an NLA track.
    for item in ([] if CHARACTER in ['assassin_tpose','native','nigel','mage'] else json.loads((out/'inventory.json').read_text())['actions']):
        action=bpy.data.actions.get(item['name'])
        if action and action not in actions:actions.append(action)
    rig.animation_data_clear()
def reset():
    if rig:
        for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
def rotate(suffix,axis,deg):
    pb=rig.pose.bones['mixamorig:'+suffix];pb.rotation_mode='QUATERNION';q=rig.matrix_world.to_quaternion()@pb.bone.matrix_local.to_quaternion();pb.rotation_quaternion=Quaternion(q.inverted()@Vector(axis),math.radians(deg))
def pose(name):
    reset()
    if not rig:return
    for side,sign in [('Left',1),('Right',-1)]:
        if name=='arms_overhead':rotate(side+'Arm',(0,1,0),-sign*80)
        if name=='arms_forward':rotate(side+'Arm',(0,0,1),-sign*90)
        if name=='elbows_90':rotate(side+'ForeArm',(0,0,1),-sign*90)
        if name=='wrists':rotate(side+'Hand',(1,0,0),sign*50)
        if name=='knees_90':rotate(side+'Leg',(1,0,0),90)
        if name=='ankles':rotate(side+'Foot',(1,0,0),25)
        if name=='crouch':
            rotate(side+'UpLeg',(1,0,0),-50);rotate(side+'Leg',(1,0,0),95);rotate(side+'Foot',(1,0,0),-45);rotate(side+'Arm',(0,1,0),sign*55)
    if name=='head_left':rotate('Head',(0,0,1),45)
    if name=='head_right':rotate('Head',(0,0,1),-45)
    if name=='torso_forward':rotate('Spine1',(1,0,0),30)
    if name=='torso_side_left':rotate('Spine1',(0,1,0),-25)
    if name=='torso_side_right':rotate('Spine1',(0,1,0),25)
    if name=='thigh_left':rotate('LeftUpLeg',(1,0,0),-50)
    if name=='thigh_right':rotate('RightUpLeg',(1,0,0),-50)
    if name=='crouch':rig.pose.bones['mixamorig:Hips'].location=rig.data.bones['mixamorig:Hips'].matrix_local.to_quaternion().inverted()@Vector((0,0,-.3))
    bpy.context.view_layer.update()
def coords():
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.array([list(ev.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return a
reset();rest=coords();center=(rest.min(axis=0)+rest.max(axis=0))/2;extent=rest.max(axis=0)-rest.min(axis=0);scale=max(extent[2],extent[0]*700/600)*1.3
edges=np.array([list(e.vertices) for e in obj.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);valid=length>1e-7
def measure():
    a=coords();ratio=np.linalg.norm(a[edges[:,0]]-a[edges[:,1]],axis=1)[valid]/length[valid]
    return {'vertices_moved_over_1e_5':int((np.linalg.norm(a-rest,axis=1)>1e-5).sum()),'max_vertex_displacement':float(np.linalg.norm(a-rest,axis=1).max()),'edge_ratio_max':float(ratio.max()),'stretch_edges_gt_1_5':int((ratio>1.5).sum()),'compression_edges_lt_0_5':int((ratio<.5).sum()),'bounds_min':a.min(axis=0).tolist(),'bounds_max':a.max(axis=0).tolist()}
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=600;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
sh=scene.display.shading;sh.light='STUDIO';sh.color_type='SINGLE';sh.single_color=(.64,.67,.70);sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD'
if not scene.world:scene.world=bpy.data.worlds.new('InspectionWorld_'+CHARACTER)
scene.world.color=(.045,.045,.045)
cd=bpy.data.cameras.new('InspectionCamera_'+CHARACTER);camera=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(camera);scene.camera=camera;cd.type='ORTHO';cd.clip_end=100
def render(label,view='three_quarter',target=None,zoom=None):
    target=Vector(target if target is not None else center);direction={'front':(0,-1,0),'back':(0,1,0),'side':(1,0,0),'three_quarter':(3,-6,2)}[view]
    camera.location=target+Vector(direction).normalized()*7;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=zoom or scale;scene.render.filepath=str(out/f'{label}_{view}.png');bpy.ops.render.render(write_still=True)
states=['rest','arms_overhead','arms_forward','elbows_90','wrists','head_left','head_right','torso_forward','torso_side_left','torso_side_right','thigh_left','thigh_right','knees_90','ankles','crouch'] if rig else ['rest']
results={'static':{},'clips':{},'rig_present':bool(rig),'rest_bounds_min':rest.min(axis=0).tolist(),'rest_bounds_max':rest.max(axis=0).tolist(),'method':'Independent rest-local world-axis poses; original animation data cleared only on appended working scene; sampled edge strain is not collision certification'}
for name in states:
    pose(name);results['static'][name]=measure()
    for view in ['front','side','three_quarter']:render(name,view)
    if name=='rest':render(name,'back')
    if name in ['arms_overhead','head_left','crouch','knees_90']:
        focus=center+np.array([0,0,.35 if name in ['arms_overhead','head_left'] else -.2]);render(name+'_detail','three_quarter',focus,1.15)
    print('TEST_DONE',CHARACTER,name,flush=True)
pose('rest')
# Native viewport wireframes, with the viewport state restored afterwards.
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');space=area.spaces.active;rv=space.region_3d
saved=(sh.type,space.shading.type,space.overlay.show_overlays,rv.view_rotation.copy(),rv.view_location.copy(),rv.view_distance,rv.view_perspective)
space.shading.type='WIREFRAME';space.overlay.show_overlays=False;rv.view_perspective='ORTHO'
with bpy.context.temp_override(area=area,region=next(r for r in area.regions if r.type=='WINDOW')):
    for label,location,distance in [('wire_front',center,scale*1.5),('wire_detail',center+np.array([0,0,.35]),.5)]:
        rv.view_location=Vector(location);rv.view_rotation=Vector((0,-1,0)).to_track_quat('Z','Y');rv.view_distance=distance;scene.render.filepath=str(out/f'{label}.png');bpy.ops.render.opengl(write_still=True,view_context=True)
sh.type,space.shading.type,space.overlay.show_overlays,rv.view_rotation,rv.view_location,rv.view_distance,rv.view_perspective=saved
if rig:
    overlay=bpy.data.collections.new('SkeletonEvidence_'+CHARACTER);scene.collection.children.link(overlay)
    for b in rig.data.bones:
        curve=bpy.data.curves.new('evidence_'+b.name,'CURVE');curve.dimensions='3D';curve.bevel_depth=.004;p=curve.splines.new('POLY');p.points.add(1)
        for pt,v in zip(p.points,[b.head_local,b.tail_local]):pt.co=tuple(rig.matrix_world@v)+(1,)
        ob=bpy.data.objects.new(curve.name,curve);overlay.objects.link(ob);ob.color=(1,.12,.04,1)
    obj.hide_render=True;sh.color_type='OBJECT'
    for view in ['front','side']:render('skeleton_lines',view)
    obj.hide_render=False;overlay.hide_render=True
    for ob in overlay.objects:ob.hide_set(True)
    sh.color_type='SINGLE'
    for action in actions:
        reset();rig.animation_data_create();rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
        lo,hi=action.frame_range;samples=[];root_positions=[];first=None;last=None
        for i,frame in enumerate(np.linspace(lo,hi,13)):
            scene.frame_set(int(frame),subframe=float(frame-int(frame)));bpy.context.view_layer.update();a=coords()
            if first is None:first=a.copy()
            last=a.copy();root=rig.matrix_world@rig.pose.bones['mixamorig:Hips'].matrix
            root_positions.append(list(root.translation));samples.append({'frame':float(frame),**measure()});render('clip_'+action.name+'_'+str(i).zfill(2))
        roots=np.array(root_positions);delta=roots[-1]-roots[0]
        results['clips'][action.name]={'frames':[float(lo),float(hi)],'fps':scene.render.fps/scene.render.fps_base,'duration':float(hi-lo)/(scene.render.fps/scene.render.fps_base),'target_armature':rig.name,'root_name':'mixamorig:Hips','root_positions':root_positions,'root_net_translation':delta.tolist(),'root_horizontal_net_distance':float(np.linalg.norm(delta[:2])),'root_horizontal_excursion':(roots[:,:2].max(axis=0)-roots[:,:2].min(axis=0)).tolist(),'first_last_max_vertex_distance':float(np.linalg.norm(last-first,axis=1).max()),'samples':samples}
        print('CLIP_DONE',CHARACTER,action.name,flush=True)
    rig.animation_data_clear();reset()
    # Preserve the supplied actions as NLA references on this inspection copy for export tests.
    rig.animation_data_create()
    for action in actions:
        t=rig.animation_data.nla_tracks.new();t.name=action.name;s=t.strips.new(action.name,0,action);t.mute=True
        s.frame_start=action.frame_range[0];s.frame_end=action.frame_range[1]
    rig.animation_data.action=None
(out/'test_results.json').write_text(json.dumps(results,indent=2))
# Save this disposable scene to its own blend without changing the live project's filepath.
previous=list(bpy.data.objects)
bpy.data.libraries.write(str(out/'inspection_working_copy.blend'),{scene},fake_user=True,compress=True)
print('TESTS_COMPLETE',CHARACTER,flush=True)
