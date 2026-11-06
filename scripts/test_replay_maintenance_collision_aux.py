"""Auxiliary guards and complete-caller comparisons for the collision profile.

Only the comparison fixture below loads retained after-files. Neither synthesis
function receives target outputs, target digests or captured old RNG states.
"""
import copy
import datetime
import gzip
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import replay_maintenance_collision_aux as auxiliary
import replay_maintenance_collision_records as records
from replay_maintenance_placement import before_from_recipe
from replay_qb_graph import mbf


ROOT = Path(__file__).resolve().parents[1]
DATE = datetime.date(2026, 11, 2)
AUXILIARY = set(records.FILES) - {'YTDATA.DAT'}
DEFAULT_ENCOUNTERS = object()


def put(world, record, offset, value):
    data = bytearray(world)
    at = (record - 1) * 137 + offset
    data[at:at + 4] = mbf.enc(value)
    return bytes(data)


class CollisionAuxiliaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = records.DEFAULT
        recipe = json.loads((root / 'recipe.json').read_text())
        baseline = ROOT / 'research/yt-maint/initial-controls/baseline-split'
        files = {name: gzip.decompress((baseline / ('before-' + name + '.gz')).read_bytes())
                 for name in records.FILES[:3]}
        cls.fixtures = {}
        for case in recipe['cases']:
            before = {**files, 'YTDATA.DAT': before_from_recipe(recipe, case)}
            folder = root / case / 'observed-a'
            observed = json.loads(gzip.decompress((folder / 'host-time.json.gz').read_bytes()))
            inputs = records.inputs_from_observation(observed)
            actual, stats = records.synthesize(before, inputs)
            # Targets are comparison-only: they are loaded after the independent
            # full record pipeline has already generated every file.
            expected = {name: gzip.decompress((folder / ('after-' + name + '.gz')).read_bytes())
                        for name in records.FILES}
            cls.fixtures[case] = dict(before=before, inputs=inputs, actual=actual,
                                      stats=stats, expected=expected)

    def fixture(self, case='duplicate-hq'):
        return self.fixtures[case]

    def invoke(self, *, case='duplicate-hq', before=None, world=None,
               encounters=DEFAULT_ENCOUNTERS, **changes):
        fixture = self.fixture(case)
        clock = fixture['inputs'].clock
        args = dict(before_files=fixture['before'] if before is None else before,
                    after_world=fixture['actual']['YTDATA.DAT'] if world is None else world,
                    news_date=clock.news_date, news_clock=clock.news_clock,
                    score_date=clock.score_date, score_clock=clock.score_clock,
                    encounters=fixture['stats']['npcs']['encounters'] if encounters is DEFAULT_ENCOUNTERS else encounters)
        args.update(changes)
        return auxiliary.synthesize(**args)

    def test_all_twelve_full_callers_match_all_native_files(self):
        self.assertEqual(len(self.fixtures), 12)
        for case, fixture in self.fixtures.items():
            with self.subTest(case=case):
                self.assertEqual(set(fixture['actual']), set(records.FILES))
                self.assertEqual(fixture['actual'], fixture['expected'])

    def test_direct_auxiliary_calls_match_every_native_auxiliary_target(self):
        for case, fixture in self.fixtures.items():
            with self.subTest(case=case):
                actual, _ = self.invoke(case=case)
                self.assertEqual(set(actual), AUXILIARY)
                self.assertEqual(actual, {name: fixture['expected'][name] for name in AUXILIARY})

    def test_auxiliary_reads_only_the_original_executable(self):
        read = Path.read_bytes
        allowed = ROOT / 'archive/dos-original/YTMAINT.EXE'

        def guard(path):
            if path != allowed:
                raise AssertionError('auxiliary opened an after-target or unrelated file: ' + str(path))
            return read(path)

        fixture = self.fixture('wanderer-reject-two')
        with patch.object(Path, 'read_bytes', guard):
            actual, _ = self.invoke(case='wanderer-reject-two')
        self.assertEqual(actual, {name: fixture['expected'][name] for name in AUXILIARY})

    def test_complete_pipeline_reads_no_after_target_during_synthesis(self):
        read = Path.read_bytes
        allowed = ROOT / 'archive/dos-original/YTMAINT.EXE'

        def guard(path):
            if path != allowed:
                raise AssertionError('full pipeline opened an after-target: ' + str(path))
            return read(path)

        fixture = self.fixture('pointer-mercenary-sector')
        with patch.object(Path, 'read_bytes', guard):
            actual, _ = records.synthesize(fixture['before'], fixture['inputs'])
        self.assertEqual(actual, fixture['expected'])

    def test_input_worlds_and_before_files_remain_unchanged(self):
        fixture = self.fixture('wanderer-reject-two')
        before = copy.deepcopy(fixture['before'])
        world = fixture['actual']['YTDATA.DAT']
        encounters = copy.deepcopy(fixture['stats']['npcs']['encounters'])
        snapshot = copy.deepcopy((before, world, encounters))
        self.invoke(case='wanderer-reject-two', before=before, world=world, encounters=encounters)
        self.assertEqual((before, world, encounters), snapshot)

    def test_modern_private_messages_are_not_invented_by_public_encounters(self):
        actual, stats = self.invoke(case='wanderer-reject-two')
        self.assertEqual(actual['YTRMSG.DAT'], b'')
        self.assertEqual(stats['private_bytes'], 0)
        self.assertEqual(actual['YTNAME.DAT'], self.fixture()['before']['YTNAME.DAT'])
        self.assertEqual(actual['YTYNEWS.DAT'], self.fixture()['before']['YTNEWS.DAT'])

    def test_public_casualties_follow_modeled_encounter_order(self):
        fixture = self.fixture('wanderer-reject-two')
        actual, stats = self.invoke(case='wanderer-reject-two')
        forces = [int(value) for value in re.findall(
            rb'^ \*\*\* ([0-9]+) Xannor attacked the planet "The Wanderer"\r?$',
            actual['YTNEWS.DAT'], re.M)]
        encounters = fixture['stats']['npcs']['encounters']
        self.assertEqual(forces, [event['initial_force'] for event in encounters])
        self.assertEqual(len(forces), 9)
        self.assertEqual(sum(forces), 3681)
        self.assertEqual(actual['YTNEWS.DAT'].count(b' *** Xannor fighters destroyed!'), len(forces))
        self.assertEqual(stats['modeled_casualties'], 3681)
        self.assertEqual(stats['final_physical_force'], 6319)
        self.assertEqual(stats['scores'], {-1: 631900, -2: 0})

    def test_both_faction_scores_derive_from_saved_physical_forces(self):
        _, stats = self.invoke(case='pointer-mercenary-sector')
        self.assertEqual(stats['scores'], {-1: 1000000, -2: 3700})
        self.assertEqual(stats['percentages'], [100.0, 0.37])
        self.assertEqual(stats['initial_physical_force'], 10037)
        self.assertEqual(stats['final_physical_force'], 10037)
        for case in ('duplicate-mobile', 'unpointed-friendly-merge'):
            with self.subTest(case=case):
                _, stats = self.invoke(case=case)
                self.assertEqual(stats['scores'], {-1: 1003700, -2: 0})
                self.assertEqual(stats['percentages'], [100.0, 0.0])

    def test_neutral_force_is_conserved_but_not_scored_as_a_faction(self):
        fixture = self.fixture('pointer-neutral-sector')
        world = fixture['actual']['YTDATA.DAT']
        self.assertEqual((mbf.get(world, 3051, 81), mbf.get(world, 3051, 85)), (37, 0))
        _, stats = self.invoke(case='pointer-neutral-sector')
        self.assertEqual(stats['final_physical_force'], 10037)
        self.assertEqual(stats['scores'], {-1: 1000000, -2: 0})

    def test_invented_or_lost_physical_force_fails_closed(self):
        world = self.fixture()['actual']['YTDATA.DAT']
        for value in (1, 37, 10038):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.invoke(world=put(world, 3051, 81, value))
        sector = next(s for s in range(1, 3001) if mbf.get(world, 51 + s, 81) > 1)
        with self.assertRaises(ValueError):
            self.invoke(world=put(world, 51 + sector, 81, mbf.get(world, 51 + sector, 81) - 1))

    def test_negative_fractional_and_oversized_sector_force_fail_closed(self):
        world = self.fixture()['actual']['YTDATA.DAT']
        for value in (-1, .5, 10038):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):self.invoke(world=put(world, 3051, 81, value))

    def test_unmeasured_human_or_invalid_sector_owner_fails_closed(self):
        world = self.fixture()['actual']['YTDATA.DAT']
        for owner in (-3, .5, 1, 2):
            with self.subTest(owner=owner):
                with self.assertRaises(ValueError):self.invoke(world=put(world, 3051, 85, owner))

    def test_invented_encounter_receipt_cannot_hide_lost_force(self):
        fixture = self.fixture('wanderer-reject-two')
        encounters = copy.deepcopy(fixture['stats']['npcs']['encounters'])
        encounters[0]['initial_force'] += 1
        with self.assertRaises(ValueError):self.invoke(case='wanderer-reject-two', encounters=encounters)
        with self.assertRaises(ValueError):self.invoke(case='wanderer-reject-two', encounters=[])

    def test_malformed_or_unordered_encounters_fail_closed(self):
        source = self.fixture('wanderer-reject-two')['stats']['npcs']['encounters']
        mutations = [dict(source[0], group=True), dict(source[0], group=20),
                     dict(source[0], initial_force=True), dict(source[0], initial_force=0),
                     dict(source[0], force=False), dict(source[0], force=1),
                     dict(source[0], planet_name='Xannoron')]
        for event in mutations:
            with self.subTest(event=event):
                with self.assertRaises(ValueError):self.invoke(case='wanderer-reject-two', encounters=[event])
        for events in (None, {}, [None], list(reversed(source)), [source[0], source[0]]):
            with self.subTest(events=events):
                with self.assertRaises(ValueError):self.invoke(case='wanderer-reject-two', encounters=events)

    def test_unknown_extra_event_kinds_are_not_silently_omitted(self):
        for events in ({}, None, [{'kind': 'unrecovered_route'}], ['public text']):
            with self.subTest(events=events):
                with self.assertRaises(ValueError):self.invoke(events=events)

    def test_active_players_and_populated_inactive_assets_fail_closed(self):
        fixture = self.fixture()
        for record, offset, value in ((2, 85, 1), (2, 41, 1), (2, 109, 0)):
            with self.subTest(offset=offset):
                with self.assertRaises(ValueError):
                    self.invoke(world=put(fixture['actual']['YTDATA.DAT'], record, offset, value))
        before = dict(fixture['before'])
        for record, offset in ((2, 85), (2, 41)):
            with self.subTest(before_offset=offset):
                before['YTDATA.DAT'] = put(fixture['before']['YTDATA.DAT'], record, offset, 1)
                with self.assertRaises(ValueError):self.invoke(before=before)

    def test_preexisting_extra_or_missing_active_planets_fail_closed(self):
        fixture = self.fixture()
        before = dict(fixture['before'])
        before['YTDATA.DAT'] = put(before['YTDATA.DAT'], 4053, 85, 1)
        with self.assertRaises(ValueError):self.invoke(before=before)
        for record, value in ((4053, 1), (4052, 0), (4150, 0), (4151, 0)):
            with self.subTest(record=record):
                with self.assertRaises(ValueError):
                    self.invoke(world=put(fixture['actual']['YTDATA.DAT'], record, 85, value))

    def test_port_treasury_or_alternate_scoreboard_path_fails_closed(self):
        fixture = self.fixture()
        before = dict(fixture['before'])
        before['YTDATA.DAT'] = put(before['YTDATA.DAT'], 3052, 89, 1)
        with self.assertRaises(ValueError):self.invoke(before=before)
        before = dict(fixture['before'])
        before['YTDATA.DAT'] = b'OTHER.ASC  ' + before['YTDATA.DAT'][11:]
        with self.assertRaises(ValueError):self.invoke(before=before)

    def test_nondefault_geometry_is_rejected_before_formatting(self):
        fixture = self.fixture()
        for offset, value in ((53, 50), (57, 3050), (61, 4050), (93, 4150)):
            for where in ('before', 'after'):
                with self.subTest(offset=offset, where=where):
                    before = dict(fixture['before'])
                    world = fixture['actual']['YTDATA.DAT']
                    if where == 'before':before['YTDATA.DAT'] = put(before['YTDATA.DAT'], 1, offset, value)
                    else:world = put(world, 1, offset, value)
                    with self.assertRaises(ValueError):self.invoke(before=before, world=world)

    def test_raw_input_types_extents_and_exact_inventory_fail_closed(self):
        fixture = self.fixture()
        for before in (None, {}, {**fixture['before'], 'YTRMSG.DAT': b''},
                       {**fixture['before'], 'YTNEWS.DAT': bytearray(b'')},
                       {**fixture['before'], 'YTDATA.DAT': fixture['before']['YTDATA.DAT'][:-1]}):
            with self.subTest(before_type=type(before)):
                # invoke(None) is its intentional fixture default; supply the
                # helper directly to test an actual None argument.
                with self.assertRaises(ValueError):
                    auxiliary.synthesize(before, fixture['actual']['YTDATA.DAT'], DATE, '00:00:00', DATE, '00:00:00')
        for world in (bytearray(fixture['actual']['YTDATA.DAT']), fixture['actual']['YTDATA.DAT'][:-1], b''):
            with self.subTest(world_type=type(world)):
                with self.assertRaises(ValueError):self.invoke(world=world)

    def test_explicit_date_and_native_clock_admission(self):
        for key in ('news_date', 'score_date'):
            for value in ('2026-11-02', datetime.datetime(2026, 11, 2), None):
                with self.subTest(key=key, value=value):
                    with self.assertRaises(ValueError):self.invoke(**{key: value})
        for key in ('news_clock', 'score_clock'):
            for value in ('24:00:01', '25:00:00', '23:60:00', '0:00:00', None):
                with self.subTest(key=key, value=value):
                    with self.assertRaises(ValueError):self.invoke(**{key: value})
        actual, _ = self.invoke(score_clock='24:00:00')
        self.assertIn(b'11-02-2026 24:00:00', actual['YTSCORE.ASC'])

    def test_zero_and_halfway_score_denominators_fail_closed(self):
        original = auxiliary.original_literals()
        world = self.fixture()['actual']['YTDATA.DAT']
        for scores in ({-1: 0, -2: 0}, {-1: 3200, -2: 100}):
            with self.subTest(scores=scores):
                with self.assertRaises(ValueError):
                    auxiliary._npc_scoreboard(original, world, DATE, '00:00:00', scores)


if __name__ == '__main__':
    unittest.main()
