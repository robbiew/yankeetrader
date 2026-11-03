"""Independently verify fresh initializer date/path controls and auxiliary outputs."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
from verify_rng_clock import read_date, read_time
from verify_rng_trace import verify as verify_seeds

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
CASES = {
    'baseline': ('11/02/2026', '', '0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d'),
    'score-path': ('11/02/2026', 'SCORES.TXT', 'd4efcd1d3f4c2401e4e3c53345d67af72665b1027de56d289810c88e66fc1f5e'),
    'new-year': ('01/01/2027', '', 'e6d5ab5b3fab7563b279e976cdde3c4e6e494c2dffd5c35a74a60fac38fdf328'),
    'leap-day': ('02/29/2028', '', '523bfb954a8588285d6606cbdbfaa11dbccede964b512ad23bea13b496ed3d18'),
}
FILES = {'before-maint.dat.gz', 'YTNEWS.DAT', 'YTNAME.DAT', 'ANSWERS.TXT', 'COMMANDS.TXT',
         'DOSDATE.LOG', 'DOSTIME.LOG', 'ENDDATE.LOG', 'ENDTIME.LOG', 'INIT.LOG', 'INITRET.LOG', 'dosbox.log'}


def verify(destination=ROOT / 'research/yt-initializer-replay/controls'):
    destination = Path(destination)
    seeds = verify_seeds(destination / 'seed-dos', cases={name: ('timer', 5, None, date, '00:00:00')
                                                       for name, (date, _, _) in CASES.items()})
    directory = destination / 'world-dos'
    assert {p.name for p in directory.iterdir()} == set(CASES), 'fixed boundary controls'
    outcomes = {}
    for name, (date_text, scoreboard, pinned) in CASES.items():
        d = directory / name
        assert {p.name for p in d.iterdir()} == FILES | {'result.json'}, 'exact artifact/absence coverage'
        meta = json.loads((d / 'result.json').read_text())
        assert meta['name'] == name and meta['date'] == date_text and meta['scoreboard'] == scoreboard
        assert meta['recipe'] == 'original-initializer-boundaries-v1'
        assert meta['initializer_sha256'] == '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
        assert meta['runtime_sha256'] == '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
        assert meta['prior_radio_hex'] == b'prior-radio-control\r\n'.hex()
        assert meta['absent_outputs'] == ['YTRMSG.DAT'] and not (d / 'YTRMSG.DAT').exists()
        assert set(meta['files']) == FILES
        for filename, digest in meta['files'].items():
            assert SHA((d / filename).read_bytes()) == digest, (name, filename)
        commands = ['date ' + date_text, 'time 00:00:00', 'date > DOSDATE.LOG', 'time > DOSTIME.LOG',
                    'yt-init < answers.txt > INIT.LOG', 'echo INITIALIZER_RETURNED > INITRET.LOG',
                    'date > ENDDATE.LOG', 'time > ENDTIME.LOG']
        assert (d / 'COMMANDS.TXT').read_text() == '\n'.join(commands) + '\n', 'launch recipe'
        assert (d / 'ANSWERS.TXT').read_bytes() == ('Y\r\n' + scoreboard + '\r\n').encode('ascii')
        assert b'<YT-INIT Normal Termination>' in (d / 'INIT.LOG').read_bytes()
        assert b'INITIALIZER_RETURNED' in (d / 'INITRET.LOG').read_bytes()
        date = datetime.datetime.strptime(date_text, '%m/%d/%Y').date()
        assert read_date((d / 'DOSDATE.LOG').read_bytes()) == read_date((d / 'ENDDATE.LOG').read_bytes()) == date
        assert read_time((d / 'DOSTIME.LOG').read_bytes()) == 0
        assert 1 <= read_time((d / 'ENDTIME.LOG').read_bytes()) < 120
        seed = seeds[name]
        assert seed['timer_or_input_fac'] == '00004800' and seed['seeded'] == 0xc805, 'measured midnight seed'
        world = gzip.decompress((d / 'before-maint.dat.gz').read_bytes())
        assert len(world) == 4151 * 137 and SHA(world) == meta['world_sha256'] == pinned, 'pinned complete output'
        assert (d / 'YTNAME.DAT').read_bytes() == b'Dummy,Dummy,Dummy,Dummy\r\n\x1a', 'alias initialization'
        # The seven native PRINT lines have observed execution timestamp 00:00:01
        # in these controls; this is a measured boundary, not inferred from RND.
        labels = [' **********************'] * 2 + [' **                  **', ' ** Game Initialized **',
                                                    ' **                  **'] + [' **********************'] * 2
        prefix = '00:00:01 ' + date.strftime('%m-%d-%Y')
        expected_news = ''.join(prefix + label + '\r\n' for label in labels).encode('ascii') + b'\x1a'
        assert (d / 'YTNEWS.DAT').read_bytes() == expected_news, 'native newspaper layout and measured timestamp'
        outcomes[name] = dict(world=world, seed=seed['seeded'], date=date, scoreboard=scoreboard,
                              world_sha256=pinned, seed_trace_sha256=SHA((destination / 'seed-dos' / name / 'TRACE.BIN').read_bytes()))
    return outcomes


if __name__ == '__main__':
    print(json.dumps({name: {key: value for key, value in outcome.items() if key != 'world'}
                      for name, outcome in verify().items()}, default=str, indent=2))
