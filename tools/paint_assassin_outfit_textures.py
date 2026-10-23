from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import random,math
out=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\outfit\textures')
out.mkdir(parents=True,exist_ok=True)
rng=random.Random(41)
palettes={'blacksteel':(61,65,76),'gold':(155,116,62),'leather':(67,49,40),'tunic':(40,38,46),'scarlet':(120,25,37),'hood':(43,39,49),'blond':(191,156,102),'blondlight':(222,191,137),'blondshade':(130,98,61),'mask':(28,29,34)}
for name,base in palettes.items():
    n=512
    im=Image.new('RGB',(n,n));pixels=im.load()
    metal=name in ['blacksteel','gold']
    hair=name.startswith('blond')
    for y in range(n):
        for x in range(n):
            u,v=x/(n-1),y/(n-1)
            edge=min(u,v,1-u,1-v)
            brush=.045*math.sin(x*.055+math.sin(y*.018)*3)*math.sin(y*.031)
            shade=.83+.23*(1-v)+brush+rng.uniform(-.028,.028)
            if metal:
                shade+=.5*math.exp(-((edge-.025)/.012)**2)-.28*math.exp(-(edge/.009)**2)
                shade+=.10*math.cos((u-.3)*math.pi*2)*math.sin(v*math.pi)
            elif hair: shade+=.12*math.sin(x*.51+math.sin(y*.015)*2)+.05*math.sin(x*1.9+y*.009)
            else: shade+=.10*math.cos(u*math.pi*8)+.012*((x%3==0)-(y%3==0))
            pixels[x,y]=tuple(max(0,min(255,int(c*shade))) for c in base)
    d=ImageDraw.Draw(im)
    if metal:
        for _ in range(160):
            x=rng.randrange(8,n-8);y=rng.randrange(8,n-8);l=rng.randrange(2,17)
            c=tuple(min(255,int(a*rng.uniform(1.15,1.55))) for a in base)
            d.line((x,y,x+l,y+rng.randrange(-3,4)),fill=c,width=1)
        for i in range(9):
            x=12+i*59
            d.line((x,8,x+14,8),fill=tuple(int(c*1.6) for c in base),width=2)
    elif name in ['scarlet','hood','tunic','mask']:
        for _ in range(220):
            x=rng.randrange(n);y=rng.randrange(n)
            d.line((x,y,x+rng.randrange(1,6),y),fill=tuple(int(c*1.25) for c in base))
        d.line((6,0,6,n),fill=tuple(int(c*1.35) for c in base),width=2)
        d.line((n-7,0,n-7,n),fill=tuple(int(c*.55) for c in base),width=3)
    elif name=='leather':
        for y in range(8,n,12):
            for x in [9,n-10]:d.line((x,y,x,y+5),fill=(119,88,54),width=1)
    im.save(out/(name+'_painted.png'))
print('Painted 10 packed-material source maps at 512 x 512')
