"""Independent active-planet/foreign-route provenance and semantic evidence audit.

No capture writer or maintenance replay model is imported. Input fixtures are
reconstructed independently; captured raw state is audit evidence only.
"""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import re

import verify_maintenance_placement as placement
import verify_maintenance_clock_matrix as clocks
from verify_rng_native import image

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/occupied-route-controls'
PINS_SHA='7c01a0ef401f3df96f413e4aefd046c7f8a57499a1dfa537c83ea950d0dc7a3a'
SHA=lambda b:hashlib.sha256(b).hexdigest()
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only','observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
CASES={
 'wanderer-occupied':{'planets':[[1095,2,'Occupied Haven',-1,500000]],'forces':[]},
 'wanderer-two-occupied':{'planets':[[1095,2,'Occupied Haven',-1,500000],[1792,3,'Second Haven',-1,500000]],'forces':[]},
 'base-occupied':{'planets':[[2598,2,'Occupied Haven',-1,500000]],'forces':[]},
 'route-planet-friendly':{'planets':[[854,2,'Route Haven',-1,500000]],'forces':[]},
 'route-planet-neutral':{'planets':[[854,2,'Route Haven',0,500000]],'forces':[]},
 'route-mercenary-37':{'planets':[],'forces':[[854,37,-2]]},
 'route-mercenary-100000':{'planets':[],'forces':[[854,100000,-2]]},
 'route-neutral-37':{'planets':[],'forces':[[854,37,0]]},
 'wanderer-active-rejection':{'planets':[[2787,2,'Occupied Haven',-1,500000]],'forces':[]},
 'base-active-rejection':{'planets':[[20,2,'Occupied Haven',-1,500000]],'forces':[]},
}
SOURCES={'recover_maintenance_occupied.py','recover_maintenance_occupied_rejections.py','observe_maintenance_placement.js','capture_maintenance_clock_neutral.mjs','recover_maintenance_sequence.py','replay_qb_graph.py','verify_maintenance_clock_neutral.py'}
COMMON=placement.COMMON
OUTPUTS=placement.OUTPUTS
field=placement.field
rawfield=placement.rawfield
encode=placement.encode
verify_launch=placement.verify_launch


def before_inputs(case):
    assert case in CASES,'independent occupied-route case inventory'
    result=clocks.neutral.before_input_bytes();world=bytearray(result['YTDATA.DAT'])
    def put(rec,offset,value):
        at=(rec-1)*137+offset;world[at:at+4]=encode(value)
    for sector,slot,name,owner,ground in CASES[case]['planets']:
        rec=4051+slot;at=(rec-1)*137
        world[at:at+137]=name.encode('ascii').ljust(41,b' ')+bytes(96)
        for offset,value in [(41,305),(45,1000),(49,1000),(53,1000),(73,owner),(77,ground),(85,len(name))]:put(rec,offset,value)
        put(51+sector,93,slot)
    for sector,force,owner in CASES[case]['forces']:
        put(51+sector,81,force);put(51+sector,85,owner)
    result['YTDATA.DAT']=bytes(world)
    verify_fixture(result['YTDATA.DAT'],case)
    return result


def verify_fixture(before,case):
    assert case in CASES and len(before)==4151*137,'complete admitted before-world'
    seen=set()
    for sector,slot,name,owner,ground in CASES[case]['planets']:
        assert 7<sector<=3000 and 2<=slot<=98 and slot not in seen,'ordinary unique active planet slot'
        seen.add(slot);rec=4051+slot
        assert field(before,51+sector,93)==slot,'active planet has actual sector link'
        assert before[(rec-1)*137:(rec-1)*137+41]==name.encode('ascii').ljust(41,b' '),'actual named active planet'
        assert field(before,rec,85)==len(name) and field(before,rec,73)==owner and field(before,rec,77)==ground,'active owner/ground/name fields'
        assert field(before,rec,41)==305 and all(field(before,rec,o)==1000 for o in(45,49,53)),'prior-day production rates'
        assert all(field(before,rec,o)==0 for o in range(41,137,4) if o not in(41,45,49,53,73,77,85)),'explicitly empty remaining planet fields'
    for sector,force,owner in CASES[case]['forces']:
        assert field(before,51+sector,81)==force and field(before,51+sector,85)==owner,'actual foreign/neutral sector force'
    active={r-4051 for r in range(4052,4152) if field(before,r,85)>0}
    assert active==seen,'no hidden active before-planets'


def verify_observation(observation):
    """Authenticate complete raw source context without assuming pre-planet RNG."""
    assert observation.get('recipe')=='host-dos-placement-cache-observer-v1','occupied-route source observation identity'
    standard=copy.deepcopy(observation);standard['recipe']='host-dos-clock-matrix-observer-v1';witnesses=[]
    for ordinal,event in enumerate(standard['events'],1):
        states=[]
        for side in('before','after'):
            raw=event[side].pop('rng_raw')
            assert type(raw)is str and re.fullmatch('[0-9a-f]{8}',raw),'four complete raw RNG bytes'
            state=int.from_bytes(bytes.fromhex(raw),'little');assert state<2**24,'actual24bit RNG state';states.append(state)
        assert states[0]==states[1],'DOS callback preserves RNG state'
        pair=clocks.event_pair(event,ordinal)
        if pair.get('kind')=='timer'and pair.get('role')=='helper1'and pair['nested_return_ip']in(0x1f88,0x437a):
            witnesses.append(dict(role='wanderer'if pair['nested_return_ip']==0x1f88 else'base',ordinal=ordinal,old_state=states[0],timer=pair['seconds']))
    inputs=clocks.model_inputs(standard)
    assert inputs['cycles']==200000,'fixed observed CPU budget'
    assert witnesses and witnesses[0]['role']=='wanderer','complete original placement phase evidence'
    return witnesses,inputs


def verify_initial_rng(witnesses,inputs,active_count):
    assert type(active_count)is int and 0<=active_count<=2,'bounded admitted active-planet count'
    timer=bytearray(inputs['startup']);timer[2]^=128
    state=5|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16)
    for _ in range(3*active_count):state=(214013*state+1744579)&0xffffff
    assert witnesses[0]['old_state']==state,'bounded prior active-planet RNG advancement'


def verify_semantics(case,before,outputs):
    """Saved forces, literal public outcomes and scores independently reconcile.

    The retained 100000-force case's misleading lost/dstrd source labels are not
    treated as general gameplay semantics: actual faction deltas select the
    measured mapping, and an independent literal inventory prevents relabeling.
    """
    world=outputs['YTDATA.DAT'];assert len(world)==4151*137,'complete semantic world'
    totals={-1:0,-2:0,0:0}
    for sector in range(1,3001):
        force=field(world,51+sector,81);owner=field(world,51+sector,85)
        assert force.denominator==1 and 0<=force<=100000,'bounded whole saved physical force'
        if force:
            assert owner in totals,'admitted saved physical owner'
            totals[owner]+=int(force)
    news=outputs['YTNEWS.DAT'];xloss=mloss=0;planet_attacks=0;mercenary_rows=[]
    lines=news.split(b'\r\n')
    for index,line in enumerate(lines):
        if b'Xannor attacked the planet'in line:
            match=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor attacked the planet "Route Haven"',line)
            assert match and lines[index+1]==b' *** Xannor fighters destroyed!','exact retained planetary attack/death pair'
            xloss+=int(match[1]);planet_attacks+=1
        if b'Mercenaries: lost'in line:
            match=re.fullmatch(rb' \*\*\* Mercenaries: lost ([1-9][0-9]*), dstrd ([1-9][0-9]*) \((Xannor|Plyr) ftrs dstrd\)',line)
            assert match,'exact retained foreign-force result literal'
            mercenary_rows.append((int(match[1]),int(match[2]),match[3]));xloss+=int(match[1]);mloss+=int(match[2])
    initial={-1:0,-2:0,0:0}
    for sector in range(1,3001):
        force=field(before,51+sector,81);owner=field(before,51+sector,85)
        if force:initial[owner]+=int(force)
    assert totals[-1]+xloss==initial[-1] and totals[-2]+mloss==initial[-2] and totals[0]==initial[0],'physical before/after and literal public casualties reconcile'
    if case=='route-planet-neutral':
        assert planet_attacks==19 and mercenary_rows==[] and xloss==5978 and field(world,4053,77)==504975,'retained neutral planetary casualties and spent ground'
    elif case=='route-mercenary-37':
        assert planet_attacks==0 and mercenary_rows==[(15,10,b'Xannor'),(22,27,b'Plyr')],'retained mixed foreign-force source labels'
    elif case=='route-mercenary-100000':
        assert planet_attacks==0 and len(mercenary_rows)==19 and all(row[2]==b'Xannor'for row in mercenary_rows) and(xloss,mloss)==(4852,2475),'retained large foreign-force casualties'
    else:assert planet_attacks==0 and mercenary_rows==[],'noncombat control has no invented combat news'
    rows=re.findall(rb'^ *([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% +([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% *\r?$',outputs['YTSCORE.ASC'],re.M)
    assert len(rows)==1 and tuple(int(x.replace(b',',b''))for x in rows[0])==(totals[-1]*100,totals[-2]*100),'actual faction score columns match saved survivors'
    return dict(xannor=totals[-1],mercenary=totals[-2],neutral=totals[0],xannor_losses=xloss,mercenary_losses=mloss,planet_attacks=planet_attacks,foreign_summaries=len(mercenary_rows))


def verify_active_outputs(case,before,outputs):
    """These strong retained planets survive; do not infer arbitrary combat rules."""
    world=outputs['YTDATA.DAT'];assert len(world)==len(before)==4151*137,'complete full-run world'
    for sector,slot,name,owner,ground in CASES[case]['planets']:
        rec=4051+slot
        assert field(world,51+sector,93)==slot,'retained active planet sector link'
        assert world[(rec-1)*137:(rec-1)*137+41]==name.encode('ascii').ljust(41,b' ')and field(world,rec,85)==len(name),'retained active planet name'
        assert field(world,rec,41)==306 and all(field(world,rec,o)==1010 for o in(45,49,53)),'actual initial active-planet maintenance growth'
        expected_ground=504975 if case=='route-planet-neutral' else 505000
        assert field(world,rec,73)==owner and field(world,rec,77)==expected_ground,'exact surviving strong planet owner/ground'
    assert outputs['YTRMSG.DAT']==b'','inactive-player controls do not invent private notices'
    assert set(outputs)==OUTPUTS,'complete six output files'

def verify_case(folder,case,mode,observer):
    folder=Path(folder);meta=json.loads((folder/'capture.json').read_text())
    assert set(meta)=={'recipe','case','mode','date','clock','cycles','patches','argv','host_sha256','guests','inputs','outputs','controller','elapsed_seconds','files'},'exact occupied-route metadata schema'
    assert case in CASES and mode in MODES and (meta['recipe'],meta['case'],meta['mode'])==('maintenance-occupied-route-v1',case,mode),'independent case/mode identity'
    assert (meta['date'],meta['clock'],meta['cycles'])==('11/02/2026','00:00:00',200000)and meta['patches']==CASES[case],'independent a-priori fixture declaration'
    assert meta['host_sha256']==clocks.neutral.HOST_SHA and 0<meta['elapsed_seconds']<40,'pinned host and bounded capture'
    before=before_inputs(case);assert meta['inputs']=={n:SHA(b)for n,b in before.items()},'independently reconstructed three before-inputs'
    assert meta['guests']==clocks.GUESTS,'unmodified original full-run guests'
    for guest,digest in clocks.GUESTS.items():assert SHA((ROOT/'archive/dos-original'/guest).read_bytes())==digest,'immutable original guest identity'
    names=COMMON|{'after-'+n+'.gz'for n in OUTPUTS}
    if MODES[mode]!='unobserved':names|={'host-time.json.gz','loaded-observer.js'}
    assert set(meta['files'])==names and {p.name for p in folder.iterdir()}==names|{'capture.json'},'complete exact capture artifact inventory'
    for name in names:assert SHA((folder/name).read_bytes())==meta['files'][name],'declared raw capture file hash '+name
    mounted=verify_launch(folder,meta)
    assert(folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n','natural DOS return witnesses'
    controller=json.loads((folder/'controller.json').read_text());assert controller==meta['controller'],'actual lifecycle metadata'
    trace=(folder/'TRACE.BIN').read_bytes();assert trace.startswith(b'\r\nYankee Trader Maintenance program\r\n'),'original maintenance transcript header'
    observation=None;witnesses=None
    if MODES[mode]!='unobserved':
        obraw=gzip.decompress((folder/'host-time.json.gz').read_bytes());observation=json.loads(obraw)
        config=dict(observe=MODES[mode]=='observed',output=str(mounted/'host-time.json'))
        assert(folder/'loaded-observer.js').read_text()=='const CONFIG='+json.dumps(config,separators=(',',':'))+';\n'+observer,'exact actual observer source/config'
        if config['observe']:
            witnesses,inputs=verify_observation(observation)
            verify_initial_rng(witnesses,inputs,len(CASES[case]['planets']))
        else:
            assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'}and observation['recipe']=='host-dos-placement-cache-observer-v1'and observation['observe']is False and observation['events']==observation['errors']==[]and observation['exit_code']==observation['dropped']==0,'attach-only has no hooks/events'
            clocks.neutral.verify_module(observation['module'])
        clocks.neutral.verify_controller(controller,MODES[mode],observation,obraw)
    else:clocks.neutral.verify_controller(controller,'unobserved')
    outputs={name:gzip.decompress((folder/('after-'+name+'.gz')).read_bytes())for name in OUTPUTS}
    assert meta['outputs']=={n:SHA(b)for n,b in outputs.items()},'complete raw output identity'
    assert trace.count(b'Daily Maintenance Completed OK')==1 and trace.endswith(b'Daily Maintenance Completed OK\r\n'),'complete untouched maintenance footer'
    verify_active_outputs(case,before['YTDATA.DAT'],outputs)
    verify_semantics(case,before['YTDATA.DAT'],outputs)
    if witnesses is not None:placement.verify_placements(before['YTDATA.DAT'],outputs,trace,witnesses)
    return dict(before=before,outputs=outputs,witnesses=witnesses,trace=trace)


def verify_native(root):
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    assert SHA(original)==clocks.GUESTS['YTMAINT.EXE'],'immutable original native subject'
    loaded=image(original);packet=json.loads((Path(root)/'native/rea.json').read_text())
    assert set(packet)=={'records'}and len(packet['records'])==1,'one complete original native read'
    record=packet['records'][0];params=record['parameters'];result=record['normalized_result']
    assert record['operation']=='read_bytes'and record['subject']['name']=='YTMAINT.EXE'and record['subject']['digest']['sha256']==clocks.GUESTS['YTMAINT.EXE'],'original native read identity'
    assert int(params['address'],16)==0x11660 and params['length']==720,'source-qualified active-planet native range'
    data=bytes.fromhex(result['bytes_hex'])
    assert result['complete']is True and result['requested_bytes']==result['returned_bytes']==len(data)==720,'complete active-planet native extent'
    assert data==loaded[0x1660:0x1660+720],'all observed native bytes match relocated original'
    for site in(0x16a9,0x16bb,0x16e5):assert loaded[site:site+3]==bytes.fromhex('cd3d34'),'source-qualified original active-planet RND call'


def verify_paired_outputs(cases):
    assert set(cases)==set(MODES),'all six independent modes for complete output comparison'
    reference=cases['unobserved-a']['outputs']
    assert set(reference)==OUTPUTS,'six complete reference outputs'
    for result in cases.values():
        assert set(result['outputs'])==OUTPUTS and result['outputs']==reference,'all six complete outputs equal both unobserved controls'
    return reference


def verify(directory=DEFAULT):
    directory=Path(directory);raw=(directory/'pins.json').read_bytes()
    assert SHA(raw)==PINS_SHA,'immutable occupied-route corpus manifest'
    pins=json.loads(raw);assert set(pins)=={'files'},'exact independent manifest schema'
    actual={str(p.relative_to(directory))for p in directory.rglob('*')if p.is_file()and p.name!='pins.json'}
    assert actual==set(pins['files']),'complete pinned artifact inventory'
    for name,digest in pins['files'].items():assert SHA((directory/name).read_bytes())==digest,'immutable artifact '+name
    assert json.loads((directory/'recipe.json').read_text())=={'recipe':'maintenance-occupied-route-v1','cases':CASES},'independent complete fixture recipe'
    assert {p.name for p in(directory/'acquisition').iterdir()}==SOURCES,'complete frozen acquisition source inventory'
    assert {p.name for p in directory.iterdir()}==set(CASES)|{'pins.json','recipe.json','acquisition','native'},'ten-case corpus inventory'
    verify_native(directory)
    observer=(directory/'acquisition/observe_maintenance_placement.js').read_text();accepted={}
    for case in CASES:
        assert {p.name for p in(directory/case).iterdir()}==set(MODES),'all six independent modes'
        cases={mode:verify_case(directory/case/mode,case,mode,observer)for mode in MODES}
        reference=verify_paired_outputs(cases)
        for mode in('observed-a','observed-b','observed-c'):
            values=placement.verify_placements(cases[mode]['before']['YTDATA.DAT'],reference,cases[mode]['trace'],cases[mode]['witnesses'])
            if case in accepted:assert values==accepted[case],'repeat source-qualified placement outcomes'
            accepted[case]=values
    return dict(cases=10,full_runs=60,paired_files=360,native_reads=1,placements=accepted)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',nargs='?',type=Path,default=DEFAULT);a=p.parse_args()
    print('Occupied-route evidence verified:',verify(a.directory))
