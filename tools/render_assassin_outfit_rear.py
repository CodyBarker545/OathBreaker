import bpy,os
from mathutils import Vector
OUT=r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\blendswap_assassin'
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'assassin_refined.blend'))
scene=bpy.context.scene;cam=scene.camera;cam.location=(-3,5,2.8);cam.rotation_euler=(Vector((0,0,1.03))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.6
scene.cycles.samples=24;scene.render.resolution_x=1000;scene.render.resolution_y=1000
scene.render.filepath=os.path.join(OUT,'reference_rear.png');bpy.ops.render.render(write_still=True)
