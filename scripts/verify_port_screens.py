"""Verify DOS port capture identity, provenance, frame metadata and prompt coverage."""
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESEARCH=ROOT/'research/yt-port-screens'
ARCHIVE=ROOT/'archive'
scenarios={'earth':4,'holds':4,'holds-buy':4,'forces':4,'shields':4,'buy':3,'sell':3,'owned':3,'self':3,'decline':3}
sha=lambda b:hashlib.sha256(b).hexdigest()
sys.path.insert(0,str(ARCHIVE/'analysis/yt-maint'))
from experiments import put
for name,count in scenarios.items():
    directory=RESEARCH/name
    p=json.loads((directory/'provenance.json').read_text())
    base=ARCHIVE/'analysis/yt-combat/experiments'/p['fixture']
    assert p['executable_sha256']==sha((ARCHIVE/'dos-original/YT.EXE').read_bytes()),name
    assert p['before_sha256']==sha((base/'before.dat').read_bytes()),name
    data=bytearray((base/'before.dat').read_bytes())
    expected=[{'record':2,'offset':65,'value':10}] if name=='holds-buy' else []
    assert p['patches']==expected,name
    for patch in p['patches']:put(data,patch['record'],patch['offset'],patch['value'])
    assert p['input_sha256']==sha(data),name
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
    assert '<Port>' in text and 'Commerce report for ' in text,name
    marker={'earth':'Buy how many fighters? [0]?','holds':'You dont need any holds.','holds-buy':'Buy how many holds? [0]?','forces':'Buy how many ground force units? [0]?','shields':'Buy how much shield power? [0]?','owned':'This port is owned by: Enemy','self':'This port is owned by: YOU, Credits: 0','decline':'Never mind!'}.get(name,'Do you agree? [Y/n]')
    assert marker in text,(name,marker)
print('Verified 35 original DOS port frames in 10 isolated sessions, executable/fixture/tool hashes, keystrokes and transaction prompts.')
