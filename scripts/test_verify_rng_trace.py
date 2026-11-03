"""Rehashed corruption controls for the independent raw RNG evidence verifier."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_rng_trace import ROOT, SHA, verify, verify_trace, decode_single, verify_fixture

SOURCE = ROOT / 'research/yt-rng-seeding/trace-dos'

class RNGTraceTests(unittest.TestCase):
    def mutate(self, name, filename, change):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'trace'; shutil.copytree(SOURCE, root)
            d = root / name; p = d / filename
            p.write_bytes(change(p.read_bytes()))
            meta_path = d / 'result.json'; meta = json.loads(meta_path.read_text())
            meta['files'][filename] = SHA(p.read_bytes())
            meta_path.write_text(json.dumps(meta))
            with self.assertRaises(AssertionError): verify(root)

    def test_retained_controls(self):
        results = verify(SOURCE)
        self.assertEqual(len(results), 16)
        self.assertEqual(results['raw-preserved-low']['seeded'] & 255, 0xab)
        self.assertNotEqual(results['raw-zero']['seeded'], results['raw-zero-residue']['seeded'])
        self.assertEqual(results['raw-zero']['input_value'], 0)
        self.assertEqual(results['raw-zero-residue']['input_value'], 0)

    def test_zero_residue_decodes(self):
        self.assertEqual(decode_single(bytes.fromhex('abcdef00')), 0)

    def test_rehashed_trace_corruption(self):
        for index in (0, 4, 8, 12, 16, 20, 24, 20 + 255 * 8, 24 + 255 * 8, 2068):
            with self.subTest(index=index):
                def flip(raw):
                    result = bytearray(raw); result[index] ^= 1; return result
                self.mutate('raw-zero-residue', 'TRACE.BIN', flip)

    def test_rehashed_boundary_corruption(self):
        for name in ('unseeded-next-zero', 'unseeded-next-max'):
            for index in (20, 27):
                with self.subTest(name=name, index=index):
                    def flip(raw):
                        result = bytearray(raw); result[index] ^= 1; return result
                    self.mutate(name, 'TRACE.BIN', flip)

    def test_rehashed_control_corruption(self):
        controls = (
            ('RETURN.LOG', lambda raw: raw.replace(b'PROBE_RETURNED', b'NOT_RETURNED')),
            ('COMMANDS.TXT', lambda raw: raw.replace(b'time 00:00:00', b'time 00:00:01')),
            ('DOSDATE.LOG', lambda raw: raw.replace(b'11/02/2026', b'11/03/2026')),
            ('DOSTIME.LOG', lambda raw: raw.replace(b'am', b'pm')),
        )
        for filename, change in controls:
            with self.subTest(filename=filename): self.mutate('raw-zero', filename, change)

    def test_metadata_and_payload_contract(self):
        for field in ('payload_hex', 'copied_initializer_sha256', 'copied_runtime_sha256', 'payload_file_offset', 'samples'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'trace'; shutil.copytree(SOURCE, root)
                p = root / 'raw-zero/result.json'; meta = json.loads(p.read_text())
                meta[field] = meta[field] + 1 if isinstance(meta[field], int) else '00' + meta[field]
                p.write_text(json.dumps(meta))
                with self.assertRaises(AssertionError): verify(root)

    def test_portable_fixture_matches_and_rejects_corruption(self):
        fixture = ROOT / 'internal/qbrng/testdata/native_rng.json'
        verify_fixture(SOURCE, fixture)
        with tempfile.TemporaryDirectory() as tmp:
            data = json.loads(fixture.read_text())
            data['cases'][0]['trace_hex'] = '00' + data['cases'][0]['trace_hex'][2:]
            target = Path(tmp) / 'native.json'; target.write_text(json.dumps(data))
            with self.assertRaises(AssertionError): verify_fixture(SOURCE, target)

    def test_case_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'trace'; shutil.copytree(SOURCE, root)
            shutil.rmtree(root / 'timer-repeat')
            with self.assertRaises(AssertionError): verify(root)

if __name__ == '__main__': unittest.main()
