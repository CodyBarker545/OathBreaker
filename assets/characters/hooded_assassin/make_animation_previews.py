"""Assemble actual Blender renders into GIFs and a contact sheet using Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw

out=Path(__file__).resolve().parent/'blendswap_assassin'
clips=['Idle','Walk','Arm_Motion_Test']
contact=Image.new('RGB',(1000,930),(22,25,31))
draw=ImageDraw.Draw(contact)
for row,name in enumerate(clips):
    paths=sorted((out/'frames'/name).glob('*.png'))
    assert paths, name
    images=[Image.open(p).convert('RGB') for p in paths]
    palette=images[0].quantize(colors=160)
    frames=[im.quantize(palette=palette) for im in images]
    duration=167 if name=='Idle' else 83
    frames[0].save(out/(name.lower()+'.gif'),save_all=True,append_images=frames[1:],loop=0,duration=duration,disposal=2,optimize=False)
    draw.text((18,row*310+12),name.replace('_',' '),fill=(236,226,211))
    for col,fraction in enumerate([0,.25,.5,.75]):
        im=images[min(len(images)-1,round(fraction*len(images)))].resize((240,270))
        contact.paste(im,(10+col*247,row*310+34))
contact.save(out/'animation_contact_sheet.jpg',quality=92)
print('Created 3 animation GIFs and contact sheet:',out)
