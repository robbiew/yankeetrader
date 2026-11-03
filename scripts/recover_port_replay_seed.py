"""Capture the missing +2-second raw seed input for exact port replay."""
import argparse
from pathlib import Path
from recover_rng_trace import run

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);a=p.parse_args()
    run(a.destination,[dict(name='timer-plus-two',mode='timer',date='11/02/2026',time='00:00:02')])
