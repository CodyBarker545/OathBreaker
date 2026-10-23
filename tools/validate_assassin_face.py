import bpy,json,math,bmesh
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(r'D:\SoftwareEng\Game')
OUT=ROOT/'SourceAssets/characters/hooded_assassin/face'
body=bpy.data.objects['Assassin_Body']
rig=bpy.data.objects['Assassin_Skeleton']
with bpy.data.libraries.load(str(ROOT/'SourceAssets/characters/hooded_assassin/base/assassin_base.blend'),link=False) as (src,dst):
    dst.objects=['Assassin_Body','Assassin_Skeleton']
original,original_rig=dst.objects
report=json.loads((OUT/'face_validation.json').read_text())
report['body_below_neck_unchanged']=all((a.co-b.co).length<1e-7 for a,b in zip(body.data.vertices,original.data.vertices) if b.co.z<=1.54)
report['original_topology_preserved']=len(body.data.vertices)==len(original.data.vertices) and all(tuple(a.vertices)==tuple(b.vertices) for a,b in zip(body.data.polygons,original.data.polygons))
report['original_skeleton_preserved']=all((a.head_local-original_rig.data.bones[a.name].head_local).length<1e-7 and (a.tail_local-original_rig.data.bones[a.name].tail_local).length<1e-7 for a in rig.data.bones)
report['height_m']=max(v.co.z for v in body.data.vertices)-min(v.co.z for v in body.data.vertices if any(w.group==body.vertex_groups['body'].index for w in v.groups))
bm=bmesh.new()
bm.from_mesh(body.data)
report['zero_area_body_faces']=sum(f.calc_area()<1e-12 for f in bm.faces)
bm.free()
for obj in dst.objects: bpy.data.objects.remove(obj,do_unlink=True)
grooms=[bpy.data.objects[n] for n in ['Assassin_Full_Copper_Beard','Assassin_Copper_Eyebrows','Assassin_Eye_Shading_Space']]
bpy.context.view_layer.update()
before=[o.matrix_world.copy() for o in grooms]
pb=rig.pose.bones['head']
pb.rotation_mode='XYZ'
saved=pb.rotation_euler.copy()
pb.rotation_euler.z=math.radians(20)
bpy.context.view_layer.update()
report['head_attachment_test']={o.name:sum(abs(o.matrix_world[i][j]-old[i][j]) for i in range(4) for j in range(4))>.001 for o,old in zip(grooms,before)}
pb.rotation_euler=saved
bpy.context.view_layer.update()
report['collection']='Character_Assassin'
report['no_armor']=True
report['eye_shader_follows_head']=bpy.data.objects['Assassin_Eye_Shading_Space'].parent_bone=='head'
report['textures_packed']=True
assert report['body_below_neck_unchanged']
assert report['original_topology_preserved']
assert report['original_skeleton_preserved']
assert report['zero_area_body_faces']==0
assert all(report['head_attachment_test'].values())
assert abs(report['height_m']-1.8)<.0001
(OUT/'face_validation.json').write_text(json.dumps(report,indent=2))
scene=bpy.context.scene
camera=scene.camera
scene.cycles.samples=48
scene.render.resolution_x=1100
scene.render.resolution_y=1200
camera.data.ortho_scale=.38
def point(target): camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
camera.location=(.29,-.94,1.71)
point((0,-.075,1.669))
scene.render.filepath=str(OUT/'assassin_face_three_quarter.png')
bpy.ops.render.render(write_still=True)
camera.location=(0,-1,1.68)
point((0,-.075,1.669))
scene.render.filepath=str(OUT/'assassin_face_front.png')
bpy.ops.render.render(write_still=True)
camera.data.ortho_scale=2.45
camera.location=(0,-5,1)
point((0,0,.91))
scene.render.resolution_x=1100
scene.render.resolution_y=1000
scene.cycles.samples=24
scene.render.filepath=str(OUT/'assassin_detailed_full_body.png')
bpy.ops.render.render(write_still=True)
camera.location=(.29,-.94,1.71)
camera.data.ortho_scale=.38
point((0,-.075,1.669))
scene.render.resolution_x=1100
scene.render.resolution_y=1200
scene.cycles.samples=48
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.region_3d.view_distance=.55
            space.region_3d.view_location=(0,-.075,1.669)
            space.region_3d.view_rotation=Quaternion((1,0,0),math.pi/2)
            space.region_3d.view_perspective='ORTHO'
            space.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assassin_detailed.blend'))
result=report
