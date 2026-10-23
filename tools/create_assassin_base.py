import bpy, json, sys, math
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT = Path(r'D:\SoftwareEng\Game')
OUT = ROOT / 'SourceAssets/characters/hooded_assassin/base'
OUT.mkdir(parents=True, exist_ok=True)
module = 'bl_ext.blender_org.mpfb'
if module not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=module)
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
from bl_ext.blender_org.mpfb.services.targetservice import TargetService
from bl_ext.blender_org.mpfb.services.rigservice import RigService
from bl_ext.blender_org.mpfb.services.locationservice import LocationService
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for old in list(bpy.data.collections):
    if old.name.startswith('Character_Assassin') and not old.objects:
        bpy.data.collections.remove(old)
collection = bpy.data.collections.new('Character_Assassin')
bpy.context.scene.collection.children.link(collection)
macro = TargetService.get_default_macro_info_dict()
macro.update(gender=1.0, age=0.34, muscle=0.68, weight=0.38, proportions=0.65, height=0.55)
body = HumanService.create_human(macro_detail_dict=macro)
body.name = 'Assassin_Body'
tree=KDTree(len(body.data.vertices))
for v in body.data.vertices: tree.insert(v.co,v.index)
tree.balance()
body['symmetry_pairs']=[tree.find(Vector((-v.co.x,v.co.y,v.co.z)))[1] for v in body.data.vertices]
rig = HumanService.add_builtin_rig(body, 'game_engine', import_weights=True)
rig.name = 'Assassin_Skeleton'
pose_file = Path(LocationService.get_mpfb_data('poses')) / 'game_engine_fk/t-pose.json'
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='POSE')
RigService.set_pose_from_dict(rig, json.loads(pose_file.read_text()))
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
print('CREATED', len(body.data.vertices), len(body.data.polygons))
print('BONES', [(b.name, tuple(b.head), tuple(b.tail)) for b in rig.pose.bones if any(s in b.name for s in ['arm','hand','thigh','foot','clavicle'])])
for obj in [body,rig]:
    for col in list(obj.users_collection): col.objects.unlink(obj)
    collection.objects.link(obj)
result = {'body': body.name, 'rig':rig.name,'bones':len(rig.data.bones)}
