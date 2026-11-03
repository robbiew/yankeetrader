"""Additional seed evidence must remain independently bound to its clock and patch."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_port_replay_seed import ROOT, verify
from verify_rng_trace import SHA

SOURCE = ROOT / 'research/yt-port-replay/seed-dos'

class ExtraSeedTests(unittest.TestCase):
    def test_retained(self):
        self.assertEqual(verify(SOURCE)['seeded'], 0xa90a05)

    def test_rehashed_corruption(self):
        for filename in ('TRACE.BIN', 'DOSTIME.LOG', 'RETURN.LOG', 'COMMANDS.TXT'):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'seed'; shutil.copytree(SOURCE, root)
                d = root / 'timer-plus-two'; p = d / filename
                raw = bytearray(p.read_bytes()); raw[0] ^= 1; p.write_bytes(raw)
                # A mount-path-only change is immaterial; corrupt the fixed command instead.
                if filename == 'COMMANDS.TXT':
                    p.write_text((d / filename).read_text().replace('time 00:00:02', 'time 00:00:03'))
                meta_path = d / 'result.json'; meta = json.loads(meta_path.read_text())
                meta['files'][filename] = SHA(p.read_bytes()); meta_path.write_text(json.dumps(meta))
                with self.assertRaises((AssertionError, ValueError)): verify(root)

    def test_patch_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'seed'; shutil.copytree(SOURCE, root)
            p = root / 'timer-plus-two/result.json'; data = json.loads(p.read_text())
            data['payload_hex'] = '90' + data['payload_hex'][2:]; p.write_text(json.dumps(data))
            with self.assertRaises(AssertionError): verify(root)

if __name__ == '__main__': unittest.main()
