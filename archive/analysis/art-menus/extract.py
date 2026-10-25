#!/usr/bin/env python3
"""Rebuild the reference pack from original files; never modify the DOS inputs."""
from pathlib import Path
import hashlib, html, json, re, shutil, struct
from collections import Counter
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

def sha(b): return hashlib.sha256(b).hexdigest()
def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8')

def literals(name):
    b = (ROOT/name).read_bytes()
    candidates = []
    for p in range(len(b)-4):
        n, ptr = struct.unpack_from('<HH', b, p)
        raw = b[p+4:p+4+n]
        if 1 <= n <= 4096 and len(raw) == n and all(x >= 32 or x in (9,10,13,27) for x in raw):
            candidates.append((p+4-ptr, p, raw))
    base = Counter(v[0] for v in candidates).most_common(1)[0][0]
    rows = [{'descriptor_offset':p, 'text_offset':p+4, 'length':len(raw),
             'text':raw.decode('cp437'), 'hex':raw.hex()} for k,p,raw in candidates if k == base]
    return {'source':name, 'sha256':sha(b), 'pointer_base':base, 'strings':rows}

sources = ['YT.EXE','YTCONFIG.EXE','YT-INIT.EXE','YTMAINT.EXE','RMT-INIT.EXE']
catalog = {n:literals(n) for n in sources}
write(OUT/'strings.json', json.dumps(catalog, indent=2, ensure_ascii=False)+'\n')
for n,c in catalog.items():
    write(OUT/'strings'/f'{n}.txt', '\n'.join(f"{r['text_offset']:08x}  {r['text']}" for r in c['strings'])+'\n')

# Bounds identify original literal groups, not inferred terminal rows or colors.
menus = [
 ('fighter-encounter','YT.EXE',0x23655,0x2371e),
 ('main-command','YT.EXE',0x23c79,0x2405b),
 ('planet','YT.EXE',0x24ee2,0x2506c),
 ('planet-transfer','YT.EXE',0x25146,0x251e4),
 ('team','YT.EXE',0x25594,0x25698),
 ('computer','YT.EXE',0x26428,0x26660),
 ('port-report-filters','YT.EXE',0x26660,0x266fa),
 ('sysop-configuration','YTCONFIG.EXE',0x271e,0x29b7),
]
sections=['<section><h2>Recovered DOS layouts and colors</h2><p><a href="screen-recovery/index.html">View ten original DOS screen captures</a></p></section>']
for slug,n,lo,hi in menus:
    rows=[r for r in catalog[n]['strings'] if lo<=r['text_offset']<hi]
    # Two command-alphabet implementation literals are not menu display text.
    rows=[r for r in rows if r['text'] not in ('W!+ABCFLMPQTD$GN',)]
    body='\n'.join(r['text'] for r in rows)+'\n'
    write(OUT/'menus'/f'{slug}.txt',body)
    write(OUT/'menus'/f'{slug}.json',json.dumps({'source':n,'strings':rows},indent=2,ensure_ascii=False)+'\n')
    sections.append(f'<section><h2>{slug}</h2><p>Extracted literals from {n}; original order. Layout and color are not reconstructed.</p><pre>{html.escape(body)}</pre></section>')

# Render original opening ANSI to an 80-column character grid with DOS colors.
COLORS=['#000000','#aa0000','#00aa00','#aa5500','#0000aa','#aa00aa','#00aaaa','#aaaaaa',
        '#555555','#ff5555','#55ff55','#ffff55','#5555ff','#ff55ff','#55ffff','#ffffff']
def ansi_html(raw):
    grid={}; x=y=0; fg=7; bg=0; bold=False; saved=(0,0)
    s=raw.decode('cp437'); i=0
    while i<len(s):
        if s[i]=='\x1b':
            m=re.match(r'\x1b\[([0-9;?]*)([A-Za-z])',s[i:])
            if m:
                args=[int(a) if a else 0 for a in m[1].lstrip('?').split(';')]; op=m[2]; a=args[0]; i+=len(m[0])
                if op=='m':
                    for v in args:
                        if v==0: fg,bg,bold=7,0,False
                        elif v==1: bold=True
                        elif v==22: bold=False
                        elif 30<=v<=37: fg=v-30
                        elif 40<=v<=47: bg=v-40
                        elif v==39: fg=7
                        elif v==49: bg=0
                elif op in ('H','f'): y=max(0,(a or 1)-1); x=max(0,((args[1] if len(args)>1 else 1) or 1)-1)
                elif op=='A': y=max(0,y-(a or 1))
                elif op=='B': y+=a or 1
                elif op=='C': x+=a or 1
                elif op=='D': x=max(0,x-(a or 1))
                elif op=='J' and a==2: grid.clear()
                elif op=='K':
                    for xx in range(x,80): grid.pop((y,xx),None)
                elif op=='s': saved=(x,y)
                elif op=='u': x,y=saved
                else: raise ValueError(f'Unsupported ANSI sequence: {m[0]!r}')
                continue
            raise ValueError(f'Unrecognized escape at {i}')
        c=s[i]; i+=1
        if c=='\r': x=0
        elif c=='\n': y+=1
        elif c in ('\x1a','\x07'): pass
        else:
            if x>=80: x=0; y+=1
            grid[y,x]=(c,fg+8 if bold and fg<8 else fg,bg); x+=1
    lines=[]
    for yy in range(max((p[0] for p in grid),default=0)+1):
        line=''
        for xx in range(80):
            c,f,b=grid.get((yy,xx),(' ',7,0))
            line+=f'<span style="color:{COLORS[f]};background:{COLORS[b]}">{html.escape(c)}</span>'
        lines.append(line)
    return '\n'.join(lines)

manifest=[]
for n in ['YTOPEN.ANS','YTOPEN.ASC','YTINSTR.DOC']:
    raw=(ROOT/n).read_bytes(); dest=OUT/'originals'/n; dest.parent.mkdir(exist_ok=True); shutil.copyfile(ROOT/n,dest)
    assert dest.read_bytes()==raw
    manifest.append({'source':n,'sha256':sha(raw),'bytes':len(raw)})
    text=raw.decode('cp437'); write(OUT/'decoded'/f'{n}.txt',text)
    if n.startswith('YTOPEN'):
        rendered=ansi_html(raw) if n.endswith('ANS') else html.escape(text)
        sections.insert(0,f'<section><h2>{n}</h2><p>Original CP437 artwork; ANSI colors and cursor positioning rendered at 80 columns.</p><pre class="art">{rendered}</pre></section>')

# Preserve existing DOS capture evidence, indexed by source and hash.
logs=[]
for src in sorted((ROOT/'analysis').rglob('GAME.LOG')):
    if OUT in src.parents: continue
    raw=src.read_bytes(); slug=src.parent.name; dest=OUT/'dos-captures'/f'{slug}.txt'
    assert not dest.exists() or dest.read_text()==raw.decode('cp437').replace('\r\n','\n'), dest
    write(dest,raw.decode('cp437').replace('\r\n','\n'))
    logs.append({'source':str(src.relative_to(ROOT)), 'reference':str(dest.relative_to(OUT)), 'sha256':sha(raw)})
manifest.extend({'source':n,'sha256':catalog[n]['sha256'],'literal_count':len(catalog[n]['strings'])} for n in sources)
write(OUT/'manifest.json',json.dumps({'sources':manifest,'dos_captures':logs},indent=2)+'\n')
links=''.join(f'<li><a href="{html.escape(r["reference"])}">{html.escape(Path(r["source"]).parent.name)}</a></li>' for r in logs)
write(OUT/'index.html','<!doctype html><meta charset="utf-8"><title>Yankee Trader 3.6 — Art and menus</title><style>body{background:#17191e;color:#eee;font:16px system-ui;margin:32px}section{margin:36px 0}pre{padding:20px;background:#000;color:#aaa;line-height:1.1;font:16px/1.1 "Menlo","Consolas",monospace;overflow:auto;white-space:pre}a{color:#91caff}p{max-width:850px}</style><h1>Yankee Trader 3.6 — Art and menus</h1><p>Original opening artwork, executable menu literals, and existing DOS session captures. Menu literal groups preserve wording and order; they do not establish runtime spacing, conditional options, or colors. Captures contain fixture player names and balances.</p>'+''.join(sections)+'<h2>DOS session captures</h2><ul>'+links+'</ul>')
print(json.dumps({'menu_groups':len(menus),'literals':{n:len(c['strings']) for n,c in catalog.items()},'dos_captures':len(logs)},indent=2))
