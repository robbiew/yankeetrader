import base64,copy,gzip,json,unittest
from pathlib import Path
from unittest.mock import patch
import export_evolved_occupied_chain_fixture as e
class EvolvedOccupiedChainFixture(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.expected=e.check()
 def reject(self,change):
  d=copy.deepcopy(self.expected);change(d)
  with self.assertRaises(AssertionError):e.validate(d,self.expected)
 def test_original_only_inventory_and_complete_receipts(self):
  self.assertEqual(len(self.expected['cases']),12)
  self.assertEqual(sum(len(c['days'])for c in self.expected['cases']),36)
  refs={h for c in self.expected['cases']for h in c['initial_files'].values()}
  self.assertEqual(refs,set(self.expected['worlds']),'only original before bytes are portable synthesis inputs')
  self.reject(lambda d:d['cases'].pop())
  self.reject(lambda d:d['cases'][0]['days'].pop())
  for key,value in [('day',310),('startup_state',1<<24),('final_state',0),('routing_final_state',0)]:
   self.reject(lambda d,k=key,v=value:d['cases'][0]['days'][2].__setitem__(k,v))
  self.reject(lambda d:d['cases'][0]['days'][2]['ports']['timers'].__setitem__(999,'00000000'))
  self.reject(lambda d:d['cases'][0]['days'][2]['reports'].__setitem__('score_date','2026-11-02'))
  self.reject(lambda d:d['cases'][0]['days'][2]['expected_files'].__setitem__('YTNEWS.DAT','0'*64))
  self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
  self.reject(lambda d:d.__setitem__('native_rng_witnesses',0))
 def test_compression_transport_and_initial_byte_corruption(self):
  d=copy.deepcopy(self.expected);key=next(iter(d['worlds']));raw=gzip.decompress(base64.b64decode(d['worlds'][key]))
  d['worlds'][key]=base64.b64encode(gzip.compress(raw,mtime=17)).decode();e.validate(d,self.expected)
  raw=bytearray(raw);raw[-1]^=1;d['worlds'][key]=e.PACK(raw)
  with self.assertRaises(AssertionError):e.validate(d,self.expected)
 def test_whole_prediction_precedes_child_targets(self):
  real=e.chain.synthesize_chain;read=Path.read_bytes;complete=[];targets=[]
  def synth(*args):v=real(*args);complete.append(1);return v
  def guarded(path):
   if e.chain.DEFAULT in path.parents:
    self.assertFalse(path.name.startswith('before-'),'captured child before worlds cannot enter composition')
    if path.name.startswith('after-'):
     self.assertEqual(len(complete),len(targets)//72+1);targets.append(path)
   return read(path)
  with patch.object(e.native,'verify'),patch.object(e.chain,'synthesize_chain',synth),patch.object(Path,'read_bytes',guarded):e.validate(e.build(),self.expected)
  self.assertEqual((len(complete),len(targets)),(12,864))
 def test_corrupt_native_file_cannot_correct_model(self):
  read=Path.read_bytes
  def changed(path):
   raw=read(path)
   if e.chain.DEFAULT in path.parents and path.name=='after-YTDATA.DAT.gz':
    w=bytearray(gzip.decompress(raw));w[-1]^=1;return gzip.compress(w,mtime=0)
   return raw
  with patch.object(e.native,'verify'),patch.object(Path,'read_bytes',changed):
   with self.assertRaises((ValueError,AssertionError)):e.build()
 def test_poisoned_rng_witnesses_do_not_seed_chain(self):
  read=Path.read_bytes;extract=e.chain.inputs_from_observation;inputs=[]
  def capture(ob):v=extract(ob);inputs.append(v);return v
  def changed(path):
   raw=read(path)
   if e.chain.DEFAULT in path.parents and path.name=='host-time.json.gz':
    ob=json.loads(gzip.decompress(raw))
    for row in ob['events']:
     for side in ('before','after'):row[side]['rng_raw']='00000000'
    return gzip.compress(json.dumps(ob).encode(),mtime=0)
   return raw
  with patch.object(e.native,'verify'),patch.object(Path,'read_bytes',changed),patch.object(e.chain,'inputs_from_observation',capture):
   with self.assertRaises((ValueError,AssertionError)):e.build()
  self.assertEqual(len(inputs),3)
if __name__=='__main__':unittest.main()
