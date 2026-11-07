"""Modeled-parent, target-read separation and exact stock-replay properties."""
import builtins
import copy
from dataclasses import replace
import datetime
from fractions import Fraction
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_departed_stock_records as replay
from replay_maintenance_collision_records import validate_rng_witnesses
from replay_qb_graph import mbf


def observation(p):return json.loads(gzip.decompress(p.read_bytes()))


class FriendlyStockRecords(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.before=replay.initial_before();cls.obs={};cls.inputs={};cls.outputs={};cls.stats={}
  for case in replay.CASES:
   obs=tuple(observation(p)for p in replay.observation_paths(case,'observed-a'))
   values=tuple((replay.combat.inputs_from_observation if i<3 else replay.inputs_from_observation)(o)for i,o in enumerate(obs))
   cls.obs[case]=obs;cls.inputs[case]=values;cls.outputs[case],cls.stats[case]=replay.synthesize_chain(cls.before,values,case)

 def reject(self,values,case='second-four-half',before=None):
  with self.assertRaises((ValueError,AssertionError,TypeError)):replay.synthesize_chain(self.before if before is None else before,values,case)

 def test_complete_four_day_model_precedes_every_target_and_matches_all_modes(self):
  real=replay.synthesize_chain;read=Path.read_bytes;events=[]
  def modeled(*args):
   result=real(*args);self.assertEqual(len(result[0]),4);events.append('complete');return result
  def guarded(path):
   if path.name.startswith('after-'):
    self.assertTrue(events);events.append('target')
   return read(path)
  with patch.object(replay,'synthesize_chain',side_effect=modeled),patch.object(Path,'read_bytes',guarded):report=replay.compare_cases()
  self.assertEqual(events,(['complete']+['target']*36)*24)
  audit=replay.assert_comparisons(report);self.assertEqual((audit['exact_comparisons'],audit['files'],audit['normalized_bytes']),(144,864,0))
  self.assertGreater(audit['rng_witness_checks'],1000)
  self.assertEqual(len([r for r in report['cases']if r['observation']==r['target']]),24)
  for mutate in('missing','duplicate','byte','hash'):
   wrong=copy.deepcopy(report)
   if mutate=='missing':wrong['cases'].pop()
   elif mutate=='duplicate':wrong['cases'][0]=wrong['cases'][1]
   elif mutate=='byte':wrong['cases'][0]['files']['YTDATA.DAT']['byte_mismatches']=1
   else:wrong['cases'][0]['files']['YTDATA.DAT']['replayed_sha256']='0'*64
   with self.subTest(mutate=mutate),self.assertRaises(ValueError):replay.assert_comparisons(wrong)

 def test_child_consumes_exact_modeled_parent_then_declared_fixture(self):
  realprefix=replay.combat.synthesize_chain;realfixture=replay.apply_fixture;realchild=replay._synthesize_day
  prefix=[];fixtures=[];seen=[];made=[]
  def pre(*args):
   result=realprefix(*args);prefix.extend(result[0]);return result
  def fixture(parent,case):
   self.assertIs(parent,prefix[2]);result=realfixture(parent,case);fixtures.append(result[0]);return result
  def child(parent,values):
   seen.append(parent);result=realchild(parent,values);made.append(result[0]);return result
  with patch.object(replay.combat,'synthesize_chain',side_effect=pre),patch.object(replay,'apply_fixture',side_effect=fixture),patch.object(replay,'_synthesize_day',side_effect=child):
   out,_=replay.synthesize_chain(self.before,self.inputs['second-four-whole'],'second-four-whole')
  self.assertIs(seen[0],fixtures[0]);self.assertIs(out[3],made[0]);self.assertEqual(out,self.outputs['second-four-whole'])

 def test_marker_in_modeled_parent_survives_pure_handoff(self):
  marker=b'modeled-only-journal';case='second-four-half';seen=[]
  prefix=tuple({**self.outputs[case][i],'YTNEWS.DAT':marker}for i in range(3))
  def child(parent,values):seen.append(parent);return {**parent,'YTNEWS.DAT':parent['YTNEWS.DAT']+b'!'},{}
  with patch.object(replay.combat,'synthesize_chain',return_value=(prefix,({},{},{}))),patch.object(replay,'_synthesize_day',side_effect=child):out,_=replay.synthesize_chain(self.before,self.inputs[case],case)
  self.assertEqual(seen[0]['YTNEWS.DAT'],marker);self.assertEqual(out[3]['YTNEWS.DAT'],marker+b'!')

 def test_core_reads_only_original_source_constants_not_targets_or_metadata(self):
  read=Path.read_bytes;opened=Path.open;allowed=replay.ROOT/'archive/dos-original/YTMAINT.EXE'
  def guarded(path):
   self.assertEqual(path,allowed);return read(path)
  def guarded_open(path,*a,**kw):
   self.assertEqual(path,allowed);return opened(path,*a,**kw)
  for case in('second-four-empty','second-four-whole','second-eight-whole'):
   with patch.object(Path,'read_bytes',guarded),patch.object(Path,'open',guarded_open),patch.object(builtins,'open',side_effect=AssertionError('unqualified open')),patch.object(replay,'initial_before',side_effect=AssertionError('comparison loader')):
    out,_=replay.synthesize_chain(self.before,self.inputs[case],case)
   self.assertEqual(out,self.outputs[case])

 def test_fifteen_edit_transform_matches_independent_recipe_and_keeps_side_objects(self):
  from verify_maintenance_departed_stock import fixture_inputs
  parent=self.outputs['second-four-half'][2];saved=copy.deepcopy(parent)
  for case in replay.CASES:
   result,edits=replay.apply_fixture(parent,case)
   self.assertEqual(result,fixture_inputs(case,'observed-a'));self.assertEqual(len(edits),15)
   self.assertEqual(Fraction.from_float(mbf.get(result['YTDATA.DAT'],4054,129)),replay.CASES[case][2])
   self.assertTrue(all(result[n]is parent[n]for n in replay.FILES if n!='YTDATA.DAT'));self.assertEqual(parent,saved)
   self.assertEqual(list(edits),json.loads(((replay.SUPPLEMENT if case in ('second-four-empty','second-four-half') else replay.DEFAULT)/case/'child-1/observed-a/capture.json').read_text())['fixture_edits'])
   self.assertEqual(self.stats[case][3]['fixture_edits'],edits)

 def test_admission_rejects_wrong_case_world_and_mutable_or_extra_days(self):
  values=self.inputs['second-four-half']
  for case in('unknown',True,'pickup'):self.reject(values,case)
  for before in({**self.before,'YTRMSG.DAT':b''},{**self.before,'YTDATA.DAT':self.before['YTDATA.DAT'][:-1]+b'!'},self.outputs['second-four-half'][2]):self.reject(values,before=before)
  for rows in(list(values),values[:-1],values+(values[-1],)):self.reject(rows)

 def test_unknown_fixture_bytes_and_mutable_sidefiles_fail_without_parent_writes(self):
  parent=self.outputs['second-four-half'][2]
  for record,offset,n in((1,81,307),(2419,81,97336),(2419,85,0),(3051,81,1),(3051,93,1),(4054,85,1)):
   before=dict(parent);w=bytearray(before['YTDATA.DAT']);mbf.put(w,record,offset,n);before['YTDATA.DAT']=bytes(w);saved=copy.deepcopy(before)
   with self.assertRaises(ValueError):replay.apply_fixture(before,'second-four-half')
   self.assertEqual(before,saved)
  with self.assertRaises(ValueError):replay.apply_fixture({**parent,'YTNEWS.DAT':bytearray()},'second-four-half')

 def test_clock_dates_raw_minutes_callers_and_chronology_are_explicit(self):
  values=self.inputs['second-four-half'];row=values[3]
  for name,n in(('startup_date',datetime.date(2026,11,6)),('news_clock','00:00:01'),('score_clock','00:00:00'),('final_date',datetime.date(2026,11,6))):
   self.reject(values[:3]+(replace(row,clock=replace(row.clock,**{name:n})),))
  for name in('port_dates','port_timer_minutes','h1_timers','h2_timers'):
   self.reject(values[:3]+(replace(row,clock=replace(row.clock,**{name:list(getattr(row.clock,name))})),))
  for schedule in(list(row.schedule),row.schedule[:-1],((row.schedule[0][0],0x9999,row.schedule[0][2]),)+row.schedule[1:]):self.reject(values[:3]+(replace(row,schedule=schedule),))
  self.reject(values[:3]+(replace(row,planet_clocks=list(row.planet_clocks)),))
  self.reject(values[:3]+(replace(row,clock=replace(row.clock,initial_state=True)),))

 def test_forged_consistent_out_of_profile_timers_reject(self):
  values=self.inputs['second-four-half'];row=values[3]
  for raw in(mbf.enc(-1),mbf.enc(60),mbf.enc(720)):
   schedule=((row.schedule[0][0],row.schedule[0][1],raw),)+row.schedule[1:]
   clock=replace(row.clock,h1_timers=tuple(r[2]for r in schedule if r[0]=='h1'),h2_timers=tuple(r[2]for r in schedule if r[0]=='h2'))
   self.reject(values[:3]+(replace(row,clock=clock,schedule=schedule),))

 def test_observed_rng_state_is_witness_only_and_poison_cannot_change_model(self):
  for case in('second-four-empty','second-two-half','second-four-whole','second-six-whole'):
   changed=copy.deepcopy(self.obs[case][3])
   for event in changed['events']:
    for side in('before','after'):event[side]['rng_raw']='ffffffff'
   row=replay.inputs_from_observation(changed);self.assertEqual(row,self.inputs[case][3])
   out,stats=replay.synthesize_chain(self.before,self.inputs[case][:3]+(row,),case);self.assertEqual(out,self.outputs[case])
   with self.assertRaises((ValueError,AssertionError)):validate_rng_witnesses(changed,stats[3])

 def test_physical_floor_clear_and_no_zero_receipt_are_derived_for_all_cases(self):
  for case,(friendly,governor,stock) in replay.CASES.items():
   stock=Fraction(stock);whole=stock.numerator//stock.denominator;out=self.outputs[case][3];row=self.stats[case][3]
   self.assertEqual(mbf.get(out['YTDATA.DAT'],3051,81),97337+(0 if row['npcs']['mercenary']['events'][0]['captured'] else friendly)+whole)
   self.assertEqual(out['YTDATA.DAT'][4053*137+129:4053*137+133],bytes.fromhex('00008000'))
   self.assertEqual(mbf.get(out['YTDATA.DAT'],4054,73),governor)
   self.assertEqual(row['npcs']['mercenary']['events'][0]['captured'],case.split('-')[1] in ('four','eight'))
   self.assertEqual(row['auxiliary']['stock_pickup'],whole);self.assertEqual(row['auxiliary']['fractional_discard'],float(stock-whole))
   self.assertEqual(b'taking 0 fighters'in out['YTNEWS.DAT'],False)
   self.assertEqual((b'taking '+str(whole).encode()+b' fighters')in out['YTNEWS.DAT'],whole>0)

if __name__=='__main__':unittest.main()
