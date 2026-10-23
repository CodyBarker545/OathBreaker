import json,hashlib,struct
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin')
out=root/'inspection_full_shadowblade'
before=json.loads((out/'integrity_before.json').read_text())
after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before}
assert before==after,'Protected asset checksum changed'
(out/'integrity_verification.json').write_text(json.dumps({'all_original_files_unchanged':before==after,'before':before,'after':after},indent=2))
source=root/'orignal_models/Meshy_AI_crimson_shadowblade_1021021027_generate.glb'
with source.open('rb') as f:
    header=struct.unpack('<III',f.read(12));n,kind=struct.unpack('<II',f.read(8));g=json.loads(f.read(n))
(out/'glb_inventory.json').write_text(json.dumps({'header':header,'bytes':source.stat().st_size,'materials':g.get('materials',[]),'images':g.get('images',[]),'textures':g.get('textures',[]),'skins':g.get('skins',[]),'animations':g.get('animations',[]),'meshes':g.get('meshes',[]),'nodes':g.get('nodes',[])},indent=2))
# The Viewer Node image belongs to Blender, not the imported GLB.
data=json.loads((out/'geometry.json').read_text())
data['scene_images_not_used_by_asset']=data.pop('images')
data['asset_texture_images']=[]
(out/'geometry.json').write_text(json.dumps(data,indent=2))
views=['front','back','left','right','three_quarter','top']
canvas=Image.new('RGB',(1440,1180),(32,32,32));draw=ImageDraw.Draw(canvas)
for i,label in enumerate(views):
    im=Image.open(out/f'model_{label}.png').convert('RGB')
    im.thumbnail((480,560))
    x=(i%3)*480;y=(i//3)*590
    canvas.paste(im,(x+(480-im.width)//2,y+30))
    draw.text((x+18,y+10),label.replace('_',' ').title(),fill=(240,240,240))
canvas.save(out/'overview.jpg',quality=93)
print('Verified',len(before),'protected files unchanged; overview and GLB inventory saved.')
