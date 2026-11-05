"""Diagnostic-only read-only386comparison of the current port index.

This is not the default counter profile. It preserves flags and original dispatch
but still perturbs one port's TIMER transition in the measured initial fixture.
"""
import argparse
import json
from pathlib import Path
import struct
import recover_maintenance_sequence as acquisition
from replay_qb_ports import graph


def patch(original,site,target):
    """Return same-size disposable copy with46-byte read-only port gate."""
    assert site==0x934 and original[512+site:517+site]==bytes.fromhex('cd3f7d9090')
    assert len(target)==4
    code=bytearray.fromhex('0e1fba0000eb0f9c66813ed67a')+target
    code+=bytes.fromhex('7512ba1a00bb0100b90400b440cd21b8004ccd219d')
    code+=original[512+site:517+site]+b'\xe9'+struct.pack('<H',(site+5-0x72)&65535)
    assert len(code)==46
    out=bytearray(original);out[0x244:0x272]=code
    out[512+site:517+site]=b'\xe9'+struct.pack('<H',(0x4b-site-3)&65535)+b'\x90\x90'
    assert out[:512]==original[:512]and len(out)==len(original)
    return bytes(out)


def capture(destination):
    destination.mkdir(parents=True,exist_ok=False)
    ordinary=acquisition.patch
    try:
        for name,target in [('untouched',None),('miss',bytes.fromhex('ffffffff'))]+[(f'port-{n:04}',graph.mbf.enc(n))for n in (1,605,606,607,1000)]:
            acquisition.patch=lambda original,site,nth,source:patch(original,site,target)
            acquisition.run(destination,name,None if target is None else 0x934,65535,0x1a if target else 0x234)
            p=destination/name/'result.json';m=json.loads(p.read_text())
            m['recipe']='port-clock-readonly-compare-v1'
            m['target_port_raw']=target.hex()if target else None
            m['complete']=target is None or name=='miss'
            p.write_text(json.dumps(m,indent=2)+'\n')
    finally:acquisition.patch=ordinary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);a=p.parse_args();capture(a.destination)
