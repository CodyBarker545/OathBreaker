import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
root=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin')
out=root/'inspection_full_shadowblade'
scene=bpy.context.scene
model=bpy.data.objects['Mesh_0']
helper=Path(r'D:\SoftwareEng\Game\tools\inspect_assassin_originals.py').read_text()
exec(helper[helper.index('def bounds('):helper.index('for index,path in enumerate(files,1):')])
render_views('model',[model],{'front':(0,-1,0),'back':(0,1,0),'left':(-1,0,0),'right':(1,0,0),'three_quarter':(3,-5,2),'top':(0,0,1)})
# Read the MPFB library into a separate disposable scene; never open/save its project.
base_scene=bpy.data.scenes.new('MPFB_Comparison_Disposable')
with bpy.data.libraries.load(str(root/'base/assassin_base.blend'),link=False) as (src,dst):
    dst.objects=src.objects
base_objects=[o for o in dst.objects if o]
for o in base_objects:base_scene.collection.objects.link(o)
base={'path':'base/assassin_base.blend','bounds':bounds(base_objects),'meshes':[{'name':o.name,'bounds':bounds([o]),'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)} for o in base_objects if o.type=='MESH'],'armatures':[{'name':o.name,'bones':len(o.data.bones),'bone_data':[{'name':b.name,'head_world':list(o.matrix_world@b.head_local),'tail_world':list(o.matrix_world@b.tail_local)} for b in o.data.bones]} for o in base_objects if o.type=='ARMATURE']}
(out/'base_comparison.json').write_text(json.dumps(base,indent=2))
bpy.context.window.scene=base_scene
render_views('mpfb',base_objects,{'front':(0,-1,0),'side':(1,0,0)})
bpy.context.window.scene=scene
print('RENDERS_COMPLETE',base['bounds'],[(a['name'],a['bones']) for a in base['armatures']])
