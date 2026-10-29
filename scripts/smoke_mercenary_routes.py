"""Check daily NPC route aftermath and its saved player-facing encounter."""
import copy
import datetime
import json
import subprocess
import tempfile
from pathlib import Path

from smoke_newspaper import BINARY, play


def exercise(root, today):
    seed = root / 'seed'
    subprocess.run([BINARY, '-data', str(seed), '-init', '-sectors', '12'], check=True, capture_output=True)
    play(seed, 'Captain', 'q')
    original = json.loads((seed / 'world.json').read_text())
    for mode in ('mines', 'planet'):
        data = root / mode
        data.mkdir()
        path = data / 'world.json'
        world = copy.deepcopy(original)
        # Isolate Mercenary routes from the separate score-funded Xannor HQ phase.
        world['Players']['1']['StoredScore'] = 0
        world['LastMaintenance'] = (today - datetime.timedelta(days=1)).isoformat()
        for sector in range(8, 13):
            world['Sectors'][str(sector)]['Warps'] = [sector + 1] if sector < 12 else []
        world['Sectors']['8']['Defense'] = {'Owner': -2, 'Fighters': 1 if mode == 'mines' else 100}
        if mode == 'mines':
            world['Sectors']['9']['Minefield'] = [{'Owner': 1, 'Count': 3}]
        else:
            world['Players']['1']['Sector'] = 9
            world['Sectors']['9']['Planet'] = 2
            # Suppress unrelated production while isolating title/stock changes.
            stamp = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2)).isoformat().replace('+00:00', 'Z')
            world['Planets']['2'] = dict(ID=2, Sector=9, Owner=1, Name='Probe', Updated=stamp,
                                        Production=[0, 0, 0], Cargo=[0, 0, 0], Fighters=37.75,
                                        Missiles=0, Mines=0, Plasma=0, Ground=500000, Bank=0)
        path.write_text(json.dumps(world))
        result = subprocess.run([BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, text=True, timeout=10)
        assert 'Daily economy maintenance completed.' in result.stdout, result.stdout
        after = json.loads(path.read_text())
        assert not after['Sectors']['8'].get('Defense')
        if mode == 'mines':
            assert all(not s.get('Defense') for s in after['Sectors'].values())
            assert after['Sectors']['9']['Minefield'] == [{'Owner': 1, 'Count': 2}]
            assert not after['Players']['1'].get('Death')
        else:
            assert after['Sectors']['9']['Defense'] == {'Owner': -2, 'Fighters': 137}
            assert after['Planets']['2']['Fighters'] == .75
            assert after['Planets']['2']['Owner'] == 1 and after['Planets']['2']['Ground'] == 500000
        result = subprocess.run([BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, text=True, timeout=10)
        assert 'no daily phases repeated' in result.stdout
        assert json.loads(path.read_text()) == after
        text = play(data, 'Captain', 'q')
        if mode == 'planet':
            assert 'Hostile sector fighters block normal actions.' in text and 'BRIBE' in text, text
        assert not json.loads(path.read_text())['Players']['1'].get('Death')


for attempt in range(3):
    today = datetime.datetime.now(datetime.timezone.utc).date()
    try:
        with tempfile.TemporaryDirectory(prefix='yt-routes-smoke-') as temp:
            exercise(Path(temp), today)
    except Exception:
        if datetime.datetime.now(datetime.timezone.utc).date() == today:
            raise
    else:
        if datetime.datetime.now(datetime.timezone.utc).date() == today:
            print('Mercenary routes smoke passed: daily mine aftermath, retained attribution, planetary pickup, title/ground preservation, replay and reconnect encounter.')
            break
else:
    raise AssertionError('UTC date changed during all three disposable route attempts')
