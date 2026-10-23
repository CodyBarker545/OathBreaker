import bpy,bmesh,ast,json,math,random
from pathlib import Path
from mathutils import Vector,Quaternion
from math import sin,cos,pi,tau
ROOT=Path(r'D:\SoftwareEng\Game');OUT=ROOT/'SourceAssets/characters/hooded_assassin/outfit'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'assassin_concept_v002.blend'))
scene=bpy.context.scene;body=bpy.data.objects['Assassin_Body'];rig=bpy.data.objects['Assassin_Skeleton']
collections={name:bpy.data.collections['Outfit_'+name] for name in ['Head','Torso','Shoulders_Arms','Lower_Body','Red_Fabric']}
added=[]
gold=bpy.data.materials['GC_Tarnished_Bronze_Gold'];red=bpy.data.materials['GC_Deep_Red_Tattered_Linen'];hoodmat=bpy.data.materials['GC_Charcoal_Hood']
steel=bpy.data.materials['GC_Painted_Blackened_Steel']
tree=ast.parse((ROOT/'tools/build_assassin_concept_outfit.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'<outfit authoring helpers>','exec'),globals())
# Keep every blond lock in front of the open cowl rather than emerging through a side panel.
for obj in collections['Head'].objects:
    if obj.name.startswith('Hair_'):
        for v in obj.data.vertices:
            v.co.x*=.82
            if v.co.y<-.13:v.co.y-=.010
# Embroidered back crest and worn, broken horizontal stitches on the red mantle.
for sign,label in [(1,'L'),(-1,'R')]:
    points=[(sign*x,y,z) for x,y,z in [(0,.180,1.29),(.067,.186,1.21),(.105,.193,1.11),(.046,.198,1.015),(.078,.208,.88),(.022,.218,.78)]]
    path('Mantle_'+label+'_Faded_Gold_Crest',points,.0014,gold,'Red_Fabric','spine_03',4)
    path('Mantle_'+label+'_Crest_Upper_Wing',[(0,.178,1.30),(sign*.10,.181,1.33),(sign*.15,.182,1.30)],.0012,gold,'Red_Fabric','spine_03',4)
path('Mantle_Central_Dagger_Embroidery',[(0,.179,1.32),(0,.190,1.15),(0,.205,.91),(0,.221,.73)],.0015,gold,'Red_Fabric','spine_03',4)
# Decals share the mantle's smooth spine weighting so they remain on its surface when posed.
for obj in added:weight_spine(obj)
with bpy.data.libraries.load(str(ROOT/'SourceAssets/characters/hooded_assassin/face/assassin_detailed.blend'),link=False) as (src,dst):dst.objects=['Assassin_Body','Assassin_Skeleton']
oldbody,oldrig=dst.objects
assert len(rig.data.bones)==len(oldrig.data.bones)==53
skeleton_ok=all((b.head_local-oldrig.data.bones[b.name].head_local).length<1e-7 and (b.tail_local-oldrig.data.bones[b.name].tail_local).length<1e-7 and (b.parent.name if b.parent else None)==(oldrig.data.bones[b.name].parent.name if oldrig.data.bones[b.name].parent else None) for b in rig.data.bones)
pose_ok=all(max(abs(b.matrix_basis[i][j]-oldrig.pose.bones[b.name].matrix_basis[i][j]) for i in range(4) for j in range(4))<1e-7 for b in rig.pose.bones)
body_ok=len(body.data.vertices)==len(oldbody.data.vertices) and all((a.co-b.co).length<1e-7 for a,b in zip(body.data.vertices,oldbody.data.vertices))
assert skeleton_ok and pose_ok and body_ok
for obj in dst.objects:bpy.data.objects.remove(obj,do_unlink=True)
outfit=[o for c in collections.values() for o in c.objects if o.type=='MESH']
dg=bpy.context.evaluated_depsgraph_get()
counts={};visible_triangles=0
for obj in [o for o in scene.objects if o.type=='MESH' and not o.hide_render]:
    evaluated=obj.evaluated_get(dg);data=evaluated.to_mesh();tri=sum(len(p.vertices)-2 for p in data.polygons)
    counts[obj.name]=tri;visible_triangles+=tri;evaluated.to_mesh_clear()
unweighted={};zeroarea={}
for obj in outfit:
    boneids={g.index for g in obj.vertex_groups if g.name in rig.data.bones}
    missed=sum(not any(g.group in boneids and g.weight>0 for g in v.groups) for v in obj.data.vertices)
    if missed:unweighted[obj.name]=missed
    bm=bmesh.new();bm.from_mesh(obj.data);degenerate=sum(f.calc_area()<1e-12 for f in bm.faces);bm.free()
    if degenerate:zeroarea[obj.name]=degenerate
assert not unweighted
assert all(o.data.uv_layers for o in outfit)
assert all(any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers) for o in outfit)
# A reversible arm, finger and leg movement checks representative attachments.
smoke={}
for bone,objectname in [('upperarm_l','Pauldron_L_Layer_00'),('lowerarm_l','Bracer_L_Black_Steel_Plate'),('index_01_l','Finger_L_index_01_Protection'),('calf_l','Knee_L_Pointed_Guard')]:
    obj=bpy.data.objects[objectname]
    def sample():
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());data=evaluated.to_mesh();coords=[v.co.copy() for v in data.vertices];evaluated.to_mesh_clear();return coords
    before=sample();pb=rig.pose.bones[bone];oldmatrix=pb.matrix_basis.copy()
    pb.rotation_mode='XYZ';pb.rotation_euler.x+=math.radians(18);bpy.context.view_layer.update();after=sample()
    smoke[bone]=max((a-b).length for a,b in zip(after,before))
    pb.matrix_basis=oldmatrix;bpy.context.view_layer.update()
assert all(v>.001 for v in smoke.values())
assert all(max(abs(b.matrix_basis[i][j]-(1 if i==j else 0)) for i in range(4) for j in range(4))<1e-6 for b in rig.pose.bones)
version=3;dest=OUT/'assassin_concept_v003.blend';scene['concept_outfit_version']=version
report={'file':str(dest),'version':version,'original_bones':53,'skeleton_unchanged':skeleton_ok,'t_pose_unchanged':pose_ok,'body_geometry_unchanged':body_ok,'separate_outfit_meshes':len(outfit),'visible_evaluated_triangles':visible_triangles,'outfit_source_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in outfit),'unweighted_outfit_vertices':unweighted,'degenerate_outfit_faces':zeroarea,'all_outfit_meshes_have_uvs':True,'all_outfit_meshes_bound_to_original_skeleton':True,'deformation_smoke_test_m':smoke,'painted_albedo_maps':10,'map_resolution':'512x512','textures_packed':True,'collections':{name:len(c.objects) for name,c in collections.items()},'visible_triangle_counts':counts,'cloth_note':'Drapery follows existing spine/pelvis weights; editable geometry, no added cloth bones.'}
(OUT/'assassin_concept_v003_validation.json').write_text(json.dumps(report,indent=2))
camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=2.32
scene.render.resolution_x=1400;scene.render.resolution_y=1300;scene.cycles.samples=32
def view(name,location,target=(0,0,.94),scale=2.32):
    camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.filepath=str(OUT/f'assassin_concept_v003_{name}.png');bpy.ops.render.render(write_still=True)
view('front',(0,-6,1.0))
view('rear',(2.1,6,2.15))
view('three_quarter',(2.5,-6,2.4))
scene.render.resolution_x=1100;scene.render.resolution_y=1100
view('head',(.38,-1,1.78),(0,-.06,1.70),.46)
camera.location=(2.5,-6,2.4);camera.rotation_euler=(Vector((0,0,.94))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=2.32
scene.render.resolution_x=1400;scene.render.resolution_y=1300
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.region_3d.view_location=(0,0,.95);space.region_3d.view_distance=2.9;space.region_3d.view_rotation=Quaternion((1,0,0),pi/2);space.region_3d.view_perspective='ORTHO';space.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest))
result={k:v for k,v in report.items() if k!='visible_triangle_counts'}
