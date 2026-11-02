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
        run('-season-export', str(archive), '-admin-reset', '1', ok=False)
        run('-maint', '-season-export', str(root / 'invalid.json'), ok=False)
        assert world.read_bytes() == before
        reset_archive = root / 'reset.json'
        assert 'reset committed' in run('-admin-reset', '1', '-season-export', str(reset_archive), '-seed', '77')
        saved = json.loads(world.read_bytes())
        assert saved['Version'] == 30 and saved['Season'] == 2
        assert saved['Players'] == {} and saved['GenesisPorts'] == 20
        result = saved['SeasonResults'][0]
        assert result['Administrative'] and not result['Winner'] and result['Player'] == 0
        run('-admin-reset', '1', '-season-export', str(root / 'replay.json'), ok=False)
        assert not (root / 'replay.json').exists()
        print('Season export/admin reset CLI passed.')

if __name__ == '__main__':
    main()
