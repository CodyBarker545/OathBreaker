import bpy
import sys
sys.path.append(r'C:\Users\cody_\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons')
import blender_mcp
if not hasattr(bpy.types.Scene, 'blendermcp_port'):
    blender_mcp.register()
bpy.ops.blendermcp.start_server()
bpy.ops.import_scene.gltf(filepath=r'D:\Downloads\Meshy_AI_Spiked_Bronze_Pauldro_1021014504_generate.glb')
for o in bpy.context.scene.objects:
    if o.type in {'CAMERA', 'LIGHT'}:
        o.hide_set(True)
print('PAULDRON_INSPECTION_READY', flush=True)
