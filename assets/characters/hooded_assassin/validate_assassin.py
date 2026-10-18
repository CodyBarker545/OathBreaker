"""Smoke-check both saved formats with Blender itself."""
import bpy
import os
import json
from mathutils import Vector

folder=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(folder,'hooded_assassin.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.data.collections['ASSASSIN | editable character parts'].objects if o.type=='MESH']
assert len(rig.data.bones)==16
assert len(meshes)>100
assert all(len(o.data.uv_layers)>0 for o in meshes)
assert all(len(o.vertex_groups)==1 for o in meshes)
assert all(any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers) for o in meshes)
hand=next(o for o in meshes if o.name=='Glove.L')
def centroid(obj):
    dg=bpy.context.evaluated_depsgraph_get()
    evaluated=obj.evaluated_get(dg)
    points=[evaluated.matrix_world @ v.co for v in evaluated.data.vertices]
    return sum(points,Vector())/len(points)
before=centroid(hand)
rig.pose.bones['forearm.L'].rotation_mode='XYZ'
rig.pose.bones['forearm.L'].rotation_euler.x=.5
bpy.context.view_layer.update()
assert (centroid(hand)-before).length>.02, 'Posing did not move the glove'
result={'blend_mesh_parts':len(meshes),'rig_bones':len(rig.data.bones),'base_polygons':sum(len(o.data.polygons) for o in meshes),'rig_pose_check':'passed'}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(folder,'hooded_assassin.glb'))
assert not any(o.type in {'CAMERA','LIGHT'} for o in bpy.data.objects)
assert not any('plinth' in o.name.lower() for o in bpy.data.objects)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
assert len(rig.data.bones)==16
result['glb_import_check']='passed'
result['glb_meshes']=sum(o.type=='MESH' for o in bpy.data.objects)
with open(os.path.join(folder,'validation.json'),'w') as f: json.dump(result,f,indent=2)
print(json.dumps(result))
