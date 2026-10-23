import bpy,json
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\base\assassin_base.blend')
body=bpy.data.objects['Assassin_Body']
rig=bpy.data.objects['Assassin_Skeleton']
groups={}
for g in body.vertex_groups:
    if any(s in g.name.lower() for s in ['head','jaw','eye','mouth','nose','chin']):
        vs=[v.co for v in body.data.vertices if any(w.group==g.index and w.weight>0.5 for w in v.groups)]
        if vs: groups[g.name]={'count':len(vs),'mean':[sum(p[i] for p in vs)/len(vs) for i in range(3)]}
result={'groups':groups,'head_bones':[(b.name,list(b.head_local),list(b.tail_local)) for b in rig.data.bones if any(s in b.name.lower() for s in ['head','neck','eye','jaw'])],'materials':[(o.name,[m.name for m in o.data.materials]) for o in [body,bpy.data.objects['Assassin_Eyes']]]}
