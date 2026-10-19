import bpy, os, sys, json, shutil
from mathutils import Vector
ROOT=r'D:\SoftwareEng\Game';OUT=os.path.join(ROOT,'SourceAssets','characters','komodo_axe_warrior')
sys.path.insert(0,os.path.join(ROOT,'tools'))
from komodo_hands import build_hands
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'komodo_axe_warrior.blend'))
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
for o in list(bpy.data.objects):
    if o.name.startswith(('Clawed fist ', 'Knuckle ', 'Hand claw ', 'Axe ', 'Crescent axe')):bpy.data.objects.remove(o,do_unlink=True)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
collection=bpy.data.collections['KOMODO • character and equipment']
def mat(prefix):return next(m for m in bpy.data.materials if m.name.startswith(prefix))
hands=build_hands(rig,collection,mat('01 '),mat('09 '),mat('03 '),mat('02 '))
for text in bpy.data.texts:
    if text.name.startswith('START HERE'):
        text.from_string(text.as_string().replace('18-bone','48-bone')+'\nHands: adjust rig custom properties Grip.L / Grip.R (0 relaxed, 1 curled). Finger controls are Blender drivers; bake grip poses for game use.\n')
scene=bpy.context.scene;scene.frame_set(1)
meshes=[o for o in collection.objects if o.type=='MESH']
# Render the open hand and a grip demonstration on a temporary studio cylinder.
camera=scene.camera;old_matrix=camera.matrix_world.copy();old_scale=camera.data.ortho_scale
camera.location=(1.8,-3.8,1.8);camera.rotation_euler=(Vector((.65,-.38,1.02))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=.61
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.filepath=os.path.join(OUT,'hand_detail.png');bpy.ops.render.render(write_still=True)
rig['Grip.L']=.75;rig['Grip.R']=.75;scene.frame_set(2)
scene.render.filepath=os.path.join(OUT,'hand_grip.png');bpy.ops.render.render(write_still=True)
rig['Grip.L']=0.;rig['Grip.R']=0.;scene.frame_set(1)
camera.matrix_world=old_matrix;camera.data.ortho_scale=old_scale
scene.render.resolution_x=1200;scene.render.resolution_y=1200
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'komodo_axe_warrior.glb'),export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
shutil.copy2(os.path.join(OUT,'komodo_axe_warrior.glb'),os.path.join(ROOT,'Assets','Characters','Komodo','Komodo.glb'))
scene.render.filepath=os.path.join(OUT,'komodo_preview.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'komodo_axe_warrior.blend'))
bpy.ops.render.render(write_still=True)
camera.location=(-3.3,5.3,2.8);camera.rotation_euler=(Vector((0,.25,1.1))-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(OUT,'komodo_rear.png');bpy.ops.render.render(write_still=True)
for o in meshes:o.data.calc_loop_triangles()
with open(os.path.join(OUT,'build_report.json')) as f:report=json.load(f)
report.update(mesh_objects=len(meshes),triangles=sum(len(o.data.loop_triangles) for o in meshes),rig_bones=len(rig.data.bones),hand_digits=5,grip_controls=['Grip.L','Grip.R'])
with open(os.path.join(OUT,'build_report.json'),'w') as f:json.dump(report,f,indent=2)
print('HANDS_COMPLETE',json.dumps(report))
