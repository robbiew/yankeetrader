"""Independent semantic and provenance corruption controls for encounter evidence."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

import verify_maintenance_wanderer as verify


class EncounterEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = verify.DEFAULT
        folder = cls.root / 'untouched/late/unobserved-a'
        cls.outputs = {name: gzip.decompress((folder / ('after-' + name + '.gz')).read_bytes())
                       for name in verify.matrix.neutral.OUTPUTS}
        cls.native = json.loads((cls.root / 'native/rea.json').read_text())

    def test_complete_untouched_diagnostic_and_native_corpus(self):
        result = verify.verify()
        self.assertEqual(result['untouched_runs'], 6)
        self.assertEqual(result['diagnostic_runs'], 14)
        self.assertEqual(result['native_reads'], 2)
        self.assertEqual(result['paired_files'], 36)
        self.assertEqual(result['attacks'], 18)
        self.assertEqual(result['casualties'] + result['survivors'], 10000)

    def test_semantics_are_checked_without_a_replay_model_or_manifest(self):
        result = verify.verify_outputs(self.outputs)
        self.assertEqual(result, dict(attacks=18, casualties=6923, survivors=3077,
                                      wanderer_sector=658))

    def test_all_diagnostic_sites_have_their_own_source_qualified_specification(self):
        values = {name: verify.verify_probe(self.root / 'diagnostics' / name, spec)
                  for name, spec in verify.PROBES.items()}
        self.assertEqual(verify.PROBES['first-preferred-output'][2], 0x7BAC)
        self.assertEqual(verify.PROBES['first-group-index'][2], 0x7BE8)
        self.assertEqual(int.from_bytes(values['first-gate-before'], 'little'), 0xEA7184)
        self.assertEqual(verify.matrix.neutral.mbf_fraction(values['first-preferred-output']), 658)
        self.assertEqual(verify.matrix.neutral.mbf_fraction(values['first-group-index']), 2)

    def native_rejected(self, mutate):
        data = copy.deepcopy(self.native)
        mutate(data)
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'native').mkdir()
            (folder / 'native/rea.json').write_text(json.dumps(data))
            with self.assertRaises(AssertionError):
                verify.verify_native(folder)

    def probe_rejected(self, name, mutate):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / name
            shutil.copytree(self.root / 'diagnostics' / name, folder)
            meta = json.loads((folder / 'result.json').read_text())
            mutate(folder, meta)
            (folder / 'result.json').write_text(json.dumps(meta))
            with self.assertRaises((AssertionError, ValueError)):
                verify.verify_probe(folder, verify.PROBES[name])

    def test_pins_cannot_be_replaced_by_rehashed_mutated_corpus(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pins = json.loads((self.root / 'pins.json').read_text())
            pins['files']['native/rea.json'] = '0' * 64
            (root / 'pins.json').write_text(json.dumps(pins))
            with self.assertRaisesRegex(AssertionError, 'immutable encounter corpus manifest'):
                verify.verify(root)

    def test_missing_artifact_inventory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'corpus'
            shutil.copytree(self.root, root)
            (root / 'native/rea.json').unlink()
            with self.assertRaisesRegex(AssertionError, 'artifact inventory'):
                verify.verify(root)

    def test_unlisted_extra_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'corpus'
            shutil.copytree(self.root, root)
            (root / 'unreviewed.json').write_text('{}')
            with self.assertRaisesRegex(AssertionError, 'artifact inventory'):
                verify.verify(root)

    def test_existing_artifact_bytes_cannot_change_under_unchanged_pins(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'corpus'
            shutil.copytree(self.root, root)
            (root / 'native/rea.json').write_text('{}')
            with self.assertRaisesRegex(AssertionError, 'immutable encounter artifact'):
                verify.verify(root)


def world_field(outputs, record, offset, raw):
    world = bytearray(outputs['YTDATA.DAT'])
    start = (record - 1) * 137 + offset
    world[start:start + 4] = raw
    outputs['YTDATA.DAT'] = bytes(world)


def world_integer(outputs, record, offset, value):
    """Independent exact MBF encoding for small nonnegative integer mutations."""
    if value == 0:
        raw = bytes(4)
    else:
        exponent = value.bit_length() - 1
        mantissa = value << (23 - exponent)
        raw = struct.pack('<I', (mantissa & 0x7FFFFF) | ((exponent + 129) << 24))
    world_field(outputs, record, offset, raw)


def replace_news(outputs, before, after):
    assert before in outputs['YTNEWS.DAT'], 'mutation must affect actual retained text'
    outputs['YTNEWS.DAT'] = outputs['YTNEWS.DAT'].replace(before, after, 1)


def output_mutation(name, mutate):
    def test(self):
        outputs = dict(self.outputs)
        mutate(outputs)
        with self.assertRaises((AssertionError, ValueError)):
            verify.verify_outputs(outputs)
    setattr(EncounterEvidenceTests, 'test_reject_' + name, test)


output_mutation('public_casualty_amount', lambda o: replace_news(o, b' *** 382 Xannor attacked', b' *** 383 Xannor attacked'))
output_mutation('missing_public_death', lambda o: replace_news(o, b' *** Xannor fighters destroyed!\r\n', b''))
output_mutation('death_before_attack', lambda o: replace_news(o,
    b' *** 382 Xannor attacked the planet "The Wanderer"\r\n *** Xannor fighters destroyed!\r\n',
    b' *** Xannor fighters destroyed!\r\n *** 382 Xannor attacked the planet "The Wanderer"\r\n'))
output_mutation('interrupted_encounter_block', lambda o: replace_news(o,
    b' *** Xannor fighters destroyed!\r\n', b' *** Xannor fighters destroyed!\r\n  -  Mercenary Report:\r\n'))
output_mutation('encounters_before_regeneration', lambda o: replace_news(o,
    b'Calculated Dynamic Xannor Regeneration is 0 fighters.', b'  -  Mercenary Report:'))
output_mutation('wrong_public_planet_name', lambda o: replace_news(o,
    b'Xannor attacked the planet "The Wanderer"', b'Xannor attacked the planet "Xannoron"'))
output_mutation('invented_private_message', lambda o: o.update({'YTRMSG.DAT': b'private encounter report'}))
output_mutation('wrong_surviving_score', lambda o: o.update({'YTSCORE.ASC': o['YTSCORE.ASC'].replace(b'307,700', b'307,701')}))
output_mutation('canonical_owner_zero', lambda o: world_field(o, 4052, 73, bytes(4)))
output_mutation('canonical_ground_zero', lambda o: world_field(o, 4052, 77, bytes(4)))
output_mutation('canonical_stock_zero', lambda o: world_field(o, 4052, 57, bytes(4)))
output_mutation('invented_bank_loot', lambda o: world_integer(o, 4052, 117, 249999))
output_mutation('phantom_surviving_deployment', lambda o: world_integer(o, 51 + 10, 81, 1))
output_mutation('dead_mobile_location', lambda o: world_integer(o, 51 + 2, 105, 658))
output_mutation('duplicate_wanderer_link', lambda o: world_integer(o, 51 + 10, 93, 1))
output_mutation('removed_wanderer_link', lambda o: world_integer(o, 51 + 658, 93, 0))
output_mutation('destroyed_wanderer_name', lambda o: world_integer(o, 4052, 85, 0))
output_mutation('unchanged_wanderer_rate', lambda o: world_integer(o, 4052, 45, 5000))
output_mutation('unsupported_small_rate', lambda o: world_integer(o, 4052, 49, 500))
output_mutation('missing_output_file', lambda o: o.pop('YTRMSG.DAT'))
output_mutation('truncated_world', lambda o: o.update({'YTDATA.DAT': o['YTDATA.DAT'][:-1]}))


def native_mutation(name, mutate):
    def test(self):
        self.native_rejected(mutate)
    setattr(EncounterEvidenceTests, 'test_reject_native_' + name, test)


native_mutation('missing_record', lambda d: d['records'].pop())
native_mutation('wrong_address', lambda d: d['records'][0]['parameters'].update(address='0x15efe'))
native_mutation('zero_length', lambda d: d['records'][0]['parameters'].update(length=0))
native_mutation('truncated_read', lambda d: d['records'][0]['normalized_result'].update(
    bytes_hex=d['records'][0]['normalized_result']['bytes_hex'][:-2]))
native_mutation('opcode_corruption', lambda d: d['records'][0]['normalized_result'].update(
    bytes_hex='00' + d['records'][0]['normalized_result']['bytes_hex'][2:]))
native_mutation('incomplete_read', lambda d: d['records'][0]['normalized_result'].update(complete=False))
native_mutation('false_returned_extent', lambda d: d['records'][0]['normalized_result'].update(returned_bytes=2090))
native_mutation('wrong_original_identity', lambda d: d['records'][0]['subject']['digest'].update(sha256='0' * 64))
native_mutation('wrong_operation', lambda d: d['records'][0].update(operation='trace_native_values'))


def probe_mutation(name, mutate, case='production-count'):
    def test(self):
        self.probe_rejected(case, mutate)
    setattr(EncounterEvidenceTests, 'test_reject_probe_' + name, test)


probe_mutation('wrong_site', lambda p, m: m.update(site=0x6351))
probe_mutation('wrong_nth', lambda p, m: m.update(nth=1))
probe_mutation('wrong_source', lambda p, m: m.update(source=0x234), case='first-preferred-output')
probe_mutation('wrong_requested_clock', lambda p, m: m.update(clock='00:00:00'))
probe_mutation('modified_original_identity', lambda p, m: m['binaries'].update({'YTMAINT.EXE': '0' * 64}))
probe_mutation('undeclared_patch', lambda p, m: m['patches'].append({'offset': 1, 'before': '00', 'after': '01'}))
probe_mutation('wrong_before_world', lambda p, m: m['inputs'].update({'YTDATA.DAT': '0' * 64}))
probe_mutation('wrong_patched_executable', lambda p, m: m.update(copied_sha256='0' * 64))
probe_mutation('missing_natural_return', lambda p, m: (p / 'RETURN.LOG').write_bytes(b''))
probe_mutation('reported_dos_error', lambda p, m: (p / 'ERROR.LOG').write_bytes(b'PROGRAM_ERROR\r\n'))
probe_mutation('relabelled_actual_clock', lambda p, m: (p / 'DOSTIME.LOG').write_bytes(
    (p / 'DOSTIME.LOG').read_bytes().replace(b'11:59:58.80', b'11:59:59.00')))
probe_mutation('wrong_actual_date', lambda p, m: (p / 'DOSDATE.LOG').write_bytes(
    (p / 'DOSDATE.LOG').read_bytes().replace(b'11/02/2026', b'11/03/2026')))
probe_mutation('false_completed_stop', lambda p, m: m.update(complete=True), case='first-gate-before')
probe_mutation('false_incomplete_counter', lambda p, m: m.update(complete=False))
probe_mutation('wrong_count', lambda p, m: (p / 'TRACE.BIN').write_bytes(
    (p / 'TRACE.BIN').read_bytes()[:-4] + struct.pack('<H', 65535 - 52) + b'C!'))
probe_mutation('missing_count_marker', lambda p, m: (p / 'TRACE.BIN').write_bytes(
    (p / 'TRACE.BIN').read_bytes()[:-2] + b'??'))
probe_mutation('wrong_first_raw_state', lambda p, m: (p / 'TRACE.BIN').write_bytes(
    (p / 'TRACE.BIN').read_bytes()[:-4] + bytes.fromhex('8571ea00')), case='first-gate-before')


def replace_log(folder, before, after):
    path = folder / 'dosbox.log'
    text = path.read_text()
    assert before in text, 'mutation must affect the actual diagnostic launch log'
    path.write_text(text.replace(before, after, 1))


probe_mutation('requested_cpu_cycles', lambda p, m: replace_log(p, 'cpu_cycles=200000', 'cpu_cycles=100000'))
probe_mutation('actual_cpu_budget', lambda p, m: replace_log(p,
    'CPU: Setting fixed 200000 cycles.', 'CPU: Setting fixed 100000 cycles.'))
probe_mutation('actual_host_version', lambda p, m: replace_log(p,
    'dosbox-staging version 0.83.0 ()', 'dosbox-staging version 0.82.0 ()'))
probe_mutation('requested_sound_setting', lambda p, m: replace_log(p, 'nosound=true', 'nosound=false'))
probe_mutation('actual_sound_mode', lambda p, m: replace_log(p,
    "MIXER: Sound output disabled ('nosound' mode)", 'MIXER: Sound output enabled'))
probe_mutation('actual_video_driver', lambda p, m: replace_log(p,
    'SDL: dummy video initialised', 'SDL: cocoa video initialised'))
probe_mutation('missing_launch_arguments', lambda p, m: (p / 'dosbox.log').write_text(
    '\n'.join(line for line in (p / 'dosbox.log').read_text().splitlines() if ' | arguments: ' not in line)))
probe_mutation('wrong_actual_dispatch', lambda p, m: replace_log(p,
    'ytmaint\\ >\\ TRACE.BIN', 'ytinit\\ >\\ TRACE.BIN'))
probe_mutation('missing_declared_command', lambda p, m: (p / 'COMMANDS.TXT').write_text(
    (p / 'COMMANDS.TXT').read_text().replace('time > ENDTIME.LOG\n', '')))


if __name__ == '__main__':
    unittest.main()
