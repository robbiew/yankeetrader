"""Exercise playable QB creation, rejection, real PTY play, reset and restore."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import smoke_newspaper as terminal

ROOT = Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        binary = root / 'yt'
        subprocess.run(['go', 'build', '-o', str(binary), './cmd/yt'], cwd=ROOT, check=True)
        data = root / 'world'
        def run(*args, ok=True, target=data):
            result = subprocess.run([str(binary), '-data', str(target), *args], capture_output=True, text=True)
            assert (result.returncode == 0) == ok, (args, result.stdout, result.stderr)
            return result.stdout
        flags = ['-generation-profile', 'qb36-v1', '-qb-state', '0xc805', '-qb-date', '2027-01-01']
        for i, extra in enumerate((['-seed','36'], ['-dos-warps=false'], ['-dos-ports'], ['-sectors','32'], ['-qb-state','-1'], ['-qb-state','0x1000000'], ['-qb-date','2027-01-10'], ['-qb-date','2026-02-29'], ['-qb-state','0xa90a05'], ['-qb-state','619'])):
            target = root / f'reject-{i}'
            run('-init', *flags, *extra, ok=False, target=target)
            assert not (target / 'world.json').exists()
        run(*flags, '-maint', ok=False)
        run('-init', '-generation-profile', 'unknown', ok=False)
        run('-init', '-generation-profile', 'qb36-v1', '-qb-date', '2027-01-01', ok=False)
        run('-init', *flags, '-genesis-ports', '20')
        path = data / 'world.json'
        initial = json.loads(path.read_bytes())
        recipe = initial['QBRecipe']
        assert initial['Version'] == 35 and recipe['Profile'] == 'qb36-v1' and recipe['State'] == 0xc805
        assert recipe['Date'] == '2027-01-01' and len(recipe['SourceSHA256']) == 64
        before = path.read_bytes()
        run('-init', *flags, ok=False)
        assert path.read_bytes() == before
        terminal.BINARY = str(binary)
        terminal.play(data, 'QB Trader', 'm 2;q')
        played = json.loads(path.read_bytes())
        assert played['Players']['1']['Sector'] == 2 and played['QBRecipe'] == recipe
        port = played['Ports']['2']
        played['Players']['1'].update(Sector=port['Sector'])
        path.write_text(json.dumps(played))
        good = next(i for i,c in enumerate(port['Coefficient']) if c > 0)
        terminal.play(data, 'QB Trader', 'p;buy '+('ore','organics','equipment')[good]+' 1;q')
        traded = json.loads(path.read_bytes())
        assert traded['Players']['1']['Cargo'][good] == 1 and traded['QBRecipe'] == recipe
        # Classic terminal admission and safe port display use the same saved profile.
        terminal.play(data, 'QB Trader', 'p;0;q;y', classic=True)
        archive = root / 'season.json'
        run('-admin-reset', '1', '-season-export', str(archive), '-seed', '77')
        saved = json.loads(path.read_bytes())
        assert saved['Season'] == 2 and saved['QBRecipe'] == recipe and saved['Players'] == {}
        for key in initial['Sectors']:
            assert saved['Sectors'][key]['Warps'] == initial['Sectors'][key]['Warps']
        for key,p in initial['Ports'].items():
            assert all(saved['Ports'][key][f] == p[f] for f in ('Sector','Name','Production','Coefficient'))
        raw = archive.read_bytes()
        exported = json.loads(raw)
        world_bytes = raw.split(b'"World":', 1)[1].rstrip()[:-1]
        assert hashlib.sha256(world_bytes).hexdigest() == exported['WorldSHA256']
        restore = root / 'restore'
        restore.mkdir()
        (restore/'world.json').write_bytes(world_bytes)
        run('-maint', target=restore)
        assert json.loads((restore/'world.json').read_bytes())['QBRecipe'] == recipe
        run('-admin-reset', '1', '-season-export', str(root/'retry.json'), ok=False)
        assert not (root/'retry.json').exists()
        print('QB profile CLI/PTY passed: admission, navigation/trading, recipe, reset, archive/restore and replay guard.')

if __name__ == '__main__':
    main()
