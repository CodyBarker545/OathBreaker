from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

folder = Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\modular\chest_plate')
font = ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf', 27)
small = ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf', 21)
canvas = Image.new('RGB', (1280, 4*810+64), '#202327')
draw = ImageDraw.Draw(canvas)
draw.text((24, 16), 'Original: 697,806 triangles', font=font, fill='white')
draw.text((664, 16), 'Initial copy: 60,000 triangles', font=font, fill='white')
for row, view in enumerate(['front','back','side','three_quarter']):
    top = 64 + row*810
    for col, label in enumerate(['highpoly','optimized']):
        image = Image.open(folder / f'v002_{label}_{view}.png').convert('RGB')
        canvas.paste(image, (col*640, top+40))
        draw.text((col*640+24, top+8), view.replace('_',' ').title(), font=small, fill='#d4d9df')
canvas.save(folder / 'v002_comparison.png')
report = json.loads((folder / 'validation_v002.json').read_text())
print(json.dumps(report, indent=2))
print('COMPARISON_SAVED', folder / 'v002_comparison.png')
