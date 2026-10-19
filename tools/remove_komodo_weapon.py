import bpy, os, shutil, json
ROOT=r'D:\SoftwareEng\Game'
OUT=os.path.join(ROOT,'SourceAssets','characters','komodo_axe_warrior')
path=os.path.join(OUT,'komodo_axe_warrior.blend')
bpy.ops.wm.open_mainfile(filepath=path)
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
removed=[]
for obj in list(bpy.data.objects):
    if obj.name.startswith(('Axe ', 'Crescent axe')):
        removed.append(obj.name)
        bpy.data.objects.remove(obj,do_unlink=True)
assert removed, 'No weapon parts found'
meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.get('asset_role')=='Character mesh']
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
scene=bpy.context.scene;scene.frame_set(1)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'komodo_axe_warrior.glb'),export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
shutil.copy2(os.path.join(OUT,'komodo_axe_warrior.glb'),os.path.join(ROOT,'Assets','Characters','Komodo','Komodo.glb'))
scene.render.filepath=os.path.join(OUT,'komodo_preview.png')
bpy.ops.wm.save_as_mainfile(filepath=path)
bpy.ops.render.render(write_still=True)
from mathutils import Vector
cam=scene.camera;cam.location=(-3.3,5.3,2.8);cam.rotation_euler=(Vector((0,.25,1.1))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=os.path.join(OUT,'komodo_rear.png');bpy.ops.render.render(write_still=True)
report_path=os.path.join(OUT,'build_report.json')
with open(report_path) as f:report=json.load(f)
for o in meshes:o.data.calc_loop_triangles()
report.update(mesh_objects=len(meshes),triangles=sum(len(o.data.loop_triangles) for o in meshes),weapon_included=False)
with open(report_path,'w') as f:json.dump(report,f,indent=2)
print('REMOVED_WEAPON',len(removed),'parts;',json.dumps(report))
