"""Synthetic before-only Mercenary contracts, without captured after inputs."""
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_collision_mercenary as model
from replay_qb_graph import F32, mbf


def put(world, record, offset, value):
    at = (record - 1) * 137 + offset
    world[at:at + 4] = mbf.enc(value)


def raw(world, sector, offset):
    at = (50 + sector) * 137 + offset
    return bytes(world[at:at + 4])


def fixture(origin=100, route=(100, 101, 200)):
    """Construct a complete zero-human, zero-tax world in memory."""
    world = bytearray(4151 * 137)
    for off, value in ((53, 51), (57, 3051), (61, 4051), (93, 4151)):
        put(world, 1, off, value)
    if origin is not None:
        put(world, 51 + origin, 81, 37)
        put(world, 51 + origin, 85, -2)
    for source, target in zip(route, route[1:]):
        put(world, 51 + source, 41, target)
    return world


class Draws:
    def __init__(self, values):
        self.values = iter(values)
        self.calls = []

    def rnd(self):
        value = next(self.values)
        self.calls.append(value)
        return value


class Stream:
    """Finite injected branch witnesses, never an observed RNG-state oracle."""
    def __init__(self, draws=(), targets=()):
        self.rng = Draws(draws)
        self.targets = iter(targets)
        self.calls = []

    def one(self, bound, *, caller):
        assert type(bound) is int and bound > 0
        assert caller == 0x48cf, 'unexpected source helper call site'
        self.calls.append((bound, caller))
        return next(self.targets)


class MercenaryTailProperties(unittest.TestCase):
    def test_descending_reactivation_conserves37_and_writes_source_zero(self):
        world = fixture(3000, (3000, 1228, 2786))
        before = bytes(world)
        stream = Stream((.11, .22, .33), (1228, 2786))
        stats = model.maintain(world, stream)
        self.assertEqual([a['origin'] for a in stats['activations']], [3000, 1228])
        self.assertEqual([a['route'] for a in stats['activations']],
                         [[3000, 1228], [1228, 2786]])
        self.assertEqual(stats['final_sectors'], [2786])
        self.assertEqual(stats['force'], 37)
        self.assertEqual((mbf.get(world, 2837, 81), mbf.get(world, 2837, 85)), (37, -2))
        self.assertEqual((stats['desertion_draws'], stats['movement_gate_draws'],
                          stats['target_draws']), (1, 2, 2))
        self.assertEqual(stream.rng.calls, [.11, .22, .33])
        self.assertEqual(stream.calls, [(3000, 0x48cf)] * 2)
        self.assertEqual(stats['events'], [])
        changed = {i for i, (a, b) in enumerate(zip(before, world)) if a != b}
        owned = {(50 + s) * 137 + o + b for s in (3000, 1228, 2786)
                 for o in (81, 85) for b in range(4)}
        self.assertTrue(changed)
        self.assertLessEqual(changed, owned)
        for sector in (3000, 1228):
            for offset in (81, 85):
                self.assertEqual(raw(world, sector, offset), bytes.fromhex('00002800'))

    def test_same_origin_rejection_repeats48cf_without_another_gate(self):
        stream = Stream((.1, .9), (100, 100, 200))
        stats = model.maintain(fixture(), stream)
        self.assertEqual(stats['activations'][0]['candidates'], [100, 100, 200])
        self.assertEqual(stats['target_draws'], 3)
        self.assertEqual(stats['movement_gate_draws'], 1)
        self.assertEqual(stream.calls, [(3000, 0x48cf)] * 3)
        self.assertEqual(stream.rng.calls, [.1, .9])

    def test_eager_desertion_rolls_include_xannor_and_neutral_forces(self):
        world = fixture(origin=None, route=())
        for sector, owner, force in ((3, -1, 10000), (9, 0, 11)):
            put(world, 51 + sector, 81, force)
            put(world, 51 + sector, 85, owner)
        before = bytes(world)
        stream = Stream((.25, .75))
        stats = model.maintain(world, stream)
        self.assertEqual(stats['desertion_sectors'], [3, 9])
        self.assertEqual(stats['desertion_draws'], 2)
        self.assertEqual(stream.rng.calls, [.25, .75])
        self.assertEqual(stream.calls, [])
        self.assertEqual(stats['activations'], [])
        self.assertEqual(stats['events'], [])
        self.assertEqual(world, before)

    def test_no_planet_still_consumes_small_origin_gate_and_moves(self):
        stream = Stream((.8, .01), (200,))
        stats = model.maintain(fixture(), stream)
        self.assertFalse(stats['activations'][0]['held'])
        self.assertEqual(stats['activations'][0]['gate'], .01)
        self.assertEqual(stream.rng.calls, [.8, .01])
        self.assertEqual(stream.calls, [(3000, 0x48cf)])

    def test_positive_origin_link_and_small_gate_hold_without_clearing(self):
        world = fixture()
        put(world, 151, 93, 4053)
        before = bytes(world)
        stream = Stream((.8, .65))
        stats = model.maintain(world, stream)
        self.assertEqual(stats['activations'],
                         [dict(origin=100, force=37, gate=.65, held=True)])
        self.assertEqual(stats['final_sectors'], [100])
        self.assertEqual(stats['target_draws'], 0)
        self.assertEqual(stream.calls, [])
        self.assertEqual(stream.rng.calls, [.8, .65])
        self.assertEqual(world, before)

    def test_positive_origin_link_at_threshold_is_not_a_hold(self):
        world = fixture()
        put(world, 151, 93, 4053)
        stream = Stream((.8, F32(.66)))
        with self.assertRaisesRegex(ValueError, 'departing an occupied origin'):
            model.maintain(world, stream)
        self.assertEqual(stream.rng.calls, [.8, F32(.66)])
        self.assertEqual(stream.calls, [])

    def test_route_planets_mines_and_foreign_or_neutral_defense_fail_closed(self):
        for sector in (101, 200):
            for offset, value, owner, message in (
                    (93, 4053, 0, 'planet stock pickup'),
                    (129, 1, 0, 'mine damage'),
                    (81, 11, -1, 'merge/defense combat'),
                    (81, 11, 0, 'merge/defense combat')):
                with self.subTest(sector=sector, offset=offset, owner=owner):
                    world = fixture()
                    put(world, 51 + sector, offset, value)
                    put(world, 51 + sector, 85, owner)
                    with self.assertRaisesRegex(ValueError, message):
                        model.maintain(world, Stream((.1, .2, .9), (200,)))

    def test_split_friendly_force_cannot_silently_merge(self):
        world = fixture()
        put(world, 151, 81, 20)
        put(world, 251, 81, 17)
        put(world, 251, 85, -2)
        with self.assertRaisesRegex(ValueError, 'merged or changed Mercenary force'):
            model.maintain(world, Stream((.1, .2)))

    def test_non37_total_and_unknown_force_owners_fail_closed(self):
        for force in (1, 36, 38, 1000000):
            with self.subTest(force=force):
                world = fixture()
                put(world, 151, 81, force)
                with self.assertRaisesRegex(ValueError, 'one retained37'):
                    model.maintain(world, Stream())
        for owner in (1, 2, -3, .5):
            with self.subTest(owner=owner):
                world = fixture()
                put(world, 151, 85, owner)
                with self.assertRaisesRegex(ValueError, 'unknown sector owners'):
                    model.maintain(world, Stream())

    def test_active_players_and_tax_reject_before_source_read(self):
        for record, offset, message in ((2, 85, 'all-inactive'), (51, 85, 'all-inactive'),
                                        (3052, 89, 'tax-funded'), (4051, 89, 'tax-funded')):
            with self.subTest(record=record):
                world = fixture()
                put(world, record, offset, 1)
                with patch.object(Path, 'read_bytes', side_effect=AssertionError('file read')):
                    with self.assertRaisesRegex(ValueError, message):
                        model.maintain(world, Stream())

    def test_type_extent_and_geometry_bounds_fail_closed(self):
        valid = fixture()
        for world in (bytes(valid), valid[:-1], valid + b'\0'):
            with self.subTest(type=type(world), length=len(world)):
                with self.assertRaisesRegex(ValueError, 'complete mutable'):
                    model.maintain(world, Stream())
        for offset, value in ((53, 50), (57, 3050), (61, 4050), (93, 4150)):
            with self.subTest(offset=offset):
                world = fixture()
                put(world, 1, offset, value)
                with self.assertRaisesRegex(ValueError, 'default geometry'):
                    model.maintain(world, Stream())

    def test_force_and_graph_numeric_bounds_fail_closed(self):
        for force in (-1, .5, 1000001):
            with self.subTest(force=force):
                world = fixture()
                put(world, 151, 81, force)
                with self.assertRaisesRegex(ValueError, 'bounded whole sector force'):
                    model.maintain(world, Stream())
        for target in (-1, .5, 3001):
            with self.subTest(target=target):
                world = fixture()
                put(world, 152, 41, target)
                with self.assertRaisesRegex(ValueError, 'bounded original integer graph'):
                    model.maintain(world, Stream((.1,)))

    def test_unreachable_target_cannot_teleport_force(self):
        world = fixture(route=())
        with self.assertRaisesRegex(AssertionError, 'no directed route'):
            model.maintain(world, Stream((.1, .9), (200,)))
        self.assertEqual(mbf.get(world, 251, 81), 0)

    def test_same_origin_retry_limit_fails_closed(self):
        stream = Stream((.1, .9), (100,) * 64)
        with self.assertRaisesRegex(ValueError, 'same-origin target rejection guard'):
            model.maintain(fixture(), stream)
        self.assertEqual(stream.calls, [(3000, 0x48cf)] * 64)

    def test_only_hash_verified_original_is_read_without_after_targets(self):
        original = model.ROOT / 'archive/dos-original/YTMAINT.EXE'
        read_bytes = Path.read_bytes
        reads = []
        def guarded(path):
            self.assertEqual(path, original, 'non-original input read')
            reads.append(path)
            return read_bytes(path)
        world = fixture()
        with patch.object(Path, 'read_bytes', guarded):
            stats = model.maintain(world, Stream((.1, .9), (200,)))
        self.assertEqual(reads, [original])
        self.assertEqual(stats['final_sectors'], [200])
        for offset in (81, 85):
            self.assertEqual(raw(world, 100, offset), bytes.fromhex('00002800'))

    def test_real_source_stream_derives_rng_from_startup_and_timer_only(self):
        from replay_maintenance_collision_npcs import Stream as SourceStream
        # Two eager RND calls from startup0xc805 produce old0x749ea7.
        # TIMER0 then retains low0xa7 and its next bounded draw selects703.
        world = fixture(100, (100, 703))
        stream = SourceStream((('h1', 0x48cf, bytes(4)),), 0xc805)
        stats = model.maintain(world, stream)
        self.assertEqual(stats['final_sectors'], [703])
        self.assertEqual(stream.index, 1)
        self.assertEqual(stream.calls, {'h1': 1, 'h2': 0})
        self.assertEqual(stream.seeds, [dict(family='h1', caller=0x48cf,
                                           old_state=0x749ea7, timer='00000000',
                                           seeded_state=0xa7)])

    def test_real_source_stream_rejects_a_different_chronological_caller(self):
        from replay_maintenance_collision_npcs import Stream as SourceStream
        stream = SourceStream((('h1', 0x1f88, bytes(4)),), 0xc805)
        with self.assertRaisesRegex(ValueError, 'computed helper chronology differs'):
            model.maintain(fixture(100, (100, 703)), stream)
        self.assertEqual(stream.index, 0)
        self.assertEqual(stream.calls, {'h1': 0, 'h2': 0})

    def test_modified_original_fails_identity_guard(self):
        original = (model.ROOT / 'archive/dos-original/YTMAINT.EXE').read_bytes()
        corrupted = bytearray(original)
        corrupted[0x859e + 0xfd0] ^= 1
        with patch.object(Path, 'read_bytes', return_value=bytes(corrupted)):
            with self.assertRaisesRegex(ValueError, 'original maintenance identity'):
                model.maintain(fixture(), Stream())


if __name__ == '__main__':
    unittest.main()
