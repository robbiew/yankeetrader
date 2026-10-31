"""Real player minefield entry and a mine-attributed chained combat death."""
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

ROOT = Path(__file__).resolve().parents[1]
BINARY = str(ROOT/'bin/yt')


@without_disruption
def play(data, alias, commands, action=None, answer=None):
    master, slave = pty.openpty()
    proc = subprocess.Popen([BINARY, '-compact', '-data', str(data), '-local', alias],
                            stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    output = b''
    sent = confirmed = False
    deadline = time.monotonic()+20
    try:
        while time.monotonic() < deadline:
            if select.select([master], [], [], .1)[0]:
                try:
                    chunk = os.read(master, 65536)
                except OSError as err:
                    if err.errno == errno.EIO:
                        break
                    raise
                if not chunk:
                    break
                output += chunk
                reject_disruption(output)
                if not sent and b'> ' in output:
                    if action:
                        action()
                    os.write(master, commands.encode()+b'\r')
                    sent = True
                if answer is not None and not confirmed and any(marker in output for marker in (b'Damage and losses save immediately. [y/N] ', b'Enter this dangerous sector? [y/N] ', b'Ships entering can be damaged. [y/N] ')):
                    os.write(master, answer.encode()+b'\r')
                    # Q must arrive after confirmation; it cannot authorize the attack.
                    time.sleep(.05)
                    os.write(master,b'q\r')
                    confirmed = True
        proc.wait(timeout=2)
        return proc.returncode, output.decode(errors='replace').replace('\r', '')
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)


with tempfile.TemporaryDirectory(prefix='yt-mines-smoke-') as temp:
    temp=Path(temp)
    data=temp/'entry'
    subprocess.run([BINARY,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
    for alias in ('Explorer','Owner'):
        code,_=play(data,alias,'q'); assert code==0
    path=data/'world.json';world=json.loads(path.read_text())
    world['Sectors']['1']['Warps']=[2]
    world['Sectors']['2']['Minefield']=[dict(Owner=2,Count=20)]
    world['Players']['1'].update(Shields=1000000,Cloak=0)
    path.write_text(json.dumps(world))
    code,transcript=play(data,'Explorer','s;auto 2;y;q')
    assert code==0 and 'Sector mines: 20' in transcript and 'confirm entry manually' in transcript,transcript
    assert json.loads(path.read_text())['Players']['1']['Sector']==1
    code,text=play(data,'Explorer','m 2;y',answer='')
    assert code==0 and 'Minefield entry cancelled' in text,text
    assert json.loads(path.read_text())['Players']['1']['Turns']==500
    transcript+=text
    code,text=play(data,'Explorer','m 2',answer='y')
    assert code==0 and '20 mines exploded in 19 bursts' in text,text
    transcript+=text
    world=json.loads(path.read_text())
    assert world['Players']['1']['Sector']==2 and world['Players']['1']['Turns']==499
    assert 980000 <= world['Players']['1']['Shields'] <= 1000000
    assert not world['Sectors']['2'].get('Minefield')

    data=temp/'chain'
    subprocess.run([BINARY,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
    for alias in ('Victim','Killer'):
        code,_=play(data,alias,'q'); assert code==0
    path=data/'world.json';world=json.loads(path.read_text())
    world['Players']['1'].update(Sector=2,Cloak=0,Fighters=0,Shields=0,Holds=1,Mines=100,Credits=10000,Turns=41)
    world['Players']['2'].update(Sector=2,Cloak=0,Fighters=1,Shields=0,Holds=1,Mines=0,Turns=37)
    world['Ports']['2'].update(Owner=1,Treasury=777)
    path.write_text(json.dumps(world))
    code,text=play(data,'Killer','attack 1 1',answer='y')
    assert code==1 and 'Victim destroyed.' in text and 'Your ship was destroyed by mines from player 1' in text,text
    transcript+=text
    world=json.loads(path.read_text());victim,killer=world['Players']['1'],world['Players']['2']
    assert victim['Death']['Cause']=='combat' and victim['Death']['Killer']==2
    assert killer['Death']['Cause']=='mines' and killer['Death']['Killer']==1
    assert victim['Credits']+killer['Credits']==11005
    assert victim['Mines']==0 and killer['Mines']==0
    assert world['Ports']['2']['Owner']==0 and world['Ports']['2']['Treasury']==0
    assert not world['Sectors']['1'].get('Minefield')
    for alias,turns in [('Victim',41),('Killer',37)]:
        code,text=play(data,alias,'i;q')
        assert code==0 and f'Remaining turns: {turns}' in text,text
        transcript+=text
    world=json.loads(path.read_text())
    assert world['Version']==26 and all(world['Players'][str(i)]['Sector']==1 for i in (1,2))

    data=temp/'deploy'
    subprocess.run([BINARY,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
    code,_=play(data,'Deployer','q');assert code==0
    path=data/'world.json';world=json.loads(path.read_text())
    world['Players']['1'].update(Sector=8,Mines=10,Shields=1000000)
    world['Sectors']['8']['Warps']=[7];world['Sectors']['7']['Warps']=[8]
    path.write_text(json.dumps(world))
    code,text=play(data,'Deployer','d 5',answer='y');transcript+=text
    assert code==0 and 'Dropped 5 mines' in text and 'Mine encounter saved' not in text,text
    world=json.loads(path.read_text());p=world['Players']['1']
    assert p['Mines']==5 and p['Shields']==1000000 and p['MineGraceSector']==8 and p['Turns']==500
    assert world['Sectors']['8']['Minefield'][0]['Count']==5
    code,text=play(data,'Deployer','i;q');transcript+=text
    assert code==0 and 'Mine encounter saved' not in text,text
    code,text=play(data,'Deployer','m 7;q');transcript+=text
    assert code==0 and 'Moved to sector 7.' in text,text
    world=json.loads(path.read_text());assert not world['Players']['1'].get('MineGraceSector')
    assert world['Sectors']['8']['Minefield'][0]['Count']==5
    code,text=play(data,'Deployer','m 8',answer='y');transcript+=text
    assert code==0 and 'Mine encounter saved: 5 mines exploded' in text,text
    world=json.loads(path.read_text());assert world['Players']['1']['Turns']==498 and not world['Sectors']['8'].get('Minefield')
    (ROOT/'evidence/mines-smoke.txt').write_text(transcript)
    print('PTY mines passed: fresh entry/cancellation, autopilot stop, persisted damage, chained death attribution, protected Earth, deployment grace across reconnect, departure and hazardous reentry.')
