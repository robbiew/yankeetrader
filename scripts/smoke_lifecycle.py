"""Use real PTY/GoDoors and a separate test worker to invalidate live ships."""
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

root = Path(__file__).resolve().parents[1]
binary = str(root/'bin/yt')


@without_disruption
def play(data, commands, interrupt=None):
    master, slave = pty.openpty()
    proc = subprocess.Popen([binary, '-compact', '-data', str(data), '-local', 'Victim'],
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
                reject_disruption(output)
                if not sent and b'> ' in output:
                    if interrupt:
                        interrupt()
                    os.write(master, commands.encode()+b'\r')
                    sent = True
        proc.wait(timeout=2)
        return proc.returncode, output.decode(errors='replace').replace('\r', '')
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)


with tempfile.TemporaryDirectory(prefix='yt-lifecycle-smoke-') as temp:
    temp = Path(temp)
    worker = temp/'store-test'
    # The helper invokes the internal transaction API; no production kill/debug
    # command is added to the game. All worlds and worker binaries are disposable.
    subprocess.run(['go', 'test', '-c', '-o', str(worker), './internal/store'],
                   cwd=root, check=True, capture_output=True)
    transcript = ''
    for replace_before_old_command in (False, True):
        data = temp/str(replace_before_old_command)
        subprocess.run([binary, '-data', str(data), '-init', '-sectors', '8'],
                       check=True, capture_output=True)
        code, _ = play(data, 'q')
        assert code == 0
        path = data/'world.json'
        world = json.loads(path.read_text())
        world['Players']['1']['Turns'] = 37
        enemy = dict(world['Players']['1'])
        enemy.update(ID=2, Identity='local:killer', Alias='Killer')
        world['Players']['2'] = enemy
        world['NextPlayer'] = 3
        path.write_text(json.dumps(world))

        def kill():
            env = dict(os.environ, YT_LIFECYCLE_WORKER='1', YT_LIFECYCLE_DIR=str(data),
                       YT_LIFECYCLE_DEATH_ONLY='0' if replace_before_old_command else '1')
            subprocess.run([str(worker), '-test.run=^TestLifecycleWorker$'],
                           env=env, check=True, capture_output=True)

        code, output = play(data, 'm 2;acquire;y;q', kill)
        transcript += output
        assert code == 1 and ('ship session is no longer current' in output or
                              'ship was destroyed' in output), output
        world = json.loads(path.read_text())
        assert world['Players']['1']['Turns'] == 37
        assert world['Players']['1']['Sector'] == (1 if replace_before_old_command else 0)
        code, output = play(data, 'i;q')
        transcript += output
        assert code == 0 and 'Saved. Safe travels' in output, output
        if not replace_before_old_command:
            assert 'replacement ship has been built. Remaining turns: 37' in output
        world = json.loads(path.read_text())
        p = world['Players']['1']
        assert p['ShipGeneration'] == 2 and p.get('Death') is None
        assert (p['Sector'], p['Credits'], p['Turns'], p['Shields'], p['Missiles']) == (1, 1005, 37, 100, 1)
    (root/'evidence/lifecycle-smoke.txt').write_text(transcript)
    print('PTY lifecycle passed: independent-process death, old command-chain rejection before/after replacement, authenticated reconnect and preserved 37-turn budget.')
