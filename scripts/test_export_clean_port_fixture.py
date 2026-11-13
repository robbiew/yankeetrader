"""Protect before-only inputs, complete native byte oracles and portable export."""
import base64,copy,gzip,json,unittest
from unittest.mock import patch
import export_clean_port_fixture as e

class CleanPortExport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.expected=e.build()
 def reject(self,change):
  d=copy.deepcopy(self.expected);change(d)
  with self.assertRaises(AssertionError):e.validate(d,self.expected)
 def test_retained_fixture(self):
  e.validate(json.loads(e.FIXTURE.read_text()),self.expected)
  self.assertEqual(len(self.expected['cases']),32);self.assertEqual(sum(not c['capped']for c in self.expected['cases']),8)
 def test_clock_calendar_and_mode_corruption(self):
  for field,value in(('capped',True),('expected_sha256','0'*64),('before_sha256','0'*64),('class_counts',[0,0,1000])):
   self.reject(lambda d,f=field,v=value:d['cases'][0].__setitem__(f,v))
  self.reject(lambda d:d['cases'][0]['days'].__setitem__(999,0))
  self.reject(lambda d:d['cases'][0]['timer_minutes'].__setitem__(999,'ffffffff'))
 def test_every_native_record_has_an_oracle(self):
  for c in self.expected['cases']:
   raw=gzip.decompress(base64.b64decode(c['expected_gzip']));self.assertEqual(len(raw),137000);self.assertEqual(e.SHA(raw),c['expected_sha256'])
  def bad(d):
   r=d['cases'][0];raw=bytearray(gzip.decompress(base64.b64decode(r['expected_gzip'])));raw[-1]^=1;r['expected_gzip']=e.packed(raw);r['expected_sha256']=e.SHA(raw)
  self.reject(bad)
 def test_before_bytes_cannot_be_replaced(self):
  def bad(d):
   key=next(iter(d['worlds']));raw=bytearray(gzip.decompress(base64.b64decode(d['worlds'][key])));raw[0]^=1;d['worlds'][key]=e.packed(raw)
  self.reject(bad)
 def test_sources_inventory_and_duplicate_controls(self):
  self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
  self.reject(lambda d:d['cases'].pop())
  self.reject(lambda d:d['cases'].append(copy.deepcopy(d['cases'][0])))
 def test_compression_container_is_not_native_evidence(self):
  d=copy.deepcopy(self.expected);key=next(iter(d['worlds']));raw=gzip.decompress(base64.b64decode(d['worlds'][key]));d['worlds'][key]=base64.b64encode(gzip.compress(raw,mtime=17)).decode();e.validate(d,self.expected)
 def test_target_opens_only_after_synthesis(self):
  events=[]
  def model(*args):events.append('synthesis');return bytes(137000),dict(class_counts=[0,0,1000])
  def target():self.assertEqual(events,['synthesis']);events.append('oracle');return bytes(e.START+e.SIZE)
  with patch.object(e,'replay_ports',model):e.case(b'before',[1]*1000,[bytes(4)]*1000,False,target)
  self.assertEqual(events,['synthesis','oracle'])
 def test_mismatched_native_target_cannot_be_masked(self):
  with patch.object(e,'replay_ports',return_value=(bytes(137000),dict(class_counts=[0,0,1000]))):
   with self.assertRaises(AssertionError):e.case(b'before',[1]*1000,[bytes(4)]*1000,False,lambda:bytes(e.START)+b'X'+bytes(e.SIZE-1))

if __name__=='__main__':unittest.main()
