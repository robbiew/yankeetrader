"""Protect independent sampled clocks, before-file inheritance and all six oracles."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import export_initial_aux_fixture as e
class AuxExport(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.expected=e.build()
 def test_complete_six_file_inventory(self):
  self.assertEqual(json.loads(e.FIXTURE.read_text()),self.expected);self.assertEqual(len(self.expected['cases']),29)
  names={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'}
  for c in self.expected['cases']:
   self.assertEqual(set(c['native_files']),names);self.assertIn(c['before_aux'],self.expected['before_aux'])
 def reject(self,change):
  d=copy.deepcopy(self.expected);change(d)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
   with patch.object(e,'build',return_value=self.expected):
    with self.assertRaisesRegex(AssertionError,'portable auxiliary fixture'):e.check(p)
 def test_calendar_native_source_and_before_corruption(self):
  for f,v in(('news_date','2026-01-01'),('score_date','2026-01-01'),('news_clock','99:00:00'),('score_clock','99:00:00'),('before_aux','0'*64)):
   self.reject(lambda d,f=f,v=v:d['cases'][0].__setitem__(f,v))
  for n in self.expected['cases'][0]['native_files']:
   self.reject(lambda d,n=n:d['cases'][0]['native_files'].__setitem__(n,'0'*64))
  self.reject(lambda d:d['cases'].pop());self.reject(lambda d:d['cases'].append(copy.deepcopy(d['cases'][0])))
  self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))));self.reject(lambda d:d['before_aux'].clear())
  self.reject(lambda d:d['excluded_later_encounters'].clear())
if __name__=='__main__':unittest.main()
