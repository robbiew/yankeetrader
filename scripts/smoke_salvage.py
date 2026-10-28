"""Real PTY/GoDoors callers observe one atomic internal salvage/estate update."""
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


def play(data, alias, commands, action=None):
    master, slave = pty.openpty()
    proc = subprocess.Popen([BINARY, '-compact', '-data', str(data), '-local', alias],
                            stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    output = b''
    sent = False
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
        proc.wait(timeout=2)
        return proc.returncode, output.decode(errors='replace').replace('\r', '')
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)


with tempfile.TemporaryDirectory(prefix='yt-salvage-smoke-') as temp:
    temp = Path(temp)
    worker = temp/'store-tests'
    subprocess.run(['go', 'test', '-c', '-o', str(worker), './internal/store'],
                   cwd=ROOT, check=True, capture_output=True)
    data = temp/'world'
    subprocess.run([BINARY, '-data', str(data), '-init', '-sectors', '8'], check=True, capture_output=True)
    for alias in ('Victim', 'Killer'):
        code, _ = play(data, alias, 'q')
        assert code == 0
    path = data/'world.json'
    world = json.loads(path.read_text())
    world['Players']['1'].update(Credits=10000, Holds=100, Turns=37, Fighters=0,
                                 Shields=0, Cargo=[11, 23, 37], Missiles=100,
                                 Plasma=100, Ground=100, Mines=100)
    world['Ports']['2'].update(Owner=1, Treasury=777)
    world['Sectors']['3']['Defense'] = dict(Owner=1, Fighters=123)
    path.write_text(json.dumps(world))

    def settle():
        subprocess.run([str(worker), '-test.run=^TestFullSalvageWorker$'], check=True,
                       env=dict(os.environ, YT_SALVAGE_WORKER='1', YT_SALVAGE_DIR=str(data)),
                       capture_output=True)

    code, transcript = play(data, 'Victim', 'm 2;q', settle)
    assert code == 1 and 'ship was destroyed' in transcript, transcript
    world = json.loads(path.read_text())
    victim, killer = world['Players']['1'], world['Players']['2']
    assert victim['Credits']+killer['Credits'] == 11005
    assert victim['Holds']+killer['Holds'] == 110
    assert killer['Credits'] == 6005 and killer['Holds'] == 60
    assert world['Ports']['2']['Owner'] == 2 and world['Ports']['2']['Treasury'] == 777
    assert world['Sectors']['3']['Defense'] == dict(Owner=-2, Fighters=123)
    assert world['Sectors']['1'].get('Defense') is None
    code, output = play(data, 'Killer', 'treasury;collect;i;q')
    transcript += output
    assert code == 0 and 'Collected 777 credits' in output, output
    code, output = play(data, 'Victim', 'i;q')
    transcript += output
    assert code == 0 and 'Remaining turns: 37' in output, output
    world = json.loads(path.read_text())
    assert world['Version'] == 8 and world['Players']['2']['Credits'] == 6782
    assert world['Players']['1']['Team'] == 0 and world['Players']['1']['ShipGeneration'] == 2
    assert world['Ports']['2']['Owner'] == 2 and world['Ports']['2']['Treasury'] == 0
    (ROOT/'evidence/salvage-smoke.txt').write_text(transcript)
    print('PTY salvage passed: independent settlement, old-session rejection, persisted loot/titles/defenses, captured treasury collection and replacement without turn refill.')
