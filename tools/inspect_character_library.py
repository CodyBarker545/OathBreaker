import bpy
bpy.ops.wm.open_mainfile(filepath=r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\blendswap_assassin\assassin_refined.blend')
for o in bpy.data.objects:
 if o.type=='MESH' and (o.name.startswith(('Human hand','Finger','Natural','Upper','Lower','Blue','Eye','Inset','Mouth','Unmasked','Face |','Eliber','Continuous','Boot |','Soft glove'))):
  print('PART',o.name, 'materials',[m.name for m in o.data.materials if m], 'vertices',len(o.data.vertices))
print('ACTIONS',[(a.name,tuple(a.frame_range)) for a in bpy.data.actions])
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
print('RIG',rig.name, len(rig.data.bones))
