from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
OUT=Path(__file__).resolve().parent
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',20)
colors=['#000000','#0000aa','#00aa00','#00aaaa','#aa0000','#aa00aa','#aa5500','#aaaaaa','#555555','#5555ff','#55ff55','#55ffff','#ff5555','#ff55ff','#ffff55','#ffffff']
raw=b''.join((OUT/('run-'+r)/'SCREENS.BIN').read_bytes() for r in ['main','computer','config'])
for i in range(len(raw)//4016):
 cells=raw[i*4016+16:(i+1)*4016];lines=(OUT/f'frame-{i+1:02d}.txt').read_text().splitlines()
 im=Image.new('RGB',(960,600),'black');d=ImageDraw.Draw(im)
 for y in range(25):
  line=lines[y].ljust(80)
  for x in range(80):
   a=cells[(y*80+x)*2+1];d.rectangle((x*12,y*24,x*12+11,y*24+23),fill=colors[(a>>4)&7])
   d.text((x*12,y*24),line[x],font=font,fill=colors[a&15],anchor='la')
 im.save(OUT/f'frame-{i+1:02d}.png')
print('Rendered 10 PNG references')
