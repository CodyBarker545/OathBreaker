import bpy, json, math
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from bl_ext.blender_org.mpfb.services.assetservice import AssetService
from bl_ext.blender_org.mpfb.services.locationservice import LocationService
from bl_ext.blender_org.mpfb.services.rigservice import RigService
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
ROOT=Path(r'D:\SoftwareEng\Game')
OUT=ROOT/'SourceAssets/characters/hooded_assassin/base'
AssetService.update_all_asset_lists()
body=bpy.data.objects['Assassin_Body']
rig=bpy.data.objects['Assassin_Skeleton']
col=body.users_collection[0]
eyes=HumanService.add_mhclo_asset(str(Path(LocationService.get_user_data())/'eyes/low-poly/low-poly.mhclo'), body, asset_type='Eyes', subdiv_levels=0)
eyes.name='Assassin_Eyes'
for old in list(eyes.users_collection): old.objects.unlink(eyes)
col.objects.link(eyes)
def aim(name, direction):
    pb=rig.pose.bones[name]
    mat=pb.matrix.copy()
    q=(pb.tail-pb.head).normalized().rotation_difference(Vector(direction).normalized())
    mat=q.to_matrix().to_4x4() @ mat
    mat.translation=pb.head
    pb.matrix=mat
    bpy.context.view_layer.update()
for side,sign in [('l',1),('r',-1)]:
    for name in ['upperarm','lowerarm','hand']:
        aim(name+'_'+side, (sign,0,0))
    pb=rig.pose.bones['thigh_'+side]
    d=pb.tail-pb.head
    aim(pb.name, (sign*0.025,d.y,d.z))
RigService.apply_pose_as_rest_pose(rig)
bpy.context.view_layer.update()
mapping=list(body['symmetry_pairs'])
assert all(mapping[j]==i for i,j in enumerate(mapping)), 'Symmetry mapping must be reciprocal'
for i,j in enumerate(mapping):
    if i>j: continue
    a,b=body.data.vertices[i],body.data.vertices[j]
    if i==j:
        a.co.x=0
    else:
        avg=(a.co+Vector((-b.co.x,b.co.y,b.co.z)))*0.5
        a.co=avg
        b.co=(-avg.x,avg.y,avg.z)
del body['symmetry_pairs']
# Retain MPFB's helper geometry hidden by its original mask; preserve all vertex indices.
def coords(obj):
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    verts=[evaluated.matrix_world@v.co for v in mesh.vertices]
    evaluated.to_mesh_clear()
    return verts
points=coords(body)
low=min(p.z for p in points)
height=max(p.z for p in points)-low
scale=1.8/height
for obj in [body,eyes]:
    for v in obj.data.vertices:
        v.co=(v.co-Vector((0,0,low)))*scale
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for bone in rig.data.edit_bones:
    bone.head=(bone.head-Vector((0,0,low)))*scale
    bone.tail=(bone.tail-Vector((0,0,low)))*scale
bpy.ops.object.mode_set(mode='OBJECT')
body['generator']='MPFB 2.0.18; male athletic macro proportions'
body['height_m']=1.8
body['topology_note']='Original MPFB quad topology and hidden fitting helpers retained. T-pose baked as neutral bind pose.'
body['macro_parameters']=json.dumps({'gender':1.0,'age':0.34,'muscle':0.68,'weight':0.38,'proportions':0.65,'height':0.55})
rig.show_in_front=True
rig.data.display_type='OCTAHEDRAL'
skin=bpy.data.materials.new('Assassin_Base_Clay')
skin.diffuse_color=(0.36,0.39,0.43,1)
skin.use_nodes=True
skin.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=skin.diffuse_color
skin.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=0.76
body.data.materials.clear()
body.data.materials.append(skin)
for p in body.data.polygons: p.use_smooth=True
bpy.context.view_layer.update()
points=coords(body)
tree=KDTree(len(points))
for i,p in enumerate(points): tree.insert(p,i)
tree.balance()
sym=max(tree.find(Vector((-p.x,p.y,p.z)))[2] for p in points)
bone_names={b.name for b in rig.data.bones if b.use_deform}
ids={g.index for g in body.vertex_groups if g.name in bone_names}
body_group=body.vertex_groups['body'].index
visible=[v for v in body.data.vertices if any(g.group==body_group and g.weight>0.5 for g in v.groups)]
unweighted=[v.index for v in visible if sum(g.weight for g in v.groups if g.group in ids)<0.001]
smoke={}
for name in ['upperarm_l','lowerarm_l','thigh_l','calf_l','index_01_l']:
    if name not in rig.pose.bones: continue
    pb=rig.pose.bones[name]
    before=coords(body)
    pb.rotation_mode='XYZ'
    pb.rotation_euler.x=math.radians(25)
    bpy.context.view_layer.update()
    after=coords(body)
    smoke[name]=max((a-b).length for a,b in zip(after,before))
    pb.rotation_euler=(0,0,0)
    bpy.context.view_layer.update()
horizontal={name:abs((rig.data.bones[name].tail_local-rig.data.bones[name].head_local).z) for name in ['upperarm_l','upperarm_r','lowerarm_l','lowerarm_r','hand_l','hand_r']}
report={'generator':'MPFB','height_m':max(p.z for p in points)-min(p.z for p in points),'ground_z':min(p.z for p in points),'symmetry_max_error_m':sym,'bones':len(rig.data.bones),'vertices_with_helpers':len(body.data.vertices),'faces_with_helpers':len(body.data.polygons),'quad_faces':sum(len(p.vertices)==4 for p in body.data.polygons),'unweighted_body_vertices':len(unweighted),'horizontal_arm_vertical_error_m':horizontal,'deformation_test_max_displacement_m':smoke,'collection':col.name,'objects':[o.name for o in col.objects],'armor_objects':0}
assert abs(report['height_m']-1.8)<0.0001
print('VALIDATION',json.dumps(report))
assert sym<0.0001
assert not unweighted
assert max(horizontal.values())<0.0001
assert all(value>0.001 for value in smoke.values())
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
# A separate collection holds the presentation camera and lighting.
stage=bpy.data.collections.new('Preview_Studio')
bpy.context.scene.collection.children.link(stage)
def stage_link(obj):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    stage.objects.link(obj)
def track(obj,point): obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(0,-5,0.95))
camera=bpy.context.object
camera.name='Preview_Camera'
stage_link(camera)
camera.data.type='ORTHO'
camera.data.ortho_scale=2.45
track(camera,(0,0,0.9))
scene=bpy.context.scene
scene.camera=camera
for loc,power,size in [((-3,-4,5),600,4),((3,-2,3),400,3),((0,3,4),700,3)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    lamp=bpy.context.object
    stage_link(lamp)
    lamp.data.energy=power
    lamp.data.shape='DISK'
    lamp.data.size=size
    track(lamp,(0,0,1))
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1
scene.render.engine='CYCLES'
scene.cycles.samples=24
scene.render.resolution_x=1100
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.world.color=(0.14,0.14,0.14)
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/'assassin_base_front.png')
bpy.ops.render.render(write_still=True)
camera.location=(3,-5,2.0)
track(camera,(0,0,0.92))
scene.render.filepath=str(OUT/'assassin_base_three_quarter.png')
bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active=rig
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=3.2
            area.spaces.active.region_3d.view_location=(0,0,0.9)
            area.spaces.active.clip_end=100
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assassin_base.blend'))
result=report
