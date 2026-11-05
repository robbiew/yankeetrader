"""Model-independent provenance, native-branch and encounter-output verification.

No acquisition writer or replay model is imported. Raw DOS outputs remain the
oracle; diagnostics may change timing and never replace untouched targets.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import shlex
import struct

import verify_maintenance_clock_matrix as matrix
from verify_rng_native import image

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/wanderer-encounter'
PINS_SHA='23805f6a02550ac1cc5946c89075d858e5fb061d2cbda698a24039f8a284e316'
SHA=lambda b:hashlib.sha256(b).hexdigest()
SOURCES={'recover_maintenance_wanderer.py','recover_maintenance_clock_matrix.py','capture_maintenance_clock_neutral.mjs','observe_maintenance_clock_matrix.js','recover_maintenance_sequence.py'}
# Independent expected site inventory, not imported from the acquisition writer.
PROBES={
 'ground-count':(0x61b2,65535,0x234,0),
 'production-count':(0x632e,65535,0x234,53),
 'ore-draw-count':(0x6351,65535,0x234,27),
 'organics-draw-count':(0x6383,65535,0x234,27),
 'equipment-draw-count':(0x63ae,65535,0x234,27),
 'candidate-scan-count':(0x3348,65535,0x234,50),
 'player-scan-count':(0x3c0e,65535,0x234,23700),
 'desertion-count':(0x46af,65535,0x234,2),
 'lottery-count':(0x537e,65535,0x234,1),
 'first-gate-before':(0x632e,1,0x234,bytes.fromhex('8471ea00')),
 'first-damage-before':(0x6351,1,0x234,None),
 'second-gate-before':(0x632e,2,0x234,None),
 'first-preferred-output':(0x66e2,1,0x7bac,None),
 'first-group-index':(0x632e,1,0x7be8,None),
}


def field(world,rec,off):return matrix.neutral.mbf_fraction(world[(rec-1)*137+off:(rec-1)*137+off+4])
def rawfield(world,rec,off):return world[(rec-1)*137+off:(rec-1)*137+off+4]


def verify_outputs(outputs):
    """Reconcile saved force, inherited raw fields and actual public/private news."""
    assert set(outputs)==set(matrix.neutral.OUTPUTS),'complete six-file encounter outputs'
    world=outputs['YTDATA.DAT'];assert len(world)==4151*137,'complete original world'
    assert field(world,4052,85)==12 and world[4051*137:4051*137+12]==b'The Wanderer','surviving Wanderer identity'
    assert rawfield(world,4052,73)==bytes.fromhex('00002000'),'native zero-ground owner residue'
    for off in (57,61,65,69,77,125):
        assert rawfield(world,4052,off)==bytes.fromhex('00001c00'),'unchanged Wanderer zero/warehouse residue'
    assert all(500<field(world,4052,o)<5000 for o in (45,49,53)),'all rates damaged but surviving'
    assert field(world,4052,117)==250000,'no bank loot'
    locations={i:int(field(world,51+i,105))for i in range(1,21)}
    assert all(locations[i]==0 for i in range(2,20))and locations[1]>7 and locations[20]>0,'18 dead ordinary groups, surviving HQ and group20'
    defenses=[(i,field(world,51+i,81))for i in range(1,3001)if field(world,51+i,81)>0]
    assert len(defenses)==2 and {s for s,_ in defenses}=={locations[1],locations[20]},'no phantom surviving deployments'
    assert all(field(world,51+s,85)==-1 for s,_ in defenses),'only surviving Xannor owners'
    links=[s for s in range(1,3001)if field(world,51+s,93)==1]
    assert len(links)==1 and field(world,51+links[0],81)==0,'unscreened Wanderer link survives'
    lines=outputs['YTNEWS.DAT'].split(b'\r\n')
    attacks=[i for i,line in enumerate(lines)if b'Xannor attacked'in line]
    assert len(attacks)==18,'18 public attack lines'
    forces=[]
    for i in attacks:
        match=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor attacked the planet "The Wanderer"',lines[i])
        assert match and lines[i+1]==b' *** Xannor fighters destroyed!','exact alternating attack/death journal'
        forces.append(int(match[1]))
    assert sum(forces)+sum(f for _,f in defenses)==10000,'public casualties reconcile with saved surviving force'
    assert all(attacks[i]+2==attacks[i+1]for i in range(17)),'one uninterrupted chronological encounter block'
    assert b'Calculated Dynamic Xannor Regeneration is 0 fighters.'==lines[attacks[0]-1],'encounters follow regeneration'
    assert lines[attacks[-1]+2]==b'  -  Mercenary Report:','encounters precede Mercenary phase'
    assert outputs['YTRMSG.DAT']==b'','no private message/estate helper'
    score=sum(f for _,f in defenses)*100
    assert f'{int(score):,}'.encode()in outputs['YTSCORE.ASC'],'scoreboard reports saved surviving force'
    return dict(attacks=len(attacks),casualties=sum(forces),survivors=int(sum(f for _,f in defenses)),wanderer_sector=links[0])


def verify_native(folder):
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    assert SHA(original)==matrix.GUESTS['YTMAINT.EXE'],'original maintenance identity'
    records=json.loads((folder/'native/rea.json').read_text())['records']
    assert len(records)==2,'two complete native byte observations'
    loaded=image(original)
    for record,(address,length)in zip(records,[(0x15efd,2091),(0x13113,3357)]):
        result=record['normalized_result'];data=bytes.fromhex(result['bytes_hex'])
        assert record['subject']['digest']['sha256']==matrix.GUESTS['YTMAINT.EXE']and record['operation']=='read_bytes','native original subject and operation'
        assert record['parameters']==dict(address=hex(address),length=length),'native address/extent'
        assert result['complete']is True and result['requested_bytes']==result['returned_bytes']==len(data)==length,'complete native observation'
        assert data==loaded[address-0x10000:address-0x10000+length],'native bytes independently relocated from original'
    code=original[512:]
    assert code[0x66d4:0x66dc]==bytes.fromhex('8b7e14cd3f7d9090'),'shared preferred-target output writer'
    assert code[0x3b8c:0x3b94]==bytes.fromhex('cd3f7b9090e92c02'),'fatal assault bypasses per-edge player scan'
    assert original[0x8b98+0xfd0:0x8b9c+0xfd0]==bytes.fromhex('00002000'),'source-specific owner-zero constant'


def verify_probe(folder,spec):
    site,nth,source,expected=spec
    meta=json.loads((folder/'result.json').read_text())
    assert(meta['site'],meta['nth'],meta['source'],meta['clock'])==(site,nth,source,'23:59:59'),'declared diagnostic site/input'
    assert meta['recipe']=='maintenance-nth-site-v1'and meta['binaries']==matrix.GUESTS and meta['occupied']==meta['patches']==[],'diagnostic original inputs and patch scope'
    assert meta['inputs']=={n:SHA(b)for n,b in matrix.neutral.before_input_bytes().items()},'diagnostic original before-world'
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    # Independently reconstruct the46-byte stop/count probe and five-byte jump.
    probe=bytearray.fromhex('0e1fba6e00eb0b9c2eff0e6e007512ba3402bb0100b90400b440cd21b8004ccd219d')
    struct.pack_into('<H',probe,16,source)
    probe.extend(original[512+site:517+site]);probe.extend(b'\xe9'+struct.pack('<H',(site+5-0x6e)&65535));probe.extend(struct.pack('<H',nth)+b'C!')
    assert len(probe)==46 and original[512+site:514+site]in(b'\xcd\x3d',b'\xcd\x3e',b'\xcd\x3f'),'whole original dispatch probe boundary'
    patched=bytearray(original);patched[0x244:0x272]=probe;patched[512+site:517+site]=b'\xe9'+struct.pack('<H',(0x4b-site-3)&65535)+b'\x90\x90'
    assert meta['copied_sha256']==SHA(patched),'only declared disposable executable patch'
    assert(folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n','diagnostic natural DOS return'
    assert b'time 23:59:59' in(folder/'COMMANDS.TXT').read_bytes(),'diagnostic late clock recipe'
    messages=[line.split(' | ',1)[1]for line in(folder/'dosbox.log').read_text().splitlines()if ' | 'in line]
    arguments=[shlex.split(m[11:])for m in messages if m.startswith('arguments: ')]
    assert len(arguments)==1,'one actual diagnostic host launch'
    argv=arguments[0]
    commands=['date 11/02/2026','time 23:59:59','date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN',
              'if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG',
              'echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']
    assert len(argv)>8 and argv[0]=='/opt/homebrew/bin/dosbox-staging'and argv[8].startswith('mount c /private/tmp/'),'diagnostic host and disposable mount'
    expected_argv=[argv[0],'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']
    expected_argv += [part for command in [argv[8],'c:']+commands+['exit']for part in ('-c',command)]
    assert argv==expected_argv and (folder/'COMMANDS.TXT').read_text()=='\n'.join(commands)+'\n','complete fixed diagnostic command inventory'
    assert messages.count('dosbox-staging version 0.83.0 ()')==1,'actual diagnostic host version'
    assert len([m for m in messages if m.startswith('CPU: Setting fixed 200000 cycles.')])==1,'actual diagnostic CPU budget'
    assert 'SDL: dummy video initialised'in messages and "MIXER: Sound output disabled ('nosound' mode)"in messages,'actual diagnostic dummy video/audio'
    assert b'Current date: Mon 11/02/2026'in(folder/'DOSDATE.LOG').read_bytes(),'diagnostic actual date'
    from verify_rng_clock import read_time
    # The requested whole second quantizes to this actual BIOS/DOS shell time.
    # Do not rewrite the retained log to pretend it printed23:59:59.00.
    assert read_time((folder/'DOSTIME.LOG').read_bytes())==86398.8,'diagnostic actual time'
    value=(folder/'TRACE.BIN').read_bytes()[-4:]
    if nth==65535:
        assert meta['complete']is True and value[2:]==b'C!'and nth-int.from_bytes(value[:2],'little')==expected,'independent complete literal-site count'
    else:
        assert meta['complete']is False,'terminating diagnostic must not claim full maintenance'
        if expected is not None:assert value==expected,'source-qualified diagnostic raw state'
    return value


def verify(directory=DEFAULT):
    directory=Path(directory);pinraw=(directory/'pins.json').read_bytes()
    assert SHA(pinraw)==PINS_SHA,'immutable encounter corpus manifest'
    pins=json.loads(pinraw)
    assert set(pins)=={'files','cases'}and set(pins['cases'])==set(matrix.MODES),'six independent fresh mode pins'
    actual={str(p.relative_to(directory))for p in directory.rglob('*')if p.is_file()and p.name!='pins.json'}
    assert actual==set(pins['files']),'complete encounter artifact inventory'
    for path,digest in pins['files'].items():assert SHA((directory/path).read_bytes())==digest,'immutable encounter artifact '+path
    assert {p.name for p in(directory/'acquisition').iterdir()}==SOURCES,'complete frozen acquisition source inventory'
    assert {p.name for p in(directory/'diagnostics').iterdir()}==set(PROBES),'complete fourteen-case diagnostic inventory'
    verify_native(directory)
    observer=(directory/'acquisition/observe_maintenance_clock_matrix.js').read_text()
    cases={n:matrix.verify_case(directory/'untouched/late'/n,pins['cases'][n],observer)for n in matrix.MODES}
    reference=cases['unobserved-a']['outputs']
    for item in cases.values():assert item['outputs']==reference,'all six outputs equal untouched/attach-only/observed runs'
    semantics=verify_outputs(reference)
    values={n:verify_probe(directory/'diagnostics'/n,s)for n,s in PROBES.items()}
    state=int.from_bytes(values['first-gate-before'],'little')
    advance=lambda s:(214013*s+1744579)&0xffffff
    assert int.from_bytes(values['first-damage-before'],'little')==advance(state),'first gate consumes exactly one original draw'
    for _ in range(4):state=advance(state)
    assert int.from_bytes(values['second-gate-before'],'little')==state,'gate plus three independent production draws'
    assert matrix.neutral.mbf_fraction(values['first-preferred-output'])==semantics['wanderer_sector'],'death writes exact preferred sector'
    assert matrix.neutral.mbf_fraction(values['first-group-index'])==2,'first planetary encounter is moving group2'
    return dict(untouched_runs=6,diagnostic_runs=14,native_reads=2,paired_files=36,**semantics)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path,nargs='?',default=DEFAULT);a=p.parse_args()
    print('Wanderer encounter evidence verified:',verify(a.directory))
