"""Verify original DOS rename screens, input patches and persisted name/rule evidence."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
RESEARCH=ROOT/'research/yt-planet-rename'
ARCHIVE=ROOT/'archive'
sys.path.insert(0,str(ARCHIVE/'analysis/yt-maint'))
from experiments import get,put

NAMES={'owner':'New Eden','blank':'Test Planet','retry':'Second Name','reserved':'Test Planet','lowercase':'Test Planet','team':'New Eden','foreign':'New Eden','unowned':'New Eden','long':'12345678901234567890123456789012345678901','last-slot':'Test Planet','other-reserved':'Test Planet','spaces':'Test Name','case':'Mixed Name','punctuation':"O'brien Alpha-Beta X_Y 42Base"}
COUNTS={'owner':4,'blank':2,'retry':5,'reserved':2,'lowercase':2,'team':3,'foreign':3,'unowned':3,'long':3,'last-slot':3,'other-reserved':3,'spaces':4,'case':4,'punctuation':4}
sha=lambda data:hashlib.sha256(data).hexdigest()
for name,expected in NAMES.items():
    directory=RESEARCH/name;p=json.loads((directory/'provenance.json').read_text())
    base=ARCHIVE/'analysis/yt-combat/experiments'/p['fixture'];before=(base/'before.dat').read_bytes()
    assert p['before_sha256']==sha(before) and p['executable_sha256']==sha((ARCHIVE/'dos-original/YT.EXE').read_bytes()),name
    patches=[]
    if name=='unowned':patches=[{'record':4053,'offset':73,'value':0},{'record':4053,'offset':77,'value':0}]
    if name=='last-slot':patches=[{'copy_record':4053,'to_record':4151},{'record':151,'offset':93,'value':100}]
    assert p['patches']==patches,name
    modified=bytearray(before)
    for patch in patches:
        if 'copy_record' in patch:
            start=(patch['copy_record']-1)*137;dest=(patch['to_record']-1)*137;modified[dest:dest+137]=modified[start:start+137]
        else:put(modified,patch['record'],patch['offset'],patch['value'])
    assert sha(modified)==p['input_sha256'] and (directory/'KEYS.TXT').read_bytes()==p['keys'].encode(),name
    for tool,key in [('CAPTURE.COM','capture_sha256'),('DUMP.COM','dump_sha256')]:assert sha((ARCHIVE/'analysis/art-menus/screen-recovery'/tool).read_bytes())==p[key],name
    screens=(directory/'SCREENS.BIN').read_bytes();assert sha(screens)==p['screens_sha256'] and len(screens)==COUNTS[name]*4016,name
    for i in range(COUNTS[name]):
        frame=screens[i*4016:(i+1)*4016];assert frame[0]==3 and frame[2:4]==b'\x50\x00' and frame[6]<80 and frame[7]<25,name
    log=gzip.decompress((directory/'GAME.LOG.gz').read_bytes());assert sha(log)==p['game_log_sha256'],name
    assert b'Returning to Yankee Trader Local Logon Program' in log and b'Planet command' in log,name
    after=gzip.decompress((directory/'YTDATA.DAT.gz').read_bytes());assert sha(after)==p['after_sha256'],name
    rec=4151 if name=='last-slot' else 4053;start=(rec-1)*137
    assert after[start:start+41]==expected.encode().ljust(41,b' ') and get(after,rec,85)==len(expected),(name,'persisted name')
    for offset in [49,61,65,69,73,77,81,97,113,121,129]:assert get(after,2,offset)==get(modified,2,offset),(name,'player assets',offset)
    for offset in [73,77]:assert get(after,rec,offset)==get(modified,rec,offset),(name,'governor/garrison',offset)
print('Verified 45 DOS rename frames in 14 isolated sessions, patched inputs, persisted names and unchanged player assets/governorship.')
