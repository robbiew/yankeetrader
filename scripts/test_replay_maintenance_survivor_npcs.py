"""Derived survivor combat branches, conserved force and modeled-prefix checks."""
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from replay_qb_graph import mbf
import replay_maintenance_survivor_npcs as npc


class FiniteRNG:
    def __init__(self,values):self.values=iter(values);self.draws=0;self.state=7
    def rnd(self):
        self.draws+=1;self.state=(214013*self.state+1744579)&0xffffff
        return next(self.values)


def defense_world(force=97337,sector=2812,owner=-2):
    world=bytearray(4151*137);mbf.put(world,51+sector,81,force);mbf.put(world,51+sector,85,owner)
    return world


def planet_world(ground=341,sector=1548,name=b'The Wanderer',slot=1,owner=0):
    world=bytearray(4151*137);rec=4051+slot;at=(rec-1)*137
    world[at:at+41]=name.ljust(41,b' ');mbf.put(world,rec,85,len(name));mbf.put(world,rec,73,owner);mbf.put(world,rec,77,ground)
    mbf.put(world,51+sector,93,slot);return world


class SelectedSurvivorDefense(unittest.TestCase):
    def test_zero_foreign_damage_is_a_valid_losing_attack(self):
        world=defense_world();stream=SimpleNamespace(rng=FiniteRNG([.9]));event=npc.defense(world,stream,15,2812,1)
        self.assertEqual((event['force'],event['x_damage'],event['defender_damage']),(0,1,0))
        self.assertEqual(mbf.get(world,2863,81),97337);self.assertEqual(event['rng_draws'],1)

    def test_strict_5000_boundary_changes_batch_only_above(self):
        for force,rounds in((5000,10),(6000,3)):
            stream=SimpleNamespace(rng=FiniteRNG([.9]*rounds));event=npc.defense(defense_world(),stream,2,2812,force)
            self.assertEqual((event['force'],event['rng_draws'],event['x_damage']),(0,rounds,force))

    def test_500_boundary_uses_batch500_but499_uses_one(self):
        for force,rounds in((500,1),(499,499)):
            stream=SimpleNamespace(rng=FiniteRNG([.9]*rounds));event=npc.defense(defense_world(),stream,2,2812,force)
            self.assertEqual((event['force'],event['rng_draws']),(0,rounds))

    def test_original_half_tie_damages_defenders(self):
        world=defense_world(1);stream=SimpleNamespace(rng=FiniteRNG([.5]));event=npc.defense(world,stream,2,2812,3)
        self.assertEqual((event['force'],event['defenders'],event['defender_damage']),(3,0,1))
        self.assertEqual((mbf.get(world,2863,81),mbf.get(world,2863,85)),(0,0))

    def test_foreign_survivor_mutates_only_actual_defense_force(self):
        world=defense_world();before=bytes(world);npc.defense(world,SimpleNamespace(rng=FiniteRNG([.1,.9])),2,2812,1)
        at=(2863-1)*137+81
        self.assertEqual(mbf.get(world,2863,81),97336);self.assertEqual(world[:at],before[:at]);self.assertEqual(world[at+4:],before[at+4:])

    def test_unknown_owner_and_mixed_hazards_reject_before_draw(self):
        for off,value in((85,0),(85,2),(85,-1),(93,1),(129,1)):
            world=defense_world();mbf.put(world,2863,off,value);rng=FiniteRNG([])
            with self.subTest(off=off,value=value),self.assertRaises(ValueError):npc.defense(world,SimpleNamespace(rng=rng),2,2812,1)
            self.assertEqual(rng.draws,0)


class SelectedSurvivorGround(unittest.TestCase):
    def test_ground_spend_depends_on_actual_draw_not_named_casualty(self):
        for force,rolls,spent in((199,[.9],1),(949,[.1,.9],2),(230,[.1,.1,.1],3)):
            world=planet_world();event=npc.ground_assault(world,SimpleNamespace(rng=FiniteRNG(rolls)),15,1548,force)
            self.assertEqual((event['force'],event['ground_spent'],event['ground']),(0,spent,341-spent))

    def test_raw_negative_force_is_preserved_in_event_not_physical_world(self):
        event=npc.ground_assault(planet_world(),SimpleNamespace(rng=FiniteRNG([.9])),15,1548,199)
        self.assertEqual(event['raw_force'],-702);self.assertEqual(event['force'],0)

    def test_planetary_casualty_preserves_owner_and_sector_links(self):
        world=planet_world();before=bytes(world);npc.ground_assault(world,SimpleNamespace(rng=FiniteRNG([.9])),15,1548,199)
        at=(4052-1)*137+77
        self.assertEqual(world[:at],before[:at]);self.assertEqual(world[at+4:],before[at+4:]);self.assertEqual(mbf.get(world,4052,73),0)

    def test_friendly_or_renamed_planet_is_not_admitted_as_hostile_wanderer(self):
        for world in(planet_world(owner=-1),planet_world(name=b'Other Wanderer')):
            rng=FiniteRNG([])
            with self.assertRaises(ValueError):npc.ground_assault(world,SimpleNamespace(rng=rng),15,1548,199)
            self.assertEqual(rng.draws,0)

    def test_zero_ground_or_capture_branch_remains_excluded(self):
        with self.assertRaises(ValueError):npc.ground_assault(planet_world(ground=0),SimpleNamespace(rng=FiniteRNG([])),15,1548,199)
        with self.assertRaisesRegex(ValueError,'zero-ground'):npc.ground_assault(planet_world(ground=1),SimpleNamespace(rng=FiniteRNG([.9])),15,1548,199)


class FiveDaySurvivorComposition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import replay_maintenance_survivor_records as records
        cls.records=records;cls.outputs={};cls.rows={};cls.inputs={};cls.before={};cls.observations={}
        for profile in records.PROFILES:
            observations=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in records.observation_paths(profile,'observed-a'))
            inputs=tuple(records.inputs_from_observation(o)for o in observations);before=records.initial_before(profile)
            outputs,rows=records.synthesize_chain(before,inputs)
            cls.outputs[profile]=outputs;cls.rows[profile]=rows;cls.inputs[profile]=inputs;cls.before[profile]=before;cls.observations[profile]=observations

    def test_all_eight_complete_worlds_are_predicted_from_original_prefixes(self):
        for profile,outputs in self.outputs.items():
            for child,index in((1,3),(2,4)):
                expected=gzip.decompress((self.records.DEFAULT/profile/f'child-{child}/observed-a/after-YTDATA.DAT.gz').read_bytes())
                self.assertEqual(outputs[index]['YTDATA.DAT'],expected,(profile,child))

    def test_all_394_new_stage_rng_witnesses_follow_source_branches(self):
        count=0
        for profile in self.outputs:
            for index in(3,4):count+=self.records.validate_rng_witnesses(self.observations[profile][index],self.rows[profile][index])
        self.assertEqual(count,394)

    def test_fatal_defense_updates_shared_pursuit_for_later_groups(self):
        row=self.rows['mercenary-survivor'][4]['npcs'];events=row['events']
        self.assertEqual(len(events),18);self.assertEqual({e['sector']for e in events},{2812})
        self.assertEqual([e['group']for e in events],list(range(2,20)))
        self.assertEqual(sum(e['x_damage']for e in events),2533);self.assertEqual(sum(e['defender_damage']for e in events),3491)
        self.assertEqual([e['defender_damage']for e in events if e['initial_force']==1],[2,0])
        for route in row['routes']:
            if 2<=route['group']<=19:self.assertEqual(route['preferred'],2812)
        self.assertEqual(row['mercenary']['force'],93846)

    def test_stale_group8_normalizes_then_receives_new_source_allocation(self):
        row=self.rows['mercenary-survivor'][3]['npcs'];before=self.outputs['mercenary-survivor'][2]['YTDATA.DAT'];after=self.outputs['mercenary-survivor'][3]['YTDATA.DAT']
        self.assertEqual(mbf.get(before,59,105),109);self.assertEqual((row['cache_locations'][8],row['cache_forces'][8]),(0,0))
        self.assertEqual((row['groups'][8]['sector'],row['groups'][8]['strength']),(328,2));self.assertEqual(mbf.get(after,59,105),328)

    def test_mercenary_four_activations_are_source_ordered_each_day(self):
        first=self.rows['mercenary-survivor'][3]['npcs']['mercenary'];second=self.rows['mercenary-survivor'][4]['npcs']['mercenary']
        self.assertEqual([a['origin']for a in first['activations']],[2368,1680,1389,1082]);self.assertEqual(first['final_sectors'],[2812])
        self.assertEqual([a['origin']for a in second['activations']],[2812,2499,1351,815]);self.assertEqual(second['final_sectors'],[2790])
        self.assertEqual((first['events'],second['events']),([],[]))

    def test_wanderer_and_ordinary_ground_casualties_are_computed(self):
        for profile,index,count,force,ground in(('neutral-survivor',4,5,1425,7),('mine-survivor',3,4,818,5),('planet-survivor',3,18,146,18),('planet-survivor',4,18,70,18)):
            events=self.rows[profile][index]['npcs']['events']
            self.assertEqual((len(events),sum(e['initial_force']for e in events),sum(e['ground_spent']for e in events)),(count,force,ground))
        self.assertEqual(self.rows['mine-survivor'][4]['npcs']['events'],[])

    def test_mine_persistence_is_not_reported_as_selected_damage(self):
        for index in(3,4):
            world=self.outputs['mine-survivor'][index]['YTDATA.DAT']
            self.assertEqual([mbf.get(world,51+s,129)for s in(439,474,1169)],[1,1,1]);self.assertEqual(mbf.get(world,1031,129),0)
            self.assertFalse(any(e['kind']=='mine'for e in self.rows['mine-survivor'][index]['npcs']['events']))

    def test_complete_five_day_synthesis_cannot_read_child_targets(self):
        original=Path.read_bytes
        def guarded(path):
            if 'archive/dos-original'not in str(path)or path.name not in('YTMAINT.EXE','BRUN30.EXE'):raise AssertionError('unexpected synthesis read: '+str(path))
            return original(path)
        with patch.object(Path,'read_bytes',guarded):
            for profile in self.outputs:
                outputs,_=self.records.synthesize_chain(self.before[profile],self.inputs[profile]);self.assertEqual(outputs,self.outputs[profile])


if __name__=='__main__':unittest.main()
