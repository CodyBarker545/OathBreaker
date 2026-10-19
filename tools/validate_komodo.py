import bpy, os, json, struct
from mathutils import Vector
root=r'D:\SoftwareEng\Game\SourceAssets\characters\komodo_axe_warrior'
bpy.ops.wm.read_factory_settings(use_empty=True)
glb_path=os.path.join(root,'komodo_axe_warrior.glb')
with open(glb_path,'rb') as f:
    header=f.read(12);length,kind=struct.unpack('<II',f.read(8));data=json.loads(f.read(length))
mesh_names={n['name'] for n in data['nodes'] if 'mesh' in n}
assert all('skin' in n for n in data['nodes'] if 'mesh' in n),'Exported mesh missing skin'
assert not data.get('cameras') and not data.get('extensions',{}).get('KHR_lights_punctual'),'Studio in GLB'
bpy.ops.import_scene.gltf(filepath=glb_path)
# Blender's importer creates an Icosphere bone display helper, which is not a GLB mesh.
meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.name in mesh_names]
rigs=[o for o in bpy.data.objects if o.type=='ARMATURE']
assert len(rigs)==1, 'Expected one deformation rig'
assert len(rigs[0].data.bones)==48
unbound=[o.name for o in meshes if not any(m.type=='ARMATURE' for m in o.modifiers)]
assert not unbound, 'Unbound mesh: '+str(unbound)
assert len(bpy.data.actions)>0, 'Missing idle animation'
assert not any(o.type in ['CAMERA','LIGHT'] for o in bpy.data.objects), 'Studio leaked into export'
points=[o.matrix_world@Vector(p) for o in meshes for p in o.bound_box]
minimum=[min(p[i] for p in points) for i in range(3)];maximum=[max(p[i] for p in points) for i in range(3)]
assert minimum[2]>-.05 and maximum[2]<2.6, 'Unexpected vertical scale'
images=[im for im in bpy.data.images if im.type=='IMAGE']
assert len(images)>=6, 'Packed albedo maps missing'
report={'passed':True,'imported_meshes':len(meshes),'bones':len(rigs[0].data.bones),'actions':[a.name for a in bpy.data.actions],'albedo_images':len(images),'bounds_min':minimum,'bounds_max':maximum,'studio_excluded':True}
with open(os.path.join(root,'validation_report.json'),'w') as f:json.dump(report,f,indent=2)
print('VALIDATION',json.dumps(report))
