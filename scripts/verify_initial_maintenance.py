"""Independently verify bounded original initializer-to-maintenance evidence."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import sys
from verify_rng_clock import get, read_date, read_time

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'research/yt-maint/initial-controls'
SHA = lambda b: hashlib.sha256(b).hexdigest()
BINARIES = {
    'YT-INIT.EXE': '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2',
    'BRUN30.EXE': '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
    'YTMAINT.EXE': '8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6',
}
# Independent capture pins include every raw side file as well as whole worlds.
PINS = {'baseline-integrated': {'after-YTDATA.DAT.gz': '855da6bbcbe399c018a45997fbe50e931f811c457970d0831fa6e2b97fec6536',
                         'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                         'after-YTNEWS.DAT.gz': 'ad1eb158fe9329796129424cadf845f614695b6e42314df5a5f0acb81f8a66b1',
                         'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                         'after-YTSCORE.ASC.gz': '69d6f2d38b2d362df0e641a94d6669cf8a939c701787c4d5fa6b23730958d191',
                         'after-YTYNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a'},
 'baseline-split': {'after-YTDATA.DAT.gz': 'ada65f0695c768cdf59c853ac4800da33c15047ce06eb9332a563da767f1e983',
                    'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                    'after-YTNEWS.DAT.gz': '496dd8e6f9d32228c2e3b50c714a33edfa97366e1e0609e9b2a2dfd555ad041c',
                    'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                    'after-YTSCORE.ASC.gz': 'e8c51ad1607e48ad85896c41c18639abc180801b76d5d0a4dbc0bc0486c03aba',
                    'after-YTYNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
                    'before-YTDATA.DAT.gz': '0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
                    'before-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                    'before-YTNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a'},
 'new-year-integrated': {'after-YTDATA.DAT.gz': '95a0dbe2243ff55879121d3c316cb46c09acaeb62ba9c77c6b1c4e61fb1cef16',
                         'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                         'after-YTNEWS.DAT.gz': '2641505c05ce6c79d6fb77b1045c1af7eb6fd0d4ed36c97aa27ed2ad2c0422c3',
                         'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                         'after-YTSCORE.ASC.gz': '347f20ca102f37142e87c37aaccf92da4f5ad28ceb617e0f6615013b3770b274',
                         'after-YTYNEWS.DAT.gz': '07901bde0493ec123c5cdad35c4fa32add64125f0511e05e90a74942e9352759'},
 'new-year-split': {'after-YTDATA.DAT.gz': '202337451ea390d0b20a89c4cf223755f3fa5efc7932ee9855c5ee4034f46ab6',
                    'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                    'after-YTNEWS.DAT.gz': '3ead9803ab7162a0aa4c21608eb7d969c1ee37f312288554316b58be96b215f0',
                    'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                    'after-YTSCORE.ASC.gz': '2f6387d9cef22d07859666c0c0eccfdd7c7b4ab707b71cf19347a338e88ab176',
                    'after-YTYNEWS.DAT.gz': '07901bde0493ec123c5cdad35c4fa32add64125f0511e05e90a74942e9352759',
                    'before-YTDATA.DAT.gz': 'e6d5ab5b3fab7563b279e976cdde3c4e6e494c2dffd5c35a74a60fac38fdf328',
                    'before-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                    'before-YTNEWS.DAT.gz': '07901bde0493ec123c5cdad35c4fa32add64125f0511e05e90a74942e9352759'},
 'repeat-integrated': {'after-YTDATA.DAT.gz': '855da6bbcbe399c018a45997fbe50e931f811c457970d0831fa6e2b97fec6536',
                       'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                       'after-YTNEWS.DAT.gz': 'ad1eb158fe9329796129424cadf845f614695b6e42314df5a5f0acb81f8a66b1',
                       'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                       'after-YTSCORE.ASC.gz': '69d6f2d38b2d362df0e641a94d6669cf8a939c701787c4d5fa6b23730958d191',
                       'after-YTYNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a'},
 'repeat-split': {'after-YTDATA.DAT.gz': 'ada65f0695c768cdf59c853ac4800da33c15047ce06eb9332a563da767f1e983',
                  'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                  'after-YTNEWS.DAT.gz': '496dd8e6f9d32228c2e3b50c714a33edfa97366e1e0609e9b2a2dfd555ad041c',
                  'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                  'after-YTSCORE.ASC.gz': 'e8c51ad1607e48ad85896c41c18639abc180801b76d5d0a4dbc0bc0486c03aba',
                  'after-YTYNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
                  'before-YTDATA.DAT.gz': '0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
                  'before-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                  'before-YTNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a'},
 'second-one-split': {'after-YTDATA.DAT.gz': '61006adc663daf205e812cac9e7c935b2fe7167c458a7bfed3e093f96c9364f2',
                      'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                      'after-YTNEWS.DAT.gz': '0360df86b597a9770491afe657b1d8c824d18421dbd523d59f06e2c388eba108',
                      'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                      'after-YTSCORE.ASC.gz': '19246f1e8e9cfe685adb30cbc4d9687318f3baeb54e99167989c75273103a609',
                      'after-YTYNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
                      'before-YTDATA.DAT.gz': '0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
                      'before-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                      'before-YTNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a'},
 'second-two-split': {'after-YTDATA.DAT.gz': '0cd3985c84668e50285c1592fc3c0f7a71d8faefdff30de25d20ab2c78ac655f',
                      'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                      'after-YTNEWS.DAT.gz': '5e2dc90c6e620f12f54207ac93da554a4fec76cd570f43e831c183f8b5811152',
                      'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                      'after-YTSCORE.ASC.gz': '19246f1e8e9cfe685adb30cbc4d9687318f3baeb54e99167989c75273103a609',
                      'after-YTYNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
                      'before-YTDATA.DAT.gz': '0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
                      'before-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                      'before-YTNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a'}}


def verify(root=DEFAULT):
    assert {p.name for p in root.iterdir()} == set(PINS), 'complete control matrix'
    worlds = {}
    before_worlds = {}
    for name, pins in PINS.items():
        d = root / name
        meta = json.loads((d / 'result.json').read_text())
        base, mode = name.rsplit('-', 1)
        date = datetime.date(2027, 1, 1) if base == 'new-year' else datetime.date(2026, 11, 2)
        second = {'second-one': 1, 'second-two': 2}.get(base, 0)
        assert meta['recipe'] == 'original-initial-maintenance-v1'
        assert (meta['name'], meta['mode'], meta['date'], meta['time'], meta['cpu_cycles']) == (
            base, mode, date.strftime('%m/%d/%Y'), '00:00:00', 200000)
        assert meta['binaries'] == BINARIES, 'original binary identities'
        assert meta['initializer_child'] == ('original' if mode == 'integrated' else 'exit-stub-b8004ccd21')
        assert meta['maintenance_time'] == (f'00:00:{second:02d}' if mode == 'split' else None)
        assert set(meta['files']) == {p.name for p in d.iterdir()} - {'result.json'}, 'exact file inventory'
        expected = {'ANSWERS.TXT', 'INIT.LOG', 'INITRET.LOG', 'DOSDATE.LOG', 'DOSTIME.LOG',
                    'ENDDATE.LOG', 'ENDTIME.LOG', 'init-commands.txt', 'init-dosbox.log'} | set(pins)
        if mode == 'split': expected |= {'MAINT.LOG', 'MRET.LOG', 'MDATE.LOG', 'MTIME.LOG',
                                        'MEDATE.LOG', 'METIME.LOG', 'maint-commands.txt', 'maint-dosbox.log'}
        assert set(meta['files']) == expected, 'required phase witnesses'
        commands = ['date ' + meta['date'], 'time 00:00:00', 'date > DOSDATE.LOG',
                    'time > DOSTIME.LOG', 'yt-init < answers.txt > INIT.LOG',
                    'echo INITIALIZER_RETURNED > INITRET.LOG',
                    'date > ENDDATE.LOG', 'time > ENDTIME.LOG']
        assert (d / 'init-commands.txt').read_text() == '\n'.join(commands) + '\n'
        if mode == 'split':
            commands = ['date ' + meta['date'], f'time 00:00:{second:02d}',
                        'date > MDATE.LOG', 'time > MTIME.LOG', 'ytmaint > MAINT.LOG',
                        'echo MAINTENANCE_RETURNED > MRET.LOG',
                        'date > MEDATE.LOG', 'time > METIME.LOG']
            assert (d / 'maint-commands.txt').read_text() == '\n'.join(commands) + '\n'

        for n, digest in meta['files'].items():
            assert SHA((d / n).read_bytes()) == digest, 'retained file hash: ' + n
        assert set(pins) == {p.name for p in d.glob('*.gz')}, 'all binary data pinned'
        for n, digest in pins.items():
            assert SHA(gzip.decompress((d / n).read_bytes())) == digest, 'native byte pin: ' + n
        assert (d / 'ANSWERS.TXT').read_bytes() == b'Y\r\n\r\n'
        assert (d / 'INITRET.LOG').read_bytes() == b'INITIALIZER_RETURNED\r\n'
        init = (d / 'INIT.LOG').read_bytes()
        assert b'<YT-INIT Normal Termination>' in init
        assert read_date((d / 'DOSDATE.LOG').read_bytes()) == date
        assert read_date((d / 'ENDDATE.LOG').read_bytes()) == date
        assert read_time((d / 'DOSTIME.LOG').read_bytes()) == 0
        assert 0 < read_time((d / 'ENDTIME.LOG').read_bytes()) < 30
        if mode == 'split':
            assert b'Daily Maintenance Completed OK' not in init, 'stub boundary'
            assert b'Daily Maintenance Completed OK' in (d / 'MAINT.LOG').read_bytes()
            assert (d / 'MRET.LOG').read_bytes() == b'MAINTENANCE_RETURNED\r\n'
            for n in ('MDATE.LOG', 'MEDATE.LOG'): assert read_date((d / n).read_bytes()) == date
            assert read_time((d / 'MTIME.LOG').read_bytes()) == {0: 0, 1: .98, 2: 1.97}[second]
            assert second < read_time((d / 'METIME.LOG').read_bytes()) < second + 30
        else:
            assert b'Running initial maintenance...' in init and b'Daily Maintenance Completed OK' in init
        after = gzip.decompress((d / 'after-YTDATA.DAT.gz').read_bytes())
        assert len(after) == 4151 * 137
        assert get(after, 1, 81) == date.timetuple().tm_yday
        assert [(r, get(after, r, 85)) for r in range(4052, 4152) if get(after, r, 85)] == [
            (4052, 12), (4150, 14), (4151, 8)], 'three NPC planets'
        assert gzip.decompress((d / 'after-YTRMSG.DAT.gz').read_bytes()) == b''
        if mode == 'split':
            before = gzip.decompress((d / 'before-YTDATA.DAT.gz').read_bytes())
            before_worlds[name] = before
            assert len(before) == len(after)
            for r in range(52, 3052):
                start = (r - 1) * 137
                assert before[start+41:start+65] == after[start+41:start+65], 'unchanged warp graph'
            for r in range(3052, 4052):
                start = (r - 1) * 137
                assert before[start:start+41] == after[start:start+41], 'unchanged port name'
                assert get(after, r, 45) == date.timetuple().tm_yday
            for r in range(2, 52):
                start = (r - 1) * 137
                assert before[start:start+109] == after[start:start+109]
                assert get(before, r, 109) == 0 and get(after, r, 109) == -1
                assert before[start+113:start+137] == after[start+113:start+137]
        worlds[name] = after
    for mode in ('integrated', 'split'):
        assert worlds['baseline-' + mode] == worlds['repeat-' + mode], 'exact native repeat'
    assert worlds['baseline-integrated'] != worlds['baseline-split'], 'handoff differs'
    assert all(before_worlds[n + '-split'] == before_worlds['baseline-split']
               for n in ('repeat', 'second-one', 'second-two')), 'identical starting worlds'
    placements = {'baseline-integrated': (1349, 2925), 'baseline-split': (1095, 2598),
                  'second-one-split': (1497, 78), 'second-two-split': (2982, 359)}
    economy = None
    for name, (wanderer, mercenary) in placements.items():
        world = worlds[name]
        assert [(r - 51, get(world, r, 93)) for r in range(52, 3052) if get(world, r, 93)] == sorted(
            [(wanderer, 1), (mercenary, 99), (849, 100)]), 'observed NPC placement'
        assert [sum(get(world, r, 41) == c for r in range(3052, 4052))
                for c in (1, 2, 3)] == [346, 336, 318]
        value = b''.join(world[(r-1)*137+61:(r-1)*137+85] for r in range(3052, 4052))
        if economy is None: economy = value
        assert value == economy, 'same observed port rates and coefficients'
    assert len({worlds[n + '-split'] for n in ('baseline', 'second-one', 'second-two')}) == 3, 'clock-sensitive outputs'
    print(f'Verified {len(PINS)} original DOS initial-maintenance controls')


if __name__ == '__main__':
    verify(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT)
