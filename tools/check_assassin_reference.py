import bpy,os,json,struct
from mathutils import Vector
ROOT=r'D:\SoftwareEng\Game';OUT=os.path.join(ROOT,'SourceAssets','characters','hooded_assassin','blendswap_assassin')
with open(os.path.join(OUT,'assassin_refined.glb'),'rb') as f:
    f.read(12);length,kind=struct.unpack('<II',f.read(8));data=json.loads(f.read(length))
names=[n.get('name','') for n in data['nodes']]
assert not any(n.startswith('Hood') for n in names),'Hood should be removed'
assert 'Hair | full shaded scalp foundation' in names,'Missing full hairstyle'
assert 'Cloth mask • draped woven face wrap' in names,'Missing fabric face wrap'
assert 'Continuous fitted leather torso' in names,'Missing continuous torso'
assert all(f'grip_index.01.{side}' in names for side in ['R','L']),'Missing hand joints'
assert not any('dagger' in n.lower() or 'weapon' in n.lower() for n in names),'Unexpected weapon'
actions=[a.get('name') for a in data.get('animations',[])]
assert all(any(required in name for name in actions) for required in ['Idle','Walk','Arm_Motion_Test']),actions
assert not data.get('cameras'),'Studio camera in export'
assert all('skin' in n for n in data['nodes'] if 'mesh' in n),'Unbound exported mesh'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(OUT,'assassin_refined.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
report={'passed':True,'hood':False,'mask':True,'weapon_free':True,'continuous_torso':True,'finger_joints':True,'animation_names':actions,'bones':len(rig.data.bones),'embedded_images':len(data.get('images',[]))}
with open(os.path.join(OUT,'reference_validation.json'),'w') as f:json.dump(report,f,indent=2)
print('ASSASSIN_VALIDATION',json.dumps(report))
# Pose spot checks are rendered from the editable source so lighting stays consistent.
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'assassin_refined.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene
face=bpy.data.objects['Unmasked sculpted face'];group=face.vertex_groups['head']
assert all(abs(group.weight(v.index)-1)<1e-5 for v in face.data.vertices),'Face contains unweighted orbital vertices'
scene.cycles.samples=24;scene.render.resolution_x=1100;scene.render.resolution_y=1100
scene.render.filepath=os.path.join(OUT,'refined_preview.png');bpy.ops.render.render(write_still=True)
cam=scene.camera;old_matrix=cam.matrix_world.copy();old_scale=cam.data.ortho_scale
cam.location=(1,-3,2.03);cam.rotation_euler=(Vector((0,-.02,1.82))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.56
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.filepath=os.path.join(OUT,'reference_head_detail.png');bpy.ops.render.render(write_still=True)
cam.location=(3,.35,1.98);cam.rotation_euler=(Vector((0,.025,1.83))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.59
scene.render.filepath=os.path.join(OUT,'reference_head_profile.png');bpy.ops.render.render(write_still=True)
cam.matrix_world=old_matrix;cam.data.ortho_scale=old_scale
scene.cycles.samples=16;scene.render.resolution_x=700;scene.render.resolution_y=700
for name,frame,out in [('Walk',7,'reference_walk_check.png'),('Arm_Motion_Test',18,'reference_arm_check.png')]:
    action=bpy.data.actions[name];rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    scene.frame_set(frame);bpy.context.view_layer.update()
    scene.render.filepath=os.path.join(OUT,out);bpy.ops.render.render(write_still=True)
