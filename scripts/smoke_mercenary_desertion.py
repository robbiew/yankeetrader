"""Exercise saved human-defense desertion and reconnect encounter visibility."""
import copy
import datetime
import json
import subprocess
import tempfile
from pathlib import Path

from smoke_newspaper import BINARY, play


def exercise(root, today):
    seed = root / 'seed'
    subprocess.run([BINARY, '-data', str(seed), '-init', '-sectors', '8'], check=True, capture_output=True)
    play(seed, 'Captain', 'q')
    original = json.loads((seed / 'world.json').read_text())
    for strength in (100, 1):
        for attempt in range(8):
            data = root / f'force-{strength}-{attempt}'
            data.mkdir()
            path = data / 'world.json'
            world = copy.deepcopy(original)
            world['LastMaintenance'] = (today - datetime.timedelta(days=1)).isoformat()
            world['Players']['1'].update(Sector=8, Fighters=1000, Ground=500)
            world['Ports']['2']['Treasury'] = 90
            world['Ports']['8']['Owner'] = 1
            world['Sectors']['7']['Defense'] = {'Owner': 1, 'Fighters': 1}
            world['Sectors']['8']['Defense'] = {'Owner': 1, 'Fighters': strength}
            path.write_text(json.dumps(world))
            subprocess.run([BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, timeout=10)
            after = json.loads(path.read_text())
            defense = after['Sectors']['8']['Defense']
            assert defense['Fighters'] == strength and defense['Owner'] in (1, -2)
            assert after['Sectors']['7']['Defense'] == world['Sectors']['7']['Defense']
            assert after['Players']['1']['Fighters'] == 1000 and after['Players']['1']['Ground'] == 500
            assert after['Ports']['8']['Owner'] == 1 and after['Ports']['2']['Treasury'] == 81
            result = subprocess.run([BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, text=True, timeout=10)
            assert 'no daily phases repeated' in result.stdout
            assert json.loads(path.read_text()) == after
            converted = defense['Owner'] == -2
            assert strength != 100 or not converted
            text = play(data, 'Captain', 'q')
            assert ('Hostile sector fighters block normal actions.' in text) == converted, text
            if converted:
                text = play(data, 'Captain', 'q;y', classic=True)
                assert 'Hostile sector fighters block normal actions.' in text and 'BRIBE' in text, text
            if strength == 100 or converted:
                break
        else:
            raise AssertionError('Eight valid one-fighter probes all retained their owner; conversion UI not exercised')


for attempt in range(3):
    today = datetime.datetime.now(datetime.timezone.utc).date()
    try:
        with tempfile.TemporaryDirectory(prefix='yt-desertion-smoke-') as temp:
            exercise(Path(temp), today)
    except Exception:
        if datetime.datetime.now(datetime.timezone.utc).date() == today:
            raise
    else:
        if datetime.datetime.now(datetime.timezone.utc).date() == today:
            print('Human-defense desertion smoke passed: first-player conversion, strong/protected groups, exact force/tax persistence, daily replay and compact/classic reconnect encounter.')
            break
else:
    raise AssertionError('UTC date changed during all three disposable desertion attempts')
