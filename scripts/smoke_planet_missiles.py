"""Real terminal cancellation, ground-only bounds and persisted bombardment receipt."""
from pathlib import Path
import datetime
import errno
import json
import os
import pty
import re
import select
import subprocess
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
BINARY=str(ROOT/'bin/yt')

def play(data,alias,command,answer=None):
    master,slave=pty.openpty()
    proc=subprocess.Popen([BINARY,'-compact','-data',str(data),'-local',alias],stdin=slave,stdout=slave,stderr=slave)
    os.close(slave);output=b'';sent=confirmed=False;deadline=time.monotonic()+20
    try:
        while time.monotonic()<deadline:
            if select.select([master],[],[],.1)[0]:
                try:chunk=os.read(master,65536)
                except OSError as err:
                    if err.errno==errno.EIO:break
                    raise
                if not chunk:break
                output+=chunk
                if not sent and b'> ' in output:
                    os.write(master,command.encode()+b'\r');sent=True
                if answer is not None and not confirmed and b'without capturing the planet. [y/N] ' in output:
                    os.write(master,answer.encode()+b'\r');confirmed=True
                    time.sleep(.05)
                    if proc.poll() is None:os.write(master,b'q\r')
        proc.wait(timeout=2)
        text=output.decode(errors='replace').replace('\r','')
        assert proc.returncode==0,text
        return text
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
        os.close(master)

with tempfile.TemporaryDirectory(prefix='yt-planet-missile-smoke-') as temp:
    data=Path(temp)/'data'
    subprocess.run([BINARY,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
    transcript=play(data,'Launcher','q')+play(data,'Owner','q')
    path=data/'world.json';world=json.loads(path.read_text())
    world['Players']['1'].update(Missiles=300)
    world['Players']['2'].update(Sector=3,Cloak=0)
    world['Sectors']['1']['Warps']=[2];world['Sectors']['2']['Warps']=[1,3]
    world['Sectors']['2']['Planet']=2
    world['Planets']['2']=dict(ID=2,Sector=2,Owner=2,Name='Target',Updated=datetime.datetime.now(datetime.timezone.utc).isoformat(),Ground=5000,Bank=0,Production=[100,200,300],Cargo=[10,20,30])
    path.write_text(json.dumps(world))
    text=play(data,'Launcher','missile 2 201;q');transcript+=text
    assert 'production bombardment is not available yet' in text,text
    text=play(data,'Launcher','missile 2 4;y',answer='');transcript+=text
    assert 'Target; 5000 ground forces; ground-only bombardment' in text and 'Missile launch cancelled.' in text,text
    before=json.loads(path.read_text())
    assert before['Players']['1']['Missiles']==300 and before['Players']['1']['Turns']==500 and before['Planets']['2']['Ground']==5000
    text=play(data,'Launcher','missile 2 4',answer='y');transcript+=text
    result=re.search(r'Planet bombardment saved: 4 missiles reached planet 2; ground forces (\d+) -> (\d+)\.',text)
    assert result,text
    world=json.loads(path.read_text());planet=world['Planets']['2']
    assert int(result[1])==5000 and planet['Ground']==int(result[2]) and 4900<=planet['Ground']<=5000
    assert world['Players']['1']['Missiles']==296 and world['Players']['1']['Turns']==499
    assert planet['Owner']==2 and planet['Bank']==0 and not world['Players']['2'].get('Death')
    assert 'Enemy retaliation saved' not in text
    (ROOT/'evidence/planet-missiles-smoke.txt').write_text(transcript)
    print('Planet missile PTY passed: production-overrun refusal, fresh cancellation, warning and persisted ground receipt.')
