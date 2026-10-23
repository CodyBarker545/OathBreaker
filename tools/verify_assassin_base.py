import bpy,json,math,bmesh
from pathlib import Path
from mathutils import Quaternion
ROOT=Path(r'D:\SoftwareEng\Game')
OUT=ROOT/'SourceAssets/characters/hooded_assassin/base'
body=bpy.data.objects['Assassin_Body']
rig=bpy.data.objects['Assassin_Skeleton']
report=json.loads((OUT/'validation.json').read_text())
bm=bmesh.new()
bm.from_mesh(body.data)
report['zero_area_faces']=sum(f.calc_area()<1e-12 for f in bm.faces)
report['loose_vertices']=sum(not v.link_edges for v in bm.verts)
bm.free()
report['zero_length_bones']=[b.name for b in rig.data.bones if b.length<1e-6]
report['skeleton_root_bones']=[b.name for b in rig.data.bones if not b.parent]
report['skeleton_symmetry_max_error_m']=max(max((b.head_local-rig.data.bones[b.name[:-2]+'_r'].head_local*__import__('mathutils').Vector((-1,1,1))).length,(b.tail_local-rig.data.bones[b.name[:-2]+'_r'].tail_local*__import__('mathutils').Vector((-1,1,1))).length) for b in rig.data.bones if b.name.endswith('_l'))
assert report['zero_area_faces']==0
assert report['loose_vertices']==0
assert not report['zero_length_bones']
assert len(report['skeleton_root_bones'])==1
assert report['skeleton_symmetry_max_error_m']<1e-5
report['package_installation_report']='artifacts/mpfb_packages_installation.json'
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.region_3d.view_rotation=Quaternion((1,0,0),math.pi/2)
            space.region_3d.view_perspective='ORTHO'
            space.region_3d.view_location=(0,0,0.9)
            space.region_3d.view_distance=2.7
            space.shading.color_type='MATERIAL'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assassin_base.blend'))
result=report
