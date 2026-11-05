"""Research-only byte synthesis of the bounded inactive-player initial maintenance.

Core synthesis takes pre-maintenance bytes and explicit measured clock inputs.
Completed DOS outputs are used only by the separate comparison/verification path.
This does not read or write modern gameplay saves or implement general MBF.
"""
from dataclasses import dataclass
import datetime
import hashlib

from replay_qb_ports import graph
from replay_maintenance_ports import replay_ports
from replay_maintenance_npcs import synthesize as replay_npcs
from replay_maintenance_aux import synthesize as replay_aux

SHA=lambda b:hashlib.sha256(b).hexdigest()
RECORD_SIZE=137


@dataclass(frozen=True)
class Inputs:
    date: datetime.date
    clock: str
    port_timer_minutes: tuple
    h1_timers: tuple
    h2_timers: tuple
    xannoron_timer: bytes
    initial_state: int=0xc805


def configuration_and_inactive_ranks(world, date):
    """The final day watermark and all-inactive sorted-score writer branch."""
    if type(world)is not bytes or len(world)!=4151*137:raise ValueError('default 4151-record input required')
    if not isinstance(date,datetime.date):raise ValueError('explicit calendar date required')
    day=date.timetuple().tm_yday
    get=lambda r,o:graph.mbf.get(world,r,o)
    if any(get(1,o)!=n for o,n in [(53,51),(57,3051),(61,4051),(93,4151)]):
        raise ValueError('only default record geometry is recovered')
    if any(get(r,85)!=0 for r in range(2,52)):raise ValueError('only the all-inactive-player branch is recovered')
    output=bytearray(world)
    output[81:85]=graph.mbf.enc(day)
    for r in range(2,52):
        start=(r-1)*137+109
        output[start:start+4]=graph.mbf.enc(-1)
    return bytes(output)


def synthesize(before_files, inputs):
    """Return complete six-file outputs, generated without an after-world input."""
    if type(inputs)is not Inputs:raise ValueError('explicit measured Inputs required')
    if set(before_files)!={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT'}:
        raise ValueError('the three initial handoff files are required')
    if any(type(b)is not bytes for b in before_files.values()):raise ValueError('raw before-input bytes required')
    if not isinstance(inputs.date,datetime.date):
        raise ValueError('an explicit calendar date is required')
    if type(inputs.initial_state)is not int or not 0<=inputs.initial_state<2**24:
        raise ValueError('a 24-bit startup state is required')
    day=inputs.date.timetuple().tm_yday
    before=before_files['YTDATA.DAT']
    if graph.mbf.get(before,1,45)!=inputs.date.year%100:
        raise ValueError('the input calendar year must match the explicit replay date')
    if before[:11]!=b'YTSCORE.ASC' or graph.mbf.get(before,1,41)!=11:
        raise ValueError('the default scoreboard path is required for this six-file corpus')
    if any(graph.mbf.get(before,51+sector,129)!=0 for sector in range(1,3001)):
        raise ValueError('initial mine hazards are outside this replay')
    block,port_stats=replay_ports(before,day,inputs.port_timer_minutes)
    work=before[:3051*137]+block+before[4051*137:]
    work,npc_stats=replay_npcs(work,inputs.h1_timers,inputs.h2_timers,day,
                              xannoron_timer=inputs.xannoron_timer,initial_state=inputs.initial_state)
    work=configuration_and_inactive_ranks(work,inputs.date)
    auxiliary=replay_aux(before_files,work,inputs.date,inputs.clock)
    result={'YTDATA.DAT':work,**auxiliary}
    assert set(result)=={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'}
    return result,dict(ports=port_stats,npcs=npc_stats,world_records=4151,world_bytes=len(work),
                       file_bytes={n:len(b)for n,b in result.items()})


def compare(expected, actual):
    """Compare complete files; never masks timestamps, unused fields or residues."""
    if set(expected)!=set(actual):raise ValueError('completeoutputinventoriesmustmatch')
    files={};differences=[]
    for name in sorted(expected):
        a,b=expected[name],actual[name]
        count=sum(x!=y for x,y in zip(a,b))+abs(len(a)-len(b))
        files[name]=dict(observed_bytes=len(a),replayed_bytes=len(b),byte_mismatches=count,
                         observed_sha256=SHA(a),replayed_sha256=SHA(b))
        if count:
            for offset in range(max(len(a),len(b))):
                x=a[offset]if offset<len(a)else None;y=b[offset]if offset<len(b)else None
                if x!=y:
                    if len(differences)<24:
                        row=dict(file=name,offset=offset,observed=x,replayed=y)
                        if name=='YTDATA.DAT':row.update(record=offset//137+1,field_offset=offset%137)
                        differences.append(row)
    return dict(files=files,byte_mismatches=sum(f['byte_mismatches']for f in files.values()),
                compared_bytes=sum(len(b)for b in expected.values()),first_differences=differences)


def measured_case_inputs(root=None):
    """Load pre-inputs and declared instrumented clock observations, not targets.

    The caller must authenticate these files with verify_maintenance_record_inputs
    before treating the report as verified evidence. Core synthesize() accepts no
    filesystem paths and does not call this loader.
    """
    import gzip
    from pathlib import Path
    from replay_maintenance_ports import timer_epochs
    base=Path(__file__).resolve().parents[1]
    root=Path(root)if root is not None else base/'research/yt-maint/record-input-controls'
    before_root=base/'research/yt-maint/initial-controls/baseline-split'
    before={n:gzip.decompress((before_root/('before-'+n+'.gz')).read_bytes())for n in ('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT')}
    prior=base/'research/yt-maint/sequence-controls'
    times={h:tuple((prior/f'baseline--{h}-timer-{n:03}'/'TRACE.BIN').read_bytes()[-4:] for n in range(1,c+1)) for h,c in [('h1',41),('h2',19)]}
    # These are the diagnostic's independently measured epochs. In the untouched
    # run its clock boundary differs at one port; no target-derived correction
    # is substituted into the synthesis profile.
    port_root=root/'port-default'
    epochs=[(1,(port_root/'port-0001/TRACE.BIN').read_bytes()[-4:]),
            (606,(port_root/'port-0606/TRACE.BIN').read_bytes()[-4:])]
    startup=bytearray((root/'entry/startup-timer/TRACE.BIN').read_bytes()[-4:]);startup[2]^=128
    initial=(5&255)|((startup[0]^startup[2])<<8)|((startup[1]^startup[3])<<16)
    parameters=Inputs(date=datetime.date(2026,11,2),clock='00:00:00',
                      port_timer_minutes=tuple(timer_epochs(epochs)),h1_timers=times['h1'],h2_timers=times['h2'],
                      xannoron_timer=(root/'entry/xannoron-timer/TRACE.BIN').read_bytes()[-4:],initial_state=initial)
    return before,parameters


def controlled_cases(root=None):
    """The comparison layer may read completed targets; synthesis never does."""
    import gzip
    from pathlib import Path
    from replay_qb_initializer import compare as compare_world
    root=Path(root)if root is not None else Path(__file__).resolve().parents[1]/'research/yt-maint/record-input-controls'
    before,inputs=measured_case_inputs(root)
    actual,statistics=synthesize(before,inputs)
    cases=[]
    for relative,kind in [('entry/untouched','untouched'),('entry/untouched-repeat','untouched'),
                          ('port-default/untouched','untouched'),('port-readonly/untouched','untouched'),
                          ('port-default/count-clock','instrumented-body-end'),('port-readonly/miss','instrumented-body-end')]:
        folder=root/relative
        target={p.name[len('after-'):-len('.gz')]:gzip.decompress(p.read_bytes())for p in folder.glob('after-*.gz')}
        comparison=compare(target,actual)
        comparison['world_blocks']=compare_world(target['YTDATA.DAT'],actual['YTDATA.DAT'])['blocks']
        cases.append(dict(control=relative,kind=kind,**comparison))
    return dict(recipe='bounded-initial-maintenance-record-replay-v1',statistics=statistics,cases=cases,
                clock_profile='instrumented raw TIMER/60 epochs; untouched one-port timing uncertainty retained',
                limitations=['Research only: no production gameplay, save-format or dependency change.',
                             'Default geometry, all players/planets inactive, no owned ports or hazards.',
                             'Explicit measured helper TIMER inputs; not a predictor from a clock string.',
                             'Four port timestamp bytes remain unmatched in untouched outputs; no masking or target correction.',
                             'Instrumented main-body-end output matching is not untouched normal-completion parity.',
                             'Arbitrary worlds, clocks, general MBF and native-host durability are not established.'])


def main():
    import argparse
    import json
    from pathlib import Path
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path)
    p.add_argument('--require-untouched-exact',action='store_true',help='fail while any untouched output byte differs')
    args=p.parse_args()
    from verify_maintenance_record_inputs import verify
    from verify_maintenance_sequence import verify as verify_helper_inputs
    verify_helper_inputs()
    verify()
    result=controlled_cases()
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if args.require_untouched_exact and any(c['byte_mismatches']for c in result['cases']if c['kind']=='untouched'):
        raise SystemExit('untouched replay retains a measured port TIMER boundary gap')

if __name__=='__main__':main()
