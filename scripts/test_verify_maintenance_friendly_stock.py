"""Independent held-friendly absorption, stock, receipts and provenance tests."""
import copy
from fractions import Fraction
import gzip,json,re,shutil,tempfile,unittest
from pathlib import Path
import verify_maintenance_friendly_stock as v


def put(world,record,offset,value):
    out=bytearray(world);at=(record-1)*137+offset;out[at:at+4]=v.encode(value);return bytes(out)


class FriendlyStockEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=v.DEFAULT;cls.observer=(cls.root/'acquisition/observe_maintenance_departure.js').read_text();cls.rows={};cls.obs={};cls.trace={};cls.clocks={}
  for case in v.CASES:
   folder=cls.root/case/'child-1'/'observed-a'
   cls.rows[case]={kind:{name:gzip.decompress((folder/(kind+'-'+name+'.gz')).read_bytes())for name in v.FILES}for kind in('before','after')}
   cls.obs[case]=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()));cls.trace[case]=(folder/'TRACE.BIN').read_bytes()
   cls.clocks[case]=v.verify_observation(cls.obs[case],case,cls.rows[case]['before'],cls.rows[case]['after'])

 def sem(self,case='friendly-whole',outputs=None,trace=None):
  row=self.rows[case];return v.verify_semantics(case,row['before'],row['after']if outputs is None else outputs,self.trace[case]if trace is None else trace,self.clocks[case]['gateway_timer'])

 def observe(self,case='friendly-whole',ob=None,outputs=None):
  row=self.rows[case];return v.verify_observation(self.obs[case]if ob is None else ob,case,row['before'],row['after']if outputs is None else outputs)

 def modified(self,mutation,case='friendly-whole',mode='observed-a'):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);folder=Path(tmp.name)/mode;shutil.copytree(self.root/case/'child-1'/mode,folder)
  meta=json.loads((folder/'capture.json').read_text());mutation(folder,meta);meta['files']={p.name:v.SHA(p.read_bytes())for p in folder.iterdir()if p.name!='capture.json'};(folder/'capture.json').write_text(json.dumps(meta));return folder,case,mode

 def case(self,item):return v.verify_case(*item,self.observer)

 def controller_sample(self):
  folder=self.root/'friendly-whole'/'child-1'/'observed-a';body=gzip.decompress((folder/'host-time.json.gz').read_bytes());return json.loads((folder/'controller.json').read_text()),json.loads(body),body,(folder/'host-flush.json').read_bytes()

 def test_full48controls_have288_equal_outputs_and_exact_fixture_accounting(self):
  r=v.verify();self.assertEqual((r['profiles'],r['full_runs'],r['output_files'],r['unchanged_file_links'],r['transformed_file_links']),(8,48,288,240,48))
  self.assertTrue(all(row['paired']['equal']for row in r['stages'].values()));self.assertTrue(all(row['composition']['classification']=='measured held-friendly absorption plus positive INT stock'for row in r['stages'].values()))

 def test_all48_fixtures_independently_reconstruct15_edits_friendly_stock_and_governor(self):
  for case,recipe in v.CASES.items():
   for mode in v.MODES:
    folder=self.root/case/'child-1'/mode;before={n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes())for n in v.FILES};meta=json.loads((folder/'capture.json').read_text())
    self.assertEqual(before,v.fixture_inputs(case,mode));self.assertEqual(v.verify_fixture(before,case,mode,meta['fixture_edits']),dict(unchanged_links=5,transformed_links=1,edits=15))
    self.assertEqual(v.field(before['YTDATA.DAT'],3051,81),recipe['friendly']);self.assertEqual(v.field(before['YTDATA.DAT'],3051,85),-2)
    self.assertEqual(v.field(before['YTDATA.DAT'],4054,73),recipe['governor']);self.assertEqual(v.field(before['YTDATA.DAT'],4054,129),Fraction(*recipe['stock']))
    parent=v.parent_inputs(case,mode);self.assertTrue(all(before[n]==parent[n]for n in v.FILES if n!='YTDATA.DAT'))

 def test_edits_cannot_be_reordered_omitted_or_claimed_as_unmodified(self):
  for change in(lambda f,m:m.update(applied_fixture=False),lambda f,m:m['fixture_edits'].pop(),lambda f,m:m['fixture_edits'].reverse(),lambda f,m:m['fixture_edits'][0].update(after='00000000')):
   with self.assertRaises(AssertionError):self.case(self.modified(change))

 def test_unlisted_world_or_sidefile_edits_fail_despite_rebound_metadata_hashes(self):
  for name in('YTDATA.DAT','YTNEWS.DAT'):
   def change(f,m):
    p=f/('before-'+name+'.gz');raw=gzip.decompress(p.read_bytes());raw=raw[:100]+bytes([raw[100]^1])+raw[101:];p.write_bytes(gzip.compress(raw,mtime=0));m['inputs'][name]=v.SHA(raw)
   with self.assertRaises(AssertionError):self.case(self.modified(change))

 def test_wrong_case_parent_mode_manifest_or_recipe_reject(self):
  for change in(dict(profile='friendly-half'),dict(mode='unobserved-a'),dict(parent_mode='observed-b'),dict(parent_pins='0'*64),dict(parent_source=dict(v.PARENT_SOURCE,stage='child-1')),dict(recipe='maintenance-stock-conversion-controls-v1')):
   with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:m.update(change)))

 def test_eight_native_outcomes_include_friendly_force_exactly_once(self):
  expected={'friendly-one-empty':97338,'friendly-empty':97374,'friendly-half':97374,'friendly-whole':97411,'friendly-odd-half':97375,'friendly-large':286902,'friendly-owned-whole':97411,'friendly-large-force':194711}
  for case,final in expected.items():
   measured=self.sem(case);qualified=v.qualify_composition(case,measured)
   self.assertEqual(measured['final_physical'][-2],final);self.assertEqual(qualified['final_force'],final)
   self.assertEqual(measured['observed_unexplained_inventory_difference'],0)
   self.assertEqual(qualified['held_friendly_force'],v.CASES[case]['friendly'])

 def test_descending_gate_force_holds_before_only_incoming_departure(self):
  for case in v.CASES:
   r=self.sem(case);self.assertEqual([(m['actor'],m['origin'])for m in r['mercenary_moves']],[(97337,2368)])
   self.assertEqual(r['earlier_mercenary_losses'],0);self.assertEqual(r['offensive_battles'],[]);self.assertEqual(r['quantified_mine_losses'],0)
   v.qualify_composition(case,r)

 def test_capture_is_suppressed_for_all_positive_local_forces_regardless_of_governor(self):
  for case in v.CASES:
   r=self.sem(case);self.assertEqual(r['captures'],[]);self.assertNotIn(b'Mercenaries captured planet',self.rows[case]['after']['YTNEWS.DAT'])
   self.assertEqual(v.field(self.rows[case]['after']['YTDATA.DAT'],4054,73),v.CASES[case]['governor'])

 def test_taking_receipt_stamps_combined_force_before_integer_stock(self):
  for case in('friendly-whole','friendly-odd-half','friendly-large','friendly-owned-whole','friendly-large-force'):
   r=self.sem(case);row=r['taking_receipts'][0];local=v.CASES[case]['friendly'];stock=Fraction(*v.CASES[case]['stock'])
   self.assertEqual(row['actor'],97337+local);self.assertEqual(row['amount'],stock.numerator//stock.denominator)
   self.assertEqual(r['final_physical'][-2],row['actor']+row['amount'])

 def test_empty_and_subunit_stocks_clear_without_capture_or_taking_zero(self):
  for case in('friendly-one-empty','friendly-empty','friendly-half'):
   r=self.sem(case);self.assertTrue(r['stock_cleared']);self.assertEqual(r['taking_receipts'],[]);self.assertEqual(r['captures'],[])
   self.assertNotIn(b'taking 0 fighters',self.trace[case]);self.assertEqual(v.rawfield(self.rows[case]['after']['YTDATA.DAT'],4054,129),bytes.fromhex('00008000'))

 def coherent_force(self,new_force,new_actor,case='friendly-whole'):
  original=self.sem(case);out=dict(self.rows[case]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],3051,81,new_force)
  oldactor=97337+v.CASES[case]['friendly'];old=f'{oldactor} Mercenaries taking'.encode();new=f'{new_actor} Mercenaries taking'.encode()
  out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(old,new);trace=self.trace[case].replace(old,new)
  oldscore=f'{100*original["final_physical"][-2]:,}'.encode();newscore=f'{100*new_force:,}'.encode();out['YTSCORE.ASC']=out['YTSCORE.ASC'].replace(oldscore,newscore)
  return self.sem(case,out,trace)

 def test_coherent_local_force_overwrite_is_recorded_then_fails_measured_absorption(self):
  measured=self.coherent_force(97337+37,97337)
  self.assertEqual(measured['observed_unexplained_inventory_difference'],37)
  with self.assertRaises(AssertionError):v.qualify_composition('friendly-whole',measured)

 def test_coherent_double_count_is_recorded_then_fails_measured_absorption(self):
  measured=self.coherent_force(97337+2*37+37,97337+2*37)
  self.assertEqual(measured['observed_unexplained_inventory_difference'],-37)
  with self.assertRaises(AssertionError):v.qualify_composition('friendly-whole',measured)

 def test_wrong_taking_actor_or_nearest_fraction_transfer_cannot_qualify(self):
  raw=self.trace['friendly-whole'];out=dict(self.rows['friendly-whole']['after']);old=b'97374 Mercenaries taking';new=b'97337 Mercenaries taking';out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(old,new)
  measured=self.sem('friendly-whole',out,raw.replace(old,new))
  with self.assertRaises(AssertionError):v.qualify_composition('friendly-whole',measured)
  measured=self.coherent_force(97337+37+2,97337+37,'friendly-odd-half')
  with self.assertRaises(AssertionError):v.qualify_composition('friendly-odd-half',measured)

 def test_invented_capture_or_unreported_friendly_merge_news_reject(self):
  case='friendly-whole';raw=self.trace[case];out=dict(self.rows[case]['after']);taking=b'  -  97374 Mercenaries taking 37 fighters from planet Gateway Cache!'
  capture=b'  -  97337 Mercenaries captured planet Gateway Cache!';out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(taking,capture+b'\r\n'+taking);trace=raw.replace(taking,capture+b'\r\n'+taking)
  measured=self.sem(case,out,trace)
  with self.assertRaises(AssertionError):v.qualify_composition(case,measured)
  out=dict(self.rows[case]['after']);out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(taking,b'  -  Friendly force joined!\r\n'+taking)
  with self.assertRaises(AssertionError):self.sem(case,out,raw.replace(taking,b'  -  Friendly force joined!\r\n'+taking))

 def test_raw_departure_and_complete_stock_clear_zeros_are_not_normalized(self):
  for record,offset in((2419,81),(2419,85),(4054,129)):
   out=dict(self.rows['friendly-whole']['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],record,offset,0)
   with self.assertRaises(AssertionError):v.qualify_composition('friendly-whole',self.sem(outputs=out))

 def test_cache_governor_ground_bank_and_private_inbox_are_bound(self):
  for offset,value in((73,-2),(77,1),(117,1),(45,0)):
   out=dict(self.rows['friendly-whole']['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],4054,offset,value)
   with self.assertRaises(AssertionError):self.sem(outputs=out)
  out=dict(self.rows['friendly-whole']['after']);out['YTRMSG.DAT']=b'fake'
  with self.assertRaises(AssertionError):self.sem(outputs=out)

 def test_public_receipt_and_actual_physical_score_must_agree(self):
  out=dict(self.rows['friendly-whole']['after']);out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(b'taking 37 fighters',b'taking 38 fighters')
  with self.assertRaises(AssertionError):self.sem(outputs=out)
  out=dict(self.rows['friendly-whole']['after']);out['YTSCORE.ASC']=out['YTSCORE.ASC'].replace(b'9,741,100',b'9,741,101')
  with self.assertRaises(AssertionError):self.sem(outputs=out)

 def test_source_clocks_cpu_and_rng_context_bind_actual_saved_values(self):
  for case in v.CASES:self.assertEqual(self.observe(case)['active_planets'],4)
  for record,offset,value in((3657,101,999),(3657,45,310),(4054,89,999)):
   out=dict(self.rows['friendly-whole']['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],record,offset,value)
   with self.assertRaises(AssertionError):self.observe(outputs=out)
  for name,value in(('runtime_signature','0'*16),('cycle_max',100000),('caller_code','00')):
   ob=copy.deepcopy(self.obs['friendly-whole']);event=next(e for e in ob['events']if e['before']['runtime_signature']is not None)
   for side in('before','after'):event[side][name]=value
   with self.assertRaises(AssertionError):self.observe(ob=ob)

 def test_clock_loss_wrong_exit_or_nonpreserving_rng_witness_reject(self):
  for change in(dict(observe=False),dict(exit_code=1),dict(errors=['lost']),dict(dropped=1)):
   ob=copy.deepcopy(self.obs['friendly-whole']);ob.update(change)
   with self.assertRaises(AssertionError):self.observe(ob=ob)
  ob=copy.deepcopy(self.obs['friendly-whole']);ob['events'][1]['after']['rng_raw']='01000000'
  with self.assertRaises(AssertionError):self.observe(ob=ob)

 def test_natural_exit_wait_and_persisted_receipt_cannot_override_failed_process(self):
  controller,ob,body,receipt=self.controller_sample()
  for wait in(None,dict(checks=0,elapsed_ms=0),dict(checks=True,elapsed_ms=0),dict(checks=1,elapsed_ms=2001),dict(checks=1,elapsed_ms=float('nan'))):
   c=copy.deepcopy(controller);c['natural_exit_wait']=wait
   with self.assertRaises(AssertionError):v.verify_controller(c,'observed',ob,body,receipt)
  for change in(dict(process_exited=False),dict(forced=True),dict(success=False),dict(exit_code=1),dict(ready=False)):
   c=copy.deepcopy(controller);c.update(change)
   with self.assertRaises(AssertionError):v.verify_controller(c,'observed',ob,body,receipt)

 def test_receipt_exact_utf8_counts_and_any_delivered_ack_must_agree(self):
  controller,ob,body,receipt=self.controller_sample()
  for key in('bytes','expected_bytes','events','errors','dropped','exit_code'):
   changed=json.loads(receipt);changed[key]+=1;raw=(json.dumps(changed,separators=(',',':'))+'\n').encode()
   with self.assertRaises(AssertionError):v.verify_controller(controller,'observed',ob,body,raw)
  with self.assertRaises(AssertionError):v.verify_controller(controller,'observed',ob,body,receipt[:-1])
  c=copy.deepcopy(controller);c['messages'][1]['payload']['bytes']+=1
  with self.assertRaises(AssertionError):v.verify_controller(c,'observed',ob,body,receipt)

 def test_loaded_observer_guest_receipt_and_actual_shell_clock_reject_mutations(self):
  for change in(lambda f,m:(f/'loaded-observer.js').write_text((f/'loaded-observer.js').read_text()+'//fake'),lambda f,m:(f/'host-flush.json').unlink(),lambda f,m:m['guests'].update(**{'YTMAINT.EXE':'0'*64})):
   with self.assertRaises(AssertionError):self.case(self.modified(change))
  def changed_clock(f,m):
   p=f/'DOSTIME.LOG';p.write_bytes(re.sub(rb'Current time: [^\r]+',b'Current time: 0:00:09.98am',p.read_bytes(),count=1))
  with self.assertRaises(AssertionError):self.case(self.modified(changed_clock))

 def test_forged_manifest_rejects_and_no_file_difference_can_be_hidden(self):
  with tempfile.TemporaryDirectory()as tmp:
   (Path(tmp)/'pins.json').write_text('{"files":{}}')
   with self.assertRaises(AssertionError):v.verify(Path(tmp))
  rows={m:dict(outputs=dict(self.rows['friendly-whole']['after']))for m in v.MODES};rows['observed-c']['outputs']['YTDATA.DAT']=put(rows['observed-c']['outputs']['YTDATA.DAT'],4054,77,1)
  compared=v.departure.paired_outputs(rows);self.assertFalse(compared['equal']);self.assertEqual(compared['differences']['observed-c'],['YTDATA.DAT'])

 def test_unchanged_zero_governor_bytes_cannot_be_replaced_by_another_zero(self):
  out=dict(self.rows['friendly-whole']['after']);world=bytearray(out['YTDATA.DAT']);at=(4054-1)*137+73;world[at:at+4]=bytes.fromhex('00008000');out['YTDATA.DAT']=bytes(world)
  with self.assertRaises(AssertionError):self.sem(outputs=out)

if __name__=='__main__':unittest.main()
