"""Before-only initial-maintenance replay for the explicit host clock/date matrix.

The historical midnight profile is unchanged. This profile consumes separately
source-qualified DATE$, TIME$ and TIMER inputs, including per-port dates and
creation-phase dates. Completed native files belong only to compare_cases().
"""
import argparse
from dataclasses import dataclass
import datetime
import gzip
import json
from pathlib import Path

from replay_qb_ports import graph
from replay_maintenance_ports import replay_capped_initial_ports
from replay_maintenance_npcs import synthesize_clock_matrix as npc_matrix,UnsupportedClockMatrixEncounter
from replay_maintenance_aux import synthesize_clock_matrix as auxiliary_matrix
from replay_maintenance_records import compare

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/clock-matrix-controls'
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')


class UnsupportedProfile(ValueError):
    """An authentic matrix trace reaches an explicitly unmodeled source branch."""
    def __init__(self,message,context=None):
        super().__init__(message)
        self.context={}if context is None else context


@dataclass(frozen=True)
class Inputs:
    startup_date: datetime.date
    final_date: datetime.date
    port_dates: tuple
    wanderer_date: datetime.date
    xannoron_date: datetime.date
    base_date: datetime.date
    news_date: datetime.date
    news_clock: str
    score_date: datetime.date
    score_clock: str
    port_timer_minutes: tuple
    h1_timers: tuple
    h2_timers: tuple
    xannoron_timer: bytes
    initial_state: int


def legacy_day(before,date):
    """Original base-year calendar count for the admitted2026/2027 matrix."""
    if type(before)is not bytes or len(before)!=4151*137:raise ValueError('default before-world extent required')
    base_year=graph.mbf.get(before,1,45)
    if base_year!=26:raise UnsupportedProfile('only saved base-year2026 is admitted')
    if type(date)is not datetime.date or not 2026<=date.year<=2027:
        raise UnsupportedProfile('only source dates in2026/2027 are admitted')
    # Those two years have no century exception; this equals the recovered
    # helper's base-year accumulation (Jan1,2027 is366, not GregorianDOY1).
    return (date-datetime.date(2026,1,1)).days+1


def inputs_from_observation(observation):
    """Extract explicit clock inputs from authenticated raw host events only."""
    from verify_maintenance_clock_matrix import model_inputs
    raw=model_inputs(observation)
    startup=bytearray(raw['startup']);startup[2]^=128
    initial=5|((startup[0]^startup[2])<<8)|((startup[1]^startup[3])<<16)
    return Inputs(startup_date=raw['startup_date'],final_date=raw['final_date'],port_dates=tuple(raw['port_dates']),
                  wanderer_date=raw['wanderer_date'],xannoron_date=raw['xannoron_date'],base_date=raw['base_date'],
                  news_date=raw['news_date'],news_clock=raw['news_clock'],score_date=raw['score_date'],score_clock=raw['score_clock'],
                  port_timer_minutes=tuple(raw['port_minutes']),h1_timers=tuple(raw['helper1']),h2_timers=tuple(raw['helper2']),
                  xannoron_timer=raw['xannoron'],initial_state=initial)


def _watermark_and_inactive_ranks(world,day):
    """Same admitted source writers; watermark is base-year day, not DOY."""
    get=lambda rec,off:graph.mbf.get(world,rec,off)
    if any(get(1,o)!=n for o,n in [(53,51),(57,3051),(61,4051),(93,4151)]):
        raise UnsupportedProfile('only default record geometry is admitted')
    if any(get(r,85)!=0 for r in range(2,52)):
        raise UnsupportedProfile('only all-inactive ranks are admitted')
    output=bytearray(world);output[81:85]=graph.mbf.enc(day)
    for r in range(2,52):
        at=(r-1)*137+109;output[at:at+4]=graph.mbf.enc(-1)
    return bytes(output)


_UNMODELED_NPC={
    'this retained fixture has no Wanderer rejection',
    'selected fixture has no same-location fallback retry',
    'no candidate foreign force','no accepted candidate planet',
    'no entered planet/mine action in selected fixture',
    'selected fixture has20 nonmerged Xannor groups',
    'zero-bound stale-result defect is outside this fixture',
    'bounded fixture has no directed route',
    'all measured helper inputs consumed exactly once',
}


def synthesize(before_files,inputs):
    """Generate six complete files from before-bytes and declared clock inputs."""
    if type(inputs)is not Inputs:raise ValueError('explicit matrix Inputs required')
    if set(before_files)!=set(FILES[:3])or any(type(v)is not bytes for v in before_files.values()):
        raise ValueError('three raw pre-maintenance input files required')
    before=before_files['YTDATA.DAT']
    if len(before)!=4151*137:raise ValueError('default before-world extent required')
    if before[:11]!=b'YTSCORE.ASC' or graph.mbf.get(before,1,41)!=11:
        raise UnsupportedProfile('default scoreboard path required')
    if any(graph.mbf.get(before,51+s,129)!=0 for s in range(1,3001)):
        raise UnsupportedProfile('initial mine hazards are outside this profile')
    if type(inputs.initial_state)is not int or not 0<=inputs.initial_state<2**24:
        raise ValueError('24-bit startup state required')
    if len(inputs.port_dates)!=1000:raise ValueError('1000 source-qualified port dates required')
    if len(inputs.h1_timers)not in(41,42)or len(inputs.h2_timers)!=19:
        raise UnsupportedProfile('helper inventory exceeds41/42single and19shrinking calls')
    port_days=tuple(legacy_day(before,date)for date in inputs.port_dates)
    phase_days={name:legacy_day(before,date)for name,date in [('wanderer',inputs.wanderer_date),('xannoron',inputs.xannoron_date),('base',inputs.base_date)]}
    final_day=legacy_day(before,inputs.final_date)
    chronology=[legacy_day(before,inputs.startup_date),*port_days,*phase_days.values(),final_day]
    if chronology!=sorted(chronology):raise UnsupportedProfile('calendar moved backward between admitted phases')
    block,port_stats=replay_capped_initial_ports(before,port_days,inputs.port_timer_minutes)
    work=before[:3051*137]+block+before[4051*137:]
    try:
        work,npc_stats=npc_matrix(work,inputs.h1_timers,inputs.h2_timers,phase_days,
                                  xannoron_timer=inputs.xannoron_timer,initial_state=inputs.initial_state)
    except UnsupportedClockMatrixEncounter as error:
        raise UnsupportedProfile('NPC branch: '+str(error),error.context)from error
    except AssertionError as error:
        if str(error)in _UNMODELED_NPC:raise UnsupportedProfile('NPC branch: '+str(error))from error
        raise
    work=_watermark_and_inactive_ranks(work,final_day)
    auxiliary=auxiliary_matrix(before_files,work,inputs.news_date,inputs.news_clock,inputs.score_date,inputs.score_clock)
    result={'YTDATA.DAT':work,**auxiliary}
    assert set(result)==set(FILES),'complete six-file model output inventory'
    return result,dict(ports=port_stats,npcs=npc_stats,final_day=final_day,
                       news_date=inputs.news_date.isoformat(),news_clock=inputs.news_clock,
                       score_date=inputs.score_date.isoformat(),score_clock=inputs.score_clock,
                       world_records=4151,world_bytes=len(work),file_bytes={n:len(b)for n,b in result.items()})


def compare_cases(root=DEFAULT):
    """Comparison-only loader. No expected output is passed to synthesis."""
    root=Path(root)
    before_root=ROOT/'research/yt-maint/initial-controls/baseline-split'
    before={n:gzip.decompress((before_root/('before-'+n+'.gz')).read_bytes())for n in FILES[:3]}
    rows=[];statistics=[]
    for recipe in sorted(p for p in root.iterdir()if p.is_dir()):
        controls=[p for p in recipe.iterdir()if p.is_dir()]
        for observed in sorted(controls):
            host=observed/'host-time.json.gz'
            if not host.exists():continue
            trace=json.loads(gzip.decompress(host.read_bytes()))
            if not trace['observe']:continue
            try:
                actual,stats=synthesize(before,inputs_from_observation(trace))
            except UnsupportedProfile as error:
                rows.append(dict(recipe=recipe.name,observation=observed.name,model_status='unsupported',reason=str(error),context=error.context))
                continue
            statistics.append(dict(recipe=recipe.name,observation=observed.name,**stats))
            for target in sorted(controls):
                expected={n:gzip.decompress((target/('after-'+n+'.gz')).read_bytes())for n in FILES}
                rows.append(dict(recipe=recipe.name,observation=observed.name,target=target.name,model_status='compared',**compare(expected,actual)))
    return dict(recipe='bounded-maintenance-clock-matrix-replay-v1',cases=rows,statistics=statistics,
                limitations=['Explicit measured DATE$/TIME$/TIMER inputs, not prediction from a textclock.',
                             'Only the admitted all-inactive base-year2026 world and source branches are modeled.',
                             'Unknown encounter/rejection/numeric branches remain named gaps; no timestamp masks or target corrections.'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--output',type=Path);p.add_argument('--require-all-exact',action='store_true',help='fail on documented unsupported profiles as well as every compared mismatch');args=p.parse_args()
    from verify_maintenance_clock_matrix import verify
    verify(args.root)
    report=compare_cases(args.root)
    if args.output:args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if any(r['model_status']=='compared'and r['byte_mismatches']for r in report['cases']):
        raise SystemExit('at least one supported matrix comparison has byte mismatches')
    if args.require_all_exact and any(r['model_status']!='compared'for r in report['cases']):
        raise SystemExit('matrix contains an explicitly unsupported profile')

if __name__=='__main__':main()
