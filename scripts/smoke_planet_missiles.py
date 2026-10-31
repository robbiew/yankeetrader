"""Real terminal cancellation and persisted planetary production destruction."""
from smoke_arrival_control import without_disruption, reject_disruption
from pathlib import Path
import datetime
import errno
import json
import os
import pty
import select
import subprocess
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
BINARY=str(ROOT/'bin/yt')

@without_disruption
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
                reject_disruption(output)
                if not sent and b'> ' in output:
                    os.write(master,command.encode()+b'\r');sent=True
                if answer is not None and not confirmed and b'Hostile planets along the course may be damaged or destroyed. [y/N] ' in output:
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
    world['Planets']['2']=dict(Generation=2,ID=2,Sector=2,Owner=2,Name='Target',Updated=datetime.datetime.now(datetime.timezone.utc).isoformat(),Ground=25,Bank=0,Production=[100,200,300],Cargo=[10,20,30])
    path.write_text(json.dumps(world))
    text=play(data,'Launcher','missile 2 4;y',answer='');transcript+=text
    assert 'Target; 25 ground forces; production 100/200/300' in text and 'Missile launch cancelled.' in text,text
    before=json.loads(path.read_text())
    assert before['Players']['1']['Missiles']==300 and before['Players']['1']['Turns']==500 and before['Planets']['2']['Ground']==25
    text=play(data,'Launcher','missile 2 201',answer='y');transcript+=text
    assert 'Planet bombardment saved:' in text and 'Planet 2 destroyed' in text,text
    world=json.loads(path.read_text())
    assert '2' not in world['Planets'] and world['Sectors']['2']['Planet']==0
    assert world['Players']['1']['Missiles']==99 and world['Players']['1']['Turns']==499
    assert world['Players']['2']['Sector']==3 and not world['Players']['2'].get('Death')
    assert 'Enemy retaliation saved' not in text
    (ROOT/'evidence/planet-missiles-smoke.txt').write_text(transcript)
    print('Planet missile PTY passed: production warning, fresh cancellation, persisted production damage and logical destruction.')
