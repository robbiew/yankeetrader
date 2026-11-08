"""Complete gateway synthesis, modeled fixture handoffs and hostile input boundaries."""
import builtins
import copy
from dataclasses import fields,replace
import datetime
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_defender_stock_records as replay
from replay_maintenance_collision_records import validate_rng_witnesses
from replay_qb_graph import mbf


def observation(p):return json.loads(gzip.decompress(p.read_bytes()))


class GatewayRecords(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=replay.initial_before();cls.obs={};cls.inputs={};cls.outputs={};cls.stats={}
        for case in replay.CASES:
            obs=tuple(observation(p)for p in replay.observation_paths(case,'observed-a'))
            values=tuple((replay.combat.inputs_from_observation if i<3 else replay.inputs_from_observation)(o)for i,o in enumerate(obs))
            cls.obs[case]=obs;cls.inputs[case]=values
            cls.outputs[case],cls.stats[case]=replay.synthesize_chain(cls.before,values,case)

    def reject(self,inputs,case='balanced-37-whole',before=None):
        with self.assertRaises((ValueError,AssertionError,TypeError)):replay.synthesize_chain(self.before if before is None else before,inputs,case)

    def test_complete_chain_exists_before_any_native_target_is_opened(self):
        real=replay.synthesize_chain;read=Path.read_bytes;events=[]
        def modeled(*args):
            result=real(*args);events.append('five-complete');return result
        def guarded(path):
            if path.name.startswith('after-'):
                self.assertTrue(events);events.append('target')
            return read(path)
        with patch.object(replay,'synthesize_chain',side_effect=modeled),patch.object(Path,'read_bytes',guarded):report=replay.compare_cases()
        self.assertEqual(events,sum((['five-complete']+['target']*72 for _ in range(12)),[]))
        self.assertEqual((len(report['cases']),len(report['statistics'])),(144,24))
        self.assertTrue(all(r['byte_mismatches']==0 for r in report['cases']))
        self.assertEqual({(r['case'],r['child'],r['observation'],r['target'])for r in report['cases']},
                         {(p,c,o,t)for p in replay.CASES for c in(1,2)for o in('observed-a','observed-b','observed-c')for t in replay.MODES})

    def test_prefix_fixture_and_two_children_are_actual_modeled_objects(self):
        realprefix=replay.combat.synthesize_chain;realfixture=replay.apply_fixture;realchild=replay._synthesize_day
        prefix=[];fixtures=[];seen=[];made=[]
        def pre(*args):
            result=realprefix(*args);prefix.extend(result[0]);return result
        def fixture(parent,case):
            self.assertIs(parent,prefix[2]);result=realfixture(parent,case);fixtures.append(result[0]);return result
        def child(parent,i):
            seen.append(parent);result=realchild(parent,i);made.append(result[0]);return result
        with patch.object(replay.combat,'synthesize_chain',side_effect=pre),patch.object(replay,'apply_fixture',side_effect=fixture),patch.object(replay,'_synthesize_day',side_effect=child):
            out,_=replay.synthesize_chain(self.before,self.inputs['balanced-37-whole'],'balanced-37-whole')
        self.assertIs(seen[0],fixtures[0]);self.assertIs(seen[1],made[0]);self.assertIs(out[3],made[0]);self.assertIs(out[4],made[1]);self.assertEqual(out,self.outputs['balanced-37-whole'])

    def test_modeled_parent_marker_survives_fixture_and_children_without_native_reload(self):
        marker=b'modeled-news-only';seen=[]
        prefix=tuple({n:(marker if n=='YTNEWS.DAT'else self.outputs['one-versus-37-empty'][i][n])for n in replay.FILES}for i in range(3))
        def child(parent,i):
            seen.append(parent);return {**parent,'YTNEWS.DAT':parent['YTNEWS.DAT']+b'!'},{}
        with patch.object(replay.combat,'synthesize_chain',return_value=(prefix,({},{},{}))),patch.object(replay,'_synthesize_day',side_effect=child):
            out,_=replay.synthesize_chain(self.before,self.inputs['one-versus-37-empty'],'one-versus-37-empty')
        self.assertEqual(seen[0]['YTNEWS.DAT'],marker);self.assertEqual(seen[1]['YTNEWS.DAT'],marker+b'!');self.assertEqual(out[4]['YTNEWS.DAT'],marker+b'!!')

    def test_core_opens_only_original_maintenance_and_never_observation_or_target(self):
        read=Path.read_bytes
        def allowed(path):
            if path!=replay.ROOT/'archive/dos-original/YTMAINT.EXE':raise AssertionError(str(path))
            return read(path)
        with patch.object(Path,'read_bytes',allowed),patch.object(builtins,'open',side_effect=AssertionError('unqualified open')),patch.object(replay,'initial_before',side_effect=AssertionError('loader')):
            out,_=replay.synthesize_chain(self.before,self.inputs['37-versus-1000-whole'],'37-versus-1000-whole')
        self.assertEqual(out,self.outputs['37-versus-1000-whole'])

    def test_fixture_is_pure_exact_fifteen_edits_and_only_first_child(self):
        parent=self.outputs['one-versus-37-empty'][2];saved=copy.deepcopy(parent)
        from verify_maintenance_defender_stock import fixture_inputs
        for case in replay.CASES:
            result,edits=replay.apply_fixture(parent,case)
            self.assertEqual(result,fixture_inputs(case,'observed-a'))
            self.assertEqual(len(edits),15);self.assertEqual(parent,saved)
            self.assertTrue(all(result[n]is parent[n]for n in replay.FILES if n!='YTDATA.DAT'))
            self.assertEqual(self.stats[case][3]['fixture_edits'],edits);self.assertEqual(self.stats[case][4]['fixture_edits'],())

    def test_original_input_and_case_boundaries(self):
        self.assertEqual({f.name for f in fields(replay.Inputs)},{'clock','schedule','planet_clocks'})
        self.reject(self.inputs['balanced-37-whole'],case='unknown');self.reject(self.inputs['balanced-37-whole'],case=1)
        for before in ({**self.before,'YTRMSG.DAT':b''},{**self.before,'YTDATA.DAT':self.before['YTDATA.DAT'][:-1]+b'!'},self.outputs['balanced-37-whole'][2]):self.reject(self.inputs['balanced-37-whole'],before=before)
        for value in (list(self.inputs['balanced-37-whole']),self.inputs['balanced-37-whole'][:-1],self.inputs['balanced-37-whole']+(self.inputs['balanced-37-whole'][-1],)):self.reject(value)

    def test_unknown_fixture_context_is_rejected_before_edit(self):
        for r,o,value in((1,81,307),(2419,81,97336),(2419,85,0),(3051,81,1),(3051,93,1),(4054,85,1)):
            parent=dict(self.outputs['balanced-37-whole'][2]);world=bytearray(parent['YTDATA.DAT']);mbf.put(world,r,o,value);parent['YTDATA.DAT']=bytes(world)
            with self.subTest(record=r,offset=o),self.assertRaises(ValueError):replay.apply_fixture(parent,'balanced-37-whole')

    def test_reordered_dates_and_unmeasured_publication_clocks_rejected(self):
        inputs=self.inputs['balanced-37-whole']
        self.reject(inputs[:3]+(inputs[4],inputs[3]))
        for name,value in(('startup_date',datetime.date(2026,11,7)),('news_clock','00:00:01'),('score_clock','00:00:01'),('final_date',datetime.date(2026,11,6)),('news_date',datetime.date(2026,11,6))):
            row=replace(inputs[3],clock=replace(inputs[3].clock,**{name:value}));self.reject(inputs[:3]+(row,inputs[4]))

    def test_mutable_clock_arrays_and_bad_source_callers_rejected(self):
        inputs=self.inputs['37-versus-1000-whole'];row=inputs[3]
        for name in('port_dates','port_timer_minutes','h1_timers','h2_timers'):
            bad=replace(row,clock=replace(row.clock,**{name:list(getattr(row.clock,name))}));self.reject(inputs[:3]+(bad,inputs[4]),'37-versus-1000-whole')
        for schedule in(list(row.schedule),row.schedule[:-1],((row.schedule[0][0],0x9999,row.schedule[0][2]),)+row.schedule[1:]):
            self.reject(inputs[:3]+(replace(row,schedule=schedule),inputs[4]),'37-versus-1000-whole')
        self.reject(inputs[:3]+(replace(row,planet_clocks=list(row.planet_clocks)),inputs[4]),'37-versus-1000-whole')

    def test_captured_rng_bytes_cannot_influence_source_inputs_or_predictions(self):
        for case in replay.CASES:
            changed=copy.deepcopy(self.obs[case][3:])
            for ob in changed:
                for e in ob['events']:
                    for side in('before','after'):e[side]['rng_raw']='ffffffff'
            values=self.inputs[case][:3]+tuple(replay.inputs_from_observation(o)for o in changed)
            self.assertEqual(values,self.inputs[case]);out,_=replay.synthesize_chain(self.before,values,case);self.assertEqual(out,self.outputs[case])

    def test_each_new_helper_and_final_rng_witness_is_audited(self):
        for case in replay.CASES:
            for i in(3,4):
                stats=self.stats[case][i];ob=self.obs[case][i]
                validate_rng_witnesses(ob,stats)
                self.assertTrue(stats['npcs']['helper_seeds'])
                for seed in stats['npcs']['helper_seeds']:
                    corrupt=copy.deepcopy(stats);index=stats['npcs']['helper_seeds'].index(seed);corrupt['npcs']['helper_seeds'][index]['old_state']^=1
                    with self.assertRaises((ValueError,AssertionError)):validate_rng_witnesses(ob,corrupt)
                corrupt=copy.deepcopy(stats);corrupt['npcs']['final_rng_state']^=1
                with self.assertRaises((ValueError,AssertionError)):validate_rng_witnesses(ob,corrupt)

    def test_source_clock_parser_keeps_gateway_indices_and_older_parser_strict(self):
        ob=self.obs['balanced-37-whole'][3]
        self.assertEqual(tuple(r[0]for r in replay.inputs_from_observation(ob).planet_clocks),(4052,4054,4150,4151))
        with self.assertRaises(ValueError):replay.combat.inputs_from_observation(ob)
        for key,value in(('observe',False),('exit_code',1),('dropped',1),('errors',['failure'])):
            corrupt=copy.deepcopy(ob);corrupt[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):replay.inputs_from_observation(corrupt)

    def test_all_cases_derive_defender_survivors_and_uncollected_production(self):
        defenders={'one-versus-37-whole':37,'one-versus-37-empty':37,'37-versus-1000-whole':964,'balanced-37-whole':1}
        for case in replay.CASES:
            stock=replay.CASES[case][0]
            for i in(3,4):
                w=self.outputs[case][i]['YTDATA.DAT']
                self.assertEqual(sum(mbf.get(w,51+s,81)for s in range(1,3001)if mbf.get(w,51+s,85)==-2),0)
                self.assertEqual(mbf.get(w,3051,81),defenders[case]);self.assertEqual(mbf.get(w,3051,85),-1)
                self.assertEqual(mbf.get(w,4054,129),stock+(3 if i==4 else 0))
                self.assertNotIn(b'captured planet',self.outputs[case][i]['YTNEWS.DAT'])
                self.assertNotIn(b'taking ',self.outputs[case][i]['YTNEWS.DAT'])
            self.assertIn(b'The Mercenaries Lost!',self.outputs[case][3]['YTNEWS.DAT'])
            self.assertNotIn(b'The Mercenaries Lost!',self.outputs[case][4]['YTNEWS.DAT'])

    def test_source_rng_audit_is_bound_to_observed_clocks_and_witnessed_progression(self):
        case='balanced-37-whole';row=self.stats[case][3]
        replay.validate_rng_witnesses(self.obs[case][3],row)
        for source_index in (0,3,4):
            bad=copy.deepcopy(row);source=list(bad['npcs']['rng_source']);source[source_index]^=1;bad['npcs']['rng_source']=tuple(source)
            with self.assertRaises(ValueError):replay.validate_rng_witnesses(self.obs[case][3],bad)


if __name__=='__main__':unittest.main()
