"""Verify saved Xannor routes, mines, safe encounters and reconnect terminals."""
import copy
import datetime
import json
import subprocess
import tempfile
from pathlib import Path

from smoke_newspaper import BINARY, play, run_on_stable_date


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix='yt-xannor-mobile-smoke-') as temp:
        root = Path(temp)
        seed = root / 'seed'
        guard.run(subprocess.run, [BINARY, '-data', str(seed), '-init', '-sectors', '12'], check=True, capture_output=True)
        guard.run(play, seed, 'Captain', 'q')
        original = json.loads((seed / 'world.json').read_text())
        stamp = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2)).isoformat().replace('+00:00', 'Z')
        for mode in ('return', 'mines', 'ship', 'planet'):
            data = root / mode
            data.mkdir()
            path = data / 'world.json'
            world = copy.deepcopy(original)
            world['LastMaintenance'] = (guard.day - datetime.timedelta(days=1)).isoformat()
            world['Players']['1'].update(Sector=10 if mode == 'ship' else 1, StoredScore=4000, Cloak=1 if mode == 'ship' else 0)
            world['Xannor'] = dict(HQ=8, Reserve=0)
            for sector in range(8, 13):
                world['Sectors'][str(sector)]['Warps'] = []
            world['Sectors']['9']['Warps'] = [8] if mode == 'return' else [10]
            world['Sectors']['10']['Warps'] = [8]
            world['Sectors']['8']['Defense'] = dict(Owner=-1, Fighters=1)
            force = 100000 if mode == 'mines' else 100
            world['Sectors']['9']['Defense'] = dict(Owner=-1, Fighters=force)
            for slot, sector, owner, faction, name, stock in [(99, 11, -2, 'mercenaries', 'Mercenary Base', 0), (100, 8, -1, 'xannor', 'Xannoron', 37.5)]:
                world['Planets'][str(slot)] = dict(ID=slot, Sector=sector, Owner=owner, FactionHome=faction, Name=name, Updated=stamp,
                    Production=[0, 0, 0], Cargo=[0, 0, 0], Fighters=stock, Missiles=0, Mines=0, Plasma=0, Ground=100, Bank=1)
                world['Sectors'][str(sector)]['Planet'] = slot
            if mode != 'return':
                world['Sectors']['10']['Minefield'] = [dict(Owner=1, Count=3)]
            if mode in ('ship', 'planet'):
                world['Sectors']['10']['Defense'] = dict(Owner=1, Fighters=100)
            if mode == 'planet':
                world['Planets']['2'] = dict(ID=2, Sector=10, Owner=0, Name='Neutral probe', Updated=stamp, Production=[0, 0, 0], Cargo=[0, 0, 0], Fighters=37.5, Missiles=0, Mines=0, Plasma=0, Ground=0, Bank=1234)
                world['Sectors']['10']['Planet'] = 2
            path.write_text(json.dumps(world))
            guard.run(subprocess.run, [BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, timeout=10)
            saved = json.loads(path.read_text())
            assert saved['Version'] == 14 and saved['Xannor'] == dict(HQ=8, Reserve=0)
            assert saved['Planets']['100']['Fighters'] == 37.5
            assert saved['Players']['1']['Fighters'] == world['Players']['1']['Fighters'] and not saved['Players']['1'].get('Death')
            if mode in ('ship', 'planet'):
                assert saved['Sectors']['9']['Defense'] == dict(Owner=-1, Fighters=100)
                assert saved['Sectors']['8']['Defense'] == dict(Owner=-1, Fighters=1)
                assert saved['Sectors']['10']['Minefield'] == [dict(Owner=1, Count=3)]
                assert saved['Sectors']['10']['Defense'] == dict(Owner=1, Fighters=100)
                if mode == 'planet':
                    actual, expected = saved['Planets']['2'].copy(), world['Planets']['2'].copy()
                    assert datetime.datetime.fromisoformat(actual.pop('Updated')) == datetime.datetime.fromisoformat(expected.pop('Updated'))
                    assert actual == expected, (actual, expected)
            else:
                assert not saved['Sectors']['9'].get('Defense')
                final = saved['Sectors']['8']['Defense']
                assert final['Owner'] == -1
                if mode == 'return':
                    assert final['Fighters'] == 101
                else:
                    assert not saved['Sectors']['10'].get('Minefield')
                    assert 3 <= 100001 - final['Fighters'] <= 3000
            result = guard.run(subprocess.run, [BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, text=True, timeout=10)
            assert 'no daily phases repeated' in result.stdout
            assert json.loads(path.read_text()) == saved
            if mode in ('return', 'mines'):
                saved['Players']['1']['Sector'] = 8
                path.write_text(json.dumps(saved))
                for classic in (False, True):
                    text = guard.run(play, data, 'Captain', 'q;y' if classic else 'q', classic=classic)
                    assert 'Hostile sector fighters block normal actions.' in text and 'BRIBE' in text, text


if __name__ == '__main__':
    run_on_stable_date(exercise)
    print('Xannor mobile PTY passed: saved return routes, uniform mine accounting, retained friendly stocks, ship/planet holds, daily replay and compact/classic reconnect encounters.')
