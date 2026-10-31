"""Real player commands confirm one Earth kill while another caller is online."""
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
                if answer is not None and not confirmed and b'Damage and losses save immediately. [y/N] ' in output:
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


with tempfile.TemporaryDirectory(prefix='yt-attack-smoke-') as temp:
    data = Path(temp)/'world'
    subprocess.run([BINARY,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
    for alias in ('Victim','Killer'):
        code,_ = play(data,alias,'q')
        assert code == 0
    path = data/'world.json'
    world = json.loads(path.read_text())
    world['Players']['1'].update(Cloak=0,Fighters=0,Shields=0,Mines=100,Credits=10000,Turns=37)
    world['Players']['2'].update(Cloak=0,Fighters=100)
    world['Ports']['2'].update(Owner=1,Treasury=777)
    path.write_text(json.dumps(world))
    # Stacked Y and command repeats do not approve; a separate blank cancels.
    transcript = ''
    for commands,answer in [('attack 1 1;y\ry\r',''),('attack 1 1','y/')]:
        code,text = play(data,'Killer',commands,answer=answer)
        assert code == 0 and 'Attack cancelled.' in text,text
        assert json.loads(path.read_text())['Players']['1'].get('Death') is None
        transcript += text
    killer_output = []
    def attack():
        code,text = play(data,'Killer','attack 1 1',answer='y')
        assert code == 0 and 'Victim destroyed.' in text and 'Earth protection safely disposed' in text,text
        killer_output.append(text)
    # Victim remains online while a second real game process executes the attack.
    code,old = play(data,'Victim','m 2;q',action=attack)
    assert code == 1 and 'ship was destroyed' in old,old
    transcript += ''.join(killer_output)+old
    world = json.loads(path.read_text())
    victim,killer = world['Players']['1'],world['Players']['2']
    assert victim['Mines'] == 0 and 0 <= killer['Mines'] < 100
    assert victim['Credits']+killer['Credits'] == 11005
    assert victim['Death']['Cause'] == 'combat' and victim['Death']['Killer'] == 2
    assert world['Ports']['2']['Owner'] == 2 and world['Ports']['2']['Treasury'] == 777
    assert world['Sectors']['1'].get('Defense') is None
    code,text = play(data,'Victim','i;m 2;q')
    assert code == 0 and 'Remaining turns: 37' in text and 'Moved to sector 2.' in text,text
    transcript += text
    code,text = play(data,'Newcomer','p;equip fighters 1;m 2;q')
    assert code == 0 and 'Equipment purchased and saved.' in text and 'Moved to sector 2.' in text,text
    transcript += text
    world = json.loads(path.read_text())
    assert world['Players']['1']['Turns'] == 36 and world['Players']['3']['Fighters'] == 26
    (ROOT/'evidence/attack-smoke.txt').write_text(transcript)
    print('PTY attacks passed: fresh confirmation, Earth mine disposal, online victim invalidation, replacement turn preservation and newcomer Earth services/exit.')
