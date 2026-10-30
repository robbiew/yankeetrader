"""Real one-hop missile kills, mine clearing and fatal, correctly attributed return fire."""
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
                if not sent and b'> ' in output:
                    if action:
                        action()
                    os.write(master, commands.encode()+b'\r')
                    sent = True
                if answer is not None and not confirmed and b'may retaliate. [y/N] ' in output:
                    os.write(master, answer.encode()+b'\r')
                    # Q must arrive after confirmation; it cannot authorize the attack.
                    time.sleep(.05)
                    if proc.poll() is None:
                        os.write(master,b'q\r')
                    confirmed = True
        proc.wait(timeout=2)
        return proc.returncode, output.decode(errors='replace').replace('\r', '')
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)


with tempfile.TemporaryDirectory(prefix='yt-missile-smoke-') as temp:
    temp=Path(temp)
    transcript=''
    def setup(name,aliases):
        data=temp/name
        subprocess.run([BINARY,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
        for alias in aliases:
            code,_=play(data,alias,'q');assert code==0
        path=data/'world.json';world=json.loads(path.read_text())
        world['Sectors']['1']['Warps']=[2]
        world['Sectors']['2']['Warps']=[1,3]
        return data,path,world

    data,path,world=setup('kill',('Launcher','Victim'))
    world['Players']['1'].update(Missiles=3)
    world['Players']['2'].update(Sector=2,Cloak=0,Fighters=0,Shields=0,Holds=1,Missiles=0,Mines=100,Credits=10000,Turns=37)
    world['Ports']['2'].update(Owner=2,Treasury=777)
    path.write_text(json.dumps(world))
    code,text=play(data,'Launcher','missile 2 3;y',answer='')
    assert code==0 and 'Missile launch cancelled.' in text,text
    assert json.loads(path.read_text())['Players']['1']['Missiles']==3
    transcript+=text
    shot=[]
    def fire():
        code,text=play(data,'Launcher','missile 2 3',answer='y')
        assert code==0 and 'Victim destroyed. You recovered' in text,text
        assert 'Enemy retaliation saved' not in text,text
        shot.append(text)
    code,text=play(data,'Victim','m 3;q',action=fire)
    assert code==1 and 'ship was destroyed' in text,text
    transcript+=''.join(shot)+text
    world=json.loads(path.read_text())
    victim,launcher=world['Players']['2'],world['Players']['1']
    assert victim['Death']['Cause']=='missile' and victim['Death']['Killer']==1
    assert launcher['Turns']==499 and launcher['Missiles']==0 and victim['Mines']==0
    import re
    destroyed=int(re.search(r'3 missiles fired, (\d+) mines destroyed',shot[0])[1])
    fields=world['Sectors']['2'].get('Minefield',[])
    assert launcher['Mines']+sum(layer['Count'] for layer in fields)+destroyed==100
    assert all(layer['Owner']==2 for layer in fields)
    assert world['Ports']['2']['Owner']==1 and world['Ports']['2']['Treasury']==777

    data,path,world=setup('counter',('Launcher','Enemy'))
    world['Players']['1'].update(Cloak=1,Fighters=0,Shields=0,Missiles=10,Mines=100,Credits=10000,Turns=37,StoredScore=500000)
    world['Players']['2'].update(Sector=2,Cloak=0,Fighters=1000000000,Shields=1000000000,Missiles=6)
    world['Ports']['2'].update(Owner=1,Treasury=777)
    path.write_text(json.dumps(world))
    code,text=play(data,'Launcher','missile 2 1',answer='y')
    assert code==1 and 'Enemy retaliation saved: 6 missiles fired' in text and 'Launcher destroyed. Enemy recovered' in text,text
    assert 'Earth protection safely disposed' in text,text
    transcript+=text
    world=json.loads(path.read_text());launcher,enemy=world['Players']['1'],world['Players']['2']
    assert launcher['Death']['Cause']=='retaliation' and launcher['Death']['Killer']==2
    assert launcher['Turns']==36 and enemy['Turns']==500
    assert launcher['Missiles']+enemy['Missiles']==9 # initial 16 minus primary 1 and return 6
    assert launcher['Mines']==0 and not world['Sectors']['1'].get('Minefield')
    assert world['Ports']['2']['Owner']==2 and world['Ports']['2']['Treasury']==777
    def replacement_cache():
        # Login preserves the previous cache until a refresh boundary.
        assert json.loads(path.read_text())['Players']['1']['StoredScore']==500000
    code,text=play(data,'Launcher','i;q',action=replacement_cache)
    assert code==0 and 'Remaining turns: 36' in text,text
    transcript+=text
    world=json.loads(path.read_text());assert world['Players']['1']['StoredScore']==34505 # clean logout scores the replacement

    data,path,world=setup('clear',('Launcher',))
    world['Players']['1'].update(Missiles=3)
    world['Sectors']['2']['Minefield']=[dict(Owner=0,Count=5)]
    path.write_text(json.dumps(world))
    code,text=play(data,'Launcher','missile 2 3',answer='y')
    assert code==0 and '3 mines destroyed. No ship struck.' in text,text
    transcript+=text
    world=json.loads(path.read_text());assert world['Version']==22 and world['Sectors']['2']['Minefield'][0]['Count']==2
    assert world['Players']['1']['Missiles']==0 and world['Players']['1']['Turns']==499
    (ROOT/'evidence/missiles-smoke.txt').write_text(transcript)
    print('PTY missiles passed: fresh launch/cancel, remote kill and online-session invalidation, mine accounting, fatal cloak-overriding retaliation, true killer, Earth disposal and replacement without turn refill.')
