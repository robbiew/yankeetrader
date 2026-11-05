"""Count executed maintenance sites and stop at selected nth hits in disposable DOS copies."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
BINS = {'YTMAINT.EXE':'8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6',
        'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'}
SITES = (0x2237,0x226c,0x2363,0x3348,0x3c0e,0x46af,0x537e,0x7900,0x7908,0x7946,0x7989)
# Same-size46-byte diagnostic, replacing only the original return/cleanup area.
# Normal return writes remaining counter plus C! marker from CS. Nth hit writes
# selected DS state/FAC. No trace output occurs before stop/normal completion.
def patch(raw, site, nth, source=0x234):
    assert 1 <= nth <= 65535
    assert raw[512+site:512+site+2] in (b'\xcd\x3d',b'\xcd\x3e',b'\xcd\x3f')
    code=bytearray.fromhex('0e1fba6e00eb0b9c2eff0e6e007512ba3402bb0100b90400b440cd21b8004ccd219d')
    if source=='caller':
        # Two extra bytes select SS:BP+2 (far-call return IP/CS). Retain the
        # original bytes at72/73 as the normal-return marker instead of C!.
        code[16:18]=b'\x00\x00'
        code[15:18]=bytes.fromhex('161f8d5602')
        code[3]=0x70;code[11]=0x70;code[6]=0x0d;code[14]=0x14
    else:
        struct.pack_into('<H',code,16,source)
    code.extend(raw[512+site:517+site])
    code.extend(b'\xe9'+struct.pack('<H',(site+5-(0x70 if source=='caller' else 0x6e))&65535))
    code.extend(struct.pack('<H',nth)+(b'' if source=='caller' else b'C!'))
    assert len(code)==46
    out=bytearray(raw);out[0x244:0x272]=code
    out[512+site:517+site]=b'\xe9'+struct.pack('<H',(0x4b-site-3)&65535)+b'\x90\x90'
    assert len(out)==len(raw) and out[:512]==raw[:512]
    return bytes(out)


def run(destination, name, site=None, nth=65535, source=0x234, clock='00:00:00', occupied=()):
    d=destination/name;d.mkdir(parents=True,exist_ok=False)
    binary={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in BINS}
    assert {n:SHA(b)for n,b in binary.items()}==BINS
    inputs={};patches=[]
    for n in ('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT'):
        b=gzip.decompress((ROOT/'research/yt-maint/initial-controls/baseline-split'/('before-'+n+'.gz')).read_bytes())
        if n=='YTDATA.DAT' and occupied:
            b=bytearray(b)
            for sector in occupied:
                at=(50+sector)*137+93
                old=bytes(b[at:at+4]);new=bytes.fromhex('00000082') # MBF2, synthetic occupancy gate only
                b[at:at+4]=new;patches.append(dict(offset=at,before=old.hex(),after=new.hex()))
            b=bytes(b)
        (d/n).write_bytes(b);inputs[n]=SHA(b)
    copied=patch(binary['YTMAINT.EXE'],site,nth,source)if site is not None else binary['YTMAINT.EXE']
    (d/'YTMAINT.EXE').write_bytes(copied);(d/'BRUN30.EXE').write_bytes(binary['BRUN30.EXE'])
    commands=['date 11/02/2026','time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN',
              'if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG',
              'echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']
    (d/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
    with(d/'dosbox.log').open('w')as log:
        subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in ['mount c '+str(d),'c:']+commands+['exit']for v in ('-c',c)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
    trace=(d/'TRACE.BIN').read_bytes();complete=(b'Daily Maintenance Completed OK' in trace) if site is None else trace[-2:]==(binary['YTMAINT.EXE'][0x272:0x274] if source=='caller' else b'C!')
    assert (d/'ERROR.LOG').read_bytes()==b'' and (d/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'
    keep={'TRACE.BIN','ERROR.LOG','OK.LOG','RETURN.LOG','DOSDATE.LOG','DOSTIME.LOG','ENDDATE.LOG','ENDTIME.LOG','COMMANDS.TXT','dosbox.log'}
    for p in list(d.iterdir()):
        if p.suffix.upper()in ('.DAT','.ASC'):
            n='after-'+p.name+'.gz';(d/n).write_bytes(gzip.compress(p.read_bytes(),mtime=0));keep.add(n)
    meta=dict(recipe='maintenance-nth-site-v1',name=name,site=site,nth=nth,source=source,clock=clock,occupied=list(occupied),patches=patches,
              binaries=BINS,copied_sha256=SHA(copied),inputs=inputs,complete=complete,files={n:SHA((d/n).read_bytes())for n in sorted(keep)})
    (d/'result.json').write_text(json.dumps(meta,indent=2)+'\n')
    for p in d.iterdir():
        if p.name not in keep|{'result.json'}:p.unlink()
    if site is not None:
        value=trace[-4:]
        print(name,'count '+str(nth-int.from_bytes(value[:2],'little'))if complete else'raw '+value.hex(),flush=True)
    else: print(name,'untouched',complete,flush=True)
    return meta

# Retained experiment matrix: one literal-site counter at a time, then independent
# nth-hit stops. These are not one simultaneous full execution trace.
LITERAL_SITES = tuple(int(s,16) for s in "0ba5 0be0 0c1c 16a9 16bb 16e5 1719 173a 1758 17a1 17b2 18cc 2237 226c 2363 25a0 260e 2c56 3348 3c0e 46af 485a 4fbf 50b4 537e 5513 551e 5541 554c 5570 557b 55f5 5622 5a25 5bed 61b2 632e 6351 6383 63ae 7656 7908 7989".split())

def matrix():
    rows=[]
    def add(name,site=None,nth=65535,source=0x234,**kw):
        rows.append(dict(name=name,site=site,nth=nth,source=source,**kw))
    for case,kw in [('baseline',{}),('repeat',{}),('shift',dict(clock='00:00:02')),('occupied',dict(occupied=(1095,)))]:
        add(case+'--untouched',**kw)
        sites=LITERAL_SITES+(0x7900,0x7946) if case=='baseline' else SITES
        for site in sites:add(f'{case}--count-{site:04x}',site,**kw)
    for group,count,before,after,draw in [('h1',41,0x7900,0x7908,0x7910),('h2',19,0x7946,0x794e,None)]:
        for n in range(1,count+1):
            add(f'baseline--{group}-old-{n:03}',before,n)
            add(f'baseline--{group}-timer-{n:03}',before,n,0x1a)
            add(f'baseline--{group}-seed-{n:03}',after,n)
            if draw:add(f'baseline--{group}-draw-{n:03}',draw,n)
    for n in range(1,77):add(f'baseline--h2-draw-{n:03}',0x7991,n)
    for n in (1,2,3,4,5,8,75,76):add(f'baseline--h2-fac-{n:03}',0x7991,n,0x1a)
    for n in range(1,5):
        for label,site,source in [('old',0x7900,0x234),('timer',0x7900,0x1a),('seed',0x7908,0x234),('draw',0x7910,0x234)]:
            add(f'occupied--h1-{label}-{n:03}',site,n,source,occupied=(1095,))
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--pilot',action='store_true');p.add_argument('--callers',action='store_true');a=p.parse_args()
    a.destination.mkdir(parents=True,exist_ok=False)
    rows=matrix()
    if a.callers:rows=[dict(name=f'baseline--{g}-caller-{n:03}',site=site,nth=n,source='caller') for g,site,count in [('h1',0x7900,41),('h2',0x7946,19)]for n in range(1,count+1)]
    if a.pilot:rows=rows[:4]
    for row in rows:run(a.destination,**row)
