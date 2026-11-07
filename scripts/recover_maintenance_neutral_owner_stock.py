"""Acquire neutral-owner and mine-stock controls in copied DOS fixtures.

Each first child has one declared data-only fixture transformation. Its five
side files are unchanged; each single-day child starts from its mode-specific parent.
Original guests are unchanged; fresh paths and natural exits required; no retry.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from fractions import Fraction

from verify_maintenance_clock_neutral import GUESTS,HOST_SHA

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only','observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
CASES={
 'neutral-one-empty':dict(friendly=1,owner=0,governor=0,stock=[0,1],mines=0,clock='00:00:02'),
 'neutral-whole':dict(friendly=37,owner=0,governor=0,stock=[37,1],mines=0,clock='00:00:02'),
 'neutral-half':dict(friendly=37,owner=0,governor=0,stock=[1,2],mines=0,clock='00:00:02'),
 'neutral-mine-whole':dict(friendly=37,owner=0,governor=0,stock=[37,1],mines=1,clock='00:00:02'),
 'friendly-mine-second-two':dict(friendly=37,owner=-2,governor=0,stock=[37,1],mines=1,clock='00:00:02'),
 'friendly-mine-second-four':dict(friendly=37,owner=-2,governor=0,stock=[37,1],mines=1,clock='00:00:04'),
}

PROFILES={name:(('11/05/2026',case['clock']),)for name,case in CASES.items()}
STAGES=('child-1',)
PARENT_SOURCE=dict(corpus='evolved-combat-controls',profile='route-mercenary-100000',stage='child-2',pins='fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5')
GATEWAY=dict(origin=2368,sector=3000,slot=3,name='Gateway Cache',redirects=[[2996,45],[2998,49],[2999,53]],day=308,minute=0,ground=500000,rates=[0,0,0],bank=0)


def encode(value):
    value=Fraction(value)
    if not value:return bytes(4)
    absolute=abs(value)
    exponent=absolute.numerator.bit_length()-absolute.denominator.bit_length()
    if absolute<Fraction(2)**exponent:exponent-=1
    mantissa=absolute*Fraction(2)**(23-exponent)
    assert mantissa.denominator==1 and 0<exponent+129<=255
    bits=int(mantissa)-(1<<23)
    if value<0:bits|=1<<23
    return bits.to_bytes(3,'little')+bytes([exponent+129])


def field(data,record,offset):
    raw=data[(record-1)*137+offset:(record-1)*137+offset+4]
    if not raw[3]:return Fraction(0)
    bits=int.from_bytes(raw[:3],'little');sign=-1 if bits&(1<<23)else 1
    return sign*Fraction((bits&0x7fffff)|(1<<23))*Fraction(2)**(raw[3]-152)


def parent_inputs(mode):
    p=PARENT_SOURCE;base=ROOT/'research/yt-maint'/p['corpus']
    raw=(base/'pins.json').read_bytes();assert SHA(raw)==p['pins'],'verified original parent corpus identity'
    pins=json.loads(raw)['files'];result={}
    for name in FILES:
        relative=p['profile']+'/'+p['stage']+'/'+mode+'/after-'+name+'.gz'
        compressed=(base/relative).read_bytes();assert SHA(compressed)==pins[relative],'immutable per-mode parent output'
        result[name]=gzip.decompress(compressed)
    return result


def graph_proof(world):
    graph={s:[int(field(world,51+s,o))for o in range(41,65,4)if field(world,51+s,o)>0]for s in range(1,3001)}
    assert all(1<=v<=3000 for row in graph.values()for v in row)
    reverse={s:[]for s in graph}
    for a,vs in graph.items():
        for v in vs:reverse[v].append(a)
    def reach(g):
        seen={3000};todo=[3000]
        for a in todo:
            for v in g[a]:
                if v not in seen:seen.add(v);todo.append(v)
        return seen
    assert len(reach(graph))==len(reach(reverse))==3000,'connected forced gateway fixture'
    assert {a for a,vs in graph.items()if 3000 in vs}=={2368},'only source predecessor reaches gateway'


def fixture_inputs(case,mode):
    inputs=parent_inputs(mode);world=bytearray(inputs['YTDATA.DAT']);edits=[];c=CASES[case]
    assert field(world,2419,81)==97337 and field(world,2419,85)==-2
    assert all(field(world,3051,o)==0 for o in(81,85,93,129)) and field(world,4054,85)==0
    assert set(c)=={'friendly','owner','governor','stock','mines','clock'} and type(c['friendly'])is int and c['friendly']in(1,37,97337) and c['governor']in(0,-2)
    assert type(c['stock'])is list and len(c['stock'])==2 and all(type(n)is int for n in c['stock']) and c['stock'][1]>0
    def raw(record,offset,value):
        at=(record-1)*137+offset;before=bytes(world[at:at+len(value)])
        edits.append(dict(record=record,offset=offset,before=before.hex(),after=value.hex()))
        world[at:at+len(value)]=value
    def put(record,offset,value):raw(record,offset,encode(value))
    for off in range(41,65,4):put(2419,off,3000)
    for sector,off in GATEWAY['redirects']:put(51+sector,off,2368)
    planet=bytearray(b'Gateway Cache'.ljust(41,b' ')+bytes(96))
    for off,value in((41,308),(73,c['governor']),(77,500000),(85,13),(89,0),(117,0),(129,Fraction(*c['stock']))):
        planet[off:off+4]=encode(value)
    raw(4054,0,bytes(planet))
    for off,value in((81,c['friendly']),(85,c['owner']),(93,3),(129,c['mines'])):put(3051,off,value)
    put(2419,81,97337)
    graph_proof(world)
    assert len(edits)==15 and field(world,2419,81)==97337 and field(world,2419,85)==-2
    assert tuple(field(world,3051,o)for o in(81,85,93,129))==(c['friendly'],c['owner'],3,c['mines'])
    assert field(world,4054,73)==c['governor'] and field(world,4054,129)==Fraction(*c['stock'])
    inputs['YTDATA.DAT']=bytes(world)
    return inputs,edits


def capture(destination,scratch,profile,stage,mode,dosbox,frida):
    date,clock=PROFILES[profile][STAGES.index(stage)]
    parent='fixture-parent'if stage=='child-1'else'child-1'
    tmp=scratch/profile/stage/mode;tmp.mkdir(parents=True,exist_ok=False)
    binaries={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in GUESTS}
    assert {n:SHA(b)for n,b in binaries.items()}==GUESTS
    if stage=='child-1':inputs,edits=fixture_inputs(profile,mode)
    else:
        inputs={n:gzip.decompress((destination/profile/'child-1'/mode/('after-'+n+'.gz')).read_bytes())for n in FILES};edits=[]
    for n,b in inputs.items():(tmp/n).write_bytes(b)
    guests=binaries
    for n,b in guests.items():(tmp/n).write_bytes(b)
    commands=['date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']
    (tmp/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
    argv=[str(dosbox),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in ['mount c '+str(tmp),'c:']+commands+['exit']for v in('-c',c)]
    (tmp/'launch.json').write_text(json.dumps(argv,indent=2)+'\n');start=time.monotonic()
    actual=MODES[mode]
    if actual=='unobserved':
        with(tmp/'dosbox.stdout').open('wb')as out,(tmp/'dosbox.stderr').open('wb')as err:
            child=subprocess.Popen(argv,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=out,stderr=err)
            try:code=child.wait(timeout=30)
            except subprocess.TimeoutExpired:child.kill();child.wait();raise
        controller=dict(mode=actual,success=code==0,exit_code=code,forced=False,process_exited=child.poll()is not None,pid=child.pid)
        (tmp/'controller.json').write_text(json.dumps(controller,indent=2)+'\n')
    else:
        subprocess.run(['node',str(ROOT/'scripts/capture_maintenance_stock_conversion.mjs'),str(frida),str(tmp),str(ROOT/'scripts/observe_maintenance_departure.js'),actual],check=True,timeout=40,stdout=subprocess.DEVNULL)
        controller=json.loads((tmp/'controller.json').read_text())
    assert controller['success']and controller['process_exited']and not controller['forced'],'natural child completion required'
    assert {n:SHA((tmp/n).read_bytes())for n in guests}=={n:SHA(b)for n,b in guests.items()},'guest bytes changed during run'
    out=destination/profile/stage/mode;out.mkdir(parents=True,exist_ok=False)
    names={'COMMANDS.TXT','launch.json','controller.json','DOSDATE.LOG','DOSTIME.LOG','ENDDATE.LOG','ENDTIME.LOG','TRACE.BIN','OK.LOG','ERROR.LOG','RETURN.LOG','dosbox.stdout','dosbox.stderr'}
    for n in names:shutil.copyfile(tmp/n,out/n)
    if actual!='unobserved':
        shutil.copyfile(tmp/'host-flush.json',out/'host-flush.json')
        (out/'host-time.json.gz').write_bytes(gzip.compress((tmp/'host-time.json').read_bytes(),mtime=0));shutil.copyfile(tmp/'loaded-observer.js',out/'loaded-observer.js')
    outputs={}
    for n,b in inputs.items():(out/('before-'+n+'.gz')).write_bytes(gzip.compress(b,mtime=0))
    for p in tmp.iterdir():
        if p.suffix.upper()in('.DAT','.ASC'):
            outputs[p.name]=SHA(p.read_bytes());(out/('after-'+p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
    meta=dict(recipe='maintenance-neutral-owner-stock-controls-v1',profile=profile,stage=stage,mode=mode,parent=parent,parent_mode=mode,parent_source=PARENT_SOURCE,parent_pins=PARENT_SOURCE['pins'],applied_fixture=stage=='child-1',fixture_edits=edits,date=date,clock=clock,cycles=200000,argv=argv,host_sha256=SHA(dosbox.resolve().read_bytes()),guests={n:SHA(b)for n,b in guests.items()},inputs={n:SHA(b)for n,b in inputs.items()},outputs=outputs,controller=controller,elapsed_seconds=time.monotonic()-start)
    meta['files']={p.name:SHA(p.read_bytes())for p in sorted(out.iterdir())};(out/'capture.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(profile,stage,mode,'complete6files',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--scratch',type=Path,required=True);p.add_argument('--frida-module',type=Path,required=True);p.add_argument('--profiles',default=','.join(PROFILES));a=p.parse_args()
    out=a.destination.absolute();scratch=a.scratch.absolute();host=Path('/opt/homebrew/bin/dosbox-staging')
    assert SHA(host.resolve().read_bytes())==HOST_SHA and a.frida_module.is_file(),'pinned installed host and Frida required'
    assert not out.exists()and not scratch.exists(),'fresh full chain paths required'
    out.mkdir(parents=True);scratch.mkdir(parents=True)
    # Freeze the actually executed recipe before the first run.
    sources=out/'sources';sources.mkdir()
    for name in ('recover_maintenance_neutral_owner_stock.py','verify_maintenance_clock_neutral.py',
                 'capture_maintenance_stock_conversion.mjs','observe_maintenance_departure.js'):
        shutil.copyfile(ROOT/'scripts'/name,sources/name)
    recipe=dict(recipe='maintenance-neutral-owner-stock-controls-v1',cases=CASES,profiles=PROFILES,
                stages=STAGES,parent_source=PARENT_SOURCE,gateway=GATEWAY,modes=MODES,
                sources={p.name:SHA(p.read_bytes())for p in sorted(sources.iterdir())})
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')

    selected=a.profiles.split(',');assert len(selected)==len(set(selected))and set(selected)<=set(PROFILES),'declared unique profiles required'
    for profile in selected:
        for stage in STAGES:
            for mode in MODES:capture(out,scratch,profile,stage,mode,host,a.frida_module)

if __name__=='__main__':main()
