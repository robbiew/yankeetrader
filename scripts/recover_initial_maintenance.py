"""Capture untouched DOS initialization/maintenance and isolated handoff controls."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
BINARIES = {
    'YT-INIT.EXE': '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2',
    'BRUN30.EXE': '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
    'YTMAINT.EXE': '8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6',
}
CASES = (('baseline', '11/02/2026'), ('repeat', '11/02/2026'), ('new-year', '01/01/2027'),
         ('second-one', '11/02/2026'), ('second-two', '11/02/2026'))


def launch(d, commands, label):
    (d / (label + '-commands.txt')).write_text('\n'.join(commands) + '\n')
    with (d / (label + '-dosbox.log')).open('w') as log:
        subprocess.run([shutil.which('dosbox-staging'), '--noprimaryconf', '--nolocalconf',
                        '--set', 'cpu_cycles=200000', '--set', 'nosound=true'] +
                       [v for c in ['mount c ' + str(d), 'c:'] + commands + ['exit'] for v in ('-c', c)],
                       env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'},
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)


def run(destination):
    binary = {n: (ROOT / 'archive/dos-original' / n).read_bytes() for n in BINARIES}
    assert {n: SHA(b) for n, b in binary.items()} == BINARIES
    assert shutil.which('dosbox-staging'), 'DOSBox Staging required'
    destination.mkdir(parents=True, exist_ok=False)
    for name, date in CASES:
        for mode in ('integrated', 'split'):
            if name.startswith('second-') and mode == 'integrated': continue
            clock = {'second-one': '00:00:01', 'second-two': '00:00:02'}.get(name, '00:00:00')
            d = destination / (name + '-' + mode)
            d.mkdir()
            for n, b in binary.items(): (d / n).write_bytes(b)
            (d / 'ANSWERS.TXT').write_bytes(b'Y\r\n\r\n')
            if mode == 'split': (d / 'YTMAINT.EXE').write_bytes(bytes.fromhex('b8004ccd21'))
            launch(d, ['date ' + date, 'time 00:00:00', 'date > DOSDATE.LOG',
                       'time > DOSTIME.LOG', 'yt-init < answers.txt > INIT.LOG',
                       'echo INITIALIZER_RETURNED > INITRET.LOG',
                       'date > ENDDATE.LOG', 'time > ENDTIME.LOG'], 'init')
            assert b'<YT-INIT Normal Termination>' in (d / 'INIT.LOG').read_bytes()
            if mode == 'split':
                for n in ('YTDATA.DAT', 'YTNEWS.DAT', 'YTNAME.DAT'):
                    (d / ('before-' + n + '.gz')).write_bytes(gzip.compress((d / n).read_bytes(), mtime=0))
                (d / 'YTMAINT.EXE').write_bytes(binary['YTMAINT.EXE'])
                launch(d, ['date ' + date, 'time ' + clock, 'date > MDATE.LOG', 'time > MTIME.LOG',
                           'ytmaint > MAINT.LOG', 'echo MAINTENANCE_RETURNED > MRET.LOG',
                           'date > MEDATE.LOG', 'time > METIME.LOG'], 'maint')
                assert b'Daily Maintenance Completed OK' in (d / 'MAINT.LOG').read_bytes()
            else:
                assert b'Daily Maintenance Completed OK' in (d / 'INIT.LOG').read_bytes()
            for p in list(d.iterdir()):
                if p.suffix.upper() in ('.DAT', '.ASC'):
                    (d / ('after-' + p.name + '.gz')).write_bytes(gzip.compress(p.read_bytes(), mtime=0))
                    p.unlink()
            for n in BINARIES: (d / n).unlink()
            meta = dict(recipe='original-initial-maintenance-v1', name=name, mode=mode,
                        date=date, time='00:00:00', maintenance_time=clock if mode == 'split' else None, cpu_cycles=200000, binaries=BINARIES,
                        initializer_child='original' if mode == 'integrated' else 'exit-stub-b8004ccd21',
                        files={p.name: SHA(p.read_bytes()) for p in sorted(d.iterdir())})
            (d / 'result.json').write_text(json.dumps(meta, indent=2) + '\n')
            print(d.name, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    run(parser.parse_args().destination.resolve())
