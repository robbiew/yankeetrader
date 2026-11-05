"""Measure bounded port TIMER/60 boundaries in disposable maintenance copies."""
import argparse
import json
from pathlib import Path
from recover_maintenance_sequence import run


def capture(destination):
    destination.mkdir(parents=True,exist_ok=False)
    run(destination,'untouched')
    run(destination,'count-clock',0x934,65535,0x1a)
    samples={}
    def sample(n):
        if n not in samples:
            folder=destination/f'port-{n:04}'
            run(destination,folder.name,0x934,n,0x1a)
            samples[n]=(folder/'TRACE.BIN').read_bytes()[-4:].hex()
        return samples[n]
    first,last=sample(1),sample(1000)
    assert first!=last,'pilot needs distinct first/last timer observations'
    low,high=1,1000
    while high-low>1:
        mid=(low+high)//2
        if sample(mid)==first:low=mid
        else:high=mid
    sample(low);sample(high)
    for n in (2,low-1,high+1,999):
        if 1<=n<=1000:sample(n)
    (destination/'search.json').write_text(json.dumps(dict(site=0x934,source=0x1a,
        first_raw=first,last_raw=last,last_first_value=low,first_changed_value=high,samples=samples),indent=2)+'\n')
    print('Measured TIMER/60 transition',low,high,first,last,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);a=p.parse_args();capture(a.destination)
