"""Verify original DOS startup captures and embedded asset provenance."""
from pathlib import Path
import hashlib
import json

root=Path(__file__).resolve().parents[1]
research=root/'research/yt-startup'
assets=root/'internal/door/assets'
manifest=json.loads((research/'assets.json').read_text())
for name,entry in manifest.items():
    data=(assets/name).read_bytes()
    assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256'],name
source=(root/'archive/analysis/art-menus/screen-recovery/run-main/SCREENS.BIN').read_bytes()
for name,index in [('title',0),('info',1),('main-help',3)]:
    assert (assets/(name+'.bin')).read_bytes()==source[index*4016+16:(index+1)*4016],name
for name in ['YTOPEN.ANS','YTOPEN.ASC','YTINSTR.DOC']:
    assert (assets/name.lower()).read_bytes()==(root/'archive/dos-original'/name).read_bytes().split(b'\x1a')[0],name
for name,count in [('new',7),('returning',4)]:
    directory=research/name
    provenance=json.loads((directory/'provenance.json').read_text())
    assert provenance['executable_sha256']==hashlib.sha256((root/'archive/dos-original/YT.EXE').read_bytes()).hexdigest()
    assert provenance['before_sha256']==hashlib.sha256((root/'archive/analysis/yt-combat/experiments/team-transfer-current/before.dat').read_bytes()).hexdigest()
    assert (directory/'KEYS.TXT').read_bytes()==provenance['keys'].encode()
    frames=(directory/'SCREENS.BIN').read_bytes()
    assert len(frames)==count*4016
    for i in range(count):assert frames[i*4016]==3 and frames[i*4016+2:i*4016+4]==b'\x50\x00'
    log=(directory/'transcript.txt').read_text()
    assert 'Returning to Yankee Trader Local Logon Program' in log
    assert 'Main Command (?=Help)?' in log and '<Help>' in log
    if name=='new':assert 'Your Alias has been recorded' in log and 'Name  : Pilot' in log
print('Verified 11 original DOS startup frames, transcript/keystroke provenance and embedded source assets.')
