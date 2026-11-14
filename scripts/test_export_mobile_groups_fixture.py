"""Protect portable native inventories, helper schedules and phase boundaries."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import export_mobile_groups_fixture as e
class MobileExport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.expected=e.build()
 def test_native_inventory_and_scope(self):
  self.assertEqual(json.loads(e.FIXTURE.read_text()),self.expected)
  self.assertEqual(len(self.expected['cases']),29)
  self.assertEqual(self.expected['excluded_later_encounters'],list(e.EXCLUDED))
  for c in self.expected['cases']:
   self.assertEqual(len(c['helper_one']),39);self.assertEqual(len(c['helper_two']),19)
   self.assertEqual(len(c['groups']),20);self.assertEqual(sum(g['strength']for g in c['groups']),10000)
 def reject(self,change):
  d=copy.deepcopy(self.expected);change(d)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
   with patch.object(e,'build',return_value=self.expected):
    with self.assertRaisesRegex(AssertionError,'portable mobile fixture'):e.check(p)
 def test_clock_native_state_and_inventory_corruption(self):
  for f,v in(('state',0),('final_state',0),('native_sha256','0'*64),('draws',0),('top_fallback',0),('helper_one',[]),('helper_two',[]),('groups',[])):
   self.reject(lambda d,f=f,v=v:d['cases'][0].__setitem__(f,v))
  self.reject(lambda d:d['cases'].pop())
  self.reject(lambda d:d['cases'].append(copy.deepcopy(d['cases'][0])))
  self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
  self.reject(lambda d:d['excluded_later_encounters'].clear())
 def test_projection_covers_all_fields_and_ignores_unrelated_bytes(self):
  b=bytearray(4151*137);baseline=e.projection(b)
  for at in(51*137+81,3050*137+85,3050*137+129,70*137+105):
   b[at]=1;self.assertNotEqual(e.projection(b),baseline);b[at]=0
  b[4150*137+117]=1;self.assertEqual(e.projection(b),baseline)
if __name__=='__main__':unittest.main()
