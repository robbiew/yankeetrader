"""Independent fractional-stock encoding, native conversion and provenance tests."""
import copy
from fractions import Fraction
import gzip,json,re,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import verify_maintenance_stock_conversion as v


def put(world,record,offset,value):
    out=bytearray(world);at=(record-1)*137+offset;out[at:at+4]=v.encode(value);return bytes(out)


class StockConversionEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=v.DEFAULT;cls.observer=(cls.root/'acquisition/observe_maintenance_departure.js').read_text();cls.rows={};cls.obs={};cls.trace={};cls.clocks={}
  for case in v.CASES:
   p=cls.root/case/'child-1'/'observed-a'
   cls.rows[case]={kind:{name:gzip.decompress((p/(kind+'-'+name+'.gz')).read_bytes())for name in v.FILES}for kind in('before','after')}
   cls.obs[case]=json.loads(gzip.decompress((p/'host-time.json.gz').read_bytes()));cls.trace[case]=(p/'TRACE.BIN').read_bytes()
   cls.clocks[case]=v.verify_observation(cls.obs[case],case,cls.rows[case]['before'],cls.rows[case]['after'])

 def sem(self,case='odd-half',outputs=None,trace=None):
  row=self.rows[case]
  return v.verify_semantics(case,row['before'],row['after']if outputs is None else outputs,self.trace[case]if trace is None else trace,self.clocks[case]['gateway_timer'])

 def observe(self,case='odd-half',ob=None,outputs=None):
  row=self.rows[case];return v.verify_observation(self.obs[case]if ob is None else ob,case,row['before'],row['after']if outputs is None else outputs)

 def modified(self,mutation,case='odd-half',mode='observed-a'):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);folder=Path(temp.name)/mode;shutil.copytree(self.root/case/'child-1'/mode,folder)
  meta=json.loads((folder/'capture.json').read_text());mutation(folder,meta)
  meta['files']={p.name:v.SHA(p.read_bytes())for p in folder.iterdir()if p.name!='capture.json'};(folder/'capture.json').write_text(json.dumps(meta))
  return folder,case,mode

 def case(self,item):return v.verify_case(*item,self.observer)

 def controller_sample(self):
  folder=self.root/'odd-half'/'child-1'/'observed-a';body=gzip.decompress((folder/'host-time.json.gz').read_bytes())
  return json.loads((folder/'controller.json').read_text()),json.loads(body),body,(folder/'host-flush.json').read_bytes()

 def test_complete72run_manifest_and_six_mode_equal432outputs(self):
  r=v.verify();self.assertEqual((r['profiles'],r['full_runs'],r['output_files'],r['unchanged_file_links'],r['transformed_file_links']),(12,72,432,360,72))
  self.assertEqual(set(r['stages']),set(v.CASES));self.assertTrue(all(row['paired']['equal']for row in r['stages'].values()))
  self.assertTrue(all(row['conversion']['classification']=='measured positive stock INT-floor'for row in r['stages'].values()))

 def test_independent_ieee_encoder_has_exact_rational_roundtrip_and_known_bytes(self):
  self.assertEqual({name:v.encode(Fraction(*v.CASES[name]['stock'])).hex()for name in('quarter','half','three-quarter','odd-half','even-half','below-one','above-one','signed-boundary-half')},{'quarter':'0000007f','half':'00000080','three-quarter':'00004080','odd-half':'00004081','even-half':'00002082','below-one':'ffff7f80','above-one':'01000081','signed-boundary-half':'00ff7f8f'})
  for case in v.CASES:
   raw=v.encode(Fraction(*v.CASES[case]['stock']));self.assertEqual(v.gateway.clocks.mbf_fraction(raw),Fraction(*v.CASES[case]['stock']))

 def test_encoder_rejects_rounded_mutable_boolean_and_unrepresentable_values(self):
  for value in(Fraction(1,3),Fraction(1,2**200),True,[1,2],.5):
   with self.subTest(value=value),self.assertRaises((AssertionError,OverflowError)):v.encode(value)

 def test_all72_fixture_inputs_have15_independent_edits_and5unchanged_sidefiles(self):
  for case in v.CASES:
   for mode in v.MODES:
    folder=self.root/case/'child-1'/mode;before={n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes())for n in v.FILES};meta=json.loads((folder/'capture.json').read_text());parent=v.parent_inputs(case,mode)
    self.assertEqual(before,v.fixture_inputs(case,mode));self.assertTrue(all(before[n]==parent[n]for n in v.FILES if n!='YTDATA.DAT'))
    self.assertEqual(v.verify_fixture(before,case,mode,meta['fixture_edits']),dict(unchanged_links=5,transformed_links=1,edits=15))
    self.assertEqual(v.field(before['YTDATA.DAT'],4054,129),Fraction(*v.CASES[case]['stock']))

 def test_fixture_cannot_be_relabelled_unchanged_or_lose_redundant_source_assignment(self):
  with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:m.update(applied_fixture=False)))
  with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:m['fixture_edits'].pop()))

 def test_wrong_edit_bytes_order_and_hidden_world_or_sidefile_change_reject(self):
  for mutation in(lambda f,m:m['fixture_edits'][0].update(before='00000000'),lambda f,m:m['fixture_edits'][0].update(after='00000000'),lambda f,m:m['fixture_edits'].reverse()):
   with self.assertRaises(AssertionError):self.case(self.modified(mutation))
  for name in('YTDATA.DAT','YTNEWS.DAT'):
   def change(f,m):
    p=f/('before-'+name+'.gz');raw=gzip.decompress(p.read_bytes());raw=raw[:100]+bytes([raw[100]^1])+raw[101:];p.write_bytes(gzip.compress(raw,mtime=0));m['inputs'][name]=v.SHA(raw)
   with self.assertRaises(AssertionError):self.case(self.modified(change))

 def test_wrong_case_mode_parent_manifest_and_recipe_reject(self):
  for change in(dict(profile='even-half'),dict(mode='unobserved-a'),dict(parent_mode='observed-b'),dict(parent_pins='0'*64),dict(parent_source=dict(v.PARENT_SOURCE,stage='child-1')),dict(recipe='maintenance-gateway-hazard-controls-v1')):
   with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:m.update(change)))

 def test_subunits_clear_exact_source_zero_without_printing_taking_zero(self):
  for case in('quarter','half','three-quarter','below-one'):
   row=self.sem(case);self.assertEqual(row['observed_converted_fighters'],0);self.assertEqual(row['taking_receipts'],0)
   self.assertEqual(v.rawfield(self.rows[case]['after']['YTDATA.DAT'],4054,129),bytes.fromhex('00008000'))
   self.assertNotIn(b'taking 0 fighters',self.trace[case]);self.assertEqual(row['capture_stamp'],97337)

 def test_all_native_ties_and_adjacent_single_values_classify_as_measured_floor(self):
  expected={'quarter':0,'half':0,'three-quarter':0,'odd-half':1,'even-half':2,'large-below':189528,'large-half':189528,'large-above':189528,'large-odd-half':189529,'below-one':0,'above-one':1,'signed-boundary-half':32767}
  self.assertEqual({case:self.sem(case)['observed_converted_fighters']for case in v.CASES},expected)
  for case in v.CASES:self.assertEqual(v.classify_conversion(case,self.sem(case))['converted_fighters'],expected[case])

 def test_coherent_nearest_round_ledger_still_fails_native_conversion_classification(self):
  for case,native,wrong in(('odd-half',1,2),('large-above',189528,189529)):
   out=dict(self.rows[case]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],3051,81,97337+wrong)
   old=f'taking {native} fighters'.encode();new=f'taking {wrong} fighters'.encode();out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(old,new)
   oldscore=f'{100*(97337+native):,}'.encode();newscore=f'{100*(97337+wrong):,}'.encode();out['YTSCORE.ASC']=out['YTSCORE.ASC'].replace(oldscore,newscore)
   trace=self.trace[case].replace(old,new)
   measured=self.sem(case,out,trace);self.assertEqual(measured['observed_converted_fighters'],wrong)
   with self.assertRaises(AssertionError):v.classify_conversion(case,measured)

 def test_printed_capture_actor_and_stock_quantity_bind_actual_force(self):
  for old,new in((b'97337 Mercenaries captured',b'97336 Mercenaries captured'),(b'taking 1 fighters',b'taking 2 fighters'),(b'planet Gateway Cache!',b'planet Another Cache!')):
   changed=self.trace['odd-half'].replace(old,new,1);self.assertNotEqual(changed,self.trace['odd-half'])
   with self.assertRaises(AssertionError):self.sem(trace=changed)

 def test_zero_receipt_and_forged_mine_or_combat_output_reject(self):
  original=self.trace['quarter'];mark=b'  -  97337 Mercenaries captured planet Gateway Cache!'
  for line in(b'  -  97337 Mercenaries taking 0 fighters from planet Gateway Cache!',b' *** The Mercenaries Won!'):
   changed=original.replace(mark,mark+b'\r\n'+line,1)
   with self.assertRaises(AssertionError):self.sem('quarter',trace=changed)

 def test_public_and_console_receipts_must_agree_exactly(self):
  out=dict(self.rows['odd-half']['after']);out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(b'taking 1 fighters',b'taking 2 fighters')
  with self.assertRaises(AssertionError):self.sem(outputs=out)

 def test_numeric_zero_cannot_replace_pickup_or_departure_raw_zero(self):
  for record,offset in((4054,129),(2419,81),(2419,85)):
   out=dict(self.rows['odd-half']['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],record,offset,0)
   with self.subTest(record=record,offset=offset),self.assertRaises(AssertionError):self.sem(outputs=out)

 def test_title_owner_ground_bank_rates_and_private_messages_are_bound(self):
  for offset,value in((73,-2),(77,1),(117,1),(45,0),(129,1)):
   out=dict(self.rows['odd-half']['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],4054,offset,value)
   with self.assertRaises(AssertionError):self.sem(outputs=out)
  out=dict(self.rows['odd-half']['after']);out['YTRMSG.DAT']=b'fake'
  with self.assertRaises(AssertionError):self.sem(outputs=out)

 def test_physical_force_and_scores_cannot_be_forged_separately(self):
  out=dict(self.rows['odd-half']['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],3051,81,97339)
  with self.assertRaises(AssertionError):self.sem(outputs=out)
  out=dict(self.rows['odd-half']['after']);out['YTSCORE.ASC']=out['YTSCORE.ASC'].replace(b'9,733,800',b'9,733,801')
  with self.assertRaises(AssertionError):self.sem(outputs=out)

 def test_four_planet_clocks_all1000ports_and_actual_text_clocks_bind_outputs(self):
  for case in v.CASES:self.assertEqual(self.observe(case)['active_planets'],4)
  for record,offset,value in((3657,101,999),(3657,45,310),(4054,89,999)):
   out=dict(self.rows['odd-half']['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],record,offset,value)
   with self.assertRaises(AssertionError):self.observe(outputs=out)
  out=dict(self.rows['odd-half']['after']);out['YTSCORE.ASC']=re.sub(rb'[0-9]{2}:[0-9]{2}:[0-9]{2}',b'00:00:09',out['YTSCORE.ASC'],count=1)
  with self.assertRaises(AssertionError):self.observe(outputs=out)

 def test_lossy_or_wrong_cpu_caller_or_rng_observation_rejects(self):
  for change in(dict(observe=False),dict(exit_code=1),dict(errors=['lost']),dict(dropped=1)):
   ob=copy.deepcopy(self.obs['odd-half']);ob.update(change)
   with self.assertRaises(AssertionError):self.observe(ob=ob)
  for name,value in(('runtime_signature','0'*16),('cycle_max',100000),('caller_code','00')):
   ob=copy.deepcopy(self.obs['odd-half']);event=next(e for e in ob['events']if e['before']['runtime_signature']is not None)
   for side in('before','after'):event[side][name]=value
   with self.assertRaises(AssertionError):self.observe(ob=ob)
  ob=copy.deepcopy(self.obs['odd-half']);ob['events'][1]['after']['rng_raw']='01000000'
  with self.assertRaises(AssertionError):self.observe(ob=ob)

 def test_natural_exit_wait_requires_bounded_actual_probe_metadata(self):
  controller,ob,body,receipt=self.controller_sample()
  for wait in(None,dict(checks=0,elapsed_ms=0),dict(checks=True,elapsed_ms=0),dict(checks=1,elapsed_ms=2001),dict(checks=1,elapsed_ms=float('nan')),dict(checks=1,elapsed_ms=0,forced=True)):
   c=copy.deepcopy(controller);c['natural_exit_wait']=wait
   with self.assertRaises(AssertionError):v.verify_controller(c,'observed',ob,body,receipt)
  self.assertTrue(v.verify_controller(controller,'observed',ob,body,receipt)['persisted'])

 def test_receipt_does_not_override_live_forced_failed_or_wrong_identity(self):
  controller,ob,body,receipt=self.controller_sample()
  for change in(dict(process_exited=False),dict(forced=True),dict(success=False),dict(exit_code=1),dict(ready=False),dict(detached_reason='application-requested')):
   c=copy.deepcopy(controller);c.update(change)
   with self.assertRaises(AssertionError):v.verify_controller(c,'observed',ob,body,receipt)
  c=copy.deepcopy(controller);c['frida']['module_sha256']='0'*64
  with self.assertRaises(AssertionError):v.verify_controller(c,'observed',ob,body,receipt)

 def test_receipt_exact_utf8_counts_and_any_delivered_ack_must_agree(self):
  controller,ob,body,receipt=self.controller_sample()
  for key in('bytes','expected_bytes','events','errors','dropped','exit_code'):
   changed=json.loads(receipt);changed[key]+=1;raw=(json.dumps(changed,separators=(',',':'))+'\n').encode()
   with self.assertRaises(AssertionError):v.verify_controller(controller,'observed',ob,body,raw)
  for raw in(receipt[:-1],json.dumps(json.loads(receipt),indent=2).encode()):
   with self.assertRaises(AssertionError):v.verify_controller(controller,'observed',ob,body,raw)
  c=copy.deepcopy(controller);c['messages'][1]['payload']['bytes']+=1
  with self.assertRaises(AssertionError):v.verify_controller(c,'observed',ob,body,receipt)

 def test_missing_loaded_observer_receipt_and_guest_identity_reject(self):
  for mutation in(lambda f,m:(f/'loaded-observer.js').write_text((f/'loaded-observer.js').read_text()+'//fake'),lambda f,m:(f/'host-flush.json').unlink(),lambda f,m:m['guests'].update(**{'YTMAINT.EXE':'0'*64})):
   with self.assertRaises(AssertionError):self.case(self.modified(mutation))

 def test_forged_cpu_actual_clock_forced_controller_and_missing_return_reject(self):
  def clock(f,m):
   p=f/'DOSTIME.LOG';p.write_bytes(re.sub(rb'Current time: [^\r]+',b'Current time: 0:00:09.98am',p.read_bytes(),count=1))
  def cpu(f,m):
   argv=json.loads((f/'launch.json').read_text());argv[argv.index('cpu_cycles=200000')]='cpu_cycles=100000';m['argv']=argv;(f/'launch.json').write_text(json.dumps(argv))
  def forced(f,m):
   c=json.loads((f/'controller.json').read_text());c['forced']=True;m['controller']=c;(f/'controller.json').write_text(json.dumps(c))
  for mutation in(clock,cpu,forced,lambda f,m:(f/'RETURN.LOG').unlink()):
   with self.assertRaises(AssertionError):self.case(self.modified(mutation))

 def test_equal_mode_claim_never_masks_any_file_difference(self):
  rows={m:dict(outputs=dict(self.rows['odd-half']['after']))for m in v.MODES};rows['observed-c']['outputs']['YTDATA.DAT']=put(rows['observed-c']['outputs']['YTDATA.DAT'],4054,77,1)
  result=v.departure.paired_outputs(rows);self.assertFalse(result['equal']);self.assertEqual(result['differences']['observed-c'],['YTDATA.DAT'])

 def test_forged_manifest_and_changed_historical_observer_source_reject(self):
  with tempfile.TemporaryDirectory()as tmp:
   (Path(tmp)/'pins.json').write_text('{"files":{}}')
   with self.assertRaises(AssertionError):v.verify(Path(tmp))
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);(root/'acquisition').mkdir();(root/'acquisition/observe_maintenance_departure.js').write_text(self.observer+'//changed')
   with self.assertRaises(AssertionError):v.verify_sources(root)

if __name__=='__main__':unittest.main()
