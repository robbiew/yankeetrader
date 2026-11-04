"""Reject altered native bytes and missing/forged phase witnesses."""
import contextlib
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_initial_maintenance import DEFAULT, verify


class InitialMaintenanceEvidenceTests(unittest.TestCase):
    def check(self, root):
        with contextlib.redirect_stdout(io.StringIO()): verify(root)

    def test_retained_native_controls(self):
        self.check(DEFAULT)

    def test_corruptions_even_with_updated_file_hash(self):
        cases = [
            ('after-YTDATA.DAT.gz', lambda b: gzip.compress(gzip.decompress(b)[:-1], mtime=0)),
            ('before-YTDATA.DAT.gz', lambda b: gzip.compress(bytes(568687), mtime=0)),
            ('after-YTNEWS.DAT.gz', lambda b: gzip.compress(b'forged news', mtime=0)),
            ('MTIME.LOG', lambda b: b.replace(b'00.00am', b'02.00am')),
            ('MDATE.LOG', lambda b: b.replace(b'11/02/2026', b'11/03/2026')),
            ('MRET.LOG', lambda b: b'FAILED\r\n'),
            ('MAINT.LOG', lambda b: b.replace(b'Daily Maintenance Completed OK', b'FAILED')),
            ('INIT.LOG', lambda b: b.replace(b'<YT-INIT Normal Termination>', b'FAILED')),
            ('maint-commands.txt', lambda b: b.replace(b'time 00:00:00', b'time 00:00:01')),
        ]
        for filename, mutate in cases:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / 'controls'; shutil.copytree(DEFAULT, root)
                d = root / 'baseline-split'; f = d / filename
                original = f.read_bytes(); altered = mutate(original)
                self.assertNotEqual(original, altered)
                f.write_bytes(altered)
                meta = json.loads((d / 'result.json').read_text())
                meta['files'][filename] = hashlib.sha256(altered).hexdigest()
                (d / 'result.json').write_text(json.dumps(meta))
                with self.assertRaises(AssertionError): self.check(root)

    def test_missing_control_and_phase_witness(self):
        for target in ('repeat-integrated', 'baseline-split/MRET.LOG'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / 'controls'; shutil.copytree(DEFAULT, root)
                p = root / target
                if p.is_dir(): shutil.rmtree(p)
                else: p.unlink()
                with self.assertRaises(AssertionError): self.check(root)

    def test_forged_binary_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'controls'; shutil.copytree(DEFAULT, root)
            p = root / 'baseline-integrated/result.json'
            meta = json.loads(p.read_text()); meta['binaries']['YTMAINT.EXE'] = '0' * 64
            p.write_text(json.dumps(meta))
            with self.assertRaises(AssertionError): self.check(root)


if __name__ == '__main__': unittest.main()
