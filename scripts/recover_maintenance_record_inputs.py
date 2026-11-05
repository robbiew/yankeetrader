"""Capture explicit TIMER input witnesses for bounded maintenance record replay."""
import argparse
from pathlib import Path
from recover_maintenance_sequence import run

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);a=p.parse_args()
    a.destination.mkdir(parents=True,exist_ok=False)
    run(a.destination,'untouched')
    run(a.destination,'untouched-repeat')
    run(a.destination,'xannoron-timer',site=0x218e,nth=1,source=0x1a)
