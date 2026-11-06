"""Before-only evolved combat chains, native equality and hostile input properties."""
import builtins
import copy
from dataclasses import fields,replace
import datetime
import gzip
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_evolved_combat_records as replay
import replay_maintenance_occupied_records as occupied
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
CASES=('route-mercenary-37','route-mercenary-100000','route-neutral-37','route-planet-neutral')
FINGERPRINTS={
 'route-mercenary-37':'40947d888c7bd9192acfc12d2531d6414fe6392c9c815ead42ea4d28ef6325bf',
 'route-mercenary-100000':'0e5d8934af1be3debc72708ecdd3e2825a2c4000398253fc8b793340907669a6',
 'route-neutral-37':'277c3cadeea74b02596c3d832566ff7de5b39a7a5a1b8edbd9a2ac563edd31b6',
 'route-planet-neutral':'f545d697b28d93910407cfeb7baac96666062ebe3cb5ac3334d6a3e85f5e45b7',
}


def force(world,owner):
    return sum(int(mbf.get(world,51+s,81))for s in range(1,3001)if mbf.get(world,51+s,85)==owner)


class EvolvedCombatChainProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before={};cls.observations={};cls.inputs={};cls.outputs={};cls.stats={}
        for case in CASES:
            cls.before[case]=occupied.before_inputs(case)
            ob=(json.loads(gzip.decompress((occupied.DEFAULT/case/'observed-a/host-time.json.gz').read_bytes())),)+tuple(json.loads(gzip.decompress((replay.DEFAULT/case/f'child-{i}/observed-a/host-time.json.gz').read_bytes()))for i in(1,2))
            cls.observations[case]=ob;cls.inputs[case]=tuple(replay.inputs_from_observation(row)for row in ob)
            cls.outputs[case],cls.stats[case]=replay.synthesize_chain(cls.before[case],cls.inputs[case])

    def reject(self,inputs,case='route-mercenary-100000'):
        with self.assertRaises((ValueError,AssertionError)):replay.synthesize_chain(self.before[case],inputs)

    def test_144_complete_native_comparisons_have_no_masks_or_mismatches(self):
        synthesize=replay.synthesize_chain;read=Path.read_bytes;events=[]
        def modeled(before,inputs):
            result=synthesize(before,inputs);events.append('chain-complete');return result
        def guarded(path):
            if path.name.startswith('after-'):
                if not events:raise AssertionError('native child target opened before full chain')
                events.append('native-target')
            return read(path)
        with patch.object(replay,'synthesize_chain',side_effect=modeled),patch.object(Path,'read_bytes',guarded):report=replay.compare_cases()
        self.assertEqual(events,sum((['chain-complete']+['native-target']*72 for _ in range(12)),[]))
        self.assertEqual((len(report['cases']),len(report['statistics'])),(144,24))
        self.assertEqual(sum(len(r['files'])for r in report['cases']),864)
        self.assertTrue(all(r['byte_mismatches']==0 for r in report['cases']))
        key='case'if 'case'in report['cases'][0]else'profile'
        self.assertEqual({(r[key],r['child'],r['observation'],r['target'])for r in report['cases']},
                         {(c,s,o,t)for c in CASES for s in(1,2)for o in('observed-a','observed-b','observed-c')for t in replay.MODES})

    def test_only_four_measured_initial_fingerprints_and_three_file_inputs(self):
        self.assertEqual(set(replay.CASES),set(CASES))
        self.assertEqual({f.name for f in fields(replay.Inputs)},{'clock','schedule','planet_clocks'})
        for case in CASES:
            self.assertEqual(set(self.before[case]),set(replay.FILES[:3]));self.assertEqual(replay.SHA(self.before[case]['YTDATA.DAT']),FINGERPRINTS[case])

    def test_actual_zero_one_then_three_four_planet_source_slots(self):
        for case in CASES:
            rows=self.inputs[case]
            self.assertEqual([r.clock.startup_date for r in rows],[datetime.date(2026,11,d)for d in(2,3,4)])
            self.assertEqual([r.clock.news_clock for r in rows],['00:00:00']*3)
            self.assertEqual(tuple(r[0]for r in rows[0].planet_clocks),(4053,)if case=='route-planet-neutral'else())
            expected=(4052,4053,4150,4151)if case=='route-planet-neutral'else(4052,4150,4151)
            self.assertEqual(tuple(r[0]for r in rows[1].planet_clocks),expected);self.assertEqual(tuple(r[0]for r in rows[2].planet_clocks),expected)
            self.assertTrue(all(type(raw)is bytes and len(raw)==4 for row in rows for _,_,raw in row.schedule))

    def test_modeled_objects_are_passed_directly_through_three_stages(self):
        case='route-mercenary-100000';old=occupied.synthesize;new=replay._synthesize_day;seen=[];made=[]
        def run(real,before,inputs):
            seen.append(before);result=real(before,inputs);made.append(result[0]);return result
        with patch.object(occupied,'synthesize',side_effect=lambda b,i:run(old,b,i)),patch.object(replay,'_synthesize_day',side_effect=lambda b,i:run(new,b,i)):
            outputs,stats=replay.synthesize_chain(self.before[case],self.inputs[case])
        self.assertIs(seen[0],self.before[case]);self.assertIs(seen[1],made[0]);self.assertIs(seen[2],made[1])
        self.assertEqual(outputs,self.outputs[case]);self.assertEqual(stats,self.stats[case]);self.assertEqual(set(seen[1]),set(replay.FILES))

    def test_marker_handoffs_cannot_be_replaced_by_captured_children(self):
        case='route-planet-neutral';seen=[];made=[]
        def synthetic(before,inputs):
            seen.append(before);result={n:before.get(n,b'')for n in replay.FILES};result['YTNEWS.DAT']=f'modeled-only-{len(made)}'.encode();made.append(result)
            return result,{'stage':len(made)}
        with patch.object(occupied,'synthesize',side_effect=synthetic),patch.object(replay,'_synthesize_day',side_effect=synthetic),patch.object(Path,'read_bytes',side_effect=AssertionError('native child read')):
            outputs,stats=replay.synthesize_chain(self.before[case],self.inputs[case])
        self.assertIs(seen[1],made[0]);self.assertIs(seen[2],made[1]);self.assertEqual(seen[2]['YTNEWS.DAT'],b'modeled-only-1')
        self.assertEqual(outputs,tuple(made));self.assertEqual([r['stage']for r in stats],[1,2,3])

    def test_entire_chain_reads_only_original_executable(self):
        allowed=ROOT/'archive/dos-original/YTMAINT.EXE';read=Path.read_bytes;original_open=io.open
        def byte_guard(path):
            if path!=allowed:raise AssertionError('core target/probe read: '+str(path))
            return read(path)
        def open_guard(path,*args,**kwargs):
            if Path(path)!=allowed:raise AssertionError('core target/probe open: '+str(path))
            return original_open(path,*args,**kwargs)
        case='route-mercenary-100000'
        with patch.object(Path,'read_bytes',byte_guard),patch.object(Path,'read_text',side_effect=AssertionError('captured text read')),patch.object(io,'open',side_effect=open_guard),patch.object(builtins,'open',side_effect=open_guard):
            outputs,stats=replay.synthesize_chain(self.before[case],self.inputs[case])
        self.assertEqual(outputs,self.outputs[case]);self.assertEqual(stats,self.stats[case])

    def test_poisoned_observed_rng_neither_seeds_nor_changes_modeled_chain(self):
        for case in CASES:
            observations=copy.deepcopy(self.observations[case])
            for ob in observations:
                for event in ob['events']:
                    for side in('before','after'):event[side]['rng_raw']='00000000'
            inputs=tuple(replay.inputs_from_observation(ob)for ob in observations);self.assertEqual(inputs,self.inputs[case])
            if case=='route-mercenary-100000':
                outputs,stats=replay.synthesize_chain(self.before[case],inputs);self.assertEqual(outputs,self.outputs[case]);self.assertEqual(stats,self.stats[case])
            for ob,row in zip(observations,self.stats[case]):
                with self.assertRaises(ValueError):replay.validate_rng_witnesses(ob,row)

    def test_input_extraction_preserves_original_observations(self):
        for case in CASES:
            ob=copy.deepcopy(self.observations[case]);snapshot=copy.deepcopy(ob)
            self.assertEqual(tuple(replay.inputs_from_observation(o)for o in ob),self.inputs[case]);self.assertEqual(ob,snapshot)

    def test_all_helper_and_final_rng_states_are_independent_witnesses(self):
        for case in CASES:
            for stage,(ob,row)in enumerate(zip(self.observations[case],self.stats[case])):
                self.assertEqual(len(row['npcs']['helper_seeds']),len(self.inputs[case][stage].schedule))
                self.assertEqual(replay.validate_rng_witnesses(ob,row),len(self.inputs[case][stage].schedule)+2)
                bad=copy.deepcopy(row);bad['npcs']['final_rng_state']^=1
                with self.assertRaises(ValueError):replay.validate_rng_witnesses(ob,bad)
                for index in {0,len(row['npcs']['helper_seeds'])//2,len(row['npcs']['helper_seeds'])-1}:
                    bad=copy.deepcopy(row);bad['npcs']['helper_seeds'][index]['old_state']^=1
                    with self.subTest(case=case,stage=stage,helper=index),self.assertRaises(ValueError):replay.validate_rng_witnesses(ob,bad)

    def test_unknown_initial_world_names_or_news_reject_before_reads(self):
        case='route-mercenary-100000'
        for n in replay.FILES[:3]:
            before=dict(self.before[case]);before[n]+=b'changed'
            with self.subTest(file=n),patch.object(Path,'read_bytes',side_effect=AssertionError('unadmitted read')):
                with self.assertRaises(ValueError):replay.synthesize_chain(before,self.inputs[case])

    def test_nonselected_occupied_initial_case_is_not_silently_admitted(self):
        before=occupied.before_inputs('route-planet-friendly')
        with patch.object(Path,'read_bytes',side_effect=AssertionError('unadmitted read')):
            with self.assertRaises(ValueError):replay.synthesize_chain(before,self.inputs['route-planet-neutral'])

    def test_mutable_or_incomplete_initial_and_input_containers_reject(self):
        case='route-mercenary-100000';initial=self.before[case];inputs=self.inputs[case]
        for before in(None,self.outputs[case][0],dict(initial,extra=b''),{n:b for n,b in initial.items()if n!='YTNEWS.DAT'},dict(initial,**{'YTDATA.DAT':bytearray(initial['YTDATA.DAT'])})):
            with self.assertRaises(ValueError):replay.synthesize_chain(before,inputs)
        for values in(None,list(inputs),inputs[:2],inputs+(inputs[-1],),(None,)+inputs[1:],(replace(inputs[0],clock=None),)+inputs[1:]):self.reject(values)

    def test_reversed_repeated_or_unknown_source_dates_reject(self):
        inputs=self.inputs['route-mercenary-100000'];self.reject(inputs[::-1]);self.reject((inputs[0],)*3)
        for index,date in((0,datetime.date(2026,11,1)),(1,datetime.date(2026,11,5)),(2,datetime.date(2026,11,5))):
            values=list(inputs);values[index]=replace(inputs[index],clock=replace(inputs[index].clock,startup_date=date));self.reject(tuple(values))

    def test_wrong_source_phase_date_or_nonmidnight_profile_rejects(self):
        inputs=self.inputs['route-mercenary-100000'];child=inputs[1]
        for clock in(replace(child.clock,news_clock='00:00:09'),replace(child.clock,score_clock='00:00:09'),replace(child.clock,score_date=datetime.date(2026,11,2)),replace(child.clock,port_dates=(datetime.date(2026,11,2),)*1000),replace(child.clock,final_date=datetime.date(2026,11,2))):
            self.reject((inputs[0],replace(child,clock=clock),inputs[2]))

    def test_mutable_child_clock_arrays_and_schedule_rows_reject(self):
        inputs=self.inputs['route-mercenary-100000'];child=inputs[1];s=child.schedule
        for row in(replace(child,schedule=list(s)),replace(child,planet_clocks=list(child.planet_clocks)),replace(child,clock=replace(child.clock,port_dates=list(child.clock.port_dates))),replace(child,schedule=(list(s[0]),)+s[1:]),replace(child,schedule=((s[0][0],True,s[0][2]),)+s[1:])):
            self.reject((inputs[0],row,inputs[2]))

    def test_bad_startup_state_and_raw_timer_widths_are_not_coerced(self):
        inputs=self.inputs['route-mercenary-100000'];child=inputs[1]
        for clock in(replace(child.clock,initial_state=-1),replace(child.clock,initial_state=True),replace(child.clock,initial_state=2**24),replace(child.clock,port_timer_minutes=(bytes(3),)*1000),replace(child.clock,port_dates=child.clock.port_dates[:-1])):
            self.reject((inputs[0],replace(child,clock=clock),inputs[2]))

    def test_child_helper_caller_order_and_clock_completion_are_computed(self):
        inputs=self.inputs['route-mercenary-100000'];child=inputs[1];s=child.schedule
        for row in(replace(child,schedule=((s[0][0],0x437a,s[0][2]),)+s[1:]),replace(child,schedule=(s[1],s[0])+s[2:]),replace(child,schedule=s[:-1],clock=replace(child.clock,h1_timers=child.clock.h1_timers[:-1]))):
            self.reject((inputs[0],row,inputs[2]))

    def test_raw_source_caller_and_observer_identity_are_authenticated(self):
        case='route-mercenary-100000'
        ob=copy.deepcopy(self.observations[case][1]);event=next(e for e in ob['events']if e['before']['runtime_signature']is not None)
        for side in('before','after'):event[side]['caller_code']='00'
        with self.assertRaises((ValueError,AssertionError)):replay.inputs_from_observation(ob)
        for change in(dict(observe=False),dict(exit_code=1),dict(dropped=1),dict(errors=['lost']),dict(events=[])):
            ob=copy.deepcopy(self.observations[case][1]);ob.update(change)
            with self.assertRaises((ValueError,AssertionError)):replay.inputs_from_observation(ob)

    def test_actual_planet_clocks_cannot_be_replaced_by_zero_or_wrong_inventory(self):
        inputs=self.inputs['route-mercenary-100000'];child=inputs[1];p=child.planet_clocks
        for rows in((),p[::-1],p+(p[0],),((p[0][0],p[0][1],bytes(3)),)+p[1:]):
            self.reject((inputs[0],replace(child,planet_clocks=rows),inputs[2]))

    def test_existing_homes_require_no_invented_creation_clocks(self):
        inputs=self.inputs['route-mercenary-100000'];child=inputs[1]
        for name,value in(('wanderer_date',child.clock.startup_date),('xannoron_date',child.clock.startup_date),('base_date',child.clock.startup_date),('xannoron_timer',bytes(4))):
            self.reject((inputs[0],replace(child,clock=replace(child.clock,**{name:value})),inputs[2]))

    def test_every_modeled_handoff_preserves_names_and_rotates_own_news(self):
        for case in CASES:
            previous=self.before[case]
            for output in self.outputs[case]:
                self.assertEqual(set(output),set(replay.FILES));self.assertTrue(all(type(b)is bytes for b in output.values()))
                self.assertEqual(output['YTNAME.DAT'],previous['YTNAME.DAT']);self.assertEqual(output['YTYNEWS.DAT'],previous['YTNEWS.DAT']);self.assertEqual(output['YTRMSG.DAT'],b'');previous=output

    def test_actual_faction_losses_and_neutral_gate_persist_through_chain(self):
        expected={
            'route-mercenary-37':[(9963,0,0)]*3,
            'route-mercenary-100000':[(5148,97525,0),(5148,97525,0),(4966,97337,0)],
            'route-neutral-37':[(10000,0,37)]*3,
            'route-planet-neutral':[(4022,0,0),(1408,0,0),(616,0,0)],
        }
        for case,totals in expected.items():
            self.assertEqual([tuple(force(o['YTDATA.DAT'],owner)for owner in(-1,-2,0))for o in self.outputs[case]],totals)
        for output in self.outputs['route-neutral-37']:
            self.assertEqual(mbf.get(output['YTDATA.DAT'],51+854,81),37);self.assertEqual(mbf.get(output['YTDATA.DAT'],51+854,85),0)

    def test_stale_killed_group_pointer_is_not_canonicalized(self):
        first,second=self.outputs['route-mercenary-100000'][1:]
        self.assertEqual(mbf.get(first['YTDATA.DAT'],51+8,105),673);self.assertEqual(mbf.get(first['YTDATA.DAT'],51+673,81),182)
        self.assertEqual(mbf.get(second['YTDATA.DAT'],51+8,105),109);self.assertEqual(mbf.get(second['YTDATA.DAT'],51+109,81),0)
        self.assertEqual(force(first['YTDATA.DAT'],-1)-force(second['YTDATA.DAT'],-1),182)

    def test_surviving_mercenary_battle_has_printed_victim_but_unprinted_own_loss(self):
        output=self.outputs['route-mercenary-100000'][2];news=output['YTNEWS.DAT']
        self.assertIn(b' *** 97525 Mercenaries attacking 182 fighters beloning to The Xannor!\r\n *** The Mercenaries Won!',news)
        self.assertNotIn(b'188',news);self.assertEqual(force(self.outputs['route-mercenary-100000'][1]['YTDATA.DAT'],-2)-force(output['YTDATA.DAT'],-2),188)
        locations=[s for s in range(1,3001)if mbf.get(output['YTDATA.DAT'],51+s,81)>0 and mbf.get(output['YTDATA.DAT'],51+s,85)==-2]
        self.assertEqual(locations,[2368])

    def test_strong_foreign_force_reactivation_and_surviving_ground_handoffs(self):
        # The physical starts/ends of each child are independent of cached group pointers.
        worlds=[o['YTDATA.DAT']for o in self.outputs['route-mercenary-100000']]
        self.assertEqual([[s for s in range(1,3001)if mbf.get(w,51+s,81)>0 and mbf.get(w,51+s,85)==-2]for w in worlds],[[2689],[2645],[2368]])
        self.assertEqual([mbf.get(o['YTDATA.DAT'],4053,77)for o in self.outputs['route-planet-neutral']],[504975,510002,515083])
        for output in self.outputs['route-planet-neutral']:
            world=output['YTDATA.DAT'];self.assertEqual(mbf.get(world,51+854,93),2);self.assertEqual(mbf.get(world,4053,73),0)

    def test_descending_mutable_mercenary_scan_reactivates_actual_arrival(self):
        rows=self.stats['route-mercenary-100000']
        for index,origins,targets in((1,[2689,1037],[1037,2645]),(2,[2645,1963],[1963,2368])):
            mercenary=rows[index]['npcs']['mercenary'];moves=mercenary['activations']
            self.assertEqual([m['origin']for m in moves],origins)
            self.assertEqual([m['target']for m in moves],targets)
            self.assertEqual(moves[0]['target'],moves[1]['origin'])
            self.assertLess(moves[1]['origin'],moves[0]['origin']);self.assertGreater(moves[1]['target'],moves[1]['origin'])
        mercenary=rows[2]['npcs']['mercenary'];self.assertEqual((mercenary['initial_force'],mercenary['force'],mercenary['losses']),(97525,97337,188))
        event=mercenary['events'][0]
        self.assertEqual((event['sector'],event['initial_defenders'],event['defenders'],event['defender_losses']),(109,182,0,182))
        self.assertEqual(event['rng_draws'],event['rounds']+1)
        self.assertIn(109,mercenary['activations'][0]['route'])

    def test_initial_and_typed_inputs_remain_immutable_after_synthesis(self):
        case='route-mercenary-100000';before=dict(self.before[case]);inputs=copy.deepcopy(self.inputs[case])
        replay.synthesize_chain(self.before[case],self.inputs[case]);self.assertEqual(self.before[case],before);self.assertEqual(self.inputs[case],inputs)


if __name__=='__main__':unittest.main()
