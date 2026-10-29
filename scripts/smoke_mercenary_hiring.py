"""Verify daily hiring, capacity and reconnect encounters through real processes."""
import datetime
import json
import subprocess
import tempfile
from pathlib import Path

from smoke_newspaper import BINARY, play


def exercise(root, today):
    data = root / 'world'
    subprocess.run([BINARY, '-data', str(data), '-init', '-sectors', '8'], check=True, capture_output=True)
    play(data, 'Captain', 'q')
    path = data / 'world.json'
    world = json.loads(path.read_text())
    world['LastMaintenance'] = (today - datetime.timedelta(days=1)).isoformat()
    world['Ports']['1']['Treasury'] = 1000000
    world['Ports']['2']['Treasury'] = 1990
    world['Players']['1']['Sector'] = 8
    path.write_text(json.dumps(world))
    result = subprocess.run([BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, text=True, timeout=10)
    assert 'Daily economy maintenance completed.' in result.stdout, result.stdout
    hired = json.loads(path.read_text())
    assert hired['Ports']['1']['Treasury'] == 1000000
    assert hired['Ports']['2']['Treasury'] == 1791
    assert hired['Sectors']['8']['Defense'] == {'Owner': -2, 'Fighters': 1}
    assert all(not hired['Sectors'][str(i)].get('Defense') for i in range(1, 8))
    result = subprocess.run([BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, text=True, timeout=10)
    assert 'no daily phases repeated' in result.stdout, result.stdout
    assert json.loads(path.read_text()) == hired
    text = play(data, 'Captain', 'q')
    assert 'Hostile sector fighters block normal actions.' in text, text
    assert 'BRIBE' in text, text
    # The full universe must still complete a fresh daily phase. No group grows
    # or moves, and the unplaced budget is not carried into a future hire.
    full = json.loads(path.read_text())
    full['LastMaintenance'] = (today - datetime.timedelta(days=1)).isoformat()
    path.write_text(json.dumps(full))
    subprocess.run([BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, timeout=10)
    full = json.loads(path.read_text())
    assert full['Ports']['2']['Treasury'] == 1612
    assert full['Sectors']['8']['Defense'] == hired['Sectors']['8']['Defense']
    # Login itself must run the same daily transaction, without a prior -maint.
    login = root / 'login'
    login.mkdir()
    (login / 'world.json').write_text(json.dumps(world))
    text = play(login, 'Captain', 'q')
    assert 'Hostile sector fighters block normal actions.' in text, text
    auto = json.loads((login / 'world.json').read_text())
    assert auto['Ports']['2']['Treasury'] == 1791
    assert auto['Sectors']['8']['Defense'] == {'Owner': -2, 'Fighters': 1}


for attempt in range(3):
    today = datetime.datetime.now(datetime.timezone.utc).date()
    try:
        with tempfile.TemporaryDirectory(prefix='yt-hiring-smoke-') as temp:
            exercise(Path(temp), today)
    except Exception:
        if datetime.datetime.now(datetime.timezone.utc).date() == today:
            raise
    else:
        if datetime.datetime.now(datetime.timezone.utc).date() == today:
            print('Mercenary hiring smoke passed: tax, finite capacity, protected sectors, daily replay and real reconnect encounter.')
            break
else:
    raise AssertionError('UTC date changed during all three disposable smoke attempts')
