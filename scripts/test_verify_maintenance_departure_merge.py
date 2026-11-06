"""Independent provenance, selected departure/merge and nonneutrality controls."""
import copy,gzip,json,re,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import verify_maintenance_departure_merge as v


def put(w,r,o,n):
 b=bytearray(w);at=(r-1)*137+o;b[at:at+4]=v.encode(n);return bytes(b)


class DepartureEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=v.DEFAULT;cls.observer=(cls.root/'acquisition/observe_maintenance_placement.js').read_text();cls.rows={};cls.observations={};cls.trace={};cls.clock={}
  for case in v.CASES:
   for stage in v.STAGES:
    key=(case,stage);p=cls.root/case/stage/'observed-a'
    cls.rows[key]={kind:{n:gzip.decompress((p/(kind+'-'+n+'.gz')).read_bytes())for n in v.FILES}for kind in('before','after')}
    cls.observations[key]=json.loads(gzip.decompress((p/'host-time.json.gz').read_bytes()));cls.trace[key]=(p/'TRACE.BIN').read_bytes()
    cls.clock[key]=v.verify_observation(cls.observations[key],*key,cls.rows[key]['before'],cls.rows[key]['after'])
  cls.key=('vacant-origin','child-1')

 def sem(self,key=None,out=None,trace=None):
  key=self.key if key is None else key;r=self.rows[key];c=self.clock[key]
  return v.verify_semantics(*key,r['before'],r['after']if out is None else out,self.trace[key]if trace is None else trace,c['gateway_timer'],c['planet_timers'])

 def observe(self,key=None,ob=None,out=None):
  key=self.key if key is None else key;r=self.rows[key]
  return v.verify_observation(self.observations[key]if ob is None else ob,*key,r['before'],r['after']if out is None else out)

 def modified(self,mutation,key=None):
  key=self.key if key is None else key;tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);folder=Path(tmp.name)/'observed-a';shutil.copytree(self.root/key[0]/key[1]/'observed-a',folder)
  meta=json.loads((folder/'capture.json').read_text());mutation(folder,meta);meta['files']={p.name:v.SHA(p.read_bytes())for p in folder.iterdir()if p.name!='capture.json'};(folder/'capture.json').write_text(json.dumps(meta))
  return folder,key,meta

 def case(self,item):
  folder,(profile,stage),meta=item
  return v.verify_case(folder,profile,stage,'observed-a',self.observer,None if stage=='child-1'else self.rows[(profile,'child-1')]['after'])

 def test_complete_pinned_corpus_distinguishes_edits_handoffs_and_nonneutral_outputs(self):
  r=v.verify();self.assertEqual((r['profiles'],r['full_runs'],r['output_files']),(8,96,576))
  self.assertEqual((r['unchanged_file_links'],r['transformed_file_links'],r['first_stage_unchanged_links'],r['second_stage_exact_links']),(528,48,240,288))
  unequal=[(case,stage)for case,stages in r['stages'].items()for stage,row in stages.items()if not row['paired']['equal']]
  self.assertEqual(unequal,[('occupied-friendly-second-two','child-1'),('occupied-friendly-second-two','child-2')])
  self.assertTrue(all(row['mode_classification']['normalized_bytes']==0 for stages in r['stages'].values()for row in stages.values()))

 def test_fixture_is_independently_reconstructed_in_all48_first_runs(self):
  for profile in v.CASES:
   for mode in v.MODES:
    p=self.root/profile/'child-1'/mode;b={n:gzip.decompress((p/('before-'+n+'.gz')).read_bytes())for n in v.FILES};m=json.loads((p/'capture.json').read_text())
    self.assertEqual(b,v.fixture_inputs(profile,mode));parent=v.parent_inputs(profile,mode)
    self.assertTrue(all(b[n]==parent[n]for n in v.FILES if n!='YTDATA.DAT'));self.assertNotEqual(b['YTDATA.DAT'],parent['YTDATA.DAT'])
    self.assertEqual(v.verify_fixture(b,profile,mode,m['fixture_edits'])['edits'],16)
    self.assertEqual(v.field(b['YTDATA.DAT'],2419,41),2364)
    self.assertEqual(v.field(b['YTDATA.DAT'],2419,45),3000)

 def test_all48_second_children_inherit_exact_same_mode_six_files(self):
  for profile in v.CASES:
   for mode in v.MODES:
    a={n:gzip.decompress((self.root/profile/'child-1'/mode/('after-'+n+'.gz')).read_bytes())for n in v.FILES}
    b={n:gzip.decompress((self.root/profile/'child-2'/mode/('before-'+n+'.gz')).read_bytes())for n in v.FILES};v.verify_inheritance(b,a)

 def test_fixture_cannot_be_claimed_unmodified_or_reapplied_on_second_day(self):
  with self.assertRaises(AssertionError):v.verify_inheritance(self.rows[self.key]['before'],v.parent_inputs(*self.key[:1],'observed-a'))
  with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:m.update(applied_fixture=False)))
  for change in(dict(applied_fixture=True),dict(fixture_edits=[dict(record=1,offset=0,before='00',after='00')])):
   with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:m.update(change),('vacant-origin','child-2')))

 def test_wrong_edit_order_or_hidden_side_file_change_rejects(self):
  for mutation in(lambda f,m:m.update(fixture_edits=[]),lambda f,m:m['fixture_edits'][0].update(before='00'*4),lambda f,m:m['fixture_edits'][0].update(after='00'*4),lambda f,m:m['fixture_edits'].reverse()):
   with self.assertRaises(AssertionError):self.case(self.modified(mutation))
  def change(f,m):
   p=f/'before-YTNEWS.DAT.gz';b=gzip.decompress(p.read_bytes())+b'fake';p.write_bytes(gzip.compress(b,mtime=0));m['inputs']['YTNEWS.DAT']=v.SHA(b)
  with self.assertRaises(AssertionError):self.case(self.modified(change))

 def test_wrong_case_parent_mode_and_lineage_rejects(self):
  for change in(dict(profile='friendly-merge'),dict(parent_mode='observed-b'),dict(parent='prior-child-2'),dict(parent_pins='0'*64),dict(parent_source=dict(v.PARENT_SOURCE,stage='child-1'))):
   with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:m.update(change)))

 def test_changed_second_day_file_is_not_hidden_by_another_mode(self):
  b=self.rows[('vacant-origin','child-2')]['before']
  for n in v.FILES:
   changed=dict(b);changed[n]+=b'fake'
   with self.assertRaises(AssertionError):v.verify_inheritance(changed,b)

 def test_complete_source_clock_and_cpu_inventory(self):
  for key in self.rows:self.assertEqual(self.observe(key)['active_planets'],4)
  for change in(dict(observe=False),dict(exit_code=False),dict(exit_code=1),dict(errors=['lost']),dict(dropped=1)):
   ob=copy.deepcopy(self.observations[self.key]);ob.update(change)
   with self.assertRaises(AssertionError):self.observe(ob=ob)
  for field,value in(('runtime_signature','0'*16),('cycle_max',100000),('caller_code','00')):
   ob=copy.deepcopy(self.observations[self.key]);e=next(e for e in ob['events']if e['before']['runtime_signature']is not None)
   for side in('before','after'):e[side][field]=value
   with self.assertRaises(AssertionError):self.observe(ob=ob)

 def test_rng_width_callback_preservation_and_event_ordinals_reject(self):
  for value in('00','000000ff'):
   ob=copy.deepcopy(self.observations[self.key])
   for side in('before','after'):ob['events'][1][side]['rng_raw']=value
   with self.assertRaises(AssertionError):self.observe(ob=ob)
  ob=copy.deepcopy(self.observations[self.key]);ob['events'][1]['after']['rng_raw']='01000000'
  with self.assertRaises(AssertionError):self.observe(ob=ob)
  ob=copy.deepcopy(self.observations[self.key]);ob['events'].pop(3)
  with self.assertRaises(AssertionError):self.observe(ob=ob)

 def test_port_saved_date_timer_and_separate_text_clocks_are_bound(self):
  for offset,n in((101,999),(45,310)):
   out=dict(self.rows[self.key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],3657,offset,n)
   with self.assertRaises(AssertionError):self.observe(out=out)
  for name in('YTNEWS.DAT','YTSCORE.ASC'):
   out=dict(self.rows[self.key]['after']);out[name]=re.sub(rb'[0-9]{2}:[0-9]{2}:[0-9]{2}',b'00:00:09',out[name],count=1)
   with self.assertRaises(AssertionError):self.observe(out=out)

 def test_actual_occupied_midnight_holds_and_second_two_departs(self):
  held=self.sem(('occupied-midnight','child-1'));departed=self.sem(('occupied-second-two','child-1'))
  self.assertTrue(held['occupied_origin_held']);self.assertFalse(held['occupied_origin_departure'])
  self.assertTrue(departed['occupied_origin_departure']);self.assertFalse(departed['occupied_origin_held'])
  self.assertEqual(held['activations'],[]);self.assertEqual(departed['activations'][0],dict(force=97337,sector=3000))

 def test_preempted_small_friendly_fixture_is_not_misreported_as_merge(self):
  r=self.sem(('friendly-merge','child-1'))
  self.assertEqual(r['earlier_defense_mercenary_losses'],37);self.assertEqual(r['observed_friendly_merge_increments'],[]);self.assertFalse(r['friendly_force_survives_earlier_phase'])
  self.assertEqual(r['physical'][-2],97337)

 def test_actual_silent_friendly_merge_adds37_exactly_once(self):
  r=self.sem(('occupied-friendly-second-four','child-1'))
  self.assertEqual(r['earlier_defense_mercenary_losses'],0);self.assertEqual(r['observed_friendly_merge_increments'],[37]);self.assertEqual(r['physical'][-2],97374);self.assertEqual(r['unmoved_friendly_reserve'],0)
  self.assertEqual(r['activations'][:2],[dict(force=97337,sector=3000),dict(force=97374,sector=13)])
  self.assertEqual(r['pickup'],0)

 def test_home_pickup_derives_fractional_before_economy_and_exact_whole_transfer(self):
  key=('occupied-second-four','child-1');r=self.sem(key)
  self.assertEqual(r['pickup_by_title'],{'The Wanderer':189528});self.assertEqual(r['physical'][-2],286865)
  self.assertEqual(r['observed_discarded_pickup_fractions'],{'The Wanderer':.296875})
  timer=bytes.fromhex(self.clock[key]['planet_timers'][1]);date=v.schedule(*key)[0]
  self.assertEqual(v.stock_after_economy(self.rows[key]['before']['YTDATA.DAT'],date,timer,4052),189528.296875)

 def test_later_mine_and_offense_losses_are_separate(self):
  r=self.sem(('occupied-second-two','child-2'))
  self.assertEqual((r['earlier_defense_mercenary_losses'],r['mine_losses'],r['observed_offensive_losses'],r['physical'][-2]),(2837,5973,9,88518))

 def test_forged_silent_merge_size_or_origin_rejects(self):
  key=('occupied-friendly-second-four','child-1');raw=self.trace[key]
  for old,new in((b'97374 Mercenaries moving',b'97375 Mercenaries moving'),(b'from sector 3000',b'from sector 2999')):
   changed=raw.replace(old,new,1);self.assertNotEqual(changed,raw)
   with self.assertRaises(AssertionError):self.sem(key,trace=changed)

 def test_numerically_equal_merge_and_departure_zeros_cannot_be_normalized(self):
  key=('occupied-friendly-second-four','child-1')
  for record in(2419,3051):
   for offset in(81,85):
    out=dict(self.rows[key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],record,offset,0)
    with self.subTest(record=record,offset=offset),self.assertRaises(AssertionError):self.sem(key,out=out)

 def test_home_pickup_receipt_fraction_and_raw_clear_cannot_be_forged(self):
  key=('occupied-second-four','child-1');raw=self.trace[key]
  for old,new in((b'taking 189528 fighters',b'taking 189529 fighters'),(b'planet The Wanderer!',b'planet Departure Cache!')):
   changed=raw.replace(old,new,1);self.assertNotEqual(changed,raw)
   with self.assertRaises(AssertionError):self.sem(key,trace=changed)
  out=dict(self.rows[key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],4052,129,0)
  with self.assertRaises(AssertionError):self.sem(key,out=out)

 def test_scores_private_mail_title_and_ground_stay_bound(self):
  for offset,value in((73,-2),(117,1),(77,1)):
   out=dict(self.rows[self.key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],4054,offset,value)
   with self.assertRaises(AssertionError):self.sem(out=out)
  out=dict(self.rows[self.key]['after']);out['YTRMSG.DAT']=b'fake'
  with self.assertRaises(AssertionError):self.sem(out=out)
  out=dict(self.rows[self.key]['after']);out['YTSCORE.ASC']=out['YTSCORE.ASC'].replace(b'9,733,700',b'9,733,701')
  with self.assertRaises(AssertionError):self.sem(out=out)

 def test_nonneutral_ports_are_reported_as_raw89_and94_byte_differences(self):
  for stage,count in(('child-1',89),('child-2',94)):
   case='occupied-friendly-second-two';results={m:dict(outputs={n:gzip.decompress((self.root/case/stage/m/('after-'+n+'.gz')).read_bytes())for n in v.FILES})for m in v.MODES}
   r=v.paired_outputs(results);self.assertFalse(r['equal']);self.assertEqual(r['byte_differences']['observed-a'],{'YTDATA.DAT':count});self.assertTrue(r['world_fields']['observed-a'])
   c=v.verify_mode_classification(case,stage,results,r);self.assertEqual(c['normalized_bytes'],0)
   forged=copy.deepcopy(r);forged['equal']=True
   with self.assertRaises(AssertionError):v.verify_mode_classification(case,stage,results,forged)

 def test_nonneutral_disclosure_cannot_hide_other_fields_or_side_file_changes(self):
  case='occupied-friendly-second-two';stage='child-1';results={m:dict(outputs={n:gzip.decompress((self.root/case/stage/m/('after-'+n+'.gz')).read_bytes())for n in v.FILES})for m in v.MODES}
  for name in('YTNEWS.DAT','YTDATA.DAT'):
   changed=copy.deepcopy(results)
   for mode in('observed-a','observed-b','observed-c'):
    if name=='YTDATA.DAT':changed[mode]['outputs'][name]=put(changed[mode]['outputs'][name],4054,77,1)
    else:changed[mode]['outputs'][name]+=b'fake'
   with self.assertRaises(AssertionError):v.verify_mode_classification(case,stage,changed,v.paired_outputs(changed))

 def test_changed_guest_loaded_observer_clock_and_controller_reject(self):
  for mutation in(lambda f,m:(f/'loaded-observer.js').write_text((f/'loaded-observer.js').read_text()+'//fake'),lambda f,m:m['guests'].update(**{'YTMAINT.EXE':'0'*64})):
   with self.assertRaises(AssertionError):self.case(self.modified(mutation))
  def forced(f,m):
   c=json.loads((f/'controller.json').read_text());c['forced']=True;m['controller']=c;(f/'controller.json').write_text(json.dumps(c))
  with self.assertRaises(AssertionError):self.case(self.modified(forced))
  with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:(f/'RETURN.LOG').unlink()))
  with tempfile.TemporaryDirectory()as tmp:
   (Path(tmp)/'pins.json').write_text('{"files":{}}')
   with self.assertRaises(AssertionError):v.verify(Path(tmp))

 def receipt_sample(self):
  folder=self.root/v.RECEIPT_PROFILE/'child-1'/'observed-a'
  controller=json.loads((folder/'controller.json').read_text());body=gzip.decompress((folder/'host-time.json.gz').read_bytes());ob=json.loads(body);receipt=(folder/'host-flush.json').read_bytes()
  return controller,ob,body,receipt

 def test_persisted_exit_receipt_independently_binds_complete_utf8_bytes_and_counts(self):
  controller,ob,body,receipt=self.receipt_sample();r=v.verify_receipt_controller(controller,'observed',ob,body,receipt)
  self.assertEqual(r['bytes'],len(body));self.assertTrue(r['persisted'])
  for key in('bytes','expected_bytes','events','errors','dropped','exit_code'):
   changed=json.loads(receipt);changed[key]+=1;raw=(json.dumps(changed,separators=(',',':'))+'\n').encode()
   with self.subTest(key=key),self.assertRaises(AssertionError):v.verify_receipt_controller(controller,'observed',ob,body,raw)

 def test_persisted_receipt_rejects_boolean_numbers_partial_and_noncanonical_writes(self):
  controller,ob,body,receipt=self.receipt_sample()
  changed=json.loads(receipt);changed['exit_code']=False
  for raw in(receipt[:-1],json.dumps(json.loads(receipt),indent=2).encode(),(json.dumps(changed,separators=(',',':'))+'\n').encode()):
   with self.assertRaises(AssertionError):v.verify_receipt_controller(controller,'observed',ob,body,raw)
  for raw in(body[:-1],json.dumps(ob,indent=2).encode()):
   with self.assertRaises(AssertionError):v.verify_receipt_controller(controller,'observed',ob,raw,receipt)

 def test_actual_optional_async_ack_must_agree_and_cannot_be_duplicated(self):
  controller,ob,body,receipt=self.receipt_sample();self.assertEqual(len(controller['messages']),2)
  for change in('mismatch','duplicate','flag'):
   c=copy.deepcopy(controller)
   if change=='mismatch':c['messages'][1]['payload']['bytes']+=1
   elif change=='duplicate':c['messages'].append(c['messages'][1])
   else:c['flush_acknowledged']=False
   with self.assertRaises(AssertionError):v.verify_receipt_controller(c,'observed',ob,body,receipt)

 def test_synthetic_no_ack_case_requires_the_same_strict_persisted_receipt(self):
  controller,ob,body,receipt=self.receipt_sample();c=copy.deepcopy(controller);c['messages']=c['messages'][:1];c['flush_acknowledged']=False
  self.assertFalse(v.verify_receipt_controller(c,'observed',ob,body,receipt)['acknowledged'])
  changed=json.loads(receipt);changed['bytes']-=1;raw=(json.dumps(changed,separators=(',',':'))+'\n').encode()
  with self.assertRaises(AssertionError):v.verify_receipt_controller(c,'observed',ob,body,raw)

 def test_persisted_receipt_does_not_override_failed_or_forced_process_identity(self):
  controller,ob,body,receipt=self.receipt_sample()
  for change in(dict(success=False),dict(forced=True),dict(process_exited=False),dict(exit_code=1),dict(ready=False),dict(detached_reason='application-requested')):
   c=copy.deepcopy(controller);c.update(change)
   with self.assertRaises(AssertionError):v.verify_receipt_controller(c,'observed',ob,body,receipt)
  c=copy.deepcopy(controller);c['frida']['module_sha256']='0'*64
  with self.assertRaises(AssertionError):v.verify_receipt_controller(c,'observed',ob,body,receipt)

 def test_failed_diagnostic_controllers_never_become_complete_observed_controls(self):
  root=v.DIAGNOSTICS;observer=(root/'acquisition/observe_maintenance_placement.js').read_text()
  for name in('failed-attempt-a','failed-attempt-b'):
   folder=root/name;controller=json.loads((folder/'controller.json').read_text());body=gzip.decompress((folder/'host-time.json.gz').read_bytes());ob=json.loads(body)
   with self.assertRaises(AssertionError):v.clocks.neutral.verify_controller(controller,'observed',ob,body)
   self.assertFalse(v.verify_failed_observer(folder,observer)['full_control'])

 def test_explicit_diagnostics_path_rejects_forged_manifest(self):
  with tempfile.TemporaryDirectory()as tmp:
   (Path(tmp)/'pins.json').write_text('{"files":{}}')
   with self.assertRaises(AssertionError):v.verify_diagnostics(self.root,Path(tmp))

 def test_public_audit_uses_the_explicit_exported_diagnostics_path(self):
  marker=Path('/private/tmp/departure-export-diagnostics-marker');result=object()
  with patch.object(v,'verify_diagnostics',return_value=result)as checked:
   report=v.verify(self.root,marker)
  checked.assert_called_once_with(self.root,marker);self.assertIs(report['diagnostics'],result)

if __name__=='__main__':unittest.main()
