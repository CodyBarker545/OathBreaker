import bpy
from pathlib import Path

folder = Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\modular\chest_plate')
source = folder / 'assassin_chest_plate_v001.blend'
with bpy.data.libraries.load(str(source), link=False) as (available, loaded):
    loaded.objects = ['mesh_node']
armor = loaded.objects[0]
assert armor is not None
assert len(armor.data.vertices) == 348899
assert len(armor.data.polygons) == 697806
for obj in list(bpy.context.scene.objects):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
bpy.context.scene.collection.objects.link(armor)
bpy.context.scene.name = 'Assassin_Chest_Plate_v001_Inspection'
bpy.context.view_layer.objects.active = armor
armor.select_set(True)
armor.hide_set(False)
bpy.context.preferences.filepaths.save_version = 0
packaged = folder / 'assassin_chest_plate_v001_packaged.blend'
assert not packaged.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(packaged), compress=True)
packaged.replace(source)
print('CHEST_INSPECTION_SAVED', source, len(armor.data.vertices), len(armor.data.polygons))
