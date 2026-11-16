"""Protect fixture reuse and separation of input recipes from native oracles."""
import hashlib,json,tempfile,unittest
from pathlib import Path
import export_replay_cli_recipes as e
class RecipeExport(unittest.TestCase):
 def test_complete_input_inventory_and_no_targets_in_recipes(self):
  rows=e.build();self.assertEqual(len(rows),32);self.assertEqual(sum(r['recipe']['profile']=='initial'for r in rows),29)
  for row in rows:
   d=row['recipe'];self.assertEqual(set(d),{'format','profile','name','before_sha256','source_sha256','recipe'})
   self.assertEqual(set(d['before_sha256']),{'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT'})
   self.assertEqual(len(d['recipe']['ports']['timer_minutes']),1000);self.assertEqual(len(d['recipe']['helper_two']),19)
   self.assertIn(len(d['recipe']['helper_one']),(41,42));self.assertEqual(d['source_sha256']['archive/dos-original/YTMAINT.EXE'],e.ORIGINAL)
   for n,b in row['before'].items():self.assertEqual(hashlib.sha256(b).hexdigest(),d['before_sha256'][n])
   self.assertNotIn('native_files',json.dumps(d));self.assertEqual(len(row['oracles']['native_files']),6)
 def test_export_never_reuses_existing_directory(self):
  with tempfile.TemporaryDirectory()as tmp:
   out=Path(tmp)/'cases';self.assertEqual(e.export(out),32)
   first=out/'matrix-late-observed-a'/'recipe.json';saved=first.read_bytes()
   with self.assertRaises(FileExistsError):e.export(out)
   self.assertEqual(first.read_bytes(),saved);self.assertTrue((out/'matrix-late-observed-a'/'oracles.json').exists())
if __name__=='__main__':unittest.main()
