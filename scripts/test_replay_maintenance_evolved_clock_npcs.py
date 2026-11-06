"""Independent fatal-route boundaries and actual clock-profile composition."""
import builtins
import gzip
import json
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import unittest

from replay_qb_graph import mbf
import replay_maintenance_evolved_clock_npcs as npc

ROOT=Path(__file__).resolve().parents[1]


class FiniteRNG:
    def __init__(self,values):self.values=iter(values);self.draws=0;self.state=5
    def rnd(self):
        value=next(self.values);self.draws+=1;self.state=(214013*self.state+1744579)&0xffffff;return value


class MineStream:
    def __init__(self,rolls):self.rolls=iter(rolls);self.rng=FiniteRNG([]);self.calls=[]
    def one(self,bound,*,caller):
        self.calls.append((bound,caller));value=next(self.rolls);self.rng.draws+=1;self.rng.state=(214013*self.rng.state+1744579)&0xffffff;return value


def mine_world(sector=980,mines=1):
    world=bytearray(4151*137);mbf.put(world,51+sector,129,mines);return world


def planet_world(slot=1,sector=222,ground=250):
    world=bytearray(4151*137);record=4051+slot
    name,owner=(b'The Wanderer',0)if slot==1 else(b'Mercenary Base',-2)
    at=(record-1)*137;world[at:at+41]=name.ljust(41,b' ')
    for off,value in((85,len(name)),(73,owner),(77,ground),(45,10000),(49,10000),(53,10000),(57,3000),(61,4000),(65,5000)):
        mbf.put(world,record,off,value)
    mbf.put(world,51+sector,93,slot);return world


class FatalMineProperties(unittest.TestCase):
    def test_effective_damage_caps_roll_to_actual_force(self):
        world=mine_world();stream=MineStream([223]);event=npc.mine_hit(world,stream,2,980,6)
        self.assertEqual((event['initial_force'],event['force'],event['losses']),(6,0,6));self.assertEqual(event['rolls'],[223])
        self.assertEqual((event['initial_mines'],event['mines'],event['mines_spent']),(1,0,1));self.assertEqual(stream.calls,[(1000,0x7312)])

    def test_initial_mine_loop_keeps_drawing_after_fatal_hit(self):
        world=mine_world(mines=3);stream=MineStream([223,999,777]);event=npc.mine_hit(world,stream,2,980,6)
        self.assertEqual(event['mines'],2);self.assertEqual(event['mines_spent'],1);self.assertEqual(event['rng_draws'],3)
        self.assertEqual(stream.calls,[(1000,0x7312)]*3)

    def test_zero_residue_derives_from_record_index_FAC_before_cancellation(self):
        outputs=[]
        for sector in(980,799):
            world=mine_world(sector=sector);npc.mine_hit(world,MineStream([1000]),2,sector,1)
            at=(50+sector)*137+129;expected=bytearray(mbf.enc(51+sector));expected[3]=0
            self.assertEqual(world[at:at+4],expected);self.assertEqual(mbf.get(world,51+sector,129),0)
            outputs.append(bytes(expected))
        self.assertNotEqual(outputs[0],outputs[1]);self.assertEqual(outputs[0],bytes.fromhex('00e00000'))

    def test_unspent_positive_mines_keep_numeric_remainder(self):
        world=mine_world(mines=2);event=npc.mine_hit(world,MineStream([1,1000]),2,980,1)
        self.assertEqual((event['mines'],event['mines_spent']),(1,1));self.assertEqual(mbf.get(world,1031,129),1)

    def test_fatal_mine_mutates_only_consumed_mine_field(self):
        world=mine_world();before=bytes(world);npc.mine_hit(world,MineStream([1000]),2,980,1)
        at=(1031-1)*137+129;self.assertEqual(world[:at],before[:at]);self.assertEqual(world[at+4:],before[at+4:])

    def test_survival_branch_is_explicitly_unsupported_without_world_patch(self):
        world=mine_world();before=bytes(world)
        with self.assertRaisesRegex(ValueError,'surviving mine'):npc.mine_hit(world,MineStream([1]),2,980,10000)
        self.assertEqual(bytes(world),before)

    def test_invalid_mine_count_mixed_planet_or_defense_rejects_before_draw(self):
        for amount in(0,.5,4):
            world=mine_world(mines=amount);stream=MineStream([])
            with self.subTest(mines=amount),self.assertRaises(ValueError):npc.mine_hit(world,stream,2,980,6)
            self.assertEqual(stream.calls,[])
        for offset,value in((81,1),(93,1)):
            world=mine_world();mbf.put(world,1031,offset,value);stream=MineStream([])
            with self.subTest(offset=offset),self.assertRaises(ValueError):npc.mine_hit(world,stream,2,980,6)
            self.assertEqual(stream.calls,[])

    def test_wrong_bounds_and_mutable_world_type_reject(self):
        for group,sector,force in((1,980,1),(21,980,1),(2,7,1),(2,3001,1),(2,980,0),(2,980,1.5),(2,980,True)):
            with self.subTest(args=(group,sector,force)),self.assertRaises(ValueError):npc.mine_hit(mine_world(),MineStream([]),group,sector,force)
        for world in(bytes(4151*137),bytearray(1)):
            with self.assertRaises(ValueError):npc.mine_hit(world,MineStream([]),2,980,1)


class GroundHomeProperties(unittest.TestCase):
    def test_first_ground_roll_uses_original_one_to_thousand_rule(self):
        for value,force,roll in((0,1,1),(1-2**-24,1000,1000)):
            world=planet_world();stream=SimpleNamespace(rng=FiniteRNG([value]));event=npc.ground_assault(world,stream,2,222,force)
            self.assertEqual(event['rolls'],[roll]);self.assertEqual(event['force'],0);self.assertEqual(event['ground'],249);self.assertEqual(event['ground_spent'],1)

    def test_raw_force_can_go_negative_but_saved_result_is_zero(self):
        world=planet_world();event=npc.ground_assault(world,SimpleNamespace(rng=FiniteRNG([.222])),2,222,6)
        self.assertEqual((event['raw_force'],event['force']),(-217,0));self.assertEqual(mbf.get(world,4052,77),249)

    def test_multiple_ground_exchanges_derive_actual_spent_units(self):
        world=planet_world();event=npc.ground_assault(world,SimpleNamespace(rng=FiniteRNG([.3,.3])),3,222,500)
        self.assertEqual(event['ground_spent'],2);self.assertEqual(event['rng_draws'],2);self.assertEqual(event['raw_force'],-102)

    def test_both_neutral_Wanderer_and_foreign_Base_use_actual_identity(self):
        for slot,name,owner in((1,'The Wanderer',0),(99,'Mercenary Base',-2)):
            world=planet_world(slot=slot,ground=1000);event=npc.ground_assault(world,SimpleNamespace(rng=FiniteRNG([.5])),2,222,1)
            self.assertEqual((event['planet_slot'],event['planet_name']),(slot,name));self.assertEqual(mbf.get(world,4051+slot,73),owner)

    def test_positive_ground_death_mutates_only_ground_not_production_or_stock(self):
        world=planet_world(slot=99,ground=1000);before=bytes(world);npc.ground_assault(world,SimpleNamespace(rng=FiniteRNG([.5])),2,222,1)
        at=(4150-1)*137+77;self.assertEqual(world[:at],before[:at]);self.assertEqual(world[at+4:],before[at+4:])

    def test_ground_exhaustion_and_zero_ground_owner_path_are_rejected(self):
        for ground,force in((1,10000),(1,1)):
            world=planet_world(ground=ground);before=bytes(world)
            with self.subTest(ground=ground,force=force),self.assertRaises(ValueError):npc.ground_assault(world,SimpleNamespace(rng=FiniteRNG([0])),2,222,force)
            self.assertEqual(world,before)

    def test_unknown_name_owner_ground_slot_and_hazards_fail_before_draw(self):
        for field,value in((85,0),(73,-1),(77,0),(77,.5),(77,600001)):
            world=planet_world();mbf.put(world,4052,field,value)
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):npc.ground_assault(world,SimpleNamespace(rng=FiniteRNG([])),2,222,1)
        for field,value in((93,2),(81,1),(129,1)):
            world=planet_world();mbf.put(world,273,field,value)
            with self.subTest(field=field),self.assertRaises(ValueError):npc.ground_assault(world,SimpleNamespace(rng=FiniteRNG([])),2,222,1)
        world=planet_world();world[(4052-1)*137]=ord('X')
        with self.assertRaises(ValueError):npc.ground_assault(world,SimpleNamespace(rng=FiniteRNG([])),2,222,1)

    def test_primitive_route_branches_never_read_files(self):
        mine=mine_world();planet=planet_world()
        with patch.object(Path,'read_bytes',side_effect=AssertionError('target/source read')),patch.object(Path,'read_text',side_effect=AssertionError('target text read')),patch.object(builtins,'open',side_effect=AssertionError('file open')):
            npc.mine_hit(mine,MineStream([223]),2,980,6)
            npc.ground_assault(planet,SimpleNamespace(rng=FiniteRNG([.5])),2,222,6)


class ClockProfileComposition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import replay_maintenance_evolved_clock_records as records
        cls.records=records
        parent=records.ROOT/'research/yt-maint/convergence-chain-controls/day-1/observed-a/host-time.json.gz'
        first=json.loads(gzip.decompress(parent.read_bytes()));cls.inputs={};cls.outputs={};cls.stats={}
        before=records.old.initial_before()
        for profile in records.DATE_PAIRS:
            raw=[first]+[json.loads(gzip.decompress((records.DEFAULT/profile/stage/'observed-a/host-time.json.gz').read_bytes()))for stage in('child-1','child-2')]
            inputs=tuple(records.inputs_from_observation(ob)for ob in raw);output,stats=records.synthesize_chain(before,inputs)
            cls.inputs[profile]=inputs;cls.outputs[profile]=output;cls.stats[profile]=stats

    def test_actual_new_year_stationary_group20_does_not_drop_another_mine(self):
        output=self.outputs['new-year'];stats=self.stats['new-year'][2]['npcs'];route=next(r for r in stats['routes']if r['group']==20)
        self.assertEqual((route['origin'],route['target']),(439,439));self.assertEqual(route['entered'],[])
        self.assertEqual(mbf.get(output[1]['YTDATA.DAT'],490,129),1);self.assertEqual(mbf.get(output[2]['YTDATA.DAT'],490,129),1)

    def test_actual_fatal_event_counts_and_casualty_totals_are_computed(self):
        events={profile:[s['npcs']['events']for s in rows[1:]]for profile,rows in self.stats.items()}
        self.assertEqual([len(v)for v in events['noon']],[14,0]);self.assertEqual(sum(e['initial_force']for e in events['noon'][0]),1700)
        self.assertEqual([len(v)for v in events['new-year']],[0,4]);self.assertEqual([e['initial_force']for e in events['new-year'][1]],[23,216,53,70])
        mine=events['second-two'][1][0];self.assertEqual((mine['kind'],mine['sector'],mine['initial_force'],mine['rolls']),('mine',980,6,[223]))

    def test_all_modeled_child_worlds_match_complete_native_records(self):
        for profile,output in self.outputs.items():
            for index,stage in enumerate(('child-1','child-2'),1):
                expected=gzip.decompress((self.records.DEFAULT/profile/stage/'observed-a/after-YTDATA.DAT.gz').read_bytes())
                self.assertEqual(output[index]['YTDATA.DAT'],expected,(profile,stage))


if __name__=='__main__':unittest.main()
