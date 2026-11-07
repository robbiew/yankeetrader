"""Independent fractional-stock fixture, capture and actual pickup conversion audit.

No acquisition writer or replay model is imported. The conversion policy is not
an input: exact native force deltas and literal receipts are classified afterward.
"""
import argparse
import copy
import datetime
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import struct

import verify_maintenance_gateway_hazards as gateway
import verify_maintenance_departure_merge as departure

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/stock-conversion-controls'
PINS_SHA='947f240ae9af8dae4ddab65aea3c09853cf7aa51907eda4687c4c5fddfa06df2'
PARENT_SOURCE=dict(corpus='evolved-combat-controls',profile='route-mercenary-100000',stage='child-2',pins='fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5')
CASES={
 'quarter':dict(stock=[1,4]),'half':dict(stock=[1,2]),'three-quarter':dict(stock=[3,4]),
 'odd-half':dict(stock=[3,2]),'even-half':dict(stock=[5,2]),
 'large-below':dict(stock=[12129823,64]),'large-half':dict(stock=[379057,2]),
 'large-above':dict(stock=[12129825,64]),'large-odd-half':dict(stock=[379059,2]),
 'below-one':dict(stock=[16777215,16777216]),'above-one':dict(stock=[8388609,8388608]),
 'signed-boundary-half':dict(stock=[65535,2]),
}
PROFILES={name:(('11/05/2026','00:00:00'),)for name in CASES}
STAGES=('child-1',)
GATEWAY=dict(origin=2368,sector=3000,slot=3,name='Gateway Cache',redirects=[[2996,45],[2998,49],[2999,53]],day=308,minute=0,ground=500000,rates=[0,0,0],bank=0)
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only','observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
SOURCES={'recover_maintenance_stock_conversion.py','verify_maintenance_clock_neutral.py','capture_maintenance_stock_conversion.mjs','observe_maintenance_departure.js'}
SHA=lambda b:hashlib.sha256(b).hexdigest()
field=gateway.field
rawfield=gateway.rawfield


def encode(value):
    """Independent IEEE-single bit mapping; all declared rationals are exact."""
    assert type(value)in(int,Fraction),'only exact fixture integers or rationals'
    value=Fraction(value)
    if value==0:return bytes(4)
    ieee=int.from_bytes(struct.pack('<f',float(value)),'little')
    exponent=(ieee>>23)&255;assert 1<=exponent<=253,'normal finite jointly representable IEEE/MBF exponent'
    mantissa=(ieee&0x7fffff)|((ieee>>8)&0x800000)
    result=mantissa.to_bytes(3,'little')+bytes([exponent+2])
    bits=int.from_bytes(result[:3],'little');decoded=(-1 if bits&0x800000 else 1)*Fraction((bits&0x7fffff)|(1<<23))*Fraction(2)**(result[3]-152)
    assert decoded==value,'no rounded fixture is admitted by the independent encoder'
    return result


def parent_inputs(profile,mode):
    assert profile in CASES and mode in MODES,'independently declared fractional fixture/mode'
    root=ROOT/'research/yt-maint'/PARENT_SOURCE['corpus'];raw=(root/'pins.json').read_bytes()
    assert SHA(raw)==PARENT_SOURCE['pins'],'immutable original parent manifest'
    pins=json.loads(raw)['files'];out={}
    for name in FILES:
        relative=PARENT_SOURCE['profile']+'/'+PARENT_SOURCE['stage']+'/'+mode+'/after-'+name+'.gz';compressed=(root/relative).read_bytes()
        assert SHA(compressed)==pins[relative],'actual per-mode parent artifact'
        out[name]=gzip.decompress(compressed)
    return out


def fixture_inputs(profile,mode):
    before=parent_inputs(profile,mode);world=bytearray(before['YTDATA.DAT'])
    def put(record,offset,value):
        at=(record-1)*137+offset;world[at:at+4]=encode(value)
    for offset in range(41,65,4):put(2419,offset,3000)
    for sector,offset in((2996,45),(2998,49),(2999,53)):put(51+sector,offset,2368)
    at=(4054-1)*137;world[at:at+137]=b'Gateway Cache'.ljust(41,b' ')+bytes(96)
    for offset,value in((41,308),(73,0),(77,500000),(85,13),(89,0),(117,0),(129,Fraction(*CASES[profile]['stock']))):put(4054,offset,value)
    for offset,value in((81,0),(85,0),(93,3),(129,0)):put(3051,offset,value)
    put(2419,81,97337)
    graph_world=bytes(world)
    graph={s:[int(field(graph_world,51+s,o))for o in range(41,65,4)if field(graph_world,51+s,o)>0]for s in range(1,3001)}
    assert set(graph[2368])=={3000}and{s for s,vs in graph.items()if 3000 in vs}=={2368},'declared compulsory first hop and sole gateway predecessor'
    reverse={s:[]for s in graph}
    for source,targets in graph.items():
        for target in targets:assert 1<=target<=3000,'bounded declared graph';reverse[target].append(source)
    for network in(graph,reverse):
        seen={3000};todo=[3000]
        for source in todo:
            for target in network[source]:
                if target not in seen:seen.add(target);todo.append(target)
        assert len(seen)==3000,'fixture preserves both directions of full graph reachability'
    before['YTDATA.DAT']=bytes(world);return before


def verify_fixture(before,profile,mode,edits):
    parent=parent_inputs(profile,mode);expected=fixture_inputs(profile,mode)
    assert before==expected,'independent exact fractional fixture plus unchanged five side files'
    plan=[(2419,o,4)for o in range(41,65,4)]+[(51+s,o,4)for s,o in((2996,45),(2998,49),(2999,53))]+[(4054,0,137)]+[(3051,o,4)for o in(81,85,93,129)]+[(2419,81,4)]
    assert type(edits)is list and[(r.get('record'),r.get('offset'),len(bytes.fromhex(r.get('after',''))))for r in edits]==plan,'complete ordered fifteen-edit plan including final redundant source assignment'
    world=bytearray(parent['YTDATA.DAT'])
    for row in edits:
        assert type(row)is dict and set(row)=={'record','offset','before','after'},'exact explicit edit schema'
        record,offset=row['record'],row['offset'];assert type(record)is int and type(offset)is int and 1<=record<=4151 and 0<=offset<137,'bounded declared write'
        assert all(type(row[k])is str and re.fullmatch('[0-9a-f]+',row[k])for k in('before','after')),'complete lowercase raw edit bytes'
        old,new=bytes.fromhex(row['before']),bytes.fromhex(row['after']);assert len(old)==len(new)>0 and offset+len(old)<=137,'edit stays within one record'
        at=(record-1)*137+offset;assert world[at:at+len(old)]==old,'edit binds actual prior bytes';world[at:at+len(new)]=new
    assert bytes(world)==expected['YTDATA.DAT'],'all fixture bytes are explained without undeclared cleanup'
    return dict(unchanged_links=5,transformed_links=1,edits=15)


def verify_launch(folder,meta,profile,mode):
    folder=Path(folder);argv=json.loads((folder/'launch.json').read_text());assert argv==meta['argv']and argv[0]=='/opt/homebrew/bin/dosbox-staging','actual original host launch'
    assert len(argv)>8 and argv[8].startswith('mount c /private/tmp/'),'disposable copied mount'
    mount=Path(argv[8][8:]);assert mount.parts[-3:]==(profile,'child-1',mode),'actual fixture/stage/mode mount identity'
    commands=gateway.commands('11/05/2026','00:00:00')
    expected=[argv[0],'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for command in[argv[8],'c:']+commands+['exit']for v in('-c',command)]
    assert argv==expected and(folder/'COMMANDS.TXT').read_text()=='\n'.join(commands)+'\n','exact predeclared launch/CPU/commands'
    messages=[line.split(' | ',1)[1]for line in(folder/'dosbox.stderr').read_text().splitlines()if' | 'in line]
    assert[shlex.split(m[11:])for m in messages if m.startswith('arguments: ')]==[argv],'actual process arguments corroborate metadata'
    assert messages.count('dosbox-staging version 0.83.0 ()')==1 and len([m for m in messages if m.startswith('CPU: Setting fixed 200000 cycles.')])==1,'actual host version and fixed CPU'
    assert'SDL: dummy video initialised'in messages and "MIXER: Sound output disabled ('nosound' mode)"in messages,'actual dummy output setup'
    assert(folder/'dosbox.stdout').read_bytes()==b'','complete empty host stdout'
    date=datetime.date(2026,11,5);assert gateway.read_date((folder/'DOSDATE.LOG').read_bytes())==date,'actual original date'
    start=gateway.read_time((folder/'DOSTIME.LOG').read_bytes());assert 0<=start<=1,'midnight shell time within BIOS quantization'
    elapsed=(gateway.read_date((folder/'ENDDATE.LOG').read_bytes())-date).days*86400+gateway.read_time((folder/'ENDTIME.LOG').read_bytes())-start
    assert 0<elapsed<40,'naturally advancing bounded DOS execution'
    return mount


def verify_observation(observation,profile,before,outputs):
    # The reused utility qualifies runtime source identities and all clocks for
    # this same November5, active1/3/99/100 context; its old pickup recipe name
    # is only a selector for the identical fixed date, never a stock outcome.
    assert profile in CASES,'declared rational stock case'
    return gateway.verify_observation(observation,'pickup','child-1',before,outputs)


def verify_controller(controller,mode,observation=None,body=None,receipt=None):
    if mode=='unobserved':gateway.clocks.neutral.verify_controller(controller,mode);return None
    base=dict(controller);wait=base.pop('natural_exit_wait',None)
    assert type(wait)is dict and set(wait)=={'checks','elapsed_ms'},'recorded bounded post-detach natural-exit wait'
    assert type(wait['checks'])is int and 1<=wait['checks']<=100000,'actual finite positive liveness probe count'
    assert type(wait['elapsed_ms'])in(int,float)and math.isfinite(wait['elapsed_ms'])and 0<=wait['elapsed_ms']<=2000,'natural disappearance within the unchanged finite wait budget'
    return departure.verify_receipt_controller(base,mode,observation,body,receipt)


def verify_semantics(profile,before,outputs,trace,source_timer=None):
    old=before['YTDATA.DAT'];world=outputs['YTDATA.DAT'];initial=departure.physical(old);final=departure.physical(world)
    stock=Fraction(*CASES[profile]['stock']);assert field(old,4054,129)==stock,'fixture stock is the exact predeclared rational'
    assert world[137:51*137]==old[137:51*137],'inactive human records remain unchanged'
    assert outputs['YTNAME.DAT']==before['YTNAME.DAT']and outputs['YTYNEWS.DAT']==before['YTNEWS.DAT']and outputs['YTRMSG.DAT']==before['YTRMSG.DAT']==b'','unchanged names, exact yesterday journal rotation and empty private messages'
    assert field(world,1,81)==309 and field(world,1,45)==26,'actual calendar/base watermark'
    assert world[(4054-1)*137:(4054-1)*137+41]==b'Gateway Cache'.ljust(41,b' ')and field(world,4054,85)==13 and field(world,4054,73)==0 and field(world,3051,93)==3,'pickup leaves actual planet title/owner/link intact'
    assert field(world,4054,117)==0 and rawfield(world,4054,129)==bytes.fromhex('00008000'),'actual pickup clears complete stock using original8472 zero and leaves bank empty'
    timer=rawfield(world,4054,89)if source_timer is None else bytes.fromhex(source_timer)
    assert gateway.stock_after_economy(old,datetime.date(2026,11,5),timer)==float(stock),'zero-rate/bank economy preserves exact fractional pickup stock'
    assert field(world,4054,77)==gateway.ground_after_economy(old,datetime.date(2026,11,5),timer),'no pickup ground debit beyond independently computed growth'
    assert [field(world,4054,o)for o in(45,49,53)]==[1,1,1],'stock conversion is separate from source minimum-rate clamp'
    lines=trace.split(b'\r\n');marker=lines.index(b'Mercenary Maintenance...');xlines=lines[:marker];mlines=lines[marker:];xloss=0;i=0
    while i<len(xlines):
        if not xlines[i].startswith(b' *** '):i+=1;continue
        event=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor attacked the planet "(The Wanderer|Mercenary Base)"',xlines[i])
        assert event and xlines[i+1]==b' *** Xannor fighters destroyed!','only actual fatal earlier home encounters are admitted';xloss+=int(event[1]);i+=2
    moves=[(int(m[1]),int(m[2]))for line in mlines if(m:=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries moving from sector ([1-9][0-9]*) *',line))]
    captures=[int(m[1])for line in mlines if(m:=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries captured planet Gateway Cache!',line))]
    taking=[(int(m[1]),int(m[2]))for line in mlines if(m:=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries taking ([0-9]+) fighters from planet Gateway Cache!',line))]
    assert moves==[(97337,2368)]and captures==[97337],'exact pre-pickup source force, compulsory departure and capture stamps'
    assert len(taking)<=1 and all(actor==97337 and amount>0 for actor,amount in taking),'optional positive taking receipt stamps entering force'
    observed_delta=final[-2]-initial[-2];assert type(observed_delta)is int and 0<=observed_delta<=200000,'bounded observed whole-force conversion delta'
    assert taking==([]if observed_delta==0 else[(97337,observed_delta)]),'actual physical transfer and positive public receipt agree without a conversion-policy preset'
    assert initial[-1]-xloss==final[-1]and initial[0]==final[0]==0,'earlier Xannor fatal events and physical totals reconcile'
    assert field(world,3051,81)==97337+observed_delta and field(world,3051,85)==-2,'complete converted physical force stops at gateway'
    assert rawfield(world,2419,81)==rawfield(world,2419,85)==bytes.fromhex('00002800'),'source departure keeps original859e raw zero'
    relevant=lambda data:tuple(line for line in data.split(b'\r\n')if line.startswith(b' *** ')or b'Mercenaries captured planet'in line or b'Mercenaries taking'in line)
    assert relevant(outputs['YTNEWS.DAT'])==relevant(trace),'all literal public/console outcomes agree exactly'
    assert len(relevant(trace))==2*(len([l for l in xlines if b'Xannor attacked the planet'in l]))+1+len(taking),'no unknown public combat or alternate pickup branch is hidden'
    rows=re.findall(rb'^ *([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% +([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% *\r?$',outputs['YTSCORE.ASC'],re.M)
    assert len(rows)==1 and tuple(int(n.replace(b',',b''))for n in rows[0])==(100*final[-1],100*final[-2]),'scores bind actual saved whole physical totals'
    return dict(stock_numerator=stock.numerator,stock_denominator=stock.denominator,stock_raw=rawfield(old,4054,129).hex(),observed_converted_fighters=observed_delta,observed_stock_minus_transfer=str(stock-observed_delta),initial_physical=initial,final_physical=final,xannor_losses=xloss,capture_stamp=97337,taking_receipts=len(taking),stock_clock_provenance='authenticated source callback'if source_timer is not None else'saved timestamp corroborated by equal source-observed outputs')


def classify_conversion(profile,stats):
    """Post-observation qualification of this measured positive-stock matrix.

    This is never a synthesis seed or an assumed output used by the ledger.
    Its complete native matrix independently rules out nearest/even conversion.
    """
    stock=Fraction(*CASES[profile]['stock']);observed=stats['observed_converted_fighters']
    assert type(observed)is int and observed==stock.numerator//stock.denominator,'measured source INT/floor classification must agree with the independently observed force and receipt ledger'
    return dict(classification='measured positive stock INT-floor',converted_fighters=observed,discarded_fraction=str(stock-observed))


def verify_case(folder,profile,mode,observer):
    folder=Path(folder);assert profile in CASES and mode in MODES,'declared exact fractional profile/mode'
    meta=json.loads((folder/'capture.json').read_text())
    keys={'recipe','profile','stage','mode','parent','parent_mode','parent_pins','parent_source','applied_fixture','fixture_edits','date','clock','cycles','argv','host_sha256','guests','inputs','outputs','controller','elapsed_seconds','files'}
    assert set(meta)==keys,'exact capture metadata schema'
    assert(meta['recipe'],meta['profile'],meta['stage'],meta['mode'],meta['parent'],meta['parent_mode'])==('maintenance-stock-conversion-controls-v1',profile,'child-1',mode,'fixture-parent',mode),'actual capture recipe and independently declared identity'
    assert meta['parent_source']==PARENT_SOURCE and meta['parent_pins']==PARENT_SOURCE['pins'],'actual original evolved-world lineage'
    assert(meta['date'],meta['clock'],meta['cycles'])==('11/05/2026','00:00:00',200000),'actual calendar/clock/fixed CPU recipe'
    assert meta['host_sha256']==gateway.clocks.neutral.HOST_SHA and type(meta['elapsed_seconds'])in(int,float)and 0<meta['elapsed_seconds']<40,'actual pinned host and bounded lifecycle'
    assert meta['guests']==gateway.clocks.GUESTS,'unchanged original guests'
    for name,digest in gateway.clocks.GUESTS.items():assert SHA((ROOT/'archive/dos-original'/name).read_bytes())==digest,'immutable original executable bytes'
    names=gateway.COMMON|{'before-'+n+'.gz'for n in FILES}|{'after-'+n+'.gz'for n in FILES}
    if MODES[mode]!='unobserved':names|={'host-time.json.gz','host-flush.json','loaded-observer.js'}
    assert set(meta['files'])==names and {p.name for p in folder.iterdir()}==names|{'capture.json'},'complete retained artifact inventory'
    for name in names:assert SHA((folder/name).read_bytes())==meta['files'][name],'actual artifact digest '+name
    before={n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes())for n in FILES};outputs={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in FILES}
    assert meta['inputs']=={n:SHA(b)for n,b in before.items()}and meta['outputs']=={n:SHA(b)for n,b in outputs.items()},'all six decompressed file identities'
    assert meta['applied_fixture']is True,'declared one-time fixture intervention is never unchanged inheritance'
    lineage=verify_fixture(before,profile,mode,meta['fixture_edits']);mount=verify_launch(folder,meta,profile,mode)
    assert(folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n','DOS itself completed and returned naturally'
    controller=json.loads((folder/'controller.json').read_text());assert controller==meta['controller'],'exact retained process controller'
    observation=None;body=None;clocks=None;receipt=None
    if MODES[mode]!='unobserved':
        body=gzip.decompress((folder/'host-time.json.gz').read_bytes());observation=json.loads(body)
        config=dict(observe=MODES[mode]=='observed',output=str(mount/'host-time.json'),flush_output=str(mount/'host-flush.json'))
        assert(folder/'loaded-observer.js').read_text()=='const CONFIG='+json.dumps(config,separators=(',',':'))+';\n'+observer,'actual frozen observer and configured receipt paths'
        if MODES[mode]=='observed':clocks=verify_observation(observation,profile,before,outputs)
        else:
            assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'}and observation['recipe']=='host-dos-placement-cache-observer-v1'and observation['observe']is False and observation['exit_code']==0 and observation['events']==observation['errors']==[]and observation['dropped']==0,'attach-only has no DOS hooks, events or losses'
            gateway.clocks.neutral.verify_module(observation['module'])
        receipt=(folder/'host-flush.json').read_bytes()
    lifecycle=verify_controller(controller,MODES[mode],observation,body,receipt)
    trace=(folder/'TRACE.BIN').read_bytes();assert trace.startswith(b'\r\nYankee Trader Maintenance program\r\n')and trace.count(b'Daily Maintenance Completed OK')==1 and trace.endswith(b'Daily Maintenance Completed OK\r\n'),'complete original maintenance transcript'
    stats=verify_semantics(profile,before,outputs,trace,None if clocks is None else clocks['gateway_timer'])
    stats['conversion']=classify_conversion(profile,stats)
    return dict(before=before,outputs=outputs,stats=stats,clocks=clocks,lineage=lineage,lifecycle=lifecycle)


def verify_sources(root):
    old=ROOT/'research/yt-maint/departure-merge-controls';raw=(old/'pins.json').read_bytes();assert SHA(raw)==departure.PINS_SHA,'immutable historical observer/control-source manifest'
    pins=json.loads(raw)['files']
    for name in('observe_maintenance_departure.js','capture_maintenance_departure.mjs'):
        path='acquisition/'+name;assert SHA((old/path).read_bytes())==pins[path],'original frozen exit-receipt source identity'
    assert(root/'acquisition/observe_maintenance_departure.js').read_bytes()==(old/'acquisition/observe_maintenance_departure.js').read_bytes(),'exact unchanged receipt observer and source instrumentation'
    def flush(text):return text.split('export function validateFlush',1)[1].split('\nexport async function ',1)[0]
    assert flush((root/'acquisition/capture_maintenance_stock_conversion.mjs').read_text())==flush((old/'acquisition/capture_maintenance_departure.mjs').read_text()),'receipt byte/count validation is unchanged; bounded natural-exit waiting is separate'


def verify(directory=DEFAULT):
    root=Path(directory);raw=(root/'pins.json').read_bytes();assert SHA(raw)==PINS_SHA,'immutable independently bound stock-conversion manifest'
    pins=json.loads(raw);assert set(pins)=={'files'},'exact manifest schema'
    actual={str(p.relative_to(root))for p in root.rglob('*')if p.is_file()and p.name!='pins.json'}
    assert actual==set(pins['files']),'complete frozen corpus inventory'
    for name,digest in pins['files'].items():assert SHA((root/name).read_bytes())==digest,'immutable artifact '+name
    assert{p.name for p in root.iterdir()}==set(CASES)|{'pins.json','recipe.json','acquisition'},'exact predeclared twelve-case inventory'
    assert{p.name for p in(root/'acquisition').iterdir()}==SOURCES,'exact executed capture/source snapshots'
    expected=dict(recipe='maintenance-stock-conversion-controls-v1',cases=CASES,gateway=GATEWAY,profiles={name:[list(row)for row in rows]for name,rows in PROFILES.items()},parent=PARENT_SOURCE)
    assert json.loads((root/'recipe.json').read_text())==expected,'independently declared rational recipes and parent identity'
    verify_sources(root);observer=(root/'acquisition/observe_maintenance_departure.js').read_text();summary={}
    for profile in CASES:
        assert {p.name for p in(root/profile).iterdir()}=={'child-1'},'only the declared complete new maintenance day'
        folder=root/profile/'child-1';assert{p.name for p in folder.iterdir()}==set(MODES),'complete six-mode controls'
        rows={mode:verify_case(folder/mode,profile,mode,observer)for mode in MODES};paired=departure.paired_outputs(rows)
        assert paired['equal'],'all six exact output sets must agree for stock-conversion controls'
        summary[profile]=dict(**rows['unobserved-a']['stats'],paired=paired,observed_clocks=rows['observed-a']['clocks'])
    return dict(profiles=12,full_runs=72,output_files=432,unchanged_file_links=360,transformed_file_links=72,stages=summary)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',nargs='?',type=Path,default=DEFAULT);a=p.parse_args()
    print('Fractional stock conversion evidence verified:',verify(a.directory))
