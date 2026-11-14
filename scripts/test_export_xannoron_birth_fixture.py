"""Protect raw creation timestamps, modeled prefixes and complete native oracles."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import export_xannoron_birth_fixture as e

class XannoronExport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.expected=e.build()
 def test_complete_native_fixture(self):
  self.assertEqual(json.loads(e.FIXTURE.read_text()),self.expected);self.assertEqual(len(self.expected['cases']),32)
  for c in self.expected['cases']:self.assertEqual(len(bytes.fromhex(c['record_hex'])),137)
 def reject(self,change):
  d=copy.deepcopy(self.expected);change(d)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
   with patch.object(e,'build',return_value=self.expected):
    with self.assertRaisesRegex(AssertionError,'portable Xannoron fixture'):e.check(p)
 def test_prefix_clock_state_and_numeric_fields(self):
  for field,value in(('initial_state',0),('wanderer_timer','ffffffff'),('wanderer_day',0),('state',0),('day',0),('timer_hex','ffffffff'),('bank_hex','00000000'),('ground',0),('timestamp_hex','00000000'),('final_state',0),('hq',0),('before_sha256','0'*64)):
   self.reject(lambda d,f=field,v=value:d['cases'][0].__setitem__(f,v))
 def test_native_and_source_inventory(self):
  self.reject(lambda d:d['cases'][0].__setitem__('record_hex','00'*137))
  self.reject(lambda d:d['cases'][0].__setitem__('link_hex','00000000'))
  self.reject(lambda d:d['cases'].pop())
  self.reject(lambda d:d['cases'].append(copy.deepcopy(d['cases'][0])))
  self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
 def test_nonzero_timer_scope_and_residue(self):
  for c in self.expected['cases']:
   self.assertTrue(any(bytes.fromhex(c['timer_hex'])))
   if bytes.fromhex(c['timestamp_hex'])[3]==0:self.assertNotEqual(c['timestamp_hex'],'00000000')
  with self.assertRaises(AssertionError):e.synthesize(bytes(4151*137),1,bytes(4),5)

if __name__=='__main__':unittest.main()
