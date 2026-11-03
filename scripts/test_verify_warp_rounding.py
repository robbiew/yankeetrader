"""Independent semantic corruption tests for retained shortcut rounding controls."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rounding_checker',ROOT/'scripts/verify_warp_rounding.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
SOURCE=ROOT/'research/yt-warp-generation/rounding-dos'


class ShortcutRoundingEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.capture=Path(self.temporary.name)/'capture';shutil.copytree(SOURCE,self.capture)

    def rehash(self,name,filename):
        d=self.capture/name;meta=json.loads((d/'result.json').read_text())
        meta['files'][filename]=hashlib.sha256((d/filename).read_bytes()).hexdigest()
        (d/'result.json').write_text(json.dumps(meta))

    def mutate_world(self,name,edit):
        d=self.capture/name;path=d/'before-maint.dat.gz'
        raw=bytearray(gzip.decompress(path.read_bytes()));edit(raw)
        path.write_bytes(gzip.compress(raw,mtime=0));self.rehash(name,path.name)

    def reject(self,baseline=None):
        with self.assertRaises((AssertionError,ValueError,KeyError)):
            checker.verify(self.capture,baseline)

    def test_original_controls(self):
        observed=checker.verify(self.capture)
        self.assertEqual([(row['index_value'],row['changed_sector'])for row in observed],
                         [(100.0,100),(100.25,100),(100.5,101),(100.75,101),(101.5,102)])

    def test_rehashed_floor_claim(self):
        def edit(raw):
            checker.mbf.put(raw,51+101,61,0);checker.mbf.put(raw,51+100,61,1)
        self.mutate_world('fraction-100-75',edit);self.reject()

    def test_rehashed_ties_even_claim(self):
        def edit(raw):
            checker.mbf.put(raw,51+101,61,0);checker.mbf.put(raw,51+100,61,1)
        self.mutate_world('tie-100-5',edit);self.reject()

    def test_rehashed_extra_warp_mutation(self):
        self.mutate_world('integer-100',lambda raw:checker.mbf.put(raw,51+95,61,1));self.reject()

    def test_rehashed_first_five_mutation(self):
        self.mutate_world('integer-100',lambda raw:checker.mbf.put(raw,51+100,41,1234));self.reject()

    def test_changed_patch_manifest(self):
        path=self.capture/'integer-100/result.json';meta=json.loads(path.read_text())
        meta['patches'][0]['after']='e98002';path.write_text(json.dumps(meta));self.reject()

    def test_rehashed_missing_normal_return(self):
        d=self.capture/'integer-100';path=d/'INIT.LOG'
        path.write_bytes(path.read_bytes().replace(b'<YT-INIT Normal Termination>',b'<INCOMPLETE INITIALIZER>'))
        self.rehash(d.name,path.name);self.reject()

    def test_missing_case(self):
        shutil.rmtree(self.capture/'tie-101-5');self.reject()

    def test_changed_reference_world(self):
        path=Path(self.temporary.name)/'baseline.dat.gz'
        raw=bytearray(gzip.decompress((ROOT/'research/yt-warp-generation/dos/repair-only/before-maint.dat.gz').read_bytes()))
        raw[700]^=1;path.write_bytes(gzip.compress(raw,mtime=0));self.reject(path)

    def test_rehashed_calendar_evidence(self):
        d=self.capture/'integer-100';path=d/'DOSDATE.LOG'
        path.write_bytes(path.read_bytes().replace(b'11/02/2026',b'08/02/2026'))
        self.rehash(d.name,path.name);self.reject()

    def test_uncontrolled_calendar(self):
        path=self.capture/'integer-100/result.json';meta=json.loads(path.read_text())
        meta['date']='08/02/2026';path.write_text(json.dumps(meta));self.reject()


if __name__=='__main__':unittest.main()
