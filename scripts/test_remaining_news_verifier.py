"""Corruption controls for remaining newspaper evidence, including rehashed files."""
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import verify_remaining_news as verify

class EvidenceControls(unittest.TestCase):
    def test_rehashed_false_registration_and_join_are_rejected(self):
        for mode in ['registration','team-state','native-bytes','source-hash']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)/'evidence';shutil.copytree(verify.DEFAULT,root)
                if mode=='native-bytes':
                    p=root/'rea.json';b=json.loads(p.read_text())
                    record=next(r for r in b['records'] if r['operation']=='read_bytes')
                    record['normalized_result']['bytes_hex']='00'+record['normalized_result']['bytes_hex'][2:]
                    p.write_text(json.dumps(b))
                elif mode=='source-hash':
                    p=root/'sources.json';b=json.loads(p.read_text());b[0]['sha256']='0'*64;p.write_text(json.dumps(b))
                else:
                    case=root/'dos'/('registration' if mode=='registration' else 'team-join')
                    if mode=='registration':
                        p=case/'sidefiles.json.gz';side=json.loads(gzip.decompress(p.read_bytes()))
                        k=next(k for k in side if k.upper()=='YTNEWS.DAT')
                        raw=bytes.fromhex(side[k]['hex']).replace(b'Newsnew  New Player Entered',b'Newsnew  No event produced')
                        side[k]['hex']=raw.hex();side[k]['after_sha256']=verify.SHA(raw)
                        p.write_bytes(gzip.compress(json.dumps(side).encode(),mtime=0))
                    else:
                        p=case/'after.dat.gz';world=bytearray(gzip.decompress(p.read_bytes()));verify.primitive.put(world,2,89,0)
                        p.write_bytes(gzip.compress(world,mtime=0))
                    r=case/'result.json';result=json.loads(r.read_text());result['files'][p.name]=verify.SHA(p.read_bytes());r.write_text(json.dumps(result))
                with self.assertRaises(AssertionError):verify.check(root)

if __name__=='__main__':unittest.main()
