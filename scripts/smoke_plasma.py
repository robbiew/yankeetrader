"""Real GoDoors plasma consent, hidden hits, atomic aftermath and reconnect."""
import copy
import errno
import json
import os
import pty
import re
import select
import subprocess
import tempfile
import time
from pathlib import Path
from smoke_newspaper import BINARY, ROOT, play, run_on_stable_date


def launch(data, classic, mode):
    master, slave = pty.openpty()
    proc = subprocess.Popen([BINARY, '-ascii' if classic else '-compact', '-data', str(data), '-local', 'Captain'], stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    output = pending = b''
    keys, phase = 0, 'startup'
    prompt = b'Main Command (?=Help)?' if classic else b'> '
    end = time.monotonic() + 20
    try:
        while time.monotonic() < end:
            if not select.select([master], [], [], .1)[0]:
                continue
            try:
                chunk = os.read(master, 65536)
            except OSError as error:
                if error.errno == errno.EIO:
                    break
                raise
            if not chunk:
                break
            output += chunk
            pending += chunk
            if classic and keys < 3 and b'[ Press any Key ]' in pending:
                pending = pending.split(b'[ Press any Key ]', 1)[1]
                os.write(master, b' ')
                keys += 1
            if phase == 'startup' and prompt in pending:
                target = 1 if mode == 'self' else 8
                command = f'+;{target};1;y' if classic else f'plasma {target} 1;y'
                os.write(master, command.encode() + b'\r')
                pending = b''
                phase = 'confirm'
            elif phase == 'confirm' and b'Confirm? [y/N]' in pending:
                if mode == 'stale':
                    path = Path(data) / 'world.json'
                    current = json.loads(path.read_text())
                    current['Players']['2']['Shields'] -= 1
                    # The owned process is paused at consent; replace the complete
                    # disposable fixture without altering the stable lock inode.
                    temporary = path.with_suffix('.test')
                    temporary.write_text(json.dumps(current))
                    temporary.replace(path)
                os.write(master, b'n\r' if mode == 'cancel' else b'y\r')
                pending = b''
                phase = 'result'
            elif phase == 'result' and mode != 'self' and prompt in pending:
                os.write(master, b'q;y\r' if classic else b'q\r')
                pending = b''
                phase = 'quit'
        proc.wait(timeout=2)
        text = output.decode(errors='replace').replace('\r', '')
        assert proc.returncode == (1 if mode == 'self' else 0), text
        assert phase == ('result' if mode == 'self' else 'quit'), text
        assert 'SECRET ALIAS' not in text and 'SECRET PLANET' not in text, text
        return text
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)


def fixture(guard):
    with tempfile.TemporaryDirectory(prefix='yt-plasma-smoke-') as temporary:
        root = Path(temporary)
        seed = root / 'seed'
        guard.run(subprocess.run, [BINARY, '-data', str(seed), '-init', '-sectors', '8'], check=True, capture_output=True)
        guard.run(play, seed, 'Captain', 'q')
        original = json.loads((seed / 'world.json').read_text())
        transcript = ''
        for classic in (False, True):
            for mode in ('hit', 'cancel', 'stale', 'self', 'mixed'):
                data = root / f'{classic}-{mode}'
                data.mkdir()
                world = copy.deepcopy(original)
                world['Planets'] = {}
                for sid, sector in world['Sectors'].items():
                    sector.update(Planet=0, Minefield=None, Defense=None, Warps=[8] if sid == '1' else [1])
                source = world['Players']['1']
                source.update(Sector=1, Credits=100000, Plasma=3, Turns=500, Fighters=0, Shields=1 if mode == 'self' else 1000000, Mines=3 if mode == 'self' else 0, Cloak=0, Cargo=[0, 0, 0], DockToken='', PlanetToken='', LandedPlanet=0)
                hidden = copy.deepcopy(source)
                hidden.update(ID=2, Identity='test:hidden', Alias='SECRET ALIAS', Sector=8, Plasma=0, Credits=1000, Holds=10, Shields=1 if mode == 'mixed' else 1000000, Mines=3 if mode == 'mixed' else 0, Cloak=1)
                world['Players']['2'] = hidden
                world['NextPlayer'] = 3
                if mode == 'mixed':
                    world['Planets']['2'] = dict(ID=2, Generation=101, Sector=8, Owner=2, Name='SECRET PLANET', Updated=world['Created'], Production=[10000, 10000, 10000], Cargo=[0, 0, 0], Ground=1, Bank=7777, Fighters=0, Missiles=0, Mines=0, Plasma=0)
                    world['Sectors']['8']['Planet'] = 2
                    world['NextPlanetGeneration'] = 102
                    world['Ports']['2']['Owner'] = 2
                path = data / 'world.json'
                path.write_text(json.dumps(world))
                text = guard.run(launch, data, classic, mode)
                transcript += text
                saved = json.loads(path.read_text())
                actor, target = saved['Players']['1'], saved['Players']['2']
                assert saved['Version'] == 26
                if mode in ('cancel', 'stale'):
                    assert actor['Plasma'] == 3 and actor['Turns'] == 500 and 'Plasma launch saved:' not in text, text
                    continue
                assert actor['Turns'] == 499 and text.count('Plasma launch saved:') == 1, text
                if mode == 'self':
                    assert actor['Death']['Cause'] == 'plasma' and actor['Death']['Killer'] == 1 and actor['Plasma'] == 0
                    assert not saved['Sectors']['1'].get('Minefield') and 'Wreck mines dropped/disarmed: 0/3' in text
                    assert 'this login has ended' in text
                    continue
                assert actor['Plasma'] == 2
                if mode == 'mixed':
                    assert target['Death']['Cause'] == 'plasma' and target['Death']['Killer'] == 1 and target['Shields'] == 0
                    assert saved['Ports']['2']['Owner'] == 1 and saved['Planets']['2']['Ground'] == 0
                    assert not saved['Sectors']['8'].get('Minefield') and 'planets struck/destroyed: 1/0' in text
                    credits = int(re.search(r'Salvage credited before any later losses: (\d+) credits', text)[1])
                    assert actor['Credits'] == 100000 + credits
                else:
                    assert target['Shields'] < 1000000 and not target.get('Death')
                guard.run(play, data, 'Captain', 'q')
                again = json.loads(path.read_text())['Players']['1']
                assert again['Plasma'] == actor['Plasma'] and again['Turns'] == actor['Turns'], 'reconnect replayed launch'
        return transcript


if __name__ == '__main__':
    text = run_on_stable_date(fixture)
    (ROOT / 'evidence/plasma-smoke.txt').write_text('\n'.join(line.rstrip() for line in text.splitlines()) + '\n')
    print('Plasma PTY passed: ten compact/classic consent, stale-state, hidden-hit, self-death, mixed wreck/planet aftermath scenarios and reconnects.')
