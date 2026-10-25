from pathlib import Path
import html,json,struct,hashlib
OUT=Path(__file__).resolve().parent
runs=['main','computer','config']
raw=b''.join((OUT/('run-'+r)/'SCREENS.BIN').read_bytes() for r in runs)
assert len(raw)%4016==0 and raw
colors=['#000000','#0000aa','#00aa00','#00aaaa','#aa0000','#aa00aa','#aa5500','#aaaaaa','#555555','#5555ff','#55ff55','#55ffff','#ff5555','#ff55ff','#ffff55','#ffffff']
titles=['Startup','Ship information','Sector display','Main command help','Computer prompt','Team menu','Planet display','Planet help','Computer help','Sysop configuration']
sections=[];manifest=[]
for i in range(len(raw)//4016):
 b=raw[i*4016:(i+1)*4016]; mode=b[0]; cols=struct.unpack_from('<H',b,2)[0]
 assert mode in (2,3) and cols==80,(mode,cols)
 cells=b[16:]; lines=[];spans=[];svg=[]
 for y in range(25):
  line=''; parts=[]
  for x in range(80):
   ch,attr=cells[(y*80+x)*2:(y*80+x)*2+2]
   c=bytes([ch]).decode('cp437') if ch>=32 else (' ' if ch==0 else {1:'☺',2:'☻',3:'♥',4:'♦',5:'♣',6:'♠',7:'•',16:'►',17:'◄',24:'↑',25:'↓',26:'→',27:'←',30:'▲',31:'▼'}.get(ch,' '))
   fg=colors[attr&15];bg=colors[(attr>>4)&7]
   line+=c;parts.append(f'<span style="color:{fg};background:{bg}">{html.escape(c)}</span>')
   svg.append(f'<rect x="{x*10}" y="{y*20}" width="10" height="20" fill="{bg}"/><text x="{x*10}" y="{y*20+16}" fill="{fg}">{html.escape(c)}</text>')
  lines.append(line.rstrip());spans.append(''.join(parts))
 text='\n'.join(lines)+'\n';name=f'frame-{i+1:02d}'
 (OUT/f'{name}.txt').write_text(text)
 (OUT/f'{name}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500"><g font-family="Menlo,Consolas,monospace" font-size="17" xml:space="preserve">'+''.join(svg)+'</g></svg>')
 sections.append(f'<section><h2>{titles[i]}</h2><p>Video mode {mode}, 80 × 25. <a href="{name}.svg">SVG</a> · <a href="{name}.txt">Text</a> · <a href="{name}.png">PNG</a></p><pre>'+ '\n'.join(spans)+'</pre></section>')
 manifest.append({'frame':name,'title':titles[i],'mode':mode,'columns':cols,'cursor_column':b[6],'cursor_row':b[7],'attributes':sorted(set(cells[1::2])),'sha256':hashlib.sha256(b).hexdigest()})
(OUT/'frames.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Original DOS screens — Yankee Trader</title><style>body{background:#17191e;color:#eee;font:16px system-ui;margin:32px}pre{font:16px/20px Menlo,Consolas,monospace;background:black;width:max-content;padding:12px;white-space:pre}a{color:#91caff}section{margin-bottom:40px}p{max-width:850px}</style><h1>Original DOS screen captures</h1><p>Character positions and color attributes captured directly from the running original YT.EXE in DOSBox. Each frame preserves an 80 × 25 text page. Colors use the standard DOS palette. Font is modern monospace; blinking attributes are displayed steadily. These are local console captures; remote terminal output has not been compared. Fixture values are test data.</p>'+''.join(sections))
print(json.dumps(manifest,indent=2))
