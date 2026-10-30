"""Exercise Xannor migration, creation, encounters and captured-home persistence."""
import datetime
import json
import subprocess
import tempfile
from pathlib import Path

from smoke_newspaper import BINARY, play, run_on_stable_date


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix='yt-xannor-smoke-') as temp:
        data = Path(temp) / 'world'
        guard.run(subprocess.run, [BINARY, '-data', str(data), '-init', '-sectors', '12'],
                  check=True, capture_output=True)
        guard.run(play, data, 'Captain', 'q')
        path = data / 'world.json'
        world = json.loads(path.read_text())
        # Deliberate disposable save overrides: pre-feature schema, an unpublished
        # stored score, and an overdue daily run. No live account is involved.
        world['Version'] = 13; world.pop("Season",None); world.pop("GenerationSeed",None)
        for p in world['Players'].values():p.pop('LastActivity',None)
        world.pop('NextBattleReport', None)
        world['Players']['1']['StoredScore'] = 1000000
        # Isolate HQ regeneration/restoration from the now-enabled planetary routes.
        for sector in world['Sectors'].values():
            if sector['ID'] > 7:
                sector['Warps'] = []
        world['LastMaintenance'] = (guard.day - datetime.timedelta(days=1)).isoformat()
        path.write_text(json.dumps(world))
        guard.run(subprocess.run, [BINARY, '-data', str(data), '-maint'],
                  check=True, capture_output=True, timeout=10)
        saved = json.loads(path.read_text())
        home = saved['Planets']['100']
        hq = saved['Xannor']['HQ']
        assert saved['Version'] == 23 and saved['Xannor']['Reserve'] == 0
        assert hq > 7 and home['Sector'] == hq and saved['Sectors'][str(hq)]['Planet'] == 100
        assert home['FactionHome'] == 'xannor' and home['Owner'] == -1
        assert home['Production'] == [100000, 100000, 100000]
        assert 0 <= home['Ground'] <= 273 and 100000 <= home['Bank'] < 10100000
        groups = [(int(id), sector['Defense']['Fighters']) for id, sector in saved['Sectors'].items() if sector.get('Defense', {}).get('Owner') == -1]
        assert sum(force for _, force in groups) == 2000
        encounter = groups[0][0]
        assert saved['Planets']['99']['FactionHome'] == 'mercenaries'
        result = guard.run(subprocess.run, [BINARY, '-data', str(data), '-maint'],
                           check=True, capture_output=True, text=True, timeout=10)
        assert 'no daily phases repeated' in result.stdout
        assert json.loads(path.read_text()) == saved
        saved['Players']['1']['Sector'] = encounter
        path.write_text(json.dumps(saved))
        for classic in (False, True):
            text = guard.run(play, data, 'Captain', 'q;y' if classic else 'q', classic=classic)
            assert 'Hostile sector fighters block normal actions.' in text and 'BRIBE' in text, text
        # Simulate a cleared sector defense to isolate planetary landing rules.
        saved = json.loads(path.read_text())
        for sector in saved['Sectors'].values():
            if sector.get('Defense', {}).get('Owner') == -1:
                sector.pop('Defense')
        saved['Players']['1']['Sector'] = hq
        saved['Planets']['100']['Ground'] = 100
        path.write_text(json.dumps(saved))
        text = guard.run(play, data, 'Captain', 'land;q')
        assert 'permission to land is denied by ground defenses' in text, text
        # Capture uses the real landing and garrison commands once ground is gone.
        saved = json.loads(path.read_text())
        saved['Planets']['100']['Ground'] = 0
        saved['Players']['1']['Ground'] = 100
        path.write_text(json.dumps(saved))
        text = guard.run(play, data, 'Captain', 'land;garrison 100;leave;q')
        captured = json.loads(path.read_text())
        home = captured['Planets']['100']
        assert home['Owner'] == 1 and home['Ground'] == 100 and home['Sector'] == hq, text
        # Isolate the captured-home policy from ordinary economic production.
        home['Ground'] = home['Bank'] = 0
        home['Updated'] = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2)).isoformat().replace('+00:00', 'Z')
        captured['LastMaintenance'] = (guard.day - datetime.timedelta(days=1)).isoformat()
        path.write_text(json.dumps(captured))
        guard.run(subprocess.run, [BINARY, '-data', str(data), '-maint'],
                  check=True, capture_output=True, timeout=10)
        saved = json.loads(path.read_text())
        home = saved['Planets']['100']
        assert home['Owner'] == 1 and home['Sector'] == hq and home['Ground'] == home['Bank'] == 0
        assert home['FactionHome'] == 'xannor' and saved['Xannor']['HQ'] != hq
        text = guard.run(play, data, 'Captain', 'land;leave;q')
        assert 'Planet Xannoron | governor 1 | garrison 0 | bank 0 credits' in text, text


if __name__ == '__main__':
    run_on_stable_date(exercise)
    print('Xannor PTY passed: version-13 migration, HQ/home creation, score regeneration, replay, compact/classic encounters, landing, capture and preserved ownership during relocation.')
