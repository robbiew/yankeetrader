"""Before-only inputs, chronology and complete-output properties for active replay."""
import copy
from dataclasses import fields, replace
import datetime
import gzip
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import replay_maintenance_occupied_records as replay
import replay_maintenance_collision_records as historical
import replay_qb_graph as qb

ROOT=Path(__file__).resolve().parents[1]


def field(world,record,offset):
    return qb.mbf.get(world,record,offset)


def physical(world,owner=None):
    return sum(int(field(world,51+s,81))for s in range(1,3001)
               if owner is None or field(world,51+s,85)==owner)


class OccupiedRecordProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe=json.loads((replay.DEFAULT/'recipe.json').read_text())
        cls.observations={case:json.loads(gzip.decompress((replay.DEFAULT/case/'observed-a/host-time.json.gz').read_bytes()))for case in cls.recipe['cases']}
        cls.inputs={case:replay.inputs_from_observation(ob)for case,ob in cls.observations.items()}
        cls.before={case:replay.before_inputs(case)for case in cls.recipe['cases']}
        cls.modeled={case:replay.synthesize(cls.before[case],cls.inputs[case])for case in cls.recipe['cases']}

    def test_explicit_profile_admits_only_ten_measured_before_inputs(self):
        self.assertEqual(len(self.before),10)
        for case,before in self.before.items():
            with self.subTest(case=case):
                self.assertEqual(replay.ADMITTED_INPUTS[replay.SHA(before['YTDATA.DAT'])],case)
        self.assertEqual({f.name for f in fields(replay.Inputs)}, {'clock','schedule','planet_clocks'})

    def test_unknown_before_world_rejects_without_original_or_target_reads(self):
        case='route-planet-neutral';before=dict(self.before[case]);world=bytearray(before['YTDATA.DAT']);world[12345]^=1;before['YTDATA.DAT']=bytes(world)
        with patch.object(Path,'read_bytes',side_effect=AssertionError('no reads admitted')):
            with self.assertRaises(ValueError):replay.synthesize(before,self.inputs[case])

    def test_changed_side_files_reject_without_original_or_target_reads(self):
        case='route-mercenary-100000'
        for name in ('YTNAME.DAT','YTNEWS.DAT'):
            before=dict(self.before[case]);before[name]+=b'changed'
            with self.subTest(file=name),patch.object(Path,'read_bytes',side_effect=AssertionError('no reads admitted')):
                with self.assertRaises(ValueError):replay.synthesize(before,self.inputs[case])

    def test_core_reads_only_immutable_original_after_explicit_inputs_loaded(self):
        read=Path.read_bytes;allowed=ROOT/'archive/dos-original/YTMAINT.EXE'
        def guard(path):
            if path!=allowed:raise AssertionError('core read target, witness, recipe or manifest: '+str(path))
            return read(path)
        for case in ('route-planet-neutral','route-mercenary-100000'):
            with self.subTest(case=case),patch.object(Path,'read_bytes',guard),patch.object(Path,'read_text',side_effect=AssertionError('no text target reads')):
                result,stats=replay.synthesize(self.before[case],self.inputs[case])
            self.assertEqual(result,self.modeled[case][0])
            self.assertEqual(stats['npcs']['final_rng_state'],self.modeled[case][1]['npcs']['final_rng_state'])

    def test_poisoned_raw_rng_is_not_a_synthesis_input(self):
        case='route-planet-neutral';ob=copy.deepcopy(self.observations[case])
        for event in ob['events']:
            for side in ('before','after'):event[side]['rng_raw']='00000000'
        poisoned=replay.inputs_from_observation(ob)
        self.assertEqual(poisoned,self.inputs[case])
        actual,stats=replay.synthesize(self.before[case],poisoned)
        self.assertEqual(actual,self.modeled[case][0])
        with self.assertRaises(ValueError):replay.validate_rng_witnesses(ob,stats)

    def test_extraction_preserves_the_original_observation(self):
        case='wanderer-two-occupied';ob=copy.deepcopy(self.observations[case]);saved=copy.deepcopy(ob)
        self.assertEqual(replay.inputs_from_observation(ob),self.inputs[case]);self.assertEqual(ob,saved)

    def test_every_derived_helper_and_final_rng_matches_independent_witnesses(self):
        for case,(_,stats) in self.modeled.items():
            with self.subTest(case=case):
                count=replay.validate_rng_witnesses(self.observations[case],stats)
                self.assertEqual(count,len(stats['npcs']['helper_seeds'])+2)

    def test_independent_audit_rejects_changed_calculated_state_and_inventory(self):
        case='route-mercenary-100000';known=self.modeled[case][1]
        changes=[lambda s:s['npcs']['helper_seeds'][0].update(old_state=0),
                 lambda s:s['npcs']['helper_seeds'][0].update(caller=0x437a),
                 lambda s:s['npcs']['helper_seeds'][0].update(timer='00000000'),
                 lambda s:s['npcs']['helper_seeds'].pop(),
                 lambda s:s['npcs'].update(final_rng_state=s['npcs']['final_rng_state']^1)]
        for mutate in changes:
            stats=copy.deepcopy(known);mutate(stats)
            with self.subTest(mutation=changes.index(mutate)):
                with self.assertRaises(ValueError):replay.validate_rng_witnesses(self.observations[case],stats)

    def test_missing_and_mutable_input_containers_fail_closed(self):
        case='route-planet-friendly';before=self.before[case];inputs=self.inputs[case]
        for invalid in (None,dict(clock=inputs.clock,schedule=inputs.schedule,planet_clocks=inputs.planet_clocks),replace(inputs,clock=None),replace(inputs,schedule=list(inputs.schedule)),replace(inputs,planet_clocks=list(inputs.planet_clocks))):
            with self.subTest(container=type(invalid).__name__):
                with self.assertRaises(ValueError):replay.synthesize(before,invalid)
        for invalid in (None,{n:b for n,b in before.items()if n!='YTNAME.DAT'},dict(before,extra=b''),dict(before,**{'YTDATA.DAT':bytearray(before['YTDATA.DAT'])})):
            with self.assertRaises(ValueError):replay.synthesize(invalid,inputs)

    def test_earlier_profile_keeps_its_unmeasured_world_boundary(self):
        for case in self.before:
            old=historical.inputs_from_observation(self.observations[case])
            with self.subTest(case=case):
                with self.assertRaisesRegex(ValueError,'unmeasured before-world'):
                    historical.synthesize(self.before[case],old)

    def test_source_helper_family_caller_and_order_are_computed(self):
        case='base-active-rejection';inputs=self.inputs[case];schedule=inputs.schedule
        for altered in (((schedule[0][0],0x437a,schedule[0][2]),)+schedule[1:],
                        (('h2',schedule[0][1],schedule[0][2]),)+schedule[1:],
                        (schedule[1],schedule[0])+schedule[2:]):
            with self.subTest(schedule=altered[:2]):
                with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,schedule=altered))

    def test_missing_and_extra_helpers_fail_closed(self):
        case='route-mercenary-100000';inputs=self.inputs[case];schedule=inputs.schedule
        for altered in ((),schedule[1:],schedule[:-1],schedule+(schedule[-1],)):
            with self.subTest(length=len(altered)):
                with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,schedule=altered))

    def test_malformed_helper_clocks_and_types_fail_closed(self):
        case='route-planet-friendly';inputs=self.inputs[case];first=inputs.schedule[0]
        for row in ((first[0],first[1],bytes(3)),(first[0],first[1],bytearray(first[2])),('h3',first[1],first[2]),(first[0],True,first[2]),list(first),first+(0,)):
            with self.subTest(row=row):
                with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,schedule=(row,)+inputs.schedule[1:]))

    def test_typed_source_planet_clock_inventory_matches_active_slots(self):
        for case,inputs in self.inputs.items():
            expected=tuple(4051+p[1]for p in self.recipe['cases'][case]['planets'])
            self.assertEqual(tuple(row[0]for row in inputs.planet_clocks),expected)
            self.assertTrue(all(type(row)is tuple and len(row)==3 and type(row[0])is int and type(row[1])is int and type(row[2])is bytes and len(row[2])==4 for row in inputs.planet_clocks))
        self.assertEqual(len(self.inputs['wanderer-two-occupied'].planet_clocks),2)
        self.assertEqual(self.inputs['route-mercenary-100000'].planet_clocks,())

    def test_missing_extra_duplicate_or_reordered_planet_clocks_fail_closed(self):
        case='wanderer-two-occupied';inputs=self.inputs[case];clocks=inputs.planet_clocks
        for altered in ((),clocks[:-1],clocks+(clocks[-1],),(clocks[0],clocks[0]),tuple(reversed(clocks))):
            with self.subTest(clocks=altered):
                with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,planet_clocks=altered))

    def test_unknown_planet_record_clock_fails_closed(self):
        case='route-planet-friendly';inputs=self.inputs[case];first=inputs.planet_clocks[0]
        for record in (4052,4054,4150,4151,True):
            with self.subTest(record=record):
                with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,planet_clocks=((record,first[1],first[2]),)))

    def test_malformed_planet_timer_row_or_raw_width_fails_closed(self):
        case='route-planet-friendly';inputs=self.inputs[case];first=inputs.planet_clocks[0]
        for row in (list(first),first+(0,),(first[0],True,first[2]),(first[0],first[1],bytes(3)),(first[0],first[1],bytearray(first[2]))):
            with self.subTest(row=row):
                with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,planet_clocks=(row,)))

    def test_planet_clocks_are_not_allowed_without_active_planets(self):
        case='route-mercenary-37';inputs=self.inputs[case]
        clocks=self.inputs['route-planet-friendly'].planet_clocks
        with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,planet_clocks=clocks))

    def test_seed_width_port_inventory_and_mutable_arrays_fail_closed(self):
        case='route-planet-friendly';inputs=self.inputs[case]
        for state in (-1,2**24,True):
            with self.subTest(seed=state):
                with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,clock=replace(inputs.clock,initial_state=state)))
        for key in ('port_dates','port_timer_minutes','h1_timers','h2_timers'):
            value=getattr(inputs.clock,key)
            for bad in (list(value),value[:-1]):
                with self.subTest(array=key,type=type(bad).__name__):
                    with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,clock=replace(inputs.clock,**{key:bad})))

    def test_conflicting_parallel_helper_arrays_cannot_override_schedule(self):
        case='route-planet-friendly';inputs=self.inputs[case]
        for key in ('h1_timers','h2_timers'):
            values=getattr(inputs.clock,key)
            with self.subTest(array=key):
                with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,clock=replace(inputs.clock,**{key:(bytes(4),)+values[1:]})))

    def test_calendar_rollback_is_not_silently_admitted(self):
        case='route-planet-friendly';inputs=self.inputs[case]
        clock=replace(inputs.clock,final_date=inputs.clock.startup_date-datetime.timedelta(days=1))
        with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,clock=clock))

    def test_initial_active_planet_draws_shift_real_rejection_candidates(self):
        expected={'wanderer-active-rejection':([2787,1310],[2689]),'base-active-rejection':([2787],[20,2308])}
        for case,(wanderer,base)in expected.items():
            npcs=self.modeled[case][1]['npcs']
            with self.subTest(case=case):
                self.assertEqual(npcs['wanderer_attempts'],wanderer);self.assertEqual(npcs['base_attempts'],base)
        self.assertEqual(self.modeled['wanderer-two-occupied'][1]['npcs']['wanderer_sector'],836)

    def test_ground_defense_spends_ground_without_capturing_or_erasing_planet(self):
        world=self.modeled['route-planet-neutral'][0]['YTDATA.DAT']
        self.assertEqual(field(world,4053,77),504975)
        self.assertEqual(field(world,4053,73),0)
        self.assertEqual(field(world,905,93),2)
        self.assertEqual(world[(4053-1)*137:(4053-1)*137+41],b'Route Haven'.ljust(41,b' '))
        for case in ('route-planet-friendly','wanderer-occupied','base-active-rejection'):
            self.assertEqual(field(self.modeled[case][0]['YTDATA.DAT'],4053,77),505000)

    def test_foreign_force_and_neutral_survivors_are_physical_not_pointer_duplicates(self):
        for case,xannor,mercenary,neutral in [('route-mercenary-37',9963,0,0),('route-mercenary-100000',5148,97525,0),('route-neutral-37',10000,0,37),('route-planet-neutral',4022,0,0)]:
            world=self.modeled[case][0]['YTDATA.DAT']
            with self.subTest(case=case):
                self.assertEqual((physical(world,-1),physical(world,-2),physical(world,0)),(xannor,mercenary,neutral))
        neutral=self.modeled['route-neutral-37'][0]['YTDATA.DAT']
        self.assertEqual((field(neutral,905,81),field(neutral,905,85)),(37,0))

    def test_public_casualties_conserve_actual_unique_sector_force(self):
        for case,(outputs,_)in self.modeled.items():
            news=outputs['YTNEWS.DAT'];world=outputs['YTDATA.DAT']
            planet=sum(int(x)for x in re.findall(rb' \*\*\* ([0-9]+) Xannor attacked the planet',news))
            summaries=[(int(x),int(m))for x,m in re.findall(rb'Mercenaries: lost ([0-9]+), dstrd ([0-9]+)',news)]
            xloss=planet+sum(x for x,_ in summaries);mloss=sum(m for _,m in summaries)
            with self.subTest(case=case):
                self.assertEqual(physical(world,-1)+xloss,physical(self.before[case]['YTDATA.DAT'],-1))
                self.assertEqual(physical(world,-2)+mloss,physical(self.before[case]['YTDATA.DAT'],-2))
                self.assertEqual(physical(world)+xloss+mloss,physical(self.before[case]['YTDATA.DAT']))
                self.assertEqual(outputs['YTRMSG.DAT'],b'')

    def test_winning_foreign_defense_clears_shared_pursuit_before_next_group(self):
        case='route-mercenary-37';npcs=self.modeled[case][1]['npcs']
        defenses=[event for event in npcs['events']if event['kind']=='defense']
        self.assertEqual([(event['group'],event['force'],event['defenders'])for event in defenses],[(2,0,27),(3,1390,0)])
        fourth=next(route for route in npcs['routes']if route['group']==4)
        self.assertEqual(fourth['preferred'],0)
        self.assertEqual(fourth['candidate_draws'],50)
        self.assertEqual(fourth['target'],fourth['fallback'])
        self.assertNotEqual(fourth['target'],854)
        self.assertEqual(replay.validate_rng_witnesses(self.observations[case],self.modeled[case][1]),len(npcs['helper_seeds'])+2)

    def test_native_misleading_foreign_labels_are_derived_not_corrected(self):
        small=self.modeled['route-mercenary-37'][0]['YTNEWS.DAT']
        self.assertIn(b'Mercenaries: lost 15, dstrd 10 (Xannor ftrs dstrd)',small)
        self.assertIn(b'Mercenaries: lost 22, dstrd 27 (Plyr ftrs dstrd)',small)
        large=self.modeled['route-mercenary-100000'][0]['YTNEWS.DAT']
        self.assertEqual(large.count(b'Mercenaries: lost'),19)
        self.assertNotIn(b'Plyr ftrs dstrd)',large)


class CompleteOccupiedComparisons(unittest.TestCase):
    def test_all_thirty_observations_match_all_six_targets_without_masks(self):
        report=replay.compare_cases()
        self.assertEqual(len(report['cases']),180)
        self.assertEqual(len(report['statistics']),30)
        self.assertEqual(len({row['case']for row in report['cases']}),10)
        self.assertEqual(sum(len(row['files'])for row in report['cases']),1080)
        for row in report['cases']:
            with self.subTest(case=row['case'],observation=row['observation'],target=row['target']):
                self.assertEqual(set(row['files']),set(replay.FILES));self.assertEqual(row['byte_mismatches'],0)
                self.assertEqual(row['files']['YTDATA.DAT']['observed_bytes'],4151*137)
                self.assertEqual(row['files']['YTDATA.DAT']['replayed_bytes'],4151*137)


if __name__=='__main__':unittest.main()
