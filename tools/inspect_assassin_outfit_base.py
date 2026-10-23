import bpy,json
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\face\assassin_detailed.blend')
rig=bpy.data.objects['Assassin_Skeleton']
body=bpy.data.objects['Assassin_Body']
report={'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in rig.data.bones},'body_slices':{str(z):{'x':max(abs(v.co.x) for v in body.data.vertices if abs(v.co.z-z)<.008 and abs(v.co.x)<.23),'front':min(v.co.y for v in body.data.vertices if abs(v.co.z-z)<.008 and abs(v.co.x)<.23),'back':max(v.co.y for v in body.data.vertices if abs(v.co.z-z)<.008 and abs(v.co.x)<.23)} for z in [.2,.4,.55,.7,.9,1.,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8]}}
Path(r'D:\SoftwareEng\Game\artifacts\assassin_outfit_base.json').write_text(json.dumps(report,indent=2))
result=report
