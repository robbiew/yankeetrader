"""Synthetic source-bound combat and tail contracts, independent of after files.

Injected draws select branch boundaries; they are not a substitute native RNG
trace or a claim that arbitrary worlds are admitted by the complete profile.
"""
from pathlib import Path
import unittest
from unittest.mock import patch

from replay_qb_graph import F32, mbf
import replay_maintenance_occupied_npcs as combat
import replay_maintenance_occupied_mercenary as mercenary


def put(world,record,offset,value):
    at=(record-1)*137+offset;world[at:at+4]=mbf.enc(value)


def raw(world,record,offset):
    at=(record-1)*137+offset;return bytes(world[at:at+4])


def defense_world(defenders=500,owner=-2):
    world=bytearray(4151*137)
    put(world,905,81,defenders);put(world,905,85,owner)
    return world


def planet_world(ground=505000):
    world=bytearray(4151*137);at=(4053-1)*137
    world[at:at+41]=b'Route Haven'.ljust(41,b' ')
    for off,value in ((85,11),(73,0),(77,ground),(45,1010),(49,1010),(53,1010),(57,1000),(61,2000),(65,3000)):
        put(world,4053,off,value)
    put(world,905,93,2)
    return world


def tail_world(origin=100,route=(100,101,200)):
    world=bytearray(4151*137)
    for off,value in ((53,51),(57,3051),(61,4051),(93,4151)):put(world,1,off,value)
    if origin is not None:
        put(world,51+origin,81,97525);put(world,51+origin,85,-2)
    for source,target in zip(route,route[1:]):put(world,51+source,41,target)
    return world


class Draws:
    """Finite explicit branch values with an independent consumption counter."""
    def __init__(self,values):
        self.values=iter(values);self.state=0x123456;self.draws=0;self.calls=[]
    def rnd(self):
        value=next(self.values);self.calls.append(value);self.draws+=1;self.state+=1
        return value


class Stream:
    def __init__(self,draws=(),targets=()):
        self.rng=Draws(draws);self.targets=iter(targets);self.calls=[]
    def one(self,bound,*,caller):
        self.calls.append((bound,caller))
        if (bound,caller)!=(3000,0x48cf):raise AssertionError('unexpected source helper')
        return next(self.targets)


class OccupiedCombatBoundaries(unittest.TestCase):
    def test_exact_half_tie_damages_defenders_while_above_half_damages_xannor(self):
        for draw,winner in ((.5,'xannor'),(.5000000596046448,'defenders')):
            world=defense_world();stream=Stream((draw,))
            event=combat.defense(world,stream,2,854,500)
            with self.subTest(draw=draw):
                self.assertEqual(stream.rng.draws,1)
                self.assertEqual((event['force'],event['defenders']),(500,0)if winner=='xannor'else(0,500))
                self.assertEqual((event['x_damage'],event['defender_damage']),(0,500)if winner=='xannor'else(500,0))

    def test_five_hundred_is_batch_boundary_but_four_ninety_nine_is_per_unit(self):
        for amount,expected_draws in ((499,499),(500,1)):
            with self.subTest(amount=amount):
                stream=Stream((.5,)*expected_draws);event=combat.defense(defense_world(amount),stream,2,854,amount)
                self.assertEqual((event['force'],event['defenders']),(amount,0))
                self.assertEqual(event['rng_draws'],expected_draws)
                self.assertEqual(event['defender_damage'],amount)

    def test_large_batch_requires_both_sides_strictly_above_five_thousand(self):
        for attackers,defenders,expected_draws in ((5000,5000,10),(5001,5001,2),(6000,5000,10),(6000,5001,2)):
            with self.subTest(attackers=attackers,defenders=defenders):
                stream=Stream((.5,)*expected_draws);event=combat.defense(defense_world(defenders),stream,2,854,attackers)
                self.assertEqual((event['force'],event['defenders']),(attackers,0))
                self.assertEqual(event['rng_draws'],expected_draws)

    def test_defense_victory_clears_only_force_and_title_with_canonical_zero(self):
        world=defense_world(37);put(world,905,69,1234);before=bytes(world)
        event=combat.defense(world,Stream((.5,)*37),3,854,1400)
        self.assertEqual((event['force'],event['defenders']),(1400,0))
        self.assertEqual((raw(world,905,81),raw(world,905,85)),(bytes(4),bytes(4)))
        allowed={(905-1)*137+off+i for off in(81,85)for i in range(4)}
        self.assertLessEqual({i for i,(a,b)in enumerate(zip(before,world))if a!=b},allowed)

    def test_defense_refuses_other_sectors_owners_forces_and_mixed_hazards_before_drawing(self):
        cases=[(853,-2,500,500,0,0),(854,0,500,500,0,0),(854,-1,500,500,0,0),
               (854,2,500,500,0,0),(854,-2,.5,500,0,0),(854,-2,500,True,0,0),
               (854,-2,500,0,0,0),(854,-2,500,10001,0,0),(854,-2,500,500,1,0),(854,-2,500,500,0,2)]
        for sector,owner,defenders,attackers,mine,planet in cases:
            world=defense_world(defenders,owner);put(world,905,129,mine);put(world,905,93,planet);stream=Stream()
            with self.subTest(case=(sector,owner,defenders,attackers,mine,planet)):
                with self.assertRaises(ValueError):combat.defense(world,stream,2,sector,attackers)
                self.assertEqual(stream.rng.draws,0)

    def test_one_ground_roll_ranges_from_one_to_one_thousand_and_clamps_group_death(self):
        for draw,damage in ((0,1),((2**24-1)/2**24,1000)):
            stream=Stream((draw,));world=planet_world()
            event=combat.ground_assault(world,stream,2,854,1)
            with self.subTest(draw=draw):
                self.assertEqual((event['raw_force'],event['force']),(1-damage,0))
                self.assertEqual(event['ground'],504999)
                self.assertEqual(field(world,4053,77),504999)
                self.assertEqual(stream.rng.draws,1)

    def test_positive_ground_defense_never_consumes_production_or_warehouse_fields(self):
        world=planet_world();before=bytes(world);stream=Stream((0,)*1000)
        event=combat.ground_assault(world,stream,20,854,1000)
        self.assertEqual((event['force'],event['raw_force'],event['ground'],event['rng_draws']),(0,0,504000,1000))
        allowed={(4053-1)*137+77+i for i in range(4)}
        self.assertLessEqual({i for i,(a,b)in enumerate(zip(before,world))if a!=b},allowed)
        self.assertEqual(field(world,4053,73),0)
        self.assertEqual(field(world,905,93),2)
        self.assertEqual(stream.rng.calls,[0]*1000)

    def test_ground_context_rejects_wrong_planet_name_owner_hazards_and_weak_ground(self):
        changes=[(905,93,0),(905,93,3),(905,81,1),(905,129,1),(4053,73,-1),(4053,85,0),(4053,77,500000),(4053,77,505001)]
        for record,offset,value in changes:
            world=planet_world();put(world,record,offset,value);stream=Stream()
            with self.subTest(record=record,offset=offset,value=value):
                with self.assertRaises(ValueError):combat.ground_assault(world,stream,2,854,10)
                self.assertEqual(stream.rng.draws,0)
        world=planet_world();world[(4053-1)*137]=ord('X')
        with self.assertRaises(ValueError):combat.ground_assault(world,Stream(),2,854,10)
        for sector,group,force in ((853,2,10),(854,1,10),(854,21,10),(854,2,0),(854,2,True)):
            with self.assertRaises(ValueError):combat.ground_assault(planet_world(),Stream(),group,sector,force)

    def test_combat_primitives_do_not_read_targets_or_original_files(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('no file reads')):
            self.assertEqual(combat.defense(defense_world(1),Stream((.5,)),2,854,1)['defenders'],0)
            self.assertEqual(combat.ground_assault(planet_world(),Stream((0,)),2,854,1)['force'],0)


class OccupiedMercenaryTailBoundaries(unittest.TestCase):
    def test_large_survivor_moves_conservatively_and_keeps_source_departure_zero(self):
        world=tail_world();stream=Stream((.1,.9),(200,));before=bytes(world)
        stats=mercenary.maintain(world,stream)
        self.assertEqual((stats['force'],stats['final_sectors']),(97525,[200]))
        self.assertEqual((field(world,251,81),field(world,251,85)),(97525,-2))
        self.assertEqual((raw(world,151,81),raw(world,151,85)),(bytes.fromhex('00002800'),)*2)
        self.assertEqual((stats['desertion_draws'],stats['movement_gate_draws'],stats['target_draws']),(1,1,1))
        self.assertEqual(stream.calls,[(3000,0x48cf)])
        self.assertEqual(stats['events'],[])
        allowed={(record-1)*137+off+i for record in(151,251)for off in(81,85)for i in range(4)}
        self.assertLessEqual({i for i,(a,b)in enumerate(zip(before,world))if a!=b},allowed)

    def test_large_survivor_reactivates_at_lower_sector_without_duplicate_force(self):
        world=tail_world(3000,(3000,1228,2786));stream=Stream((.1,.2,.3),(1228,2786))
        stats=mercenary.maintain(world,stream)
        self.assertEqual([a['origin']for a in stats['activations']],[3000,1228])
        self.assertEqual(stats['final_sectors'],[2786])
        self.assertEqual(sum(field(world,51+s,81)for s in range(1,3001)),97525)
        self.assertEqual((stats['movement_gate_draws'],stats['target_draws']),(2,2))

    def test_changed_force_or_split_large_force_does_not_silently_enter_tail(self):
        for amount in (37,97524,97526,100000):
            world=tail_world();put(world,151,81,amount)
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):mercenary.maintain(world,Stream())
        world=tail_world();put(world,151,81,97524);put(world,251,81,1);put(world,251,85,-2)
        with self.assertRaisesRegex(ValueError,'merged or changed'):mercenary.maintain(world,Stream((.1,.2)))

    def test_route_planet_mine_and_friendly_or_foreign_force_remain_unsupported(self):
        for record in (152,251):
            for off,value,owner in ((129,1,0),(93,2,0),(81,1,0),(81,1,-1),(81,1,-2)):
                world=tail_world();put(world,record,off,value);put(world,record,85,owner)
                with self.subTest(record=record,offset=off,owner=owner):
                    with self.assertRaises(ValueError):mercenary.maintain(world,Stream((.1,.2,.3),(200,)))

    def test_origin_hold_gate_is_eager_and_its_exact_threshold_is_not_a_hold(self):
        world=tail_world();put(world,151,93,2);before=bytes(world);stream=Stream((.1,.65))
        stats=mercenary.maintain(world,stream)
        self.assertEqual(world,before);self.assertEqual(stats['target_draws'],0)
        self.assertEqual(stream.rng.calls,[.1,.65]);self.assertTrue(stats['activations'][0]['held'])
        world=tail_world();put(world,151,93,2);stream=Stream((.1,F32(.66)))
        with self.assertRaisesRegex(ValueError,'departing an occupied origin'):mercenary.maintain(world,stream)
        self.assertEqual(stream.rng.calls,[.1,F32(.66)])

    def test_only_the_verified_original_is_read_for_source_departure_constant(self):
        allowed=mercenary.ROOT/'archive/dos-original/YTMAINT.EXE';read=Path.read_bytes;seen=[]
        def guard(path):
            self.assertEqual(path,allowed);seen.append(path);return read(path)
        with patch.object(Path,'read_bytes',guard),patch.object(Path,'read_text',side_effect=AssertionError('no target reads')):
            stats=mercenary.maintain(tail_world(),Stream((.1,.9),(200,)))
        self.assertEqual(seen,[allowed]);self.assertEqual(stats['force'],97525)


def field(world,record,offset):
    return mbf.get(world,record,offset)


if __name__=='__main__':unittest.main()
