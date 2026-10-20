"""Persist packed albedo images before exporting the reference characters."""
import bpy,os,shutil
ROOT=r'D:\SoftwareEng\Game'
for slug,runtime in [('forsaken_sister','ForsakenSister'),('masked_ninja','MaskedNinja'),('broken_oath_knight','BrokenOathKnight'),('ash_scholar','AshScholar')]:
 folder=os.path.join(ROOT,'SourceAssets','characters',slug)
 bpy.ops.wm.open_mainfile(filepath=os.path.join(folder,slug+'.blend'))
 textures=os.path.join(folder,'textures');os.makedirs(textures,exist_ok=True)
 for i,im in enumerate(bpy.data.images):
  if im.type in {'RENDER_RESULT','COMPOSITING'}:continue
  if 'albedo' not in im.name:continue
  im.filepath_raw=os.path.join(textures,'albedo_%02d.png'%i);im.file_format='PNG';im.save();im.pack()
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 bpy.context.scene.frame_set(1);bpy.ops.object.select_all(action='DESELECT')
 for o in bpy.data.objects:
  if o==rig or (o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)):o.select_set(True)
 bpy.context.view_layer.objects.active=rig
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(folder,slug+'.blend'))
 # Height-driven Blender bump nodes are not tangent-space glTF normal maps.
 # Keep them in the native file and export the color/roughness materials without them.
 for mat in bpy.data.materials:
  if not mat.use_nodes:continue
  for node in mat.node_tree.nodes:
   if node.type=='BSDF_PRINCIPLED':
    node.inputs['Sheen Weight'].default_value=0
    for link in list(node.inputs['Normal'].links):
     if link.from_node.type=='BUMP':mat.node_tree.links.remove(link)
 path=os.path.join(folder,slug+'.glb')
 bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
 shutil.copy2(path,os.path.join(ROOT,'Assets','Characters',runtime,runtime+'.glb'))
 print('REFRESHED',slug,flush=True)
