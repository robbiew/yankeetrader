#!/usr/bin/env python3
"""Exercise the actual administrator CLI against a disposable world."""
import hashlib
import json
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        binary = root / 'yt'
        subprocess.run(['go', 'build', '-o', str(binary), './cmd/yt'], cwd=ROOT, check=True)
        data = root / 'data'
        def run(*args, ok=True):
            result = subprocess.run([str(binary), '-data', str(data), *args], capture_output=True, text=True)
            assert (result.returncode == 0) == ok, (args, result.stdout, result.stderr)
            return result.stdout
        run('-init', '-sectors', '32', '-genesis-ports', '20')
        world = data / 'world.json'
        before = world.read_bytes()
        archive = root / 'export.json'
        run('-season-export', str(archive))
        assert world.read_bytes() == before
        raw = archive.read_bytes()
        # The compact World value is retained verbatim inside the archive.
        world_bytes = raw.split(b'"World":', 1)[1].rstrip()[:-1]
        exported = json.loads(raw)
        assert hashlib.sha256(world_bytes).hexdigest() == exported['WorldSHA256']
        assert exported['World']['Season'] == 1
        run('-admin-reset', '1', ok=False)
        for extra in ([], ['-maint'], ['-init'], ['-local', 'Ignored']):
            run('-admin-reset', '0', *extra, ok=False)
            run('-admin-reset', '0', '-season-export', str(root / 'zero.json'), *extra, ok=False)
        assert not (root / 'zero.json').exists()
        run('-season-export', str(archive), '-admin-reset', '1', ok=False)
        run('-maint', '-season-export', str(root / 'invalid.json'), ok=False)
        assert world.read_bytes() == before
        reset_archive = root / 'reset.json'
        assert 'reset committed' in run('-admin-reset', '1', '-season-export', str(reset_archive), '-seed', '77')
        saved = json.loads(world.read_bytes())
        assert saved['Version'] == 34 and saved['Season'] == 2
        assert saved['Players'] == {} and saved['GenesisPorts'] == 20
        result = saved['SeasonResults'][0]
        assert result['Administrative'] and not result['Winner'] and result['Player'] == 0
        run('-admin-reset', '1', '-season-export', str(root / 'replay.json'), ok=False)
        assert not (root / 'replay.json').exists()
        small = root / 'small'
        subprocess.run([str(binary), '-data', str(small), '-init', '-sectors', '8'], check=True, capture_output=True)
        subprocess.run([str(binary), '-data', str(small), '-admin-reset', '1', '-season-export', str(root / 'small.json')], check=True, capture_output=True)
        small_world = json.loads((small / 'world.json').read_bytes())
        assert small_world['Season'] == 2 and len(small_world['Sectors']) == 8
        print('Season export/admin reset CLI passed.')

if __name__ == '__main__':
    main()
