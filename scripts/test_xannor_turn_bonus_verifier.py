"""Reject rehashed turn awards or reports that disagree with the DOS control."""
import gzip,json,shutil,tempfile,unittest
from pathlib import Path
import verify_xannor_turn_bonus as verify

class CorruptionControls(unittest.TestCase):
 def test_rehashed_corruptions(self):
  for mode in ['missing-turns','false-bonus','missing-casualties','native']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'evidence';shutil.copytree(verify.DEFAULT,root)
    if mode=='native':
     p=root/'rea.json';b=json.loads(p.read_text());r=next(r for r in b['records'] if r['normalized_result']['address']=='0x11028');r['normalized_result']['bytes_hex']='00'+r['normalized_result']['bytes_hex'][2:];p.write_text(json.dumps(b))
    else:
     case=root/'dos'/('kills-200' if mode=='missing-turns' else 'at-cap' if mode=='false-bonus' else 'partial-escape')
     if mode=='missing-turns':
      p=case/'after.dat.gz';world=bytearray(gzip.decompress(p.read_bytes()));verify.v.put(world,2,49,100);p.write_bytes(gzip.compress(world,mtime=0))
     else:
      p=case/'sidefiles.json.gz';b=json.loads(gzip.decompress(p.read_bytes()));key=next(k for k in b if k.upper()=='YTNEWS.DAT');news=bytes.fromhex(b[key]['hex'])
      if mode=='false-bonus':news=news.rstrip(b'\x1a')+b'Q  collected 1 turns bonus for destroying 1000 Xannor!!\r\n\x1a'
      else:news=news.replace(b'destroyed 1504 fighters',b'destroyed 999 fighters')
      b[key]['hex']=news.hex();b[key]['after_sha256']=verify.SHA(news);p.write_bytes(gzip.compress(json.dumps(b).encode(),mtime=0))
     result=case/'result.json';b=json.loads(result.read_text());b['files'][p.name]=verify.SHA(p.read_bytes());result.write_text(json.dumps(b))
    with self.assertRaises(AssertionError):verify.check(root)
if __name__=='__main__':unittest.main()
