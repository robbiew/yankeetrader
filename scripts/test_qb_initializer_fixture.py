"""The portable golden fixture must stay tied to independent DOS evidence."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'internal/qbinit/testdata/native_initializer.json'


class PortableFixtureTests(unittest.TestCase):
    def check(self, path):
        return subprocess.run([sys.executable, str(ROOT / 'scripts/export_qb_initializer_fixture.py'),
                               '--check', str(path)], cwd=ROOT, capture_output=True)

    def test_retained_native_provenance(self):
        result = self.check(FIXTURE)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_reject_changed_golden_claims(self):
        for field in ('world_sha256', 'stats', 'coverage', 'source_seed_trace_sha256'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                data = json.loads(FIXTURE.read_text())
                if field == 'coverage': data['cases'].pop()
                elif field == 'stats': data['cases'][0]['stats']['draws'] += 1
                else: data['cases'][0][field] = '0' * 64
                path = Path(tmp) / 'fixture.json'; path.write_text(json.dumps(data))
                result = self.check(path)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'portable Go fixture differs', result.stderr)


if __name__ == '__main__': unittest.main()
