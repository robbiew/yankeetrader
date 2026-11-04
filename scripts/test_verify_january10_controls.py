"""Rehashed changes cannot redefine the retained native January observations."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_january10_controls import ROOT, verify

SOURCE=ROOT/'research/yt-initializer-replay/january10-controls'

class January10ControlsTests(unittest.TestCase):
    def change(self,name,filename,transform,group='world-dos'):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'controls';shutil.copytree(SOURCE,target)
            d=target/group/name;p=d/filename;p.write_bytes(transform(p.read_bytes()))
            meta=json.loads((d/'result.json').read_text());meta['files'][filename]=hashlib.sha256(p.read_bytes()).hexdigest()
            if filename=='before-maint.dat.gz':meta['world_sha256']=hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest()
            (d/'result.json').write_text(json.dumps(meta))
            with self.assertRaises((AssertionError,ValueError)):verify(target)

    def test_native_years_neighbors_and_repeat(self):
        controls=verify();self.assertEqual(len(controls),10)
        self.assertEqual({c['seed'] for c in controls.values()},{0xc805})

    def test_rehashed_zero_normalization_and_wrong_class(self):
        for year in (2026,2027,2028):
            for value in (bytes(4),bytes.fromhex('00004000')):
                with self.subTest(year=year,value=value):
                    def normalize(raw):
                        w=bytearray(gzip.decompress(raw));w[3051*137+45:3051*137+49]=value;return gzip.compress(w,mtime=0)
                    self.change(f'jan10-{year}','before-maint.dat.gz',normalize)

    def test_rehashed_clock_return_and_seed(self):
        self.change('jan10-2027','DOSDATE.LOG',lambda b:b.replace(b'01/10/2027',b'01/11/2027'))
        self.change('jan10-2027','INITRET.LOG',lambda b:b.replace(b'INITIALIZER_RETURNED',b'NOT_RETURNED'))
        self.change('jan10-2027','TRACE.BIN',lambda b:b[:16]+bytes([b[16]^1])+b[17:],group='seed-dos')

    def test_missing_neighbor_or_repeat(self):
        for case in ('jan09-2026','jan10-2027-repeat'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as tmp:
                target=Path(tmp)/'controls';shutil.copytree(SOURCE,target);shutil.rmtree(target/'world-dos'/case)
                with self.assertRaises(AssertionError):verify(target)

if __name__=='__main__':unittest.main()
