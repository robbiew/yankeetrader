"""Reject stale schedules, incomplete field oracles and mixed source identities."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import export_inactive_rank_fixture as e

class InactiveRankExport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.expected=e.build()
 def test_fixture_and_complete_fields(self):
  self.assertEqual(json.loads(e.FIXTURE.read_text()),self.expected)
  self.assertEqual(len(self.expected['cases']),32)
  for c in self.expected['cases']:self.assertEqual(len(bytes.fromhex(c['writes_hex'])),204)
 def reject(self,change):
  d=copy.deepcopy(self.expected);change(d)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
   with patch.object(e,'build',return_value=self.expected):
    with self.assertRaisesRegex(AssertionError,'portable rank fixture'):e.check(p)
 def test_field_day_and_before_identity(self):
  self.reject(lambda d:d['cases'][0].__setitem__('writes_hex','00'*204))
  self.reject(lambda d:d['cases'][0].__setitem__('final_day',0))
  self.reject(lambda d:d['cases'][0].__setitem__('before_sha256','0'*64))
 def test_control_and_source_inventory(self):
  self.reject(lambda d:d['cases'].pop())
  self.reject(lambda d:d['cases'].append(copy.deepcopy(d['cases'][0])))
  self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))

if __name__=='__main__':unittest.main()
