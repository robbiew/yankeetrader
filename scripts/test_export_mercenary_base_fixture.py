"""Protect inherited base bytes, raw constants and independently modeled handoffs."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import export_mercenary_base_fixture as e
class BaseExport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.expected=e.build()
 def test_complete_native_fixture(self):
  self.assertEqual(json.loads(e.FIXTURE.read_text()),self.expected);self.assertEqual(len(self.expected['cases']),29)
  for c in self.expected['cases']:
   record=bytes.fromhex(c['record_hex']);self.assertEqual(len(record),137)
   for o in(57,61,65,69):self.assertEqual(record[o:o+4],bytes.fromhex('0000a000'))
   self.assertEqual(record[125:129],bytes.fromhex('00003e00'))
 def reject(self,change):
  d=copy.deepcopy(self.expected);change(d)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
   with patch.object(e,'build',return_value=self.expected):
    with self.assertRaisesRegex(AssertionError,'portable base fixture'):e.check(p)
 def test_prefix_clock_native_and_source_corruption(self):
  for f,v in(('state',0),('final_state',0),('seeded_state',0),('timer_hex','ffffffff'),('day',0),('sector',0),('record_hex','00'*137),('link_hex','00000000')):
   self.reject(lambda d,f=f,v=v:d['cases'][0].__setitem__(f,v))
  self.reject(lambda d:d['cases'].pop());self.reject(lambda d:d['cases'].append(copy.deepcopy(d['cases'][0])))
  self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))));self.reject(lambda d:d['excluded_later_encounters'].clear())
 def test_inheritance_and_raw_reseed(self):
  before=bytearray(4151*137);before[4149*137+133:4150*137]=b'abcd'
  a=e.synthesize(before,1,bytes(4),5);b=e.synthesize(before,1,bytes.fromhex('01000000'),5)
  self.assertEqual(a[0][133:],b'abcd');self.assertNotEqual(a[2:],b[2:])
if __name__=='__main__':unittest.main()
