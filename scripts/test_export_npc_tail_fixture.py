"""Protect both lottery branches and complete native world oracle inventory."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import export_npc_tail_fixture as e
class TailExport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.expected=e.build()
 def test_complete_fixture_and_conditional_inventory(self):
  self.assertEqual(json.loads(e.FIXTURE.read_text()),self.expected);self.assertEqual(len(self.expected['cases']),29)
  branches=set()
  for c in self.expected['cases']:
   selected=c['lottery']>=.5;branches.add(selected);self.assertEqual(c['candidate_timer']is not None,selected);self.assertEqual(c['draws'],21+selected)
   self.assertEqual(c['candidate']!=0,selected);self.assertEqual(len(c['native_world_sha256']),64)
  self.assertEqual(branches,{False,True})
 def reject(self,change):
  d=copy.deepcopy(self.expected);change(d)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
   with patch.object(e,'build',return_value=self.expected):
    with self.assertRaisesRegex(AssertionError,'portable tail fixture'):e.check(p)
 def test_state_clock_native_and_source_corruption(self):
  for f,v in(('state',0),('final_state',0),('lottery',0),('candidate',99),('candidate_timer','ffffffff'),('draws',0),('final_day',0),('native_world_sha256','0'*64)):
   self.reject(lambda d,f=f,v=v:d['cases'][0].__setitem__(f,v))
  self.reject(lambda d:d['cases'].pop());self.reject(lambda d:d['cases'].append(copy.deepcopy(d['cases'][0])))
  self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))));self.reject(lambda d:d['excluded_later_encounters'].clear())
if __name__=='__main__':unittest.main()
