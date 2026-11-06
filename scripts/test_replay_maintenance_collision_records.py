"""Before-only, chronology and complete-output regressions for collision replay."""
import copy
from dataclasses import fields, replace
import datetime
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_collision_records as replay
import replay_maintenance_clock_matrix as historical
from replay_maintenance_placement import before_from_recipe
import replay_qb_graph as qb

ROOT=Path(__file__).resolve().parents[1]


def rawfield(world,record,offset):
    start=(record-1)*137+offset
    return world[start:start+4]


class CollisionRecordProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=ROOT/'research/yt-maint/initial-controls/baseline-split'
        cls.base={n:gzip.decompress((source/('before-'+n+'.gz')).read_bytes())for n in replay.FILES[:3]}
        cls.recipe=json.loads((replay.DEFAULT/'recipe.json').read_text())
        cls.observations={case:json.loads(gzip.decompress((replay.DEFAULT/case/'observed-a/host-time.json.gz').read_bytes()))for case in cls.recipe['cases']}
        cls.inputs={case:replay.inputs_from_observation(observation)for case,observation in cls.observations.items()}
        cls.before={case:{**cls.base,'YTDATA.DAT':before_from_recipe(cls.recipe,case)}for case in cls.recipe['cases']}
        cls.modeled={case:replay.synthesize(cls.before[case],cls.inputs[case])for case in cls.recipe['cases']}

    def test_all_declared_before_worlds_are_admitted_independently_of_after_hashes(self):
        self.assertEqual(len(self.before),12)
        for case,before in self.before.items():
            with self.subTest(case=case):
                self.assertEqual(replay.ADMITTED_INPUTS[replay.SHA(before['YTDATA.DAT'])],case)
        self.assertEqual(set(f.name for f in fields(replay.Inputs)),{'clock','schedule'})

    def test_unmeasured_mutation_is_rejected_before_original_or_target_reads(self):
        case='duplicate-mobile';before=dict(self.before[case]);world=bytearray(before['YTDATA.DAT']);world[12345]^=1
        before['YTDATA.DAT']=bytes(world)
        with patch.object(Path,'read_bytes',side_effect=AssertionError('no filesystem reads admitted')):
            with self.assertRaisesRegex(ValueError,'unmeasured before-world'):
                replay.synthesize(before,self.inputs[case])

    def test_unmeasured_side_files_reject_before_original_or_target_reads(self):
        case='duplicate-hq'
        for name in('YTNAME.DAT','YTNEWS.DAT'):
            before=dict(self.before[case]);before[name]+=b'altered before-file'
            with self.subTest(file=name):
                with patch.object(Path,'read_bytes',side_effect=AssertionError('no filesystem reads admitted')):
                    with self.assertRaisesRegex(ValueError,'side-file'):
                        replay.synthesize(before,self.inputs[case])

    def test_core_reads_only_immutable_original_after_inputs_are_loaded(self):
        case='pointer-mercenary-sector';read=Path.read_bytes;allowed=ROOT/'archive/dos-original/YTMAINT.EXE'
        def guard(path):
            if path!=allowed:raise AssertionError('core read target, witness, probe or manifest: '+str(path))
            return read(path)
        with patch.object(Path,'read_bytes',guard),patch.object(Path,'read_text',side_effect=AssertionError('no text target reads')):
            actual,stats=replay.synthesize(self.before[case],self.inputs[case])
        expected,known=self.modeled[case]
        self.assertEqual(actual,expected)
        self.assertEqual(stats['npcs']['final_rng_state'],known['npcs']['final_rng_state'])

    def test_poisoned_captured_rng_states_never_become_synthesis_inputs(self):
        case='pointer-mercenary-sector';ob=copy.deepcopy(self.observations[case]);saved=copy.deepcopy(ob)
        for event in ob['events']:
            for side in('before','after'):event[side]['rng_raw']='00000000'
        poisoned=replay.inputs_from_observation(ob)
        self.assertEqual(poisoned,self.inputs[case])
        self.assertNotEqual(ob,saved)
        actual,stats=replay.synthesize(self.before[case],poisoned)
        self.assertEqual(actual,self.modeled[case][0])
        self.assertEqual(stats['npcs']['helper_seeds'],self.modeled[case][1]['npcs']['helper_seeds'])
        with self.assertRaisesRegex(ValueError,'independent witness'):
            replay.validate_rng_witnesses(ob,stats)

    def test_all_derived_helper_and_final_states_match_independent_witnesses(self):
        for case,(_,stats) in self.modeled.items():
            with self.subTest(case=case):
                count=replay.validate_rng_witnesses(self.observations[case],stats)
                self.assertEqual(count,len(stats['npcs']['helper_seeds'])+2)

    def test_witness_comparison_cannot_hide_changed_derived_states_or_inventory(self):
        case='duplicate-hq';known=self.modeled[case][1]
        changes=[lambda s:s['npcs']['helper_seeds'][0].update(old_state=0),
                 lambda s:s['npcs']['helper_seeds'][0].update(caller=0x437a),
                 lambda s:s['npcs']['helper_seeds'][0].update(family='h2'),
                 lambda s:s['npcs']['helper_seeds'][0].update(timer='00000000'),
                 lambda s:s['npcs']['helper_seeds'].pop(),
                 lambda s:s['npcs']['helper_seeds'].append(dict(s['npcs']['helper_seeds'][-1])),
                 lambda s:s['npcs'].update(final_rng_state=(s['npcs']['final_rng_state']^1))]
        for mutate in changes:
            stats=copy.deepcopy(known);mutate(stats)
            with self.subTest(mutate=changes.index(mutate)):
                with self.assertRaises(ValueError):
                    replay.validate_rng_witnesses(self.observations[case],stats)

    def test_witness_comparison_rejects_wrong_recipe_raw_width_and_final_disagreement(self):
        case='duplicate-hq';stats=self.modeled[case][1]
        for raw in ('00','zzzzzzzz','00000001',True):
            ob=copy.deepcopy(self.observations[case])
            for side in('before','after'):ob['events'][0][side]['rng_raw']=raw
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):replay.validate_rng_witnesses(ob,stats)
        ob=copy.deepcopy(self.observations[case]);ob['recipe']='host-dos-clock-matrix-observer-v1'
        with self.assertRaises(ValueError):replay.validate_rng_witnesses(ob,stats)

    def test_missing_rng_callback_disagreement_and_scoreboard_witness_fail_closed(self):
        from verify_maintenance_clock_matrix import event_pair
        case='duplicate-hq';stats=self.modeled[case][1]
        ob=copy.deepcopy(self.observations[case]);ob['events'][0]['before'].pop('rng_raw')
        with self.assertRaises((KeyError,ValueError)):replay.validate_rng_witnesses(ob,stats)
        ob=copy.deepcopy(self.observations[case]);ob['events'][0]['after']['rng_raw']='01000000'
        with self.assertRaisesRegex(ValueError,'callback'):replay.validate_rng_witnesses(ob,stats)
        ob=copy.deepcopy(self.observations[case]);score=[]
        for event in ob['events']:
            standard=copy.deepcopy(event)
            for side in('before','after'):standard[side].pop('rng_raw')
            if event_pair(standard,standard['ordinal']).get('role')=='score':score.append(event)
        self.assertEqual(len(score),2)
        wrong=(stats['npcs']['final_rng_state']^1).to_bytes(4,'little').hex()
        for side in('before','after'):score[0][side]['rng_raw']=wrong
        with self.assertRaisesRegex(ValueError,'final scoreboard'):
            replay.validate_rng_witnesses(ob,stats)

    def test_input_extraction_does_not_mutate_the_observation(self):
        case='wanderer-reject-three';ob=copy.deepcopy(self.observations[case]);saved=copy.deepcopy(ob)
        self.assertEqual(replay.inputs_from_observation(ob),self.inputs[case])
        self.assertEqual(ob,saved)

    def test_synthesis_requires_typed_inputs_and_complete_raw_before_inventory(self):
        case='duplicate-hq';before=self.before[case];inputs=self.inputs[case]
        invalid_inputs=[None,{'clock':inputs.clock,'schedule':inputs.schedule},replace(inputs,schedule=list(inputs.schedule)),replace(inputs,clock=None)]
        for invalid in invalid_inputs:
            with self.subTest(inputs=type(invalid).__name__):
                with self.assertRaises(ValueError):replay.synthesize(before,invalid)
        invalid_before=[None,{n:b for n,b in before.items()if n!='YTNAME.DAT'},dict(before,extra=b''),dict(before,YTDATA_DAT=before['YTDATA.DAT']),dict(before,**{'YTDATA.DAT':bytearray(before['YTDATA.DAT'])})]
        for invalid in invalid_before:
            with self.subTest(before=type(invalid).__name__):
                with self.assertRaises(ValueError):replay.synthesize(invalid,inputs)

    def test_source_chronology_rejects_wrong_family_caller_and_order(self):
        case='duplicate-hq';inputs=self.inputs[case];schedule=inputs.schedule
        self.assertEqual(schedule[0][0:2],('h1',0x1f88))
        for changed in [((schedule[0][0],0x437a,schedule[0][2]),)+schedule[1:],
                        (('h2',schedule[0][1],schedule[0][2]),)+schedule[1:],
                        (schedule[1],schedule[0])+schedule[2:]]:
            with self.subTest(schedule=changed[:2]):
                with self.assertRaisesRegex(ValueError,'chronolog'):
                    replay.synthesize(self.before[case],replace(inputs,schedule=changed))

    def test_missing_and_extra_source_helpers_fail_closed(self):
        case='duplicate-hq';inputs=self.inputs[case];schedule=inputs.schedule
        for changed in ((),schedule[1:],schedule[:-1],schedule+(schedule[-1],)):
            with self.subTest(length=len(changed)):
                with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,schedule=changed))

    def test_malformed_source_clock_width_types_and_labels_fail_closed(self):
        case='duplicate-hq';inputs=self.inputs[case];first=inputs.schedule[0]
        rows=[(first[0],first[1],bytes(3)),(first[0],first[1],bytearray(first[2])),('h3',first[1],first[2]),(first[0],True,first[2]),list(first),first+(0,)]
        for row in rows:
            with self.subTest(row=row):
                with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,schedule=(row,)+inputs.schedule[1:]))

    def test_seed_width_and_port_inventory_fail_closed(self):
        case='duplicate-hq';inputs=self.inputs[case]
        for state in(-1,2**24,True):
            with self.subTest(state=state):
                with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,clock=replace(inputs.clock,initial_state=state)))
        for clock in (replace(inputs.clock,port_dates=inputs.clock.port_dates[:-1]),replace(inputs.clock,port_timer_minutes=inputs.clock.port_timer_minutes[:-1])):
            with self.assertRaises(ValueError):replay.synthesize(self.before[case],replace(inputs,clock=clock))

    def test_mutable_or_conflicting_clock_arrays_cannot_override_source_schedule(self):
        case='duplicate-hq';inputs=self.inputs[case]
        for key in('port_dates','port_timer_minutes','h1_timers','h2_timers'):
            with self.subTest(array=key):
                with self.assertRaisesRegex(ValueError,'immutable'):
                    replay.synthesize(self.before[case],replace(inputs,clock=replace(inputs.clock,**{key:list(getattr(inputs.clock,key))})))
        for key in('h1_timers','h2_timers'):
            values=getattr(inputs.clock,key)
            with self.subTest(array=key):
                with self.assertRaisesRegex(ValueError,'schedule'):
                    replay.synthesize(self.before[case],replace(inputs,clock=replace(inputs.clock,**{key:(bytes(4),)+values[1:]})))

    def test_calendar_rollback_remains_rejected(self):
        case='duplicate-hq';inputs=self.inputs[case]
        bad=replace(inputs.clock,final_date=inputs.clock.startup_date-datetime.timedelta(days=1))
        with self.assertRaisesRegex(ValueError,'backward'):
            replay.synthesize(self.before[case],replace(inputs,clock=bad))

    def test_duplicate_pointer_loading_consumes_physical_force_only_once(self):
        for case in('duplicate-hq','duplicate-hq-chain'):
            with self.subTest(case=case):
                _,stats=self.modeled[case]
                self.assertEqual(stats['npcs']['normalized_total'],10000)
                self.assertEqual(stats['npcs']['helper_calls']['h2'],19)
                self.assertEqual(stats['auxiliary']['initial_physical_force'],10000)
                self.assertEqual(stats['auxiliary']['final_physical_force'],10000)
        world,stats=self.modeled['duplicate-mobile']
        self.assertEqual(stats['npcs']['normalized_total'],10037)
        self.assertEqual(stats['npcs']['helper_calls']['h2'],18)
        self.assertEqual(rawfield(world['YTDATA.DAT'],1051,81),bytes.fromhex('00008000'))
        self.assertEqual(rawfield(world['YTDATA.DAT'],1051,85),bytes.fromhex('00008000'))
        self.assertEqual(stats['auxiliary']['final_physical_force'],10037)

    def test_rejection_loops_reseed_at_the_computed_callsite_each_attempt(self):
        for case,attempts,base_attempts in [('wanderer-reject-two',[1095,1792,1295],1),('wanderer-reject-three',[1095,1792,1295,2787],1),('base-positive-fraction',[1095],2)]:
            with self.subTest(case=case):
                _,stats=self.modeled[case];npcs=stats['npcs']
                self.assertEqual(npcs['wanderer_attempts'],attempts)
                self.assertEqual(len(npcs['base_attempts']),base_attempts)
                selected=[r for r in npcs['helper_seeds']if r['caller']==0x1f88]
                self.assertEqual(len(selected),len(attempts))
                self.assertTrue(all(r['family']=='h1'for r in selected))
        _,two=self.modeled['wanderer-reject-two']
        self.assertEqual(len(two['npcs']['encounters']),9)
        self.assertGreater(two['auxiliary']['modeled_casualties'],0)
        self.assertEqual(two['auxiliary']['private_bytes'],0)

    def test_fractional_negative_and_raw_zero_gates_keep_native_destinations(self):
        for case,expected in [('wanderer-positive-fraction',1792),('wanderer-negative-link',1095),('wanderer-zero-residue',1095)]:
            with self.subTest(case=case):
                self.assertEqual(self.modeled[case][1]['npcs']['wanderer_sector'],expected)

    def test_mixed_owner_forces_are_not_invented_as_cached_xannor(self):
        neutral,neutral_stats=self.modeled['pointer-neutral-sector']
        merc,merc_stats=self.modeled['pointer-mercenary-sector']
        self.assertEqual(neutral_stats['npcs']['normalized_total'],10000)
        self.assertEqual(merc_stats['npcs']['normalized_total'],10000)
        self.assertEqual(qb.mbf.get(neutral['YTDATA.DAT'],3051,81),37)
        self.assertEqual(qb.mbf.get(neutral['YTDATA.DAT'],3051,85),0)
        tail=merc_stats['npcs']['mercenary']
        self.assertEqual(tail['force'],37)
        self.assertEqual(len(tail['activations']),2)
        self.assertEqual(tail['target_draws'],2)
        self.assertEqual(merc_stats['auxiliary']['scores'][-2],3700)
        self.assertEqual(rawfield(merc['YTDATA.DAT'],3051,81),bytes.fromhex('00002800'))

    def test_unpointed_friendly_force_is_preserved_until_destination_addition(self):
        outputs,stats=self.modeled['unpointed-friendly-merge']
        self.assertEqual(stats['npcs']['normalized_total'],10000)
        self.assertEqual(stats['auxiliary']['final_physical_force'],10037)
        self.assertEqual(qb.mbf.get(outputs['YTDATA.DAT'],1599,81),52)
        self.assertEqual(stats['auxiliary']['scores'][-1],1003700)

    def test_historical_matrix_recipe_six_files_are_unchanged(self):
        path=ROOT/'research/yt-maint/clock-matrix-controls/next-day/observed-a/host-time.json.gz'
        observation=json.loads(gzip.decompress(path.read_bytes()))
        inputs=replay.inputs_from_observation(observation)
        actual,_=replay.synthesize(self.base,inputs)
        expected,_=historical.synthesize(self.base,inputs.clock)
        self.assertEqual(actual,expected)

    def test_historical_strict_late_gap_stays_explicit_while_new_profile_is_exact(self):
        folder=ROOT/'research/yt-maint/clock-matrix-controls/late/observed-a'
        observation=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()))
        inputs=replay.inputs_from_observation(observation)
        with self.assertRaises(historical.UnsupportedProfile) as caught:
            historical.synthesize(self.base,inputs.clock)
        self.assertEqual(caught.exception.context['rng_state'],0xEA7184)
        actual,stats=replay.synthesize(self.base,inputs)
        expected={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in replay.FILES}
        self.assertEqual(actual,expected)
        self.assertEqual(len(stats['npcs']['encounters']),18)


class CompleteCollisionComparisons(unittest.TestCase):
    def test_all_36_observations_match_all_six_targets_without_masks(self):
        report=replay.compare_cases()
        self.assertEqual(len(report['cases']),216)
        self.assertEqual(len(report['statistics']),36)
        self.assertEqual(len({r['case']for r in report['cases']}),12)
        self.assertEqual(sum(len(r['files'])for r in report['cases']),1296)
        for row in report['cases']:
            with self.subTest(case=row['case'],observation=row['observation'],target=row['target']):
                self.assertEqual(set(row['files']),set(replay.FILES))
                self.assertEqual(row['byte_mismatches'],0)
                self.assertEqual(row['files']['YTDATA.DAT']['observed_bytes'],4151*137)
                self.assertEqual(row['files']['YTDATA.DAT']['replayed_bytes'],4151*137)


if __name__=='__main__':unittest.main()
