import bpy,os,shutil
ROOT=r'D:\SoftwareEng\Game';OUT=os.path.join(ROOT,'SourceAssets','characters','hooded_assassin','blendswap_assassin')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'assassin_refined.blend'))
face=bpy.data.objects['Unmasked sculpted face']
face.vertex_groups.clear();face.vertex_groups.new(name='head').add(list(range(len(face.data.vertices))),1,'REPLACE')
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');bpy.context.scene.frame_set(1)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'assassin_refined.glb'),export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
shutil.copy2(os.path.join(OUT,'assassin_refined.glb'),os.path.join(ROOT,'Assets','Characters','Assassin','Assassin.glb'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'assassin_refined.blend'))
print('FACE_HEAD_WEIGHTS_REPAIRED',len(face.data.vertices))
