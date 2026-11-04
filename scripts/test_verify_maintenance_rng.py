"""Portable corruption regressions using retained original DOS evidence."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import verify_maintenance_rng as verifier


class MaintenanceRNGVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (verifier.ROOT / 'archive/dos-original/YTMAINT.EXE').read_bytes()
        cls.native = verifier.ROOT / 'research/yt-maint/rng-native/rea.json'
        cls.observations = {}
        for path in verifier.DEFAULT.glob('*/TRACE.BIN'):
            trace = path.read_bytes()
            if trace[-12:-8] == b'MSP1':
                cls.observations[path.parent.name] = (int.from_bytes(trace[-8:-4], 'little'), trace[-4:])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'controls'
        shutil.copytree(verifier.DEFAULT, self.root)
        self.folder = self.root / 'baseline--helper1-rnd-after'

    def write(self, filename, raw, folder=None):
        """An attacker can replace retained bytes and rehash the mutable manifest."""
        folder = folder or self.folder
        (folder / filename).write_bytes(raw)
        meta = json.loads((folder / 'result.json').read_text())
        meta['files'][filename] = verifier.SHA(raw)
        (folder / 'result.json').write_text(json.dumps(meta))

    def meta(self, field, value):
        path = self.folder / 'result.json'
        metadata = json.loads(path.read_text())
        metadata[field] = value
        path.write_text(json.dumps(metadata))

    def rejects(self):
        with self.assertRaises((AssertionError, ValueError, KeyError, FileNotFoundError)):
            verifier.verify(self.root)

    def test_retained_controls_pass(self):
        self.assertEqual(verifier.verify(self.root), {'controls': 151, 'selected_phase_hits': 108,
                         'inventory_hits': 9, 'inventory_misses': 34, 'native_reads': 2, 'untouched_oracles': 6})

    def test_raw_state_rehashed_manifest_fails(self):
        raw = bytearray((self.folder / 'TRACE.BIN').read_bytes()); raw[-8] ^= 1
        self.write('TRACE.BIN', raw)
        self.rejects()

    def test_fac_rehashed_manifest_fails(self):
        raw = bytearray((self.folder / 'TRACE.BIN').read_bytes()); raw[-4] ^= 1
        self.write('TRACE.BIN', raw)
        self.rejects()

    def test_world_rehashed_manifest_fails(self):
        raw = bytearray(gzip.decompress((self.folder / 'partial-world.dat.gz').read_bytes())); raw[800] ^= 1
        self.write('partial-world.dat.gz', gzip.compress(raw, mtime=0))
        self.rejects()

    def test_wrong_binary_identity_fails(self):
        binaries = dict(verifier.BINARIES); binaries['BRUN30.EXE'] = '0'*64
        self.meta('binaries', binaries)
        self.rejects()

    def test_wrong_fac_source_fails(self):
        self.meta('source', 0x7ea4)
        self.rejects()

    def test_wrong_date_fails(self):
        self.write('DOSDATE.LOG', (self.root / 'new-year--helper1-rnd-after/DOSDATE.LOG').read_bytes())
        self.rejects()

    def test_contradictory_sound_launch_fails(self):
        raw = (self.folder / 'dosbox.log').read_bytes()
        self.write('dosbox.log', raw+b'now | MIXER: Sound output enabled\n')
        self.rejects()

    def test_native_identity_substitution_fails(self):
        record = json.loads(self.native.read_text())
        record['records'][0]['subject']['digest']['sha256'] = '0'*64
        path = Path(self.temp.name) / 'native.json'; path.write_text(json.dumps(record))
        with self.assertRaisesRegex(AssertionError, 'native identity'):
            verifier.verify_native(path, self.original)

    def test_positive_argument_semantics_independent_of_pins(self):
        observed = copy.deepcopy(self.observations)
        state, _ = observed['baseline--helper2-argument']
        observed['baseline--helper2-argument'] = (state, bytes.fromhex('00000082'))
        with self.assertRaisesRegex(AssertionError, 'positive-one helper argument'):
            verifier.verify_semantics(observed)

    def test_untouched_completion_forgery_fails(self):
        oracles = Path(self.temp.name) / 'oracles'
        shutil.copytree(verifier.ROOT / 'research/yt-maint/rng-oracles', oracles)
        folder = oracles / 'baseline'
        raw = (folder / 'TRACE.BIN').read_bytes().replace(b'Daily Maintenance Completed OK', b'Forged normal completion claim')
        self.write('TRACE.BIN', raw, folder)
        with self.assertRaises(AssertionError):
            verifier.verify(self.root, oracles=oracles)

    def test_untouched_input_forgery_fails(self):
        oracles = Path(self.temp.name) / 'oracles'
        shutil.copytree(verifier.ROOT / 'research/yt-maint/rng-oracles', oracles)
        path = oracles / 'baseline/result.json'
        meta = json.loads(path.read_text()); meta['inputs']['YTDATA.DAT'] = '0'*64
        path.write_text(json.dumps(meta))
        with self.assertRaisesRegex(AssertionError, 'oracle input identities'):
            verifier.verify(self.root, oracles=oracles)

    def test_missing_phase_fails(self):
        shutil.rmtree(self.folder)
        self.rejects()

    def test_wrong_phase_identity_fails(self):
        self.meta('phase', 'helper2-rnd-after')
        self.rejects()

    def test_wrong_site_fails(self):
        self.meta('site', 0x798e)
        self.rejects()

    def test_wrong_probe_identity_fails(self):
        self.meta('copied_maintenance_sha256', '0'*64)
        self.rejects()

    def test_missing_hit_witness_fails(self):
        (self.folder / 'HIT.LOG').unlink()
        self.rejects()

    def test_forged_hit_on_miss_fails(self):
        folder = self.root / 'baseline--rnd-0ba5'
        self.write('HIT.LOG', b'PROBE_RECORDED\r\n', folder)
        self.rejects()

    def test_empty_hit_witness_fails(self):
        self.write('HIT.LOG', b'')
        self.rejects()

    def test_conflicting_miss_witness_fails(self):
        self.write('MISS.LOG', b'PROBE_NOT_REACHED\r\n')
        self.rejects()

    def test_forged_shell_return_fails(self):
        self.write('RETURN.LOG', b'PROBE_RETURNED\r\nforged')
        self.rejects()

    def test_clock_observation_substitution_fails(self):
        self.write('DOSTIME.LOG', (self.root / 'second-one--helper1-rnd-after/DOSTIME.LOG').read_bytes())
        self.rejects()

    def test_empty_launch_fails(self):
        self.write('dosbox.log', b'')
        self.rejects()

    def test_contradictory_cpu_launch_fails(self):
        raw = (self.folder / 'dosbox.log').read_bytes()
        self.write('dosbox.log', raw+b'now | CPU: Setting fixed 4000 cycles.\n')
        self.rejects()

    def test_contradictory_video_launch_fails(self):
        raw = (self.folder / 'dosbox.log').read_bytes()
        self.write('dosbox.log', raw+b'now | SDL: x11 video initialised\n')
        self.rejects()

    def test_wrong_launch_mount_fails(self):
        raw = (self.folder / 'dosbox.log').read_bytes().replace(b'baseline--helper1-rnd-after', b'wrong-control')
        self.write('dosbox.log', raw)
        self.rejects()

    def test_changed_launch_cycles_fails(self):
        raw = (self.folder / 'dosbox.log').read_bytes().replace(b'cpu_cycles=200000', b'cpu_cycles=200001')
        self.write('dosbox.log', raw)
        self.rejects()

    def test_extra_metadata_completion_claim_fails(self):
        self.meta('normal_maintenance_completion', True)
        self.rejects()

    def test_rewritten_raw_pins_cannot_bless_corruption(self):
        pins = json.loads(verifier.PINS_FILE.read_text())
        pins[self.folder.name]['trace_sha256'] = '0'*64
        path = Path(self.temp.name) / 'pins.json'
        path.write_text(json.dumps(pins))
        with self.assertRaisesRegex(AssertionError, 'immutable independent pins'):
            verifier.verify(self.root, pins_path=path)

    def test_native_truncation_fails(self):
        record = json.loads(self.native.read_text())
        record['records'][1]['normalized_result']['returned_bytes'] -= 1
        path = Path(self.temp.name) / 'native.json'; path.write_text(json.dumps(record))
        with self.assertRaisesRegex(AssertionError, 'native truncation'):
            verifier.verify_native(path, self.original)

    def test_native_address_substitution_fails(self):
        record = json.loads(self.native.read_text())
        record['records'][1]['normalized_result']['address'] = '0x178f4'
        record['records'][1]['parameters']['address'] = '0x178f4'
        path = Path(self.temp.name) / 'native.json'; path.write_text(json.dumps(record))
        with self.assertRaisesRegex(AssertionError, 'native address'):
            verifier.verify_native(path, self.original)

    def test_native_relocated_byte_corruption_fails(self):
        record = json.loads(self.native.read_text())
        item = record['records'][1]['normalized_result']
        item['bytes_hex'] = '00' + item['bytes_hex'][2:]
        path = Path(self.temp.name) / 'native.json'; path.write_text(json.dumps(record))
        with self.assertRaisesRegex(AssertionError, 'relocated native bytes'):
            verifier.verify_native(path, self.original)

    def test_randomize_semantics_independent_of_pins(self):
        observed = copy.deepcopy(self.observations)
        state, fac = observed['baseline--seed-after']
        observed['baseline--seed-after'] = (state ^ 0x100, fac)
        with self.assertRaisesRegex(AssertionError, 'RANDOMIZE state'):
            verifier.verify_semantics(observed)

    def test_draw_semantics_independent_of_pins(self):
        observed = copy.deepcopy(self.observations)
        state, fac = observed['baseline--wanderer-2-after']
        observed['baseline--wanderer-2-after'] = (state ^ 1, fac)
        with self.assertRaisesRegex(AssertionError, 'one RND step'):
            verifier.verify_semantics(observed)

    def test_fac_semantics_independent_of_pins(self):
        observed = copy.deepcopy(self.observations)
        state, fac = observed['baseline--wanderer-2-after']
        altered = bytearray(fac); altered[0] ^= 1
        observed['baseline--wanderer-2-after'] = (state, bytes(altered))
        with self.assertRaisesRegex(AssertionError, 'RND FAC'):
            verifier.verify_semantics(observed)


if __name__ == '__main__':
    unittest.main()
