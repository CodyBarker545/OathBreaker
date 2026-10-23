import bpy, json
from bl_ext.blender_org.mpfb.services.locationservice import LocationService
result = {'data_dir':LocationService.get_user_data(), 'objects':[o.name for o in bpy.data.objects]}
