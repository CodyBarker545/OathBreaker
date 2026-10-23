import bpy,math,json
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
OUT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\inspection_rigged_shadowblade')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'static_test_scene.blend'))
scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');obj=next(o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));cam=scene.camera
def aim(center,scale,view):
    center=Vector(center);cam.location=center+Vector({'front':(0,-1,0),'three_quarter':(3,-6,2),'side':(1,0,0)}[view]).normalized()*7;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
def render(name):
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
# Render unobscured skeleton lines for an explicitly composited x-ray overlay.
overlay=bpy.data.collections['EvidenceSkeleton'];overlay.hide_render=False;obj.hide_render=True;scene.display.shading.color_type='OBJECT'
for view in ['front','side']:
    aim((0,0,.9),2.45,view);render('skeleton_color_'+view)
overlay.hide_render=True;obj.hide_render=False;scene.display.shading.color_type='SINGLE'
aim((.78,-.04,1.31),.48,'front');render('hand_rest_detail')
p=rig.pose.bones['mixamorig:LeftHandMiddle4'];p.rotation_mode='QUATERNION';q=rig.matrix_world.to_quaternion()@p.bone.matrix_local.to_quaternion();p.rotation_quaternion=Quaternion(q.inverted()@Vector((0,0,1)),math.radians(-40));bpy.context.view_layer.update();render('hand_terminal_bend_detail');p.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update()
# Material renders include the embedded normal map, unlike Workbench articulation evidence.
scene.render.engine='BLENDER_EEVEE'
scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.16,.16,.16,1);bg.inputs['Strength'].default_value=.35
for name,location,power,size in [('Key',(2,-4,5),600,4),('Fill',(-3,-2,3),350,3),('Rim',(0,3,4),500,3)]:
    ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ob=bpy.data.objects.new(name,ld);scene.collection.objects.link(ob);ob.location=location;ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
aim((0,0,.9),2.45,'three_quarter');render('rest_material_three_quarter')
aim((0,-.03,1.48),.65,'front');render('face_material_detail')
helpers=[{'name':o.name,'role':'custom bone display geometry','used_by':[b.name for b in rig.pose.bones if b.custom_shape==o]} for o in scene.objects if o.type=='MESH' and o!=obj]
(OUT/'helper_objects.json').write_text(json.dumps(helpers,indent=2))
print('EVIDENCE_COMPLETE',flush=True)
