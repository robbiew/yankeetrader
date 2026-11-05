"""Explicit host-observed profile for the bounded initial maintenance byte model.

The historical guest-instrumented profile remains unchanged. This profile derives
all clock inputs from a single source-qualified host trace; after files belong
only to the separate comparison layer.
"""
import argparse
import datetime
import gzip
import json
from pathlib import Path

from replay_maintenance_records import Inputs, synthesize, compare
from verify_maintenance_clock_neutral import model_inputs

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/clock-neutral-controls'
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
OBSERVED=('observed-a','observed-b','observed-c')
CONTROLS=('unobserved-a','observed-a','attach-only','observed-b','unobserved-b','observed-c')
HISTORICAL=('entry/untouched','entry/untouched-repeat','port-default/untouched','port-readonly/untouched')


def inputs_from_observation(observation, date):
    """Convert one authenticated raw trace to explicit inputs without file reads.

    This selected recipe has constant text HH:MM:SS and varying hundredths.
    Reject any change to that premise rather than predict unobserved writers.
    Source attribution and both MBF rounding stages are independently verified.
    """
    if date!=datetime.date(2026,11,2):raise ValueError('only the captured initial date is recovered')
    raw=model_inputs(observation)
    clocks=set()
    for event in observation['events']:
        after=event['after'];cx,dx=after['cx'],after['dx']
        clocks.add((cx>>8,cx&255,dx>>8))
    if clocks!={(0,0,0)}:raise ValueError('selected midnight text-clock profile required')
    startup=bytearray(raw['startup']);startup[2]^=128
    # Original RANDOMIZE negates startup TIMER then mixes its raw single with
    # old seed5. Preserve BRUN's actual zero residue, not a canonical substitute.
    initial=5|((startup[0]^startup[2])<<8)|((startup[1]^startup[3])<<16)
    return Inputs(date=date,clock='00:00:00',port_timer_minutes=tuple(raw['port_minutes']),
                  h1_timers=tuple(raw['helper1']),h2_timers=tuple(raw['helper2']),
                  xannoron_timer=raw['xannoron'],initial_state=initial)


def replay_cases(root=DEFAULT):
    """Compare pure before-only synthesis against complete retained outputs."""
    root=Path(root)
    before_root=ROOT/'research/yt-maint/initial-controls/baseline-split'
    before={n:gzip.decompress((before_root/('before-'+n+'.gz')).read_bytes())for n in FILES[:3]}
    targets=[(name,root/name)for name in CONTROLS]
    targets += [('historical/'+name,ROOT/'research/yt-maint/record-input-controls'/name)for name in HISTORICAL]
    rows=[];statistics=[]
    for observed in OBSERVED:
        trace=json.loads(gzip.decompress((root/observed/'host-time.json.gz').read_bytes()))
        parameters=inputs_from_observation(trace,datetime.date(2026,11,2))
        actual,stats=synthesize(before,parameters)
        statistics.append(dict(observation=observed,**stats))
        for name,folder in targets:
            expected={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in FILES}
            rows.append(dict(observation=observed,control=name,**compare(expected,actual)))
    return dict(recipe='bounded-clock-neutral-maintenance-replay-v1',cases=rows,statistics=statistics,
                scope='One all-inactive default initial world, DOS11/02/2026 midnight, pinned macOS ARM64 DOSBox0.83.0 at200000cycles.',
                limitations=['Host instrumentation is not passive; neutrality is evidenced only by complete output equality for this recipe.',
                             'No arbitrary clock/world prediction, general MBF parity, production gameplay or native BBS acceptance is claimed.',
                             'Historical guest-instrumented profile and its four-byte mismatch remain retained without target correction.'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);args=p.parse_args()
    from verify_maintenance_clock_neutral import verify
    verify()
    report=replay_cases()
    if args.output:args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if any(row['byte_mismatches']for row in report['cases']):raise SystemExit('complete untouched replay mismatch')

if __name__=='__main__':main()
