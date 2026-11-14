"""Protect modeled step chains, raw input prefixes and native final records."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import export_wanderer_assault_fixture as e
class AssaultExport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.expected=e.build()
 def test_native_chains_and_step_inventory(self):
  self.assertEqual(json.loads(e.FIXTURE.read_text()),self.expected);self.assertEqual(len(self.expected['cases']),3)
  for c in self.expected['cases']:
   self.assertEqual(len(c['events']),18);self.assertEqual([v['group']for v in c['events']],list(range(2,20)))
   self.assertEqual(c['events'][-1]['record_hex'],c['native_record_hex']);self.assertIn(c['before_sha256'],self.expected['worlds'])
 def reject(self,change):
  d=copy.deepcopy(self.expected);change(d)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
   with patch.object(e,'build',return_value=self.expected):
    with self.assertRaisesRegex(AssertionError,'portable assault fixture'):e.check(p)
 def test_model_native_source_and_prefix_corruption(self):
  for f,v in(('group',1),('sector',0),('force',0),('state',0),('draws',0),('raw_force',0),('final_state',0),('record_hex','00'*137)):
   self.reject(lambda d,f=f,v=v:d['cases'][0]['events'][0].__setitem__(f,v))
  self.reject(lambda d:d['cases'][0]['events'].pop());self.reject(lambda d:d['cases'][0].__setitem__('native_record_hex','00'*137))
  self.reject(lambda d:d['cases'].pop());self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))));self.reject(lambda d:d['worlds'].clear())
if __name__=='__main__':unittest.main()
