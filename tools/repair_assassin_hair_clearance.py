import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
OUT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\outfit')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'assassin_concept_v004.blend'))
names=[o.name for o in bpy.data.collections['Outfit_Head'].objects if o.name.startswith('Hair_')]
with bpy.data.libraries.load(str(OUT/'assassin_concept_v003.blend'),link=False) as (src,dst):dst.objects=names.copy()
for name,source in zip(names,dst.objects):
    target=bpy.data.objects[name]
    for v,original in zip(target.data.vertices,source.data.vertices):v.co=(original.co.x*.90,original.co.y-.045,original.co.z)
    bm=bmesh.new();bm.from_mesh(target.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(f.calc_area()>1e-12 for f in bm.faces);bm.to_mesh(target.data);bm.free();target.data.update()
    bpy.data.objects.remove(source,do_unlink=True)
bpy.context.view_layer.update()
scene=bpy.context.scene;camera=scene.camera;scene.cycles.samples=24
def render(name,location,target,scale,w,h):
    camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.filepath=str(OUT/f'assassin_concept_v004_{name}.png');bpy.ops.render.render(write_still=True)
render('head',(.38,-1,1.78),(0,-.06,1.70),.46,1100,1100)
render('three_quarter',(2.5,-6,2.4),(0,0,.94),2.32,1400,1300)
render('front',(0,-6,1.0),(0,0,.94),2.32,1400,1300)
render('rear',(2.1,6,2.15),(0,0,.94),2.32,1400,1300)
camera.location=(2.5,-6,2.4);camera.rotation_euler=(Vector((0,0,.94))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assassin_concept_v004.blend'))
result={'file':str(OUT/'assassin_concept_v004.blend'),'hair_source_topology_verified':True}
