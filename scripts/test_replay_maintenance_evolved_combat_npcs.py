"""Source-derived casualty, physical ownership and evolved chain regressions."""
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from replay_qb_graph import mbf
import replay_maintenance_evolved_combat_mercenary as merc
import replay_maintenance_evolved_combat_npcs as npc


class FiniteRNG:
    def __init__(self,values):self.values=iter(values);self.draws=0;self.state=7
    def rnd(self):
        self.draws+=1;self.state=(214013*self.state+1744579)&0xffffff
        return next(self.values)


def fight_world(defenders=3,owner=-1,sector=109):
    world=bytearray(4151*137)
    mbf.put(world,51+sector,81,defenders);mbf.put(world,51+sector,85,owner)
    return world


class MercenaryCasualties(unittest.TestCase):
    def test_negative_owner_still_consumes_eager_gate_draw(self):
        world=fight_world();stream=SimpleNamespace(rng=FiniteRNG([.99,.1,.1,.1]))
        event=merc.attack(world,stream,109,1000)
        self.assertEqual((event['force'],event['defenders'],event['rng_draws']),(1000,0,4))
        self.assertEqual(event['gate'],.99)

    def test_actual_defender_count_is_not_an_expected_182_constant(self):
        for count in(1,3,17):
            world=fight_world(count);stream=SimpleNamespace(rng=FiniteRNG([.9]+[.1]*count))
            event=merc.attack(world,stream,109,97525)
            self.assertEqual((event['initial_defenders'],event['defender_losses'],event['rounds']),(count,count,count))
            self.assertEqual(event['force'],97525)

    def test_two_hundred_boundary_uses_single_not_150_damage(self):
        world=fight_world(200);stream=SimpleNamespace(rng=FiniteRNG([.3]+[.1]*200))
        event=merc.attack(world,stream,109,1000)
        self.assertEqual(event['rounds'],200);self.assertEqual(event['defender_losses'],200)

    def test_above_double_200_threshold_uses_150_then_unit_damage(self):
        world=fight_world(201);stream=SimpleNamespace(rng=FiniteRNG([.3]+[.1]*52))
        event=merc.attack(world,stream,109,1000)
        self.assertEqual((event['rounds'],event['defender_losses']),(52,201))

    def test_threshold_requires_both_sides_above_200(self):
        world=fight_world(201);stream=SimpleNamespace(rng=FiniteRNG([.3]+[.9]*200))
        event=merc.attack(world,stream,109,200)
        self.assertEqual((event['force'],event['defenders'],event['rounds']),(0,201,200))
        self.assertEqual(mbf.get(world,160,85),-1)

    def test_victory_clears_force_owner_but_preserves_group_pointer(self):
        world=fight_world(1);mbf.put(world,59,105,109)
        merc.attack(world,SimpleNamespace(rng=FiniteRNG([.3,.1])),109,200)
        self.assertEqual((mbf.get(world,160,81),mbf.get(world,160,85)),(0,0))
        self.assertEqual(mbf.get(world,59,105),109)
        self.assertEqual(world[(160-1)*137+81:(160-1)*137+89],bytes(8))

    def test_only_defense_fields_change_on_victory(self):
        world=fight_world(1);before=bytes(world)
        merc.attack(world,SimpleNamespace(rng=FiniteRNG([.3,.1])),109,200)
        at=(160-1)*137+81
        self.assertEqual(world[:at],before[:at]);self.assertEqual(world[at+8:],before[at+8:])

    def test_mixed_hazards_and_unknown_owners_reject_before_draw(self):
        for off,value in((85,0),(85,-2),(85,2),(93,1),(129,1)):
            world=fight_world();mbf.put(world,160,off,value);rng=FiniteRNG([])
            with self.subTest(off=off,value=value),self.assertRaises(ValueError):merc.attack(world,SimpleNamespace(rng=rng),109,1000)
            self.assertEqual(rng.draws,0)

    def test_invalid_force_and_geometry_reject_before_draw(self):
        for force in(0,100001,1.5,True):
            rng=FiniteRNG([])
            with self.subTest(force=force),self.assertRaises(ValueError):merc.attack(fight_world(),SimpleNamespace(rng=rng),109,force)
            self.assertEqual(rng.draws,0)
        with self.assertRaises(ValueError):merc.attack(bytearray(1),SimpleNamespace(rng=FiniteRNG([])),109,1)


class EvolvedCombatComposition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import replay_maintenance_evolved_combat_records as records
        cls.records=records;cls.outputs={};cls.stats={};cls.inputs={};cls.before={};cls.observations={}
        for case in records.CASES:
            paths=(records.PARENT/case/'observed-a',)+tuple(records.DEFAULT/case/f'child-{i}'/'observed-a'for i in(1,2))
            observations=tuple(json.loads(gzip.decompress((p/'host-time.json.gz').read_bytes()))for p in paths)
            inputs=tuple(records.inputs_from_observation(o)for o in observations);before=records.old.before_inputs(case)
            output,stats=records.synthesize_chain(before,inputs)
            cls.outputs[case]=output;cls.stats[case]=stats;cls.inputs[case]=inputs;cls.before[case]=before;cls.observations[case]=observations

    def test_all_eight_complete_worlds_match_native_records(self):
        for case,outputs in self.outputs.items():
            for stage in(1,2):
                expected=gzip.decompress((self.records.DEFAULT/case/f'child-{stage}/observed-a/after-YTDATA.DAT.gz').read_bytes())
                self.assertEqual(outputs[stage]['YTDATA.DAT'],expected,(case,stage))

    def test_all_414_rng_witnesses_follow_computed_branches(self):
        count=0
        for case in self.outputs:
            for stage in(1,2):count+=self.records.validate_rng_witnesses(self.observations[case][stage],self.stats[case][stage])
        self.assertEqual(count,414)

    def test_surviving_mercenaries_reactivate_after_lower_sector_arrival(self):
        rows=self.stats['route-mercenary-100000'][2]['npcs']['mercenary']
        self.assertEqual([(a['origin'],a['target'])for a in rows['activations']],[(2645,1963),(1963,2368)])
        self.assertEqual(rows['final_sectors'],[2368]);self.assertEqual((rows['initial_force'],rows['force'],rows['losses']),(97525,97337,188))
        self.assertIn(109,rows['activations'][0]['route'])

    def test_mercenary_casualties_are_derived_and_stale_pointer_survives(self):
        case='route-mercenary-100000';row=self.stats[case][2]['npcs']['mercenary']['events'][0];world=self.outputs[case][2]['YTDATA.DAT']
        self.assertEqual((row['sector'],row['initial_defenders'],row['defender_losses'],row['losses'],row['rounds']),(109,182,182,188,370))
        self.assertEqual((mbf.get(world,59,105),mbf.get(world,160,81),mbf.get(world,160,85)),(109,0,0))
        self.assertEqual((row['rng_draws'],row['initial_rng_state'],row['final_rng_state']),(371,10977382,628675))

    def test_neutral_force_is_preserved_not_counted_as_xannor_allocation(self):
        for stage in(1,2):
            world=self.outputs['route-neutral-37'][stage]['YTDATA.DAT']
            self.assertEqual((mbf.get(world,905,81),mbf.get(world,905,85)),(37,0))
            self.assertEqual(self.stats['route-neutral-37'][stage]['npcs']['normalized_total'],10000)

    def test_extinct_mercenary_force_is_not_recreated(self):
        for stage in(1,2):
            row=self.stats['route-mercenary-37'][stage]['npcs']
            self.assertEqual(row['normalized_total'],9963);self.assertEqual(row['mercenary']['force'],0);self.assertEqual(row['mercenary']['events'],[])

    def test_ordinary_surviving_planet_has_conserved_actual_losses(self):
        for stage,xloss,groundloss,total in((1,2614,22,1408),(2,792,19,616)):
            row=self.stats['route-planet-neutral'][stage]['npcs'];events=row['events']
            self.assertEqual(len(events),18);self.assertEqual(sum(e['initial_force']for e in events),xloss)
            self.assertEqual(sum(e['ground_spent']for e in events),groundloss);self.assertEqual(row['final_physical_force'],total)
            self.assertEqual({e['planet_name']for e in events},{'Route Haven'})

    def test_chain_reads_only_original_executable_after_inputs_loaded(self):
        original=Path.read_bytes;allowed={'YTMAINT.EXE','BRUN30.EXE'}
        def guarded(path):
            if 'archive/dos-original'not in str(path)or path.name not in allowed:raise AssertionError('unexpected synthesis read: '+str(path))
            return original(path)
        with patch.object(Path,'read_bytes',guarded):
            for case in self.outputs:
                outputs,_=self.records.synthesize_chain(self.before[case],self.inputs[case]);self.assertEqual(outputs,self.outputs[case])

    def test_unknown_foreign_owner_is_rejected(self):
        case='route-neutral-37';before=dict(self.outputs[case][0]);world=bytearray(before['YTDATA.DAT']);mbf.put(world,905,85,2);before['YTDATA.DAT']=bytes(world)
        with self.assertRaisesRegex(AssertionError,'bounded actual Xannor'):self.records._synthesize_day(before,self.inputs[case][1])


if __name__=='__main__':unittest.main()
