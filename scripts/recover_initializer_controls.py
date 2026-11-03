"""Capture copied original initializer outputs at bounded date/path boundaries."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from recover_rng_trace import run as capture_seeds

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
CASES = (
    ('baseline', '11/02/2026', ''),
    ('score-path', '11/02/2026', 'SCORES.TXT'),
    ('new-year', '01/01/2027', ''),
    ('leap-day', '02/29/2028', ''),
)


def run(destination):
    original = (ROOT / 'archive/dos-original/YT-INIT.EXE').read_bytes()
    runtime = (ROOT / 'archive/dos-original/BRUN30.EXE').read_bytes()
    assert SHA(original) == '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
    assert SHA(runtime) == '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
    executable = shutil.which('dosbox-staging')
    assert executable, 'DOSBox Staging required'
    destination.mkdir(parents=True, exist_ok=False)
    worlds = destination / 'world-dos'; worlds.mkdir()
    for name, date, scoreboard in CASES:
        directory = worlds / name; directory.mkdir()
        (directory / 'YT-INIT.EXE').write_bytes(original)
        (directory / 'BRUN30.EXE').write_bytes(runtime)
        (directory / 'YTMAINT.EXE').write_bytes(bytes.fromhex('b8004ccd21'))
        (directory / 'YTRMSG.DAT').write_bytes(b'prior-radio-control\r\n')
        (directory / 'ANSWERS.TXT').write_bytes(('Y\r\n' + scoreboard + '\r\n').encode('ascii'))
        commands = ['date ' + date, 'time 00:00:00', 'date > DOSDATE.LOG', 'time > DOSTIME.LOG',
                    'yt-init < answers.txt > INIT.LOG', 'echo INITIALIZER_RETURNED > INITRET.LOG',
                    'date > ENDDATE.LOG', 'time > ENDTIME.LOG']
        (directory / 'COMMANDS.TXT').write_text('\n'.join(commands) + '\n')
        with (directory / 'dosbox.log').open('w') as log:
            subprocess.run([executable, '--noprimaryconf', '--nolocalconf', '--set', 'cpu_cycles=200000',
                            '--set', 'nosound=true'] + [part for command in ['mount c ' + str(directory), 'c:'] + commands + ['exit']
                                                     for part in ('-c', command)],
                           env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'},
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
        assert b'<YT-INIT Normal Termination>' in (directory / 'INIT.LOG').read_bytes()
        world = (directory / 'YTDATA.DAT').read_bytes()
        assert len(world) == 4151 * 137
        (directory / 'before-maint.dat.gz').write_bytes(gzip.compress(world, mtime=0))
        keep = {'before-maint.dat.gz', 'YTNEWS.DAT', 'YTNAME.DAT',
                'ANSWERS.TXT', 'COMMANDS.TXT', 'DOSDATE.LOG', 'DOSTIME.LOG', 'ENDDATE.LOG',
                'ENDTIME.LOG', 'INIT.LOG', 'INITRET.LOG', 'dosbox.log'}
        assert not (directory / 'YTRMSG.DAT').exists(), 'radio file deleted by original initializer'
        assert keep <= {p.name for p in directory.iterdir()}, 'missing auxiliary outputs'
        meta = dict(name=name, date=date, scoreboard=scoreboard, recipe='original-initializer-boundaries-v1',
                    initializer_sha256=SHA(original), runtime_sha256=SHA(runtime),
                    world_sha256=SHA(world), prior_radio_hex=b'prior-radio-control\r\n'.hex(),
                    absent_outputs=['YTRMSG.DAT'], files={p: SHA((directory / p).read_bytes()) for p in sorted(keep)})
        (directory / 'result.json').write_text(json.dumps(meta, indent=2) + '\n')
        for p in directory.iterdir():
            if p.name not in keep | {'result.json'}: p.unlink()
        print(name, meta['world_sha256'], flush=True)
    capture_seeds(destination / 'seed-dos', [dict(name=name, mode='timer', date=date, time='00:00:00')
                                            for name, date, _ in CASES])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    run(parser.parse_args().destination.resolve())
