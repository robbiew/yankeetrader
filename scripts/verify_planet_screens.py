"""Verify DOS planet capture identity, provenance, frame metadata and prompt coverage."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESEARCH=ROOT/'research/yt-planet-screens'
ARCHIVE=ROOT/'archive'
scenarios={'menu':3,'transfer':3,'cargo':2,'bank':2,'invest':3,'garrison':2,'takeall':2,'create':4,'foreign':2,'take-cargo':6,'take-weapons':8}
sha=lambda b:hashlib.sha256(b).hexdigest()
for name,count in scenarios.items():
    directory=RESEARCH/name
    p=json.loads((directory/'provenance.json').read_text())
    base=ARCHIVE/'analysis/yt-combat/experiments'/p['fixture']
    assert p['executable_sha256']==sha((ARCHIVE/'dos-original/YT.EXE').read_bytes()),name
    assert p['before_sha256']==sha((base/'before.dat').read_bytes()),name
    assert p['input_sha256']==p['before_sha256'],name
    assert (directory/'KEYS.TXT').read_bytes()==p['keys'].encode(),name
    for tool,key in [('CAPTURE.COM','capture_sha256'),('DUMP.COM','dump_sha256')]:
        assert p[key]==sha((ARCHIVE/'analysis/art-menus/screen-recovery'/tool).read_bytes()),(name,tool)
    frames=(directory/'SCREENS.BIN').read_bytes()
    assert sha(frames)==p['screens_sha256'] and len(frames)==count*4016,name
    for i in range(count):
        frame=frames[i*4016:(i+1)*4016]
        assert frame[0]==3 and frame[2:4]==b'\x50\x00',name
        assert frame[6]<80 and frame[7]<25,name
    log=gzip.decompress((directory/'GAME.LOG.gz').read_bytes())
    assert sha(log)==p['game_log_sha256'],name
    assert b'Returning to Yankee Trader Local Logon Program' in log,name
    text=log.decode('cp437')
    assert '<Land/Create planet>' in text,name
    marker={'menu':'Planet command (?=help) [A]?','transfer':'Fighters Transferred!','cargo':'Cargo transferred!!','bank':'You have 15000 credits on deposit','invest':'Productivity increased by 1.004','garrison':'Ground force strength now at 90 units!','takeall':'<Take all>','create':'Planet \"New Eden\" created with Genesis Device!','foreign':'Permission to land is DENIED!','take-cargo':'<Take Equipment)','take-weapons':'<Take Plasma Bolts>'}[name]
    assert marker in text,(name,marker)
print('Verified 37 original DOS planet frames in 11 isolated sessions, executable/fixture/tool hashes, keystrokes and prompts.')
