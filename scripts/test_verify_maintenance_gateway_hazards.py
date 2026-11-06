"""Independent fixture-ledger, exact inheritance and gateway outcome controls."""
import copy,gzip,json,re,shutil,tempfile,unittest
from pathlib import Path
import verify_maintenance_gateway_hazards as v


def put(w,r,o,n):
 b=bytearray(w);at=(r-1)*137+o;b[at:at+4]=v.encode(n);return bytes(b)


class GatewayEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=v.DEFAULT;cls.observer=(cls.root/'acquisition/observe_maintenance_placement.js').read_text();cls.rows={};cls.observations={};cls.trace={};cls.clock={}
  for case in v.CASES:
   for stage in v.STAGES:
    key=(case,stage);p=cls.root/case/stage/'observed-a'
    cls.rows[key]={kind:{n:gzip.decompress((p/(kind+'-'+n+'.gz')).read_bytes())for n in v.FILES}for kind in('before','after')}
    cls.observations[key]=json.loads(gzip.decompress((p/'host-time.json.gz').read_bytes()));cls.trace[key]=(p/'TRACE.BIN').read_bytes()
    cls.clock[key]=v.verify_observation(cls.observations[key],*key,cls.rows[key]['before'],cls.rows[key]['after'])
  cls.key=('pickup','child-1')

 def sem(self,key=None,out=None,trace=None):
  key=self.key if key is None else key;r=self.rows[key]
  return v.verify_semantics(*key,r['before'],r['after']if out is None else out,self.trace[key]if trace is None else trace,self.clock[key]['gateway_timer'])

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

 def test_complete_pinned_corpus_counts_distinguish_fixture_and_handoff(self):
  r=v.verify();self.assertEqual((r['profiles'],r['full_runs'],r['output_files']),(6,72,432))
  self.assertEqual((r['unchanged_file_links'],r['transformed_file_links'],r['first_stage_unchanged_links'],r['second_stage_exact_links']),(396,36,180,216))
  self.assertTrue(all(row['paired']['equal']for stages in r['stages'].values()for row in stages.values()))

 def test_fixture_is_independently_reconstructed_in_every_original_mode(self):
  for profile in v.CASES:
   for mode in v.MODES:
    p=self.root/profile/'child-1'/mode;b={n:gzip.decompress((p/('before-'+n+'.gz')).read_bytes())for n in v.FILES};m=json.loads((p/'capture.json').read_text())
    self.assertEqual(b,v.fixture_inputs(profile,mode));parent=v.parent_inputs(profile,mode)
    self.assertTrue(all(b[n]==parent[n]for n in v.FILES if n!='YTDATA.DAT'));self.assertNotEqual(b['YTDATA.DAT'],parent['YTDATA.DAT'])
    self.assertEqual(v.verify_fixture(b,profile,mode,m['fixture_edits'])['edits'],15)

 def test_all_second_children_inherit_exact_same_mode_six_files(self):
  for profile in v.CASES:
   for mode in v.MODES:
    files=lambda stage:{n:gzip.decompress((self.root/profile/stage/mode/('after-'+n+'.gz')).read_bytes())for n in v.FILES}
    b={n:gzip.decompress((self.root/profile/'child-2'/mode/('before-'+n+'.gz')).read_bytes())for n in v.FILES};v.verify_inheritance(b,files('child-1'))

 def test_fixture_cannot_be_described_as_unmodified_parent_data(self):
  b=self.rows[self.key]['before'];parent=v.parent_inputs('pickup','observed-a')
  with self.assertRaises(AssertionError):v.verify_inheritance(b,parent)
  with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:m.update(applied_fixture=False)))

 def test_missing_or_wrong_edit_ledger_rejects(self):
  for mutation in(lambda f,m:m.update(fixture_edits=[]),lambda f,m:m['fixture_edits'][0].update(before='00'*4),lambda f,m:m['fixture_edits'][0].update(after='00'*4),lambda f,m:m['fixture_edits'].reverse()):
   with self.assertRaises(AssertionError):self.case(self.modified(mutation))

 def test_patched_unlisted_byte_and_side_file_reject_despite_rebound_hashes(self):
  for n in('YTDATA.DAT','YTNEWS.DAT'):
   def change(f,m):
    p=f/('before-'+n+'.gz');b=gzip.decompress(p.read_bytes());b=b[:100]+bytes([b[100]^1])+b[101:];p.write_bytes(gzip.compress(b,mtime=0));m['inputs'][n]=v.SHA(b)
   with self.assertRaises(AssertionError):self.case(self.modified(change))

 def test_second_day_cannot_repeat_or_repair_the_fixture(self):
  for change in(dict(applied_fixture=True),dict(fixture_edits=[dict(record=1,offset=0,before='00',after='00')])):
   with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:m.update(change),('pickup','child-2')))

 def test_wrong_case_parent_mode_or_source_lineage_rejects(self):
  for change in(dict(profile='empty'),dict(parent_mode='observed-b'),dict(parent='prior-child-2'),dict(parent_pins='0'*64),dict(parent_source=dict(v.PARENT_SOURCE,stage='child-1'))):
   with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:m.update(change)))

 def test_any_changed_second_day_inherited_file_rejects(self):
  b=self.rows[('pickup','child-2')]['before']
  for n in v.FILES:
   changed=dict(b);changed[n]+=b'fake'
   with self.assertRaises(AssertionError):v.verify_inheritance(changed,b)

 def test_mode_difference_is_classified_without_masking(self):
  rows={m:dict(outputs=dict(self.rows[self.key]['after']))for m in v.MODES};rows['observed-c']['outputs']['YTDATA.DAT']+=b'changed'
  result=v.paired_outputs(rows);self.assertFalse(result['equal']);self.assertEqual(result['differences']['observed-c'],['YTDATA.DAT'])

 def test_all_source_clocks_include_actual_four_planet_inventory(self):
  for key in self.rows:self.assertEqual(self.observe(key)['active_planets'],4)

 def test_clock_observer_must_be_complete_natural_and_unchanged(self):
  for change in(dict(observe=False),dict(exit_code=False),dict(exit_code=1),dict(errors=['lost']),dict(dropped=1)):
   ob=copy.deepcopy(self.observations[self.key]);ob.update(change)
   with self.assertRaises(AssertionError):self.observe(ob=ob)

 def test_source_rng_width_and_callback_preservation_reject(self):
  for value in('00','000000ff'):
   ob=copy.deepcopy(self.observations[self.key])
   for side in('before','after'):ob['events'][1][side]['rng_raw']=value
   with self.assertRaises(AssertionError):self.observe(ob=ob)
  ob=copy.deepcopy(self.observations[self.key]);ob['events'][1]['after']['rng_raw']='01000000'
  with self.assertRaises(AssertionError):self.observe(ob=ob)

 def test_source_signature_cpu_caller_and_ordinal_reject(self):
  for name,value in(('runtime_signature','0'*16),('cycle_max',100000),('caller_code','00')):
   ob=copy.deepcopy(self.observations[self.key]);event=next(e for e in ob['events']if e['before']['runtime_signature']is not None)
   for side in('before','after'):event[side][name]=value
   with self.assertRaises(AssertionError):self.observe(ob=ob)
  ob=copy.deepcopy(self.observations[self.key]);ob['events'].pop(3)
  with self.assertRaises(AssertionError):self.observe(ob=ob)

 def test_saved_port_clock_and_source_calendar_are_bound(self):
  for offset,n in((101,999),(45,310)):
   out=dict(self.rows[self.key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],3657,offset,n)
   with self.assertRaises(AssertionError):self.observe(out=out)

 def test_publication_clocks_are_source_specific(self):
  for name in('YTNEWS.DAT','YTSCORE.ASC'):
   out=dict(self.rows[self.key]['after']);out[name]=re.sub(rb'[0-9]{2}:[0-9]{2}:[0-9]{2}',b'00:00:09',out[name],count=1)
   with self.assertRaises(AssertionError):self.observe(out=out)

 def test_source_qualified_mine_helper_runs_even_after_fatal_first_hit(self):
  for case,count in(('empty',0),('mine-pickup',1),('mine-guarded',1),('fatal-before-pickup',3)):
   self.assertEqual(len(self.clock[(case,'child-1')]['mine_helper_calls']),count)
  self.assertEqual(self.sem(('fatal-before-pickup','child-1'))['mine_events'][0]['after'],2)

 def test_known_pickup_stock_and_physical_growth_reconcile(self):
  r=self.sem();self.assertEqual((r['pickup'],r['captured'],r['physical'][-2],r['saved_stock']),(37,1,97374,'0'))
  empty=self.sem(('empty','child-1'));self.assertEqual((empty['pickup'],empty['captured'],empty['physical'][-2]),(0,1,97337))

 def test_next_day_minimum_rate_growth_is_not_erased(self):
  for case in v.CASES:
   r=self.sem((case,'child-2'));self.assertEqual(r['pre_pickup_stock'],3 if case in('empty','pickup','mine-pickup')else 40)
   self.assertEqual(r['pickup'],0)

 def test_stock_economy_function_reads_only_before_fields_and_clock(self):
  for key in self.rows:
   before=self.rows[key]['before']['YTDATA.DAT'];timer=bytes.fromhex(self.clock[key]['gateway_timer']);date=v.schedule(*key)[0]
   self.assertEqual(v.stock_after_economy(before,date,timer),self.sem(key)['pre_pickup_stock'])

 def test_mine_damage_then_pickup_conserves_both_stocks(self):
  r=self.sem(('mine-pickup','child-1'));self.assertEqual((r['mine_losses'],r['pickup'],r['physical'][-2]),(712,37,96662));self.assertEqual(r['mine_events'],[dict(sector=3000,loss=712,before=1,after=0)])

 def test_guarded_planet_is_not_revisited_after_surviving_combat(self):
  r=self.sem(('guarded-pickup','child-1'));self.assertEqual((r['pickup'],r['captured'],r['observed_offensive_losses'],r['saved_stock']),(0,0,34,'37'))
  combined=self.sem(('mine-guarded','child-1'));self.assertEqual((combined['mine_losses'],combined['observed_offensive_losses'],combined['pickup']),(518,40,0))

 def test_fatal_mine_stops_before_pickup_and_preserves_unused_mines(self):
  r=self.sem(('fatal-before-pickup','child-1'));self.assertEqual((r['physical'][-2],r['mine_losses'],r['pickup'],r['saved_stock']),(0,1,0,'37'));self.assertEqual(r['mine_events'][0]['after'],2)

 def test_first_console_origin_cannot_be_forged(self):
  raw=self.trace[self.key];changed=raw.replace(b'from sector 2368',b'from sector 2367',1);self.assertNotEqual(raw,changed)
  with self.assertRaises(AssertionError):self.sem(trace=changed)

 def test_declared_offensive_winner_cannot_finish_with_zero_survivors(self):
  key=('guarded-pickup','child-1');out=dict(self.rows[key]['after']);world=out['YTDATA.DAT']
  for sector in range(1,3001):
   if v.field(world,51+sector,81)>0 and v.field(world,51+sector,85)==-2:world=put(world,51+sector,81,0)
  out['YTDATA.DAT']=world;out['YTSCORE.ASC']=out['YTSCORE.ASC'].replace(b'9,730,300',b'        0')
  before,after=self.trace[key].split(b' *** The Mercenaries Won!',1)
  after=re.sub(rb'^  -  [0-9]+ Mercenaries moving from sector [0-9]+ *\r\n',b'',after,flags=re.M)
  trace=before+b' *** The Mercenaries Won!'+after
  with self.assertRaises(AssertionError):self.sem(key,out,trace)

 def test_gateway_ground_remains_source_economy_not_capture_damage(self):
  for case in v.CASES:
   for stage in v.STAGES:
    key=(case,stage);date=v.schedule(*key)[0];expected=v.ground_after_economy(self.rows[key]['before']['YTDATA.DAT'],date,bytes.fromhex(self.clock[key]['gateway_timer']))
    self.assertEqual(v.field(self.rows[key]['after']['YTDATA.DAT'],4054,77),expected)
  out=dict(self.rows[self.key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],4054,77,1)
  with self.assertRaises(AssertionError):self.sem(out=out)

 def test_changed_capture_or_taking_stamp_and_quantity_reject(self):
  raw=self.trace[self.key]
  for old,new in((b'97337 Mercenaries taking',b'97336 Mercenaries taking'),(b'taking 37 fighters',b'taking 38 fighters'),(b'captured planet Gateway Cache!',b'captured planet Other Cache!')):
   changed=raw.replace(old,new,1);self.assertNotEqual(changed,raw)
   with self.assertRaises(AssertionError):self.sem(trace=changed)

 def test_changed_mine_loss_or_fatal_wording_rejects(self):
  key=('mine-pickup','child-1');raw=self.trace[key];changed=raw.replace(b'Lost a total of 712',b'Lost a total of 713',1)
  with self.assertRaises(AssertionError):self.sem(key,trace=changed)
  key=('fatal-before-pickup','child-1');changed=self.trace[key].replace(b'The mercenariers were killed!',b'The Mercenaries were killed!',1)
  with self.assertRaises(AssertionError):self.sem(key,trace=changed)

 def test_console_public_capture_and_outcome_order_cannot_disagree(self):
  out=dict(self.rows[self.key]['after']);out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(b'taking 37 fighters',b'taking 38 fighters',1)
  with self.assertRaises(AssertionError):self.sem(out=out)

 def test_gateway_stock_and_title_cannot_be_forged(self):
  for offset,value in((129,1),(73,-2),(117,1)):
   out=dict(self.rows[self.key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],4054,offset,value)
   with self.assertRaises(AssertionError):self.sem(out=out)

 def test_score_and_inactive_human_records_bind_saved_state(self):
  out=dict(self.rows[self.key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],2,77,1)
  with self.assertRaises(AssertionError):self.sem(out=out)
  out=dict(self.rows[self.key]['after']);out['YTSCORE.ASC']=out['YTSCORE.ASC'].replace(b'9,737,400',b'9,737,401');self.assertNotEqual(out['YTSCORE.ASC'],self.rows[self.key]['after']['YTSCORE.ASC'])
  with self.assertRaises(AssertionError):self.sem(out=out)

 def test_changed_loaded_observer_or_guest_identity_rejects(self):
  for change in(lambda f,m:(f/'loaded-observer.js').write_text((f/'loaded-observer.js').read_text()+'//fake'),lambda f,m:m['guests'].update(**{'YTMAINT.EXE':'0'*64})):
   with self.assertRaises(AssertionError):self.case(self.modified(change))

 def test_rebound_cpu_request_and_actual_clock_reject(self):
  def actual(f,m):
   p=f/'DOSTIME.LOG';p.write_bytes(re.sub(rb'Current time: [^\r]+',b'Current time: 0:00:09.98am',p.read_bytes(),count=1))
  with self.assertRaises(AssertionError):self.case(self.modified(actual))
  def cpu(f,m):
   a=json.loads((f/'launch.json').read_text());a[a.index('cpu_cycles=200000')]='cpu_cycles=100000';m['argv']=a;(f/'launch.json').write_text(json.dumps(a))
  with self.assertRaises(AssertionError):self.case(self.modified(cpu))

 def test_forced_return_missing_witness_and_forged_pin_reject(self):
  def forced(f,m):
   c=json.loads((f/'controller.json').read_text());c['forced']=True;m['controller']=c;(f/'controller.json').write_text(json.dumps(c))
  with self.assertRaises(AssertionError):self.case(self.modified(forced))
  with self.assertRaises(AssertionError):self.case(self.modified(lambda f,m:(f/'RETURN.LOG').unlink()))
  with tempfile.TemporaryDirectory()as tmp:
   (Path(tmp)/'pins.json').write_text('{"files":{}}')
   with self.assertRaises(AssertionError):v.verify(Path(tmp))

if __name__=='__main__':unittest.main()
