"""Exercise deployment, surrender confirmation and interception through real PTYs."""
from smoke_arrival_control import without_disruption, reject_disruption
from pathlib import Path
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
def play(data,alias,command,answers=(),missile=False):
    master,slave=pty.openpty()
    proc=subprocess.Popen([BINARY,'-compact','-data',str(data),'-local',alias],stdin=slave,stdout=slave,stderr=slave)
    os.close(slave)
    output=b'';sent=False;answered=0;deadline=time.monotonic()+15
    markers=(b'Accept human surrender if offered during this battle? [Y/n] ',b'defeat forces emergency escape. [y/N] ')
    if missile:markers=(b'may retaliate. [y/N] ',)
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
                if answered<len(answers) and markers[answered] in output:
                    os.write(master,answers[answered].encode()+b'\r');answered+=1
                    if answered==len(answers):
                        time.sleep(.05)
                        if proc.poll() is None:os.write(master,b'q\r')
        proc.wait(timeout=2)
        assert proc.returncode==0,output.decode(errors='replace')
        return output.decode(errors='replace').replace('\r','')
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
        os.close(master)

with tempfile.TemporaryDirectory(prefix='yt-sector-smoke-') as temp:
    data=Path(temp)/'data'
    subprocess.run([BINARY,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
    transcript=play(data,'Caller','q')+play(data,'Owner','q')
    path=data/'world.json';world=json.loads(path.read_text())
    world['Players']['1'].update(Sector=8,Fighters=1000)
    path.write_text(json.dumps(world))
    text=play(data,'Caller','f 100;i;f 0;i;q');transcript+=text
    world=json.loads(path.read_text())
    assert text.count('Sector fighter transfer saved.')==2,text
    assert world['Players']['1']['Fighters']==1000 and not world['Sectors']['8'].get('Defense')
    world['Players']['1'].update(Sector=7,Fighters=10001)
    world['Sectors']['7']['Warps']=[8]
    world['Sectors']['8']['Defense']={'Owner':2,'Fighters':1000}
    path.write_text(json.dumps(world))
    text=play(data,'Caller','breach 8 10001;y',('y',''));transcript+=text
    assert 'Defense encounter cancelled.' in text,text
    assert json.loads(path.read_text())['Players']['1']['Sector']==7
    text=play(data,'Caller','breach 8 10001',('y','y'));transcript+=text
    assert '1000 surrendered.' in text and 'Hostile defense cleared in sector 8.' in text,text
    world=json.loads(path.read_text())
    assert world['Players']['1']['Fighters']==11001 and world['Players']['1']['Sector']==8
    assert world['Players']['1']['Turns']==499 and not world['Sectors']['8'].get('Defense')
    assert not world['Players']['2'].get('Death')
    # A defense-only target consumes a volley without requiring a visible ship.
    world['Players']['1'].update(Sector=7,Missiles=1)
    world['Sectors']['7']['Warps']=[8];world['Sectors']['8']['Warps']=[7]
    world['Sectors']['8']['Defense']={'Owner':2,'Fighters':1000000000}
    path.write_text(json.dumps(world))
    text=play(data,'Caller','missile 8 1',('y',),missile=True);transcript+=text
    assert 'Sector interception: 1 missiles,' in text,text
    world=json.loads(path.read_text())
    assert world['Players']['1']['Missiles']==0 and world['Players']['1']['Turns']==498
    assert world['Sectors']['8']['Defense']['Fighters']>=999995001
    assert world['Sectors']['8']['Defense']['Owner']==2
    (ROOT/'evidence/sector-fighters-smoke.txt').write_text(transcript)
    print('Sector PTY: deployment/recovery, queued-confirmation refusal, surrender, interception passed')
