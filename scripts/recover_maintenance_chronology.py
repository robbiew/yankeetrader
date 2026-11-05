"""Capture bounded maintenance scan/phase boundaries using the retained nth-hit diagnostic."""
import argparse
from pathlib import Path
from recover_maintenance_sequence import run

# Distances between independently captured candidate outputs and next helper
# entry states suggest these 50-player scan blocks. They are tested, not assumed
# to be successful route hops. The original captured evidence remains unchanged.
BLOCKS = (29,21,22,35,38,30,24,20,40,25,23,22,25,34,21,13,26,35,13)
SOURCES = {'state':0x234,'group':0x7b8c,'player':0x7bf0,'prestep':0x7b68,'destination':0x7bc4}

def matrix():
    out=[dict(name='untouched')]
    def add(name,site,nth,source):out.append(dict(name=name,site=site,nth=nth,source=source))
    # Independent complete counters verify no new draw-family or helper count.
    for site in (0x3348,0x3c0e,0x7900,0x7946):add(f'count-{site:04x}',site,65535,0x234)
    before=0
    for phase,blocks in enumerate(BLOCKS,1):
        for edge,nth in [('first',before+1),('last',before+blocks*50)]:
            for label,source in SOURCES.items():add(f'scan-{phase:02}-{edge}-{label}',0x3c0e,nth,source)
        # The candidate player loop is distinct and has50eager draws per phase.
        for edge,nth in [('first',(phase-1)*50+1),('last',phase*50)]:
            for label,source in [('state',0x234),('group',0x7b8c),('player',0x7bc0)]:
                add(f'candidate-{phase:02}-{edge}-{label}',0x3348,nth,source)
        before+=blocks*50
    assert before==24800
    # Tail phase: all20desertion draws and one lottery gate, before/after where
    # five-byte dispatch boundaries have no extra inline operands.
    for n in range(1,21):add(f'desertion-{n:02}-before',0x46af,n,0x234)
    add('desertion-last-after',0x46b7,20,0x234)
    add('lottery-before',0x537e,1,0x234)
    add('lottery-after',0x5386,1,0x234)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--pilot',action='store_true');a=p.parse_args()
    a.destination.mkdir(parents=True,exist_ok=False)
    rows=matrix()
    if a.pilot:rows=rows[:9]
    for row in rows:run(a.destination,**row)
