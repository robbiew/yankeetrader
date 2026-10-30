"""Exercise planetary assaults and owner history through real GoDoors PTYs."""
import copy
import datetime
import json
import subprocess
import tempfile
from pathlib import Path

from smoke_newspaper import BINARY, play, run_on_stable_date


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix='yt-xannor-planets-smoke-') as temp:
        root = Path(temp)
        seed = root / 'seed'
        guard.run(subprocess.run, [BINARY, '-data', str(seed), '-init', '-sectors', '12'], check=True, capture_output=True)
        guard.run(play, seed, 'Captain', 'q')
        guard.run(play, seed, 'Visitor', 'q')
        original = json.loads((seed / 'world.json').read_text())
        stamp = (guard.clock() + datetime.timedelta(days=2)).isoformat()
        for mode in ('destroy', 'ground-victory', 'production', 'captured-home'):
            data = root / mode
            data.mkdir()
            path = data / 'world.json'
            world = copy.deepcopy(original)
            # A full read archive blocks unrelated lottery placement after destruction.
            world['Radio']=[dict(ID=i,RequestID=f'{i:032x}',From=2,To=2,FromAlias='Visitor',ToAlias='Visitor',Text='CAPACITY FIXTURE',Sent=stamp,Unread=False)for i in range(1,4097)]
            world['NextRadio']=4097
            world['LastMaintenance'] = (guard.day - datetime.timedelta(days=1)).isoformat()
            world['Players']['1'].update(Sector=1, StoredScore=4000, Cloak=0)
            world['Players']['2'].update(Sector=1, StoredScore=0)
            world['Xannor'] = dict(HQ=8, Reserve=0)
            for i in range(8, 13):
                world['Sectors'][str(i)]['Warps'] = []
            world['Sectors']['9']['Warps'] = [10]
            world['Sectors']['10']['Warps'] = [8]
            world['Sectors']['8']['Defense'] = dict(Owner=-1, Fighters=1)
            world['Sectors']['9']['Defense'] = dict(Owner=-1, Fighters=100)
            for slot, sector, owner, faction, name in [(99, 11, -2, 'mercenaries', 'Mercenary Base'), (100, 8, -1, 'xannor', 'Xannoron')]:
                world['Planets'][str(slot)] = dict(ID=slot, Sector=sector, Owner=owner, FactionHome=faction, Name=name, Updated=stamp, Production=[0, 0, 0], Cargo=[0, 0, 0], Fighters=0, Missiles=0, Mines=0, Plasma=0, Ground=100, Bank=1)
                world['Sectors'][str(sector)]['Planet'] = slot
            # Ground-victory stays at the strict civil-war threshold, isolating assault.
            planet = dict(ID=2, Sector=10, Owner=1, Name='Assault probe', Updated=stamp, Production=[.1, .1, .1] if mode == 'production' else [0, 0, 0], Cargo=[3, 4, 5], Fighters=1234, Missiles=5678, Mines=4321, Plasma=8765, Ground=1000000 if mode == 'ground-victory' else 0, Bank=123456)
            if mode == 'captured-home':
                del world['Planets']['100']
                world['Sectors']['8']['Planet'] = 0
                planet['FactionHome'] = 'xannor'
            world['Planets']['2'] = planet
            world['Sectors']['10']['Planet'] = 2
            path.write_text(json.dumps(world))
            guard.run(subprocess.run, [BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, timeout=10)
            saved = json.loads(path.read_text())
            p = saved['Players']['1']
            assert saved['Version'] == 21 and not p.get('Death') and p.get('ShipGeneration', 0) == world['Players']['1'].get('ShipGeneration', 0)
            for asset in ('Credits', 'Fighters', 'Missiles', 'Mines', 'Plasma', 'Cargo'):
                assert p[asset] == world['Players']['1'][asset], (asset, p)
            reports = p['BattleReports']
            assert len(reports) == 1 and reports[0]['Planet']['ID'] == 2 and reports[0]['Unread']
            report = reports[0]
            battle = report['Planet']
            assert battle['CargoBefore'] == [3, 4, 5] and battle['Name'] == 'Assault probe'
            assert 0 <= report['XannorLost'] <= 100
            if mode == 'ground-victory':
                assert not report['Destroyed'] and report['XannorLost'] == 100
                assert saved['Planets']['2']['Owner'] == 1 and saved['Planets']['2']['Cargo'] == [3, 4, 5]
                assert 999900 <= saved['Planets']['2']['Ground'] < 1000000
            elif mode != 'production':
                assert report['Destroyed'] and '2' not in saved['Planets'] and saved['Sectors']['10']['Planet'] == 0
                assert saved['Sectors']['8']['Defense']['Fighters'] == 101
            else:
                for i in range(3):
                    assert 0 <= battle['ProductionAfter'][i] <= .1
                    assert battle['CargoAfter'][i] == min(battle['CargoBefore'][i], 10 * battle['ProductionAfter'][i])
                assert report['Destroyed'] == (battle['ProductionAfter'] == [0, 0, 0])
                if not report['Destroyed']:
                    assert saved['Planets']['2']['Owner'] == 0
                    assert saved['Planets']['2']['Bank'] == 123456 and saved['Planets']['2']['Missiles'] == 5678
            before = path.read_bytes()
            guard.run(subprocess.run, [BINARY, '-data', str(data), '-maint'], check=True, capture_output=True, timeout=10)
            assert path.read_bytes() == before, 'maintenance replayed assault'
            public = guard.run(play, data, 'Visitor', 'battles;news;q')
            assert 'Xannor assault on Assault probe:' in public and 'Private Xannor' not in public
            assert 'ground ' not in public and 'Production ' not in public and 'Cargo ' not in public
            private = f"Assault probe: Xannor lost {report['XannorLost']} fighters; ground {battle['GroundBefore']} -> {battle['GroundAfter']}."
            for classic in (False, True):
                current = json.loads(path.read_text())
                current['Players']['1']['BattleReports'][0]['Unread'] = True
                path.write_text(json.dumps(current))
                text = guard.run(play, data, 'Captain', 'battles;q;y' if classic else 'battles;q', classic=classic)
                assert text.count(private) == 2, text
                assert 'Your ship was destroyed' not in text
                assert not json.loads(path.read_text())['Players']['1']['BattleReports'][0]['Unread']
            text = guard.run(play, data, 'Captain', 'q')
            assert 'Private Xannor planetary report' not in text


if __name__ == '__main__':
    run_on_stable_date(exercise)
    print('Xannor planetary PTY passed: ground victory, production/caps, captured-home destruction, no loot, replay, owner privacy and compact/classic history.')
