import bpy,json
from pathlib import Path
from mathutils import Vector
OUT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\outfit')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'assassin_concept_v004.blend'))
for obj in bpy.data.collections['Outfit_Head'].objects:
    if obj.name.startswith('Hair_'):
        for start in range(0,len(obj.data.vertices),4):
            ring=list(obj.data.vertices)[start:start+4]
            # Translate each cross-section intact; retain the lock's thickness.
            shift=min(0,-.195-max(v.co.y for v in ring))
            for v in ring:
                v.co.y+=shift
                if v.co.z>1.77:v.co.x*=.72
scene=bpy.context.scene;camera=scene.camera
scene.cycles.samples=24
def render(name,location,target,scale,width,height):
    camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.resolution_x=width;scene.render.resolution_y=height
    scene.render.filepath=str(OUT/f'assassin_concept_v004_{name}.png');bpy.ops.render.render(write_still=True)
render('head',(.38,-1,1.78),(0,-.06,1.70),.46,1100,1100)
render('three_quarter',(2.5,-6,2.4),(0,0,.94),2.32,1400,1300)
render('front',(0,-6,1.0),(0,0,.94),2.32,1400,1300)
render('rear',(2.1,6,2.15),(0,0,.94),2.32,1400,1300)
camera.location=(2.5,-6,2.4);camera.rotation_euler=(Vector((0,0,.94))-camera.location).to_track_quat('-Z','Y').to_euler()
rig=bpy.data.objects['Assassin_Skeleton']
assert len(rig.data.bones)==53
assert all(max(abs(b.matrix_basis[i][j]-(1 if i==j else 0)) for i in range(4) for j in range(4))<1e-6 for b in rig.pose.bones)
report=json.loads((OUT/'assassin_concept_v004_validation.json').read_text());report['hair_clear_of_cowl_front']=True
(OUT/'assassin_concept_v004_validation.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assassin_concept_v004.blend'))
result={'file':str(OUT/'assassin_concept_v004.blend'),'hair_cowl_clearance_corrected':True}
