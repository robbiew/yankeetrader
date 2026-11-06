"""Acquire the selected untouched encounter and separately labelled diagnostics.

Never execute originals in place. Each control owns a new mount/output path.
Guest nth-site probes are timing-perturbing diagnostics, not untouched goldens.
"""
import argparse
from pathlib import Path

from recover_maintenance_clock_matrix import capture,MODES
from recover_maintenance_sequence import run

PROBES=(
    ('ground-count',0x61b2,65535,0x234),
    ('production-count',0x632e,65535,0x234),
    ('ore-draw-count',0x6351,65535,0x234),
    ('organics-draw-count',0x6383,65535,0x234),
    ('equipment-draw-count',0x63ae,65535,0x234),
    ('candidate-scan-count',0x3348,65535,0x234),
    ('player-scan-count',0x3c0e,65535,0x234),
    ('desertion-count',0x46af,65535,0x234),
    ('lottery-count',0x537e,65535,0x234),
    ('first-gate-before',0x632e,1,0x234),
    ('first-damage-before',0x6351,1,0x234),
    ('second-gate-before',0x632e,2,0x234),
    ('first-preferred-output',0x66e2,1,0x7bac),
    ('first-group-index',0x632e,1,0x7be8),
)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path)
    p.add_argument('--scratch',type=Path,required=True);p.add_argument('--frida-module',type=Path,required=True)
    p.add_argument('--dosbox',type=Path,default=Path('/opt/homebrew/bin/dosbox-staging'))
    a=p.parse_args();destination=a.destination.absolute();scratch=a.scratch.absolute()
    assert not destination.exists()and not scratch.exists(),'fresh output and scratch required'
    assert a.frida_module.is_file(),'existing pinned Frida module required'
    destination.mkdir(parents=True);scratch.mkdir(parents=True)
    for mode in MODES:capture(destination/'untouched',scratch,'late',mode,a.dosbox,a.frida_module)
    diagnostics=destination/'diagnostics';diagnostics.mkdir()
    for name,site,nth,source in PROBES:run(diagnostics,name,site,nth,source,clock='23:59:59')

if __name__=='__main__':main()
