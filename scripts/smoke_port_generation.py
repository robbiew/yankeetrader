"""Exercise DOS port creation, saved profile and season reset through the CLI."""
import json
import math
import re
import smoke_newspaper as terminal
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        binary = root / 'yt'
        subprocess.run(['go', 'build', '-o', str(binary), './cmd/yt'], cwd=ROOT, check=True)
        data = root / 'world'
        def run(*args, ok=True):
            result = subprocess.run([str(binary), '-data', str(data), *args], capture_output=True, text=True)
            assert (result.returncode == 0) == ok, (args, result.stdout, result.stderr)
        run('-init', '-sectors', '32', '-dos-ports', '-seed', '36')
        path = data / 'world.json'
        first = path.read_bytes()
        world = json.loads(first)
        assert world['Version'] == 33 and world['PortGeneration'] == 'dos'
        assert [world['Ports'][str(i)]['Sector'] for i in range(1, 5)] == [1, 3, 5, 7]
        assert len({p['Sector'] for p in world['Ports'].values()}) == 32
        for p in world['Ports'].values():
            assert sum(c > 0 for c in p['Coefficient']) == 1
            assert all(1000 <= r <= 32766 for r in p['Production'])
            assert p['Supply'] == [10*r for r in p['Production']]
            assert world['Sectors'][str(p['Sector'])]['Port'] == p['ID']
        run('-init', '-dos-ports', ok=False)
        run('-maint', '-dos-ports', ok=False)
        run('-dos-ports=false', ok=False)
        assert path.read_bytes() == first
        archive = root / 'season.json'
        run('-admin-reset', '1', '-season-export', str(archive), '-seed', '77')
        saved = json.loads(path.read_bytes())
        assert saved['Season'] == 2 and saved['PortGeneration'] == 'dos'
        assert saved['Ports']['2']['Sector'] == 3
        assert json.loads(archive.read_bytes())['World'] == world
        # Existing uniform worlds migrate without selecting the new economy.
        old = root / 'old'
        subprocess.run([str(binary), '-data', str(old), '-init', '-sectors', '8'], capture_output=True, check=True)
        p = old / 'world.json'
        legacy = json.loads(p.read_bytes()); legacy['Version'] = 32
        p.write_text(json.dumps(legacy))
        subprocess.run([str(binary), '-data', str(old), '-maint'], capture_output=True, check=True)
        upgraded = json.loads(p.read_bytes())
        assert upgraded['Version'] == 33 and not upgraded.get('PortGeneration')
        assert upgraded['Ports'] == legacy['Ports']
        terminal.BINARY = str(binary)
        for classic in (False, True):
            target = root / ('classic' if classic else 'compact')
            subprocess.run([str(binary), '-data', str(target), '-init', '-sectors', '32', '-dos-ports'], capture_output=True, check=True)
            terminal.play(target, 'Trader', 'q')
            path = target / 'world.json'
            world = json.loads(path.read_bytes())
            port = world['Ports']['2']
            world['Players']['1'].update(Sector=port['Sector'], Credits=1000000)
            path.write_text(json.dumps(world))
            text = terminal.play(target, 'Trader', 'p;0;q;y' if classic else 'p;q', classic=classic)
            if classic:
                assert port['Name'][:19] in text, text
            refs = (20.051570892333984, 29.302257537841797, 41.20359420776367)
            for i, label in enumerate(('Ore', 'Organics', 'Equipment')):
                expected = max(1, math.floor(refs[i]*(1-port['Coefficient'][i]/100)+.5))
                pattern = (r'^'+label+r'\.+\s+(?:Buying|Selling)\s+[^\n]*?\s+([0-9]+)\s*$') if classic else (r'^Port (?:buys|sells) '+label.lower()+r' at ([0-9]+) credits;')
                rows = re.findall(pattern, text, re.M)
                assert rows and int(rows[0]) == expected, (label, expected, rows, text)
            saved = json.loads(path.read_bytes())
            assert saved['PortGeneration'] == 'dos' and saved['Players']['1']['Credits'] == 1000000
        print('DOS ports CLI/PTY passed: creation, no reroll, archive/reset, migration and compact/classic quotes.')

if __name__ == '__main__':
    main()
