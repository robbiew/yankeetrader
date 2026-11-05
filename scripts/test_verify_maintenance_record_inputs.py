"""Corruption and independent semantic controls for maintenance replay inputs."""
import copy
import gzip
import json
import runpy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

import verify_maintenance_record_inputs as v


class RecordInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (v.ROOT / 'archive/dos-original/YTMAINT.EXE').read_bytes()
        cls.pins = json.loads(v.PINS_FILE.read_text())
        cls.rows = {key: v.verify_control(v.DEFAULT / key, pin, cls.original, key.split('/')[0])
                    for key, pin in cls.pins['controls'].items()}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.key = 'port-default/port-0606'
        self.folder = Path(self.temp.name) / self.key.split('/')[1]
        shutil.copytree(v.DEFAULT / self.key, self.folder)

    def meta(self, key, value):
        p = self.folder / 'result.json'
        m = json.loads(p.read_text())
        m[key] = value
        p.write_text(json.dumps(m))

    def write(self, name, value):
        (self.folder / name).write_bytes(value)
        p = self.folder / 'result.json'
        m = json.loads(p.read_text())
        m['files'][name] = v.SHA(value)
        p.write_text(json.dumps(m))

    def rejects(self):
        with self.assertRaises((AssertionError, KeyError, ValueError, FileNotFoundError)):
            v.verify_control(self.folder, self.pins['controls'][self.key], self.original, self.key.split('/')[0])

    def test_complete_retained_inputs(self):
        self.assertEqual(v.verify(), dict(controls=28, profiles=3, untouched=4, native_reads=14,
                                         port_counter=1000, differing_timestamp_bytes=4))

    def test_documented_capture_command_supplies_independent_entry_contract(self):
        calls = {}
        def capture(destination, name, site=None, nth=65535, source=0x234, **kwargs):
            self.assertNotIn(name, calls)
            calls[name] = (site, nth, source)
        destination = Path(self.temp.name) / 'fresh-entry'
        script = v.ROOT / 'scripts/recover_maintenance_record_inputs.py'
        with mock.patch('recover_maintenance_sequence.run', capture), mock.patch('sys.argv', [str(script), str(destination)]):
            runpy.run_path(str(script), run_name='__main__')
        required = {key.split('/')[1]: value for key, value in v.expected_matrix().items() if key.startswith('entry/')}
        self.assertEqual(calls, required)

    def test_raw_clock_rehashed(self):
        b = bytearray((self.folder / 'TRACE.BIN').read_bytes())
        b[-1] ^= 1
        self.write('TRACE.BIN', b)
        self.rejects()

    def test_raw_world_rehashed(self):
        name = 'after-YTDATA.DAT.gz'
        b = bytearray(gzip.decompress((self.folder / name).read_bytes()))
        b[100] ^= 1
        self.write(name, gzip.compress(b, mtime=0))
        self.rejects()

    def test_wrong_site(self): self.meta('site', 0x7900); self.rejects()
    def test_unsafe_inline_site(self): self.meta('site', 0x3c13); self.rejects()
    def test_wrong_source(self): self.meta('source', 0x234); self.rejects()
    def test_wrong_counter(self): self.meta('nth', 605); self.rejects()
    def test_wrong_profile(self): self.meta('recipe', 'port-clock-readonly-compare-v1'); self.rejects()
    def test_wrong_probe_digest(self): self.meta('copied_sha256', '0' * 64); self.rejects()
    def test_wrong_original(self): self.meta('binaries', {**v.BINARIES, 'YTMAINT.EXE': '0' * 64}); self.rejects()
    def test_wrong_before(self): self.meta('inputs', {}); self.rejects()
    def test_unreported_fixture_edit(self): self.meta('patches', [{'offset': 1, 'after': '00'}]); self.rejects()
    def test_wrong_fixture(self): self.meta('occupied', [1095]); self.rejects()
    def test_wrong_declared_clock(self): self.meta('clock', '00:00:02'); self.rejects()
    def test_false_completion(self): self.meta('complete', True); self.rejects()
    def test_bad_exit(self): self.write('ERROR.LOG', b'PROGRAM_ERROR\r\n'); self.rejects()
    def test_missing_zero_exit(self): (self.folder / 'OK.LOG').unlink(); self.rejects()
    def test_forged_return(self): self.write('RETURN.LOG', b'PROGRAM_RETURNED\r\nforged'); self.rejects()
    def test_missing_launch(self): self.write('dosbox.log', b''); self.rejects()
    def test_contradictory_cpu(self): self.write('dosbox.log', (self.folder / 'dosbox.log').read_bytes() + b'now | CPU: Setting fixed 1 cycles.\n'); self.rejects()
    def test_contradictory_video(self): self.write('dosbox.log', (self.folder / 'dosbox.log').read_bytes() + b'now | SDL: opengl video initialised\n'); self.rejects()
    def test_contradictory_sound(self): self.write('dosbox.log', (self.folder / 'dosbox.log').read_bytes() + b'now | MIXER: Sound output enabled\n'); self.rejects()
    def test_wrong_mount(self): self.write('dosbox.log', (self.folder / 'dosbox.log').read_bytes().replace(b'port-0606', b'wrong-case')); self.rejects()
    def test_wrong_recipe(self): self.write('COMMANDS.TXT', (self.folder / 'COMMANDS.TXT').read_bytes() + b'exit\n'); self.rejects()
    def test_wrong_observed_clock(self): self.write('DOSTIME.LOG', b'Current time: 12:00:00.00pm\r\n'); self.rejects()
    def test_wrong_observed_date(self): self.write('DOSDATE.LOG', b'Current date: Mon 11/03/2026\r\n'); self.rejects()
    def test_extra_file(self): (self.folder / 'EXTRA.DAT').write_bytes(b'fake'); self.rejects()

    def readonly_folder(self):
        shutil.rmtree(self.folder)
        self.key = 'port-readonly/port-0606'
        shutil.copytree(v.DEFAULT / self.key, self.folder)

    def test_readonly_changed_comparison_operand(self):
        self.readonly_folder()
        self.meta('target_port_raw', v.mbf_integer(605).hex())
        self.rejects()

    def test_readonly_changed_probe(self):
        self.readonly_folder()
        self.meta('copied_sha256', '0' * 64)
        self.rejects()

    def test_readonly_false_guard_claim(self):
        self.readonly_folder()
        self.meta('complete', True)
        self.rejects()

    def semantic_reject(self, mutate, reason):
        rows = copy.deepcopy(self.rows)
        mutate(rows)
        with self.assertRaisesRegex(AssertionError, reason):
            v.verify_semantics(rows)

    def test_startup_raw_without_pins(self):
        self.semantic_reject(lambda r: r['entry/startup-timer'].__setitem__('raw', bytes(4)), 'startup TIMER zero residue')

    def test_xannoron_raw_without_pins(self):
        self.semantic_reject(lambda r: r['entry/xannoron-timer'].__setitem__('raw', bytes(4)), 'Xannoron TIMER input')

    def test_counter_total_without_pins(self):
        self.semantic_reject(lambda r: r['port-default/count-clock'].__setitem__('count', 999), '1000port counter')

    def test_605_transition_without_pins(self):
        self.semantic_reject(lambda r: r['port-default/port-0605'].__setitem__('raw', bytes.fromhex('0e745a76')), 'transition605/606')

    def test_606_transition_without_pins(self):
        self.semantic_reject(lambda r: r['port-default/port-0606'].__setitem__('raw', bytes.fromhex('00004800')), 'transition605/606')

    def test_readonly_profile_without_pins(self):
        self.semantic_reject(lambda r: r['port-readonly/port-0606'].__setitem__('raw', bytes.fromhex('00004800')), 'raw clock profile agrees')

    def test_readonly_partial_world_without_pins(self):
        self.semantic_reject(lambda r: r['port-readonly/port-0606']['outputs'].__setitem__('after-YTDATA.DAT.gz', b'wrong'), 'partial whole-output equality')

    def test_untouched_repeat_without_pins(self):
        self.semantic_reject(lambda r: r['entry/untouched-repeat']['outputs'].__setitem__('after-YTRMSG.DAT.gz', b'forged'), 'untouched whole-output equality')

    def test_miss_world_without_pins(self):
        self.semantic_reject(lambda r: r['port-readonly/miss']['outputs'].__setitem__('after-YTDATA.DAT.gz', b'wrong'), 'miss whole-output equality')

    def alter_both_instrumented(self, rows, name, value):
        for key in ('port-default/count-clock', 'port-readonly/miss'):
            rows[key]['outputs'][name] = value

    def test_changed_both_auxiliary_profiles_without_pins(self):
        self.semantic_reject(lambda r: self.alter_both_instrumented(r, 'after-YTRMSG.DAT.gz', b'forged'), 'preserves every auxiliary byte')

    def test_extra_world_difference_without_pins(self):
        def mutate(rows):
            b = bytearray(rows['port-default/count-clock']['outputs']['after-YTDATA.DAT.gz'])
            b[100] ^= 1
            self.alter_both_instrumented(rows, 'after-YTDATA.DAT.gz', bytes(b))
        self.semantic_reject(mutate, 'only port606 timestamp bytes differ')

    def test_hiding_clock_gap_without_pins(self):
        self.semantic_reject(lambda r: self.alter_both_instrumented(r, 'after-YTDATA.DAT.gz', r['entry/untouched']['outputs']['after-YTDATA.DAT.gz']), 'only port606 timestamp bytes differ')

    def test_wrong_four_timestamp_bytes_without_pins(self):
        def mutate(rows):
            b = bytearray(rows['port-default/count-clock']['outputs']['after-YTDATA.DAT.gz'])
            at = (3051 + 606 - 1) * 137 + 101
            b[at:at + 4] = b'ABCD'
            self.alter_both_instrumented(rows, 'after-YTDATA.DAT.gz', bytes(b))
        self.semantic_reject(mutate, 'untouched/probe timestamp distinction')

    def test_missing_matrix_control_without_pins(self):
        self.semantic_reject(lambda r: r.pop('port-readonly/port-0001'), 'independent experiment matrix')

    def native_reject(self, mutate, reason):
        root = Path(self.temp.name) / 'native'
        shutil.copytree(v.NATIVE, root)
        path = root / 'npc/rea.json'
        data = json.loads(path.read_text())
        mutate(data['records'][0])
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(AssertionError, reason):
            v.verify_native(root, self.original)

    def test_native_wrong_identity(self):
        self.native_reject(lambda r: r['subject']['digest'].__setitem__('sha256', '0' * 64), 'native identity')

    def test_native_truncation(self):
        self.native_reject(lambda r: r['normalized_result'].__setitem__('returned_bytes', 435), 'native truncation')

    def test_native_wrong_relocated_bytes(self):
        self.native_reject(lambda r: r['normalized_result'].__setitem__('bytes_hex', '00' * 436), 'native relocated bytes')

    def test_changed_pin_file(self):
        path = Path(self.temp.name) / 'pins.json'
        path.write_bytes(v.PINS_FILE.read_bytes() + b' ')
        with self.assertRaisesRegex(AssertionError, 'pin-file identity'):
            v.verify(pins_path=path)


if __name__ == '__main__':
    unittest.main()
