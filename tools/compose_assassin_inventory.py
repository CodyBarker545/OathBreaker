from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

root=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin')
out=root/'inspection_original_models'
entries=json.loads((out/'inventory_geometry.json').read_text())
font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',21)
small=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',16)
labels=['Boot and greave','Knee guard','Bronze bracer','Scarf and cape','Crimson hood','Belted waist skirt','Dark fantasy pauldron','Spiked shoulder armor','Strapped chest armor']
overview=Image.new('RGB',(3*480,3*610),'#202327');d=ImageDraw.Draw(overview)
for index,entry in enumerate(entries,1):
    if entry['status']!='inspected':continue
    name=labels[index-1]
    sheet=Image.new('RGB',(3*480,2*600+64),'#202327');draw=ImageDraw.Draw(sheet)
    draw.text((18,12),f'{index:02} — {name} — {entry["triangles"]:,} triangles',font=font,fill='white')
    for k,view in enumerate(['front','back','side','three_quarter','top','bottom']):
        p=out/f'{index:02}_{view}.png'
        if not p.exists():continue
        x=(k%3)*480;y=(k//3)*600+64
        sheet.paste(Image.open(p).convert('RGB'),(x,y+24))
        draw.text((x+12,y),view.replace('_',' ').title(),font=small,fill='#e1e6eb')
    sheet.save(out/f'{index:02}_views.jpg',quality=92)
    x=((index-1)%3)*480;y=((index-1)//3)*610
    p=out/f'{index:02}_three_quarter.png'
    if p.exists():overview.paste(Image.open(p).convert('RGB'),(x,y+42))
    d.text((x+12,y+8),f'{index:02} {name}',font=font,fill='white')
    d.text((x+12,y+583),f'{entry["triangles"]:,} triangles',font=small,fill='#d4d9df')
overview.save(out/'asset_overview.jpg',quality=92)
print('Composed',len(entries),'asset sheets')
