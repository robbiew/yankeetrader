"""Reject rehashed false boundary-control evidence without running DOSBox."""
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_initializer_controls import ROOT, SHA, verify

SOURCE = ROOT / 'research/yt-initializer-replay/controls'


class InitializerControlsTests(unittest.TestCase):
    def changed(self, change):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'controls'; shutil.copytree(SOURCE, destination)
            change(destination)
            with self.assertRaises((AssertionError, ValueError)):
                verify(destination)

    def rehashed(self, name, filename, change, group='world-dos'):
        def mutate(root):
            d = root / group / name; p = d / filename
            p.write_bytes(change(p.read_bytes()))
            path = d / 'result.json'; meta = json.loads(path.read_text())
            meta['files'][filename] = SHA(p.read_bytes())
            if filename == 'before-maint.dat.gz':
                meta['world_sha256'] = SHA(gzip.decompress(p.read_bytes()))
            path.write_text(json.dumps(meta))
        self.changed(mutate)

    def test_retained_controls(self):
        results = verify()
        self.assertEqual(set(results), {'baseline', 'score-path', 'new-year', 'leap-day'})
        self.assertEqual({r['seed'] for r in results.values()}, {0xc805})

    def test_rehashed_world_cannot_redefine_observation(self):
        def change(raw):
            world = bytearray(gzip.decompress(raw)); world[81] ^= 1
            return gzip.compress(world)
        self.rehashed('new-year', 'before-maint.dat.gz', change)

    def test_rehashed_auxiliary_changes(self):
        for filename in ('YTNAME.DAT', 'YTNEWS.DAT'):
            with self.subTest(filename=filename):
                self.rehashed('baseline', filename, lambda b: b'X' + b[1:])
        self.changed(lambda root: (root / 'world-dos/baseline/YTRMSG.DAT').write_bytes(b''))

    def test_rehashed_clock_and_return(self):
        for filename, change in (
            ('DOSDATE.LOG', lambda b: b.replace(b'11/02/2026', b'11/03/2026')),
            ('DOSTIME.LOG', lambda b: b.replace(b'am', b'pm')),
            ('INITRET.LOG', lambda b: b.replace(b'INITIALIZER_RETURNED', b'NOT_RETURNED')),
        ):
            with self.subTest(filename=filename): self.rehashed('baseline', filename, change)

    def test_rehashed_seed(self):
        def flip(raw):
            trace = bytearray(raw); trace[16] ^= 1; return bytes(trace)
        self.rehashed('leap-day', 'TRACE.BIN', flip, 'seed-dos')

    def test_rehashed_recipe_and_scoreboard(self):
        for filename, change in (
            ('COMMANDS.TXT', lambda b: b.replace(b'time 00:00:00', b'time 00:00:01')),
            ('ANSWERS.TXT', lambda b: b.replace(b'SCORES.TXT', b'OTHER.TXT')),
        ):
            with self.subTest(filename=filename): self.rehashed('score-path', filename, change)
        def mutate(root):
            path = root / 'world-dos/baseline/result.json'; meta = json.loads(path.read_text())
            meta['absent_outputs'] = []; path.write_text(json.dumps(meta))
        self.changed(mutate)

    def test_missing_control(self):
        self.changed(lambda root: shutil.rmtree(root / 'world-dos/leap-day'))


if __name__ == '__main__': unittest.main()
