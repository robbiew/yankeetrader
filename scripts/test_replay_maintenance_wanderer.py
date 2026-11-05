"""Before-only, stream-order and admission regressions for Wanderer encounters."""
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import replay_maintenance_clock_matrix as matrix
import replay_maintenance_wanderer as wanderer
from replay_maintenance_npcs import UnsupportedClockMatrixEncounter
import replay_qb_graph as qb


ROOT = Path(__file__).resolve().parents[1]
MBF = qb.mbf
WANDERER = 4052


def put(world, record, offset, value):
    start = (record - 1) * 137 + offset
    world[start:start + 4] = MBF.enc(value)


def raw(world, record, offset):
    start = (record - 1) * 137 + offset
    return world[start:start + 4]


class Draws:
    """A finite injected draw sequence, not an original execution oracle."""
    def __init__(self, values, repeat=None):
        self.values = iter(values)
        self.repeat = repeat
        self.state = 0xEA7184
        self.draws = 0

    def rnd(self):
        self.draws += 1
        if self.repeat is not None:
            return self.repeat
        return next(self.values)


class WandererReplayProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = ROOT / 'research/yt-maint/initial-controls/baseline-split'
        cls.before = {name: gzip.decompress((source / ('before-' + name + '.gz')).read_bytes())
                      for name in matrix.FILES[:3]}
        target = matrix.DEFAULT / 'late/observed-a'
        observation = json.loads(gzip.decompress((target / 'host-time.json.gz').read_bytes()))
        cls.inputs = matrix.inputs_from_observation(observation)
        cls.outputs, cls.stats = wanderer.synthesize(cls.before, cls.inputs)
        # Expected outputs are loaded only in the comparison fixture, never by
        # either synthesis function or the guarded invocation below.
        cls.expected = {name: gzip.decompress((target / ('after-' + name + '.gz')).read_bytes())
                        for name in matrix.FILES}

    def fixture(self):
        world = bytearray(self.outputs['YTDATA.DAT'])
        for offset in (45, 49, 53):
            put(world, WANDERER, offset, 5000)
        for offset in (57, 61, 65):
            put(world, WANDERER, offset, 0)
        put(world, WANDERER, 73, 0)
        start = (WANDERER - 1) * 137 + 77
        world[start:start + 4] = bytes.fromhex('00001c00')
        return world

    def assault(self, world=None, rng=None, **changes):
        world = self.fixture() if world is None else world
        stream = SimpleNamespace(rng=qb.QB3(0xEA7184) if rng is None else rng)
        args = dict(group=2, sector=658, force=382, wanderer_sector=658)
        args.update(changes)
        return wanderer.assault(world, stream, **args)

    def test_full_late_outputs_match_native_without_masked_bytes(self):
        self.assertEqual(set(self.outputs), set(matrix.FILES))
        for name in matrix.FILES:
            with self.subTest(file=name):
                self.assertEqual(self.outputs[name], self.expected[name])
        self.assertEqual(len(self.outputs['YTDATA.DAT']), 4151 * 137)

    def test_synthesis_reads_only_the_original_executable(self):
        read = Path.read_bytes
        allowed = ROOT / 'archive/dos-original/YTMAINT.EXE'

        def guard(path):
            if path != allowed:
                raise AssertionError('synthesis opened a target or unrelated file: ' + str(path))
            return read(path)

        with patch.object(Path, 'read_bytes', guard):
            outputs, stats = wanderer.synthesize(self.before, self.inputs)
        self.assertEqual(outputs, self.outputs)
        self.assertEqual(stats['npcs']['encounters'], self.stats['npcs']['encounters'])

    def test_historical_matrix_stays_strict_until_explicit_opt_in(self):
        with self.assertRaises(matrix.UnsupportedProfile) as caught:
            matrix.synthesize(self.before, self.inputs)
        self.assertEqual(caught.exception.context['rng_state'], 0xEA7184)
        self.assertEqual(caught.exception.context['group'], 2)
        self.assertIn('no entered planet/mine action', str(caught.exception))

    def test_first_encounter_draw_order_and_single_precision_damage(self):
        event = self.stats['npcs']['encounters'][0]
        self.assertEqual((event['group'], event['sector'], event['initial_force']), (2, 658, 382))
        self.assertEqual(event['initial_rng_state'], 0xEA7184)
        self.assertEqual(event['rng_draws'], 5)
        self.assertEqual(event['rounds'][0]['gate'], 0.056064069271087646)
        self.assertEqual(event['rounds'][0]['damage'],
                         [0.5436419248580933, 0.5432496666908264, 0.594902515411377])
        self.assertEqual(event['rounds'][1]['gate'], 0.9760157465934753)
        self.assertEqual((event['raw_force'], event['force']), (-68, 0))
        self.assertEqual(event['final_rates'], [4918.45361328125, 4918.5126953125, 4910.7646484375])

    def test_shared_pursuit_skips_later_candidates_and_fatal_edge_scans(self):
        npcs = self.stats['npcs']
        self.assertEqual([e['group'] for e in npcs['encounters']], list(range(2, 20)))
        self.assertEqual({e['sector'] for e in npcs['encounters']}, {658})
        self.assertEqual(npcs['candidate_draws'], 50)
        self.assertEqual(npcs['interception_draws'], 23700)
        for route in npcs['routes'][:18]:
            with self.subTest(group=route['group']):
                self.assertEqual(route['candidate_draws'], 50 if route['group'] == 2 else 0)
                self.assertEqual(route['entered_route'][-1], 658)
                self.assertEqual(route['interception_draws'], 50 * (len(route['entered_route']) - 1))
                self.assertEqual((route['strength'], route['sector']), (0, 0))
        last = npcs['routes'][-1]
        self.assertEqual(last['group'], 20)
        self.assertEqual(last['sector'], npcs['top_fallback'])
        self.assertNotEqual(last['sector'], 658)
        self.assertEqual(npcs['groups'][20]['strength'], 243)

    def test_raw_owner_ground_stock_and_inherited_residues_are_not_normalized(self):
        world = self.outputs['YTDATA.DAT']
        self.assertEqual(raw(world, WANDERER, 73), bytes.fromhex('00002000'))
        self.assertEqual(raw(world, WANDERER, 77), bytes.fromhex('00001c00'))
        for offset in (57, 61, 65):
            self.assertEqual(raw(world, WANDERER, offset), bytes.fromhex('00001c00'))
            self.assertEqual(MBF.get(world, WANDERER, offset), 0)
        self.assertEqual(MBF.get(world, WANDERER, 81), 305)
        self.assertEqual(MBF.get(world, WANDERER, 85), 12)
        self.assertEqual(MBF.get(world, 51 + 658, 93), 1)
        self.assertEqual([MBF.get(world, WANDERER, o) for o in (45, 49, 53)],
                         [2995.552734375, 2861.62841796875, 2778.564697265625])

    def test_scores_conserve_surviving_force_and_public_reports_stay_private_free(self):
        npcs = self.stats['npcs']
        killed = sum(e['initial_force'] for e in npcs['encounters'])
        remaining = sum(g['strength'] for g in npcs['groups'].values())
        self.assertEqual(killed + remaining, 10000)
        self.assertEqual(remaining, 3077)
        self.assertIn(b'307,700   100.00%', self.outputs['YTSCORE.ASC'])
        news = self.outputs['YTNEWS.DAT']
        pairs = b''.join(b' *** ' + str(e['initial_force']).encode() +
                         b' Xannor attacked the planet "The Wanderer"\r\n' +
                         b' *** Xannor fighters destroyed!\r\n'
                         for e in npcs['encounters'])
        self.assertIn(pairs + b'  -  Mercenary Report:', news)
        self.assertEqual(news.count(b' Xannor attacked the planet '), 18)
        self.assertNotIn(b'Planet "The Wanderer" destroyed!', news)
        self.assertEqual(self.outputs['YTRMSG.DAT'], b'')
        self.assertEqual(self.outputs['YTYNEWS.DAT'], self.before['YTNEWS.DAT'])

    def test_unrecovered_planets_owners_ground_stocks_and_screens_fail_closed(self):
        cases = [(51 + 658, 93, 2), (WANDERER, 73, 2), (WANDERER, 73, -1),
                 (WANDERER, 77, 1), (WANDERER, 85, 0),
                 (WANDERER, 57, 1), (WANDERER, 61, 1), (WANDERER, 65, 1),
                 (WANDERER, 45, 500), (WANDERER, 49, 0), (WANDERER, 53, -1),
                 (51 + 658, 81, 1), (51 + 658, 89, 1)]
        for record, offset, value in cases:
            with self.subTest(record=record, offset=offset, value=value):
                world = self.fixture()
                put(world, record, offset, value)
                before = bytes(world)
                with self.assertRaises(UnsupportedClockMatrixEncounter):
                    self.assault(world)
                self.assertEqual(bytes(world), before)
        world = self.fixture()
        world[(WANDERER - 1) * 137] = ord('X')
        with self.assertRaises(UnsupportedClockMatrixEncounter):
            self.assault(world)

    def test_force_type_bounds_and_special_group_are_rejected_before_draws(self):
        for changes in (dict(force=True), dict(force=0), dict(force=-1), dict(force=10001),
                        dict(force=382.0), dict(group=20), dict(group=1), dict(sector=659)):
            with self.subTest(changes=changes):
                rng = qb.QB3(0xEA7184)
                world = self.fixture()
                before = bytes(world)
                with self.assertRaises(UnsupportedClockMatrixEncounter):
                    self.assault(world, rng, **changes)
                self.assertEqual(rng.draws, 0)
                self.assertEqual(bytes(world), before)

    def test_injected_gate_tie_is_casualty_and_damage_draws_are_independent(self):
        rng = Draws([0.25, 0.25, 0.5, 0.75, 0.5])
        world = self.fixture()
        event = self.assault(world, rng, force=450)
        self.assertEqual(event['rng_draws'], 5)
        self.assertEqual(event['final_rates'], [4962.5, 4925, 4887.5])
        self.assertEqual((event['raw_force'], event['force']), (0, 0))
        self.assertEqual(raw(world, WANDERER, 77), bytes.fromhex('00001c00'))
        self.assertEqual(raw(world, WANDERER, 73), bytes.fromhex('00002000'))

    def test_small_rate_aftermath_is_rejected_without_partial_world_writes(self):
        world = self.fixture()
        for offset in (45, 49, 53):
            put(world, WANDERER, offset, 501)
        before = bytes(world)
        with self.assertRaisesRegex(UnsupportedClockMatrixEncounter, 'small-rate'):
            self.assault(world, Draws([0, 0.5, 0.5, 0.5, 1]))
        self.assertEqual(bytes(world), before)

    def test_unending_original_damage_path_has_a_finite_research_guard(self):
        world = self.fixture()
        before = bytes(world)
        rng = Draws([], repeat=0)
        with self.assertRaisesRegex(UnsupportedClockMatrixEncounter, 'round limit'):
            self.assault(world, rng)
        self.assertEqual(rng.draws, 4096 * 4)
        self.assertEqual(bytes(world), before)


class RetainedWandererMatrixComparisons(unittest.TestCase):
    def test_empty_root_fails_before_any_before_input_is_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('unexpected input read')):
                with self.assertRaisesRegex(ValueError, 'eight-profile matrix or six-run late'):
                    wanderer.compare_cases(Path(temporary))

    def test_partial_mode_inventory_fails_before_any_before_input_is_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'late/observed-a').mkdir(parents=True)
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('unexpected input read')):
                with self.assertRaisesRegex(ValueError, 'all six'):
                    wanderer.compare_cases(root)

    def test_missing_observed_trace_fails_before_any_before_input_is_read(self):
        from verify_maintenance_clock_matrix import MODES
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for mode in MODES:
                folder = root / 'late' / mode
                folder.mkdir(parents=True)
                if mode not in ('unobserved-a', 'unobserved-b', 'observed-b'):
                    (folder / 'host-time.json.gz').touch()
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('unexpected input read')):
                with self.assertRaisesRegex(ValueError, 'source-qualified observer inventory'):
                    wanderer.compare_cases(root)

    def test_independent_fresh_six_run_corpus_is_accepted(self):
        root = ROOT / 'research/yt-maint/wanderer-encounter/untouched'
        self.assertTrue(root.is_dir(), 'the retained fresh acceptance corpus is required')
        report = wanderer.compare_cases(root)
        self.assertEqual(len(report['cases']), 18)
        self.assertEqual(sum(len(row['files']) for row in report['cases']), 108)
        self.assertEqual({row['recipe'] for row in report['cases']}, {'late'})
        self.assertEqual({row['observation'] for row in report['cases']},
                         {'observed-a', 'observed-b', 'observed-c'})
        self.assertTrue(all(row['byte_mismatches'] == 0 for row in report['cases']))

    def test_observed_modes_cannot_claim_disabled_observers_to_skip_comparisons(self):
        from verify_maintenance_clock_matrix import MODES
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for mode in MODES:
                folder = root / 'late' / mode
                folder.mkdir(parents=True)
                if mode not in ('unobserved-a', 'unobserved-b'):
                    (folder / 'host-time.json.gz').write_bytes(
                        gzip.compress(json.dumps({'observe': False}).encode(), mtime=0))
            read = Path.read_bytes

            def guard(path):
                if path.name.startswith('after-'):
                    raise AssertionError('expected output read before rejecting mode')
                return read(path)

            with patch.object(Path, 'read_bytes', guard):
                with self.assertRaisesRegex(ValueError, 'actual observer mode'):
                    wanderer.compare_cases(root)

    def test_all_eight_recipes_have_complete_six_file_native_equality(self):
        report = wanderer.compare_cases()
        self.assertEqual(len(report['cases']), 144)
        self.assertEqual(len({r['recipe'] for r in report['cases']}), 8)
        self.assertEqual(sum(len(r['files']) for r in report['cases']), 864)
        for row in report['cases']:
            with self.subTest(recipe=row['recipe'], observation=row['observation'], target=row['target']):
                self.assertEqual(set(row['files']), set(matrix.FILES))
                self.assertEqual(row['byte_mismatches'], 0)


if __name__ == '__main__':
    unittest.main()
