"""Protect source-derived routing, receipt accounting and complete native outputs."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import export_late_clock_fixture as e
class LateExport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.expected=e.build()
 def test_complete_six_file_and_encounter_inventory(self):
  self.assertEqual(json.loads(e.FIXTURE.read_text()),self.expected);self.assertEqual(len(self.expected['cases']),3)
  for c in self.expected['cases']:
   self.assertEqual(len(c['native_files']),6);self.assertEqual([v['group']for v in c['events']],list(range(2,20)))
   self.assertEqual(len(c['helper_two']),19);self.assertIn(len(c['helper_one']),(41,42));self.assertEqual(c['desertion_draws'],2)
   self.assertEqual(sum(g['strength']for g in c['groups'])+sum(v['force']for v in c['events']),10000)
 def reject(self,change):
  d=copy.deepcopy(self.expected);change(d)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
   with patch.object(e,'build',return_value=self.expected):
    with self.assertRaisesRegex(AssertionError,'portable late-clock fixture'):e.check(p)
 def test_clock_routing_receipt_and_native_corruption(self):
  for f,v in(('initial_state',0),('helper_one',[]),('helper_two',[]),('mobile_final_state',0),('final_state',0),('draws',0),('lottery',0),('candidate',99),('desertion_draws',20)):
   self.reject(lambda d,f=f,v=v:d['cases'][0].__setitem__(f,v))
  for f,v in(('state',0),('force',0),('sector',7),('raw_force',0),('rates',[])):
   self.reject(lambda d,f=f,v=v:d['cases'][0]['events'][0].__setitem__(f,v))
  for n in self.expected['cases'][0]['native_files']:
   self.reject(lambda d,n=n:d['cases'][0]['native_files'].__setitem__(n,'0'*64))
  self.reject(lambda d:d['cases'][0]['events'].pop());self.reject(lambda d:d['cases'].pop())
  self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))));self.reject(lambda d:d['before_aux'].clear())
if __name__=='__main__':unittest.main()
