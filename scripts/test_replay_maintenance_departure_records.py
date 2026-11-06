"""Before-only modeled fixture handoffs and unmasked departure clock comparisons."""
import builtins
import copy
from dataclasses import replace,fields
import datetime
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_departure_records as replay
from replay_maintenance_collision_records import validate_rng_witnesses
from replay_qb_graph import mbf


def observation(p):return json.loads(gzip.decompress(p.read_bytes()))


class DepartureRecords(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=replay.initial_before();cls.obs={};cls.inputs={};cls.outputs={};cls.stats={}
        for case in replay.CASES:
            obs=tuple(observation(p)for p in replay.observation_paths(case,'observed-a'))
            values=tuple((replay.combat.inputs_from_observation if i<3 else replay.inputs_from_observation)(o)for i,o in enumerate(obs))
            cls.obs[case]=obs;cls.inputs[case]=values
            cls.outputs[case],cls.stats[case]=replay.synthesize_chain(cls.before,values,case)

    def reject(self,inputs,case='vacant-origin',before=None):
        with self.assertRaises((ValueError,AssertionError,TypeError)):replay.synthesize_chain(self.before if before is None else before,inputs,case)

    def test_every_complete_chain_precedes_targets_and_all_raw_comparisons_are_retained(self):
        real=replay.synthesize_chain;read=Path.read_bytes;events=[]
        def modeled(*args):
            result=real(*args);events.append('five-complete');return result
        def guarded(path):
            if path.name.startswith('after-'):
                self.assertTrue(events);events.append('target')
            return read(path)
        with patch.object(replay,'synthesize_chain',side_effect=modeled),patch.object(Path,'read_bytes',guarded):report=replay.compare_cases()
        self.assertEqual(events,sum((['five-complete']+['target']*72 for _ in range(24)),[]))
        self.assertEqual((len(report['cases']),len(report['statistics'])),(288,48))
        audit=replay.assert_comparisons(report)
        self.assertEqual(audit,dict(exact_comparisons=270,disclosed_unequal_comparisons=18,normalized_bytes=0))
        direct=[r for r in report['cases']if r['observation']==r['target']]
        self.assertEqual(len(direct),48);self.assertTrue(all(r['byte_mismatches']==0 for r in direct))
        self.assertEqual(sum(row['byte_mismatches']for row in report['cases']),1647)
        self.assertEqual(sum(v['byte_mismatches']==0 for row in report['cases']for v in row['files'].values()),1710)
        self.assertEqual({(r['case'],r['child'],r['observation'],r['target'])for r in report['cases']},
                         {(p,c,o,t)for p in replay.CASES for c in(1,2)for o in('observed-a','observed-b','observed-c')for t in replay.MODES})

    def test_prefix_fixture_and_children_are_actual_modeled_objects(self):
        realprefix=replay.combat.synthesize_chain;realfixture=replay.apply_fixture;realchild=replay._synthesize_day
        prefix=[];fixtures=[];seen=[];made=[]
        def pre(*args):
            result=realprefix(*args);prefix.extend(result[0]);return result
        def fixture(parent,case):
            self.assertIs(parent,prefix[2]);result=realfixture(parent,case);fixtures.append(result[0]);return result
        def child(parent,i):
            seen.append(parent);result=realchild(parent,i);made.append(result[0]);return result
        case='occupied-friendly-second-four'
        with patch.object(replay.combat,'synthesize_chain',side_effect=pre),patch.object(replay,'apply_fixture',side_effect=fixture),patch.object(replay,'_synthesize_day',side_effect=child):
            out,_=replay.synthesize_chain(self.before,self.inputs[case],case)
        self.assertIs(seen[0],fixtures[0]);self.assertIs(seen[1],made[0]);self.assertIs(out[3],made[0]);self.assertIs(out[4],made[1]);self.assertEqual(out,self.outputs[case])

    def test_modeled_parent_markers_are_not_replaced_by_captured_handoffs(self):
        marker=b'modeled-journal-only';case='vacant-origin';seen=[]
        prefix=tuple({n:(marker if n=='YTNEWS.DAT'else self.outputs[case][i][n])for n in replay.FILES}for i in range(3))
        def child(parent,i):
            seen.append(parent);return {**parent,'YTNEWS.DAT':parent['YTNEWS.DAT']+b'!'},{}
        with patch.object(replay.combat,'synthesize_chain',return_value=(prefix,({},{},{}))),patch.object(replay,'_synthesize_day',side_effect=child):
            out,_=replay.synthesize_chain(self.before,self.inputs[case],case)
        self.assertEqual(seen[0]['YTNEWS.DAT'],marker);self.assertEqual(seen[1]['YTNEWS.DAT'],marker+b'!');self.assertEqual(out[4]['YTNEWS.DAT'],marker+b'!!')

    def test_core_opens_only_original_maintenance_bytes(self):
        read=Path.read_bytes;opened=Path.open
        def allowed_open(path,*args,**kwargs):
            if path!=replay.ROOT/'archive/dos-original/YTMAINT.EXE':raise AssertionError('core open '+str(path))
            return opened(path,*args,**kwargs)
        def allowed(path):
            if path!=replay.ROOT/'archive/dos-original/YTMAINT.EXE':raise AssertionError('core read '+str(path))
            return read(path)
        for case in('occupied-second-four','occupied-friendly-second-four'):
            with patch.object(Path,'read_bytes',allowed),patch.object(Path,'open',allowed_open),patch.object(builtins,'open',side_effect=AssertionError('unqualified open')),patch.object(replay,'initial_before',side_effect=AssertionError('comparison loader')):
                out,_=replay.synthesize_chain(self.before,self.inputs[case],case)
            self.assertEqual(out,self.outputs[case])

    def test_pure_sixteen_edit_fixture_matches_independent_recipe_once(self):
        parent=self.outputs['vacant-origin'][2];saved=copy.deepcopy(parent)
        from verify_maintenance_departure_merge import fixture_inputs
        for case in replay.CASES:
            result,edits=replay.apply_fixture(parent,case)
            self.assertEqual(result,fixture_inputs(case,'observed-a'));self.assertEqual(len(edits),16)
            self.assertEqual(parent,saved);self.assertTrue(all(result[n]is parent[n]for n in replay.FILES if n!='YTDATA.DAT'))
            self.assertEqual(self.stats[case][3]['fixture_edits'],edits);self.assertEqual(self.stats[case][4]['fixture_edits'],())
            native=json.loads((replay.DEFAULT/case/'child-1/observed-a/capture.json').read_text())
            self.assertEqual(list(edits),native['fixture_edits'])

    def test_original_world_and_immutable_five_day_input_admission(self):
        case='vacant-origin';inputs=self.inputs[case]
        self.assertEqual({f.name for f in fields(replay.Inputs)},{'clock','schedule','planet_clocks'})
        for name in('unknown','pickup',True):self.reject(inputs,name)
        for before in({**self.before,'YTRMSG.DAT':b''},{**self.before,'YTNAME.DAT':b'unknown'},{**self.before,'YTDATA.DAT':self.before['YTDATA.DAT'][:-1]+b'!'},self.outputs[case][2]):self.reject(inputs,before=before)
        for values in(list(inputs),inputs[:-1],inputs+(inputs[-1],)):self.reject(values)

    def test_fixture_rejects_unknown_origin_or_occupied_slot_without_mutation(self):
        for r,o,value in((1,81,307),(2419,81,97336),(2419,85,0),(3051,81,1),(3051,93,1),(3050,93,1),(4054,85,1)):
            parent=dict(self.outputs['vacant-origin'][2]);w=bytearray(parent['YTDATA.DAT']);mbf.put(w,r,o,value);parent['YTDATA.DAT']=bytes(w);saved=copy.deepcopy(parent)
            with self.subTest(record=r,offset=o),self.assertRaises(ValueError):replay.apply_fixture(parent,'vacant-origin')
            self.assertEqual(parent,saved)

    def test_source_publication_dates_and_distinct_score_clock_are_explicit(self):
        inputs=self.inputs['vacant-origin'];self.assertEqual((inputs[3].clock.news_clock,inputs[3].clock.score_clock),('00:00:00','00:00:01'))
        self.reject(inputs[:3]+(inputs[4],inputs[3]))
        for name,value in(('startup_date',datetime.date(2026,11,7)),('news_clock','00:00:01'),('score_clock','00:00:00'),('final_date',datetime.date(2026,11,6)),('news_date',datetime.date(2026,11,6))):
            row=replace(inputs[3],clock=replace(inputs[3].clock,**{name:value}));self.reject(inputs[:3]+(row,inputs[4]))
        for case in('occupied-second-two','occupied-second-four'):
            values=self.inputs[case];row=replace(values[3],clock=replace(values[3].clock,news_clock='00:00:00'))
            self.reject(values[:3]+(row,values[4]),case)

    def test_mutable_clocks_wrong_callers_and_extra_helpers_fail_closed(self):
        case='occupied-second-two';values=self.inputs[case];row=values[3]
        for name in('port_dates','port_timer_minutes','h1_timers','h2_timers'):
            bad=replace(row,clock=replace(row.clock,**{name:list(getattr(row.clock,name))}));self.reject(values[:3]+(bad,values[4]),case)
        for schedule in(list(row.schedule),row.schedule[:-1],((row.schedule[0][0],0x9999,row.schedule[0][2]),)+row.schedule[1:]):
            self.reject(values[:3]+(replace(row,schedule=schedule),values[4]),case)
        self.reject(values[:3]+(replace(row,planet_clocks=list(row.planet_clocks)),values[4]),case)
        self.reject(values[:3]+(replace(row,clock=replace(row.clock,initial_state=True)),values[4]),case)

    def test_forged_consistent_but_unmeasured_helper_times_fail_before_synthesis(self):
        case='occupied-second-two';values=self.inputs[case];row=values[3]
        for timer in(mbf.enc(-1),mbf.enc(60),mbf.enc(720)):
            schedule=((row.schedule[0][0],row.schedule[0][1],timer),)+row.schedule[1:]
            clock=replace(row.clock,h1_timers=tuple(r[2]for r in schedule if r[0]=='h1'),h2_timers=tuple(r[2]for r in schedule if r[0]=='h2'))
            self.reject(values[:3]+(replace(row,clock=clock,schedule=schedule),values[4]),case)

    def test_observed_rng_bytes_are_witnesses_not_synthesis_inputs(self):
        for case in replay.CASES:
            changed=copy.deepcopy(self.obs[case][3:])
            for ob in changed:
                for event in ob['events']:
                    for side in('before','after'):event[side]['rng_raw']='ffffffff'
            inputs=self.inputs[case][:3]+tuple(replay.inputs_from_observation(o)for o in changed)
            self.assertEqual(inputs,self.inputs[case]);out,_=replay.synthesize_chain(self.before,inputs,case);self.assertEqual(out,self.outputs[case])

    def test_every_helper_and_final_rng_witness_is_audited(self):
        for case in replay.CASES:
            for i in(3,4):
                stats=self.stats[case][i];ob=self.obs[case][i];validate_rng_witnesses(ob,stats)
                for index,seed in enumerate(stats['npcs']['helper_seeds']):
                    corrupt=copy.deepcopy(stats);corrupt['npcs']['helper_seeds'][index]['old_state']^=1
                    with self.assertRaises((ValueError,AssertionError)):validate_rng_witnesses(ob,corrupt)
                corrupt=copy.deepcopy(stats);corrupt['npcs']['final_rng_state']^=1
                with self.assertRaises((ValueError,AssertionError)):validate_rng_witnesses(ob,corrupt)

    def test_same_clock_cohort_matches_without_substituting_saved_target_times(self):
        case='occupied-friendly-second-two';p=replay.DEFAULT/case/'child-1'
        predicted=self.outputs[case][3]['YTDATA.DAT'];observed=gzip.decompress((p/'observed-a/after-YTDATA.DAT.gz').read_bytes());unobserved=gzip.decompress((p/'unobserved-a/after-YTDATA.DAT.gz').read_bytes())
        self.assertEqual(predicted,observed);self.assertNotEqual(predicted,unobserved)
        # Saved unobserved TIMERs are examined only here, after synthesis.
        self.assertNotEqual(predicted[(3583-1)*137+101:(3583-1)*137+105],unobserved[(3583-1)*137+101:(3583-1)*137+105])

    def test_raw_disclosure_cannot_turn_into_zero_or_invent_new_mismatches(self):
        case='occupied-friendly-second-two';rows=[]
        for p in replay.CASES:
            for c in(1,2):
                for o in('observed-a','observed-b','observed-c'):
                    for t in replay.MODES:
                        count=(89 if c==1 else 94)if p==case and t in('unobserved-a','unobserved-b','attach-only')else 0
                        differences=[dict(file='YTDATA.DAT',offset=(3583-1+i//24)*137+49+i%24,observed=0,replayed=1)for i in range(count)]
                        rows.append(dict(case=p,child=c,observation=o,target=t,byte_mismatches=count,files={n:dict(byte_mismatches=count if n=='YTDATA.DAT'else 0)for n in replay.FILES},raw_differences=differences))
        r=dict(cases=rows);replay.assert_comparisons(r)
        idx=next(i for i,row in enumerate(rows)if row['byte_mismatches'])
        for mutate in(lambda x:x['cases'].pop(),lambda x:x['cases'][idx].update(byte_mismatches=0),lambda x:x['cases'][idx]['raw_differences'][0].update(offset=0),lambda x:x['cases'][idx]['files']['YTNEWS.DAT'].update(byte_mismatches=1),lambda x:x['cases'][idx]['raw_differences'][1].update(offset=x['cases'][idx]['raw_differences'][0]['offset'])):
            corrupt=copy.deepcopy(r);mutate(corrupt)
            with self.assertRaises(ValueError):replay.assert_comparisons(corrupt)

    def test_all_force_stock_and_fractional_transfer_outcomes_are_derived(self):
        finals={'vacant-origin':(97337,97337),'friendly-merge':(97337,97337),'occupied-midnight':(97337,97337),'occupied-second-two':(97337,88518),'occupied-second-four':(286865,286865),'occupied-friendly-midnight':(97337,97337),'occupied-friendly-second-two':(97337,97337),'occupied-friendly-second-four':(97374,97373)}
        for case,forces in finals.items():
            for i,force in zip((3,4),forces):
                w=self.outputs[case][i]['YTDATA.DAT'];self.assertEqual(sum(mbf.get(w,51+s,81)for s in range(1,3001)if mbf.get(w,51+s,85)==-2),force)
                self.assertEqual(mbf.get(w,4054,129),37 if i==3 else 40);self.assertEqual(mbf.get(w,4054,73),0)
        w=self.outputs['occupied-second-four'][3]['YTDATA.DAT'];self.assertEqual(mbf.get(w,4052,129),0)
        self.assertEqual(w[(4052-1)*137+129:(4052-1)*137+133],bytes.fromhex('00008000'))
        w=self.outputs['occupied-friendly-second-four'][3]['YTDATA.DAT'];self.assertEqual(w[(2419-1)*137+81:(2419-1)*137+89],bytes.fromhex('0000800000008000'))

if __name__=='__main__':unittest.main()
