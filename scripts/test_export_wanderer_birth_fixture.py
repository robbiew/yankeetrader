"""Protect declared exclusions, source clock/RNG inputs and full native records."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import export_wanderer_birth_fixture as e

class WandererBirthExport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.expected=e.build()
 def test_retained_fixture(self):
  self.assertEqual(json.loads(e.FIXTURE.read_text()),self.expected);self.assertEqual(len(self.expected['cases']),29)
  self.assertEqual(tuple(self.expected['excluded_later_encounters']),e.EXCLUDED)
  for c in self.expected['cases']:self.assertEqual(len(bytes.fromhex(c['record_hex'])),137)
 def reject(self,change):
  d=copy.deepcopy(self.expected);change(d)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
   with patch.object(e,'build',return_value=self.expected):
    with self.assertRaisesRegex(AssertionError,'portable birth fixture'):e.check(p)
 def test_input_and_model_corruption(self):
  for field,value in(('initial_state',0),('timer_hex','ffffffff'),('day',0),('sector',0),('final_state',0),('seeded_state',0),('before_sha256','0'*64)):
   self.reject(lambda d,f=field,v=value:d['cases'][0].__setitem__(f,v))
 def test_native_and_inventory_corruption(self):
  self.reject(lambda d:d['cases'][0].__setitem__('record_hex','00'*137))
  self.reject(lambda d:d['cases'][0].__setitem__('link_hex','00000000'))
  self.reject(lambda d:d['cases'].pop())
  self.reject(lambda d:d['excluded_later_encounters'].pop())
  self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))

if __name__=='__main__':unittest.main()
