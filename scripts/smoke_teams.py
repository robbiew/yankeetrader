"""Exercise team invitations, sharing and revocation through real PTY/GoDoors."""
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


def play(data, alias, commands, password=None, after='1;q'):
    master, slave = pty.openpty()
    proc = subprocess.Popen([binary, '-compact', '-data', str(data), '-local', alias],
                            stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    steps = [(b'> ', commands.encode()+b'\r')]
    if password is not None:
        steps += [(b'Team password (4 characters; entered separately): ', password.encode()+b'\r'),
                  (b'Team change saved.', after.encode()+b'\r')]
    output = b''
    cursor = 0
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
                while steps:
                    at = output.find(steps[0][0], cursor)
                    if at < 0:
                        break
                    expected, reply = steps.pop(0)
                    cursor = at+len(expected)
                    os.write(master, reply)
        proc.wait(timeout=2)
        assert not steps and proc.returncode == 0 and b'Saved. Safe travels' in output, output
        if password:
            assert password.encode() not in output, 'invitation echoed in transcript'
        return output.decode(errors='replace').replace('\r', '')
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)


with tempfile.TemporaryDirectory(prefix='yt-team-smoke-') as temp:
    data = Path(temp)/'world'
    subprocess.run([binary, '-data', str(data), '-init', '-sectors', '8'], check=True, capture_output=True)
    play(data, 'Captain', 'q')
    path = data/'world.json'
    world = json.loads(path.read_text())
    world['Players']['1']['Credits'] = 100000
    world['Ports']['2'].update(Owner=1, Treasury=777)
    path.write_text(json.dumps(world))
    transcript = play(data, 'Captain', 'create Home;land;bank 1000;leave;team;2;Orion', 'ABCD')
    transcript += play(data, 'Member', 'team;3;1', 'abcd', '1;land;bank 0;leave;treasury;q')
    world = json.loads(path.read_text())
    assert world['Version'] == 17 and world['Players']['2']['Team'] == 1
    assert world['Players']['2']['Credits'] == 2005 and world['Planets']['2']['Bank'] == 0
    assert world['Ports']['2']['Treasury'] == 777, 'teammate collected private port balance'
    transcript += play(data, 'Captain', 'team;7;2;y;1;q')
    transcript += play(data, 'Member', 'land;q')
    assert 'permission to land is denied' in transcript
    # Removal is a kick, not a permanent ban: the unchanged invitation still works.
    transcript += play(data, 'Member', 'team;3;1', 'ABCD')
    transcript += play(data, 'Captain', 'team;4;y;1;collect;q')
    transcript += play(data, 'Member', 'team;1;q')
    world = json.loads(path.read_text())
    assert world['Teams']['1']['Captain'] == 2 and world['Players']['1']['Team'] == 0
    assert world['Planets']['2']['Owner'] == 1 and world['Ports']['2']['Owner'] == 1
    assert world['Ports']['2']['Treasury'] == 0 and world['Players']['1']['Credits'] == 74777
    assert world['Players']['1']['Turns'] == world['Players']['2']['Turns'] == 500
    assert b'ABCD' not in path.read_bytes() and b'abcd' not in path.read_bytes()
    (root/'evidence/team-smoke.txt').write_text(transcript)
    print('PTY teams passed: masked invitations, creation/join, shared banking, personal port accounts, removal/rejoin, retained assets and visiting-member captain succession.')
