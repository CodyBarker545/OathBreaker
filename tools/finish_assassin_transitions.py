import bpy,os,shutil
from mathutils import Vector
ROOT=r'D:\SoftwareEng\Game';OUT=os.path.join(ROOT,'SourceAssets','characters','hooded_assassin','blendswap_assassin')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'assassin_refined.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
face=bpy.data.objects['Unmasked sculpted face'];oldneck=bpy.data.objects.get('Neck')
if oldneck:bpy.data.objects.remove(oldneck,do_unlink=True)
skin=face.data.materials[0]
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=(0,.018,1.655));neck=bpy.context.object;neck.scale=(.06,.06,.10);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
neck.data.materials.append(skin)
bpy.ops.object.select_all(action='DESELECT');face.select_set(True);neck.select_set(True);bpy.context.view_layer.objects.active=face;bpy.ops.object.join()
rem=face.modifiers.new('Continuous neck transition','REMESH');rem.mode='VOXEL';rem.voxel_size=.0021
while face.modifiers.find(rem.name)>0:bpy.ops.object.modifier_move_up(modifier=rem.name)
bpy.ops.object.modifier_apply(modifier=rem.name)
sm=face.modifiers.new('Smooth jaw and neck transition','SMOOTH');sm.factor=.55;sm.iterations=3
while face.modifiers.find(sm.name)>0:bpy.ops.object.modifier_move_up(modifier=sm.name)
bpy.ops.object.modifier_apply(modifier=sm.name)
face.vertex_groups.clear();face.vertex_groups.new(name='head').add(list(range(len(face.data.vertices))),1,'REPLACE')
for p in face.data.polygons:p.use_smooth=True
uv=face.data.uv_layers.new(name='Continuous face skin')
for poly in face.data.polygons:
    for li in poly.loop_indices:
        p=face.matrix_world@face.data.vertices[face.data.loops[li].vertex_index].co;uv.data[li].uv=(p.x*3+p.y*.8,p.z*3)
torso=bpy.data.objects['Continuous fitted leather torso']
for v in torso.data.vertices:
    z=v.co.z
    if z>1.55:
        t=max(0,min(1,(z-1.55)/.055));v.co.x*=1-.42*t;v.co.y*=1-.30*t
rig.data.pose_position='POSE';scene=bpy.context.scene;scene.frame_set(1)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'assassin_refined.glb'),export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
shutil.copy2(os.path.join(OUT,'assassin_refined.glb'),os.path.join(ROOT,'Assets','Characters','Assassin','Assassin.glb'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'assassin_refined.blend'))
import json
report_path=os.path.join(OUT,'reference_update_report.json')
with open(report_path) as f:report=json.load(f)
for o in meshes:o.data.calc_loop_triangles()
report.update(mesh_objects=len(meshes),triangles=sum(len(o.data.loop_triangles) for o in meshes))
with open(report_path,'w') as f:json.dump(report,f,indent=2)
print('TRANSITIONS_FINISHED')
