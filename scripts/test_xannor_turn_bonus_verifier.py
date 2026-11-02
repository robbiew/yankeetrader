"""Reject rehashed turn awards or reports that disagree with the DOS control."""
import gzip,json,shutil,tempfile,unittest
from pathlib import Path
import verify_xannor_turn_bonus as verify

class CorruptionControls(unittest.TestCase):
 def test_rehashed_corruptions(self):
  for mode in ['missing-turns','false-bonus','missing-casualties','native','missing-return','missing-normal-return','human-surrender']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'evidence';shutil.copytree(verify.DEFAULT,root)
    if mode=='native':
     p=root/'rea.json';b=json.loads(p.read_text());r=next(r for r in b['records'] if r['normalized_result']['address']=='0x11028');r['normalized_result']['bytes_hex']='00'+r['normalized_result']['bytes_hex'][2:];p.write_text(json.dumps(b))
    else:
     case=root/'dos'/('kills-200' if mode in ['missing-turns','missing-return','missing-normal-return'] else 'at-cap' if mode=='false-bonus' else 'player-defense' if mode=='human-surrender' else 'partial-escape')
     if mode=='missing-return':
      p=case/'RETURN.LOG';p.write_bytes(b'')
     elif mode=='missing-normal-return':
      p=case/'game.log.gz';raw=gzip.decompress(p.read_bytes()).replace(b'Returning to Yankee Trader Local Logon Program...',b'Never returned normally')
      p.write_bytes(gzip.compress(raw,mtime=0));(case/'transcript.txt').write_text(raw.decode('cp437').replace('\r\n','\n'))
     elif mode=='missing-turns':
      p=case/'after.dat.gz';world=bytearray(gzip.decompress(p.read_bytes()));verify.v.put(world,2,49,100);p.write_bytes(gzip.compress(world,mtime=0))
     else:
      p=case/'sidefiles.json.gz';b=json.loads(gzip.decompress(p.read_bytes()));key=next(k for k in b if k.upper()=='YTNEWS.DAT');news=bytes.fromhex(b[key]['hex'])
      if mode=='false-bonus':news=news.rstrip(b'\x1a')+b'Q  collected 1 turns bonus for destroying 1000 Xannor!!\r\n\x1a'
      elif mode=='human-surrender':news=news.replace(b'Q  destroyed 400 fighters belonging to Enemy',b'400 fighters in sector 100 surrendered to Q')
      else:news=news.replace(b'destroyed 1504 fighters',b'destroyed 999 fighters')
      b[key]['hex']=news.hex();b[key]['after_sha256']=verify.SHA(news);p.write_bytes(gzip.compress(json.dumps(b).encode(),mtime=0))
     result=case/'result.json';b=json.loads(result.read_text());b['files'][p.name]=verify.SHA(p.read_bytes())
     if mode=='missing-normal-return':b['files']['transcript.txt']=verify.SHA((case/'transcript.txt').read_bytes())
     result.write_text(json.dumps(b))
    with self.assertRaises(AssertionError):verify.check(root)
if __name__=='__main__':unittest.main()
