"""Exercise HQ revenge creation, private status and daily consumption in real PTYs."""
import copy
import datetime
import json
import subprocess
import tempfile
from pathlib import Path

from smoke_newspaper import BINARY, play, run_on_stable_date


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix='yt-xannor-revenge-smoke-') as temp:
        root = Path(temp)
        seed = root / 'seed'
        guard.run(subprocess.run, [BINARY, '-data', str(seed), '-init', '-sectors', '12'], check=True, capture_output=True)
        guard.run(play, seed, 'Captain', 'q')
        guard.run(play, seed, 'Visitor', 'q')
        original = json.loads((seed / 'world.json').read_text())
        future = (guard.clock() + datetime.timedelta(days=2)).isoformat()
        for classic in (False, True):
            for weapon in ('fighters', 'missiles'):
                data = root / (weapon + str(classic))
                data.mkdir()
                path = data / 'world.json'
                world = copy.deepcopy(original)
                p = world['Players']['1']
                p.update(Sector=7, Fighters=10000, Shields=1, Missiles=3, Cloak=0, StoredScore=4000)
                world['Players']['2']['StoredScore'] = 0
                world['Xannor'] = dict(HQ=8, Reserve=0)
                world['Sectors']['7']['Warps'] = [8]
                for i in range(8, 13):
                    world['Sectors'][str(i)]['Warps'] = []
                world['Sectors']['8']['Defense'] = dict(Owner=-1, Fighters=1)
                for slot, sector, owner, kind, name in [(99, 11, -2, 'mercenaries', 'Mercenary Base'), (100, 12, -1, 'xannor', 'Xannoron')]:
                    world['Planets'][str(slot)] = dict(ID=slot, Sector=sector, Owner=owner, FactionHome=kind, Name=name, Updated=future, Production=[0, 0, 0], Cargo=[0, 0, 0], Fighters=0, Missiles=0, Mines=0, Plasma=0, Ground=100, Bank=1)
                    world['Sectors'][str(sector)]['Planet'] = slot
                path.write_text(json.dumps(world))
                prompt = b'Main Command (?=Help)?' if classic else b'> '
                ending = b'i;q;y\r' if classic else b'i;q\r'
                if weapon == 'fighters':
                    commands = 'breach 8 10000'
                    replies = [(b'Accept human surrender if offered during this battle? [Y/n] ', b'y\r'), (b'defeat forces emergency escape. [y/N] ', b'y\r'), (prompt, ending)]
                else:
                    commands = 'missile 8 3'
                    replies = [(b'[y/N] ', b'y\r'), (prompt, ending)]
                text = guard.run(play, data, 'Captain', commands, classic=classic, followups=replies)
                assert 'Xannor revenge pending for this ship.' in text, text
                saved = json.loads(path.read_text())
                p = saved['Players']['1']
                assert saved['Version'] == 23 and saved['Xannor']['Revenge'] == dict(Player=1, Generation=p.get('ShipGeneration', 0))
                assert not saved['Sectors']['8'].get('Defense') and p['Credits'] == world['Players']['1']['Credits']+1000000
                outsider = guard.run(play, data, 'Visitor', 'i;news;q')
                assert 'revenge pending' not in outsider
                # Isolate one daily route after the real HQ victory. A returned
                # garrison holds HQ stable; the surviving mobile group passes the
                # current target and returns, with no new original-BASIC cache.
                saved = json.loads(path.read_text())
                saved['Players']['1'].update(Sector=10, Fighters=1000000000, Shields=1, Cloak=0, StoredScore=4000)
                saved['Players']['2']['StoredScore'] = 0
                saved['Xannor']['HQ'] = 8
                saved['Sectors']['8']['Defense'] = dict(Owner=-1, Fighters=1)
                saved['Sectors']['9']['Defense'] = dict(Owner=-1, Fighters=100)
                saved['Sectors']['9']['Warps'] = [10]
                saved['Sectors']['10']['Warps'] = [8]
                saved['LastMaintenance'] = (guard.day - datetime.timedelta(days=1)).isoformat()
                path.write_text(json.dumps(saved))
                guard.run(subprocess.run, [BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, timeout=10)
                after = json.loads(path.read_text())
                assert not after['Xannor'].get('Revenge') and not after['Players']['1'].get('Death')
                assert len(after['Players']['1'].get('BattleReports', [])) == 1 and after['Players']['1'].get('Cloak', 0) == 0, (weapon, classic, after['Xannor'], after['Players'], {k:v.get('Defense') for k,v in after['Sectors'].items() if v.get('Defense')})
                before = path.read_bytes()
                guard.run(subprocess.run, [BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, timeout=10)
                assert path.read_bytes() == before, 'daily replay repeated revenge/battle'
                text = guard.run(play, data, 'Captain', 'i;q;y' if classic else 'i;q', classic=classic)
                assert 'revenge pending' not in text and 'Private Xannor battle report' in text
                assert not json.loads(path.read_text())['Players']['1']['BattleReports'][0]['Unread']


if __name__ == '__main__':
    run_on_stable_date(exercise)
    print('Xannor revenge PTY passed: real fighter/missile HQ victories, compact/classic private status, queue persistence, daily consumption, reports and replay.')
