"""Verify faction-base creation, access, restoration and captured-title persistence."""
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
    # A version-12 save migrates without inventing a base until maintenance.
    world['Version'] = 12
    for p in world['Players'].values():p.pop('LastActivity',None)
    world.pop('NextBattleReport', None)
    world['LastMaintenance'] = (today - datetime.timedelta(days=1)).isoformat()
    path.write_text(json.dumps(world))
    subprocess.run([BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, timeout=10)
    created = json.loads(path.read_text())
    base = created['Planets']['99']
    assert created['Version'] == 21 and created['Sectors']['8']['Planet'] == 99
    assert base['FactionHome'] == 'mercenaries' and base['Owner'] == -2
    assert base['Production'] == [100000, 100000, 100000]
    assert base['Ground'] == 150000 and base['Bank'] == 25000000
    result = subprocess.run([BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, text=True, timeout=10)
    assert 'no daily phases repeated' in result.stdout and json.loads(path.read_text()) == created
    created['Players']['1']['Sector'] = 8
    path.write_text(json.dumps(created))
    text = play(data, 'Captain', 'land;q')
    assert 'permission to land is denied by ground defenses' in text, text
    for captured in (False, True):
        world = json.loads(path.read_text())
        world['LastMaintenance'] = (today - datetime.timedelta(days=1)).isoformat()
        base = world['Planets']['99']
        base['Owner'] = 1 if captured else -2
        base['Ground'] = base['Bank'] = 0
        # Isolate reserve restoration from unrelated normal production.
        base['Updated'] = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2)).isoformat().replace('+00:00', 'Z')
        path.write_text(json.dumps(world))
        subprocess.run([BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, timeout=10)
        saved = json.loads(path.read_text())
        assert len(saved['Planets']) == 1 and saved['Planets']['99']['FactionHome'] == 'mercenaries'
        restored = saved['Planets']['99']
        assert restored['Owner'] == (1 if captured else -2)
        assert restored['Ground'] == (0 if captured else 150000)
        assert restored['Bank'] == (0 if captured else 25000000)
    # A captured base is a normal human title for landing, even under its stable
    # faction identity. A separate process must observe that permission.
    text = play(data, 'Captain', 'land;leave;q')
    assert 'Planet Mercenary Base | governor 1 | garrison 0 | bank 0 credits' in text, text
    final = json.loads(path.read_text())
    assert final['Planets']['99']['Owner'] == 1


for attempt in range(3):
    today = datetime.datetime.now(datetime.timezone.utc).date()
    try:
        with tempfile.TemporaryDirectory(prefix='yt-base-smoke-') as temp:
            exercise(Path(temp), today)
    except Exception:
        if datetime.datetime.now(datetime.timezone.utc).date() == today:
            raise
    else:
        if datetime.datetime.now(datetime.timezone.utc).date() == today:
            print('Mercenary base smoke passed: version-12 migration, finite creation, guarded landing, reserve repair, replay and captured-title persistence.')
            break
else:
    raise AssertionError('UTC date changed during all three disposable base attempts')
